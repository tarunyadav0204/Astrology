import argparse
import copy
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("deploy_mig", SCRIPTS / "deploy_mig.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def state():
    group = {"status": {"isStable": True}, "targetSize": 2, "instanceTemplate": "new"}
    instances = [dict(instance=f"https://compute/instances/vm-{i}", id=str(i), currentAction="NONE",
                      instanceStatus="RUNNING", instanceHealth=[{"detailedHealthState": "HEALTHY"}],
                      version={"instanceTemplate": "old"}) for i in range(2)]
    backends = [{"status": {"healthStatus": [dict(instance=vm["instance"], healthState="HEALTHY")
                                            for vm in instances]}}]
    return group, instances, backends


class HealthTests(unittest.TestCase):
    def test_all_health_sources_required(self):
        group, instances, backends = state()
        self.assertTrue(m.ready_instances(group, instances, backends, 2))
        for change in ("repair", "missing_health", "lb_unknown", "singleton", "unstable"):
            g, v, b = copy.deepcopy((group, instances, backends))
            if change == "repair": v[0]["currentAction"] = "RECREATING"
            if change == "missing_health": v[0]["instanceHealth"] = []
            if change == "lb_unknown": b[0]["status"]["healthStatus"][0]["healthState"] = "UNKNOWN"
            if change == "singleton": g["targetSize"] = 1; v.pop()
            if change == "unstable": g["status"]["isStable"] = False
            with self.subTest(change=change):
                self.assertFalse(m.ready_instances(g, v, b, 2))


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.d = m.Deployment(argparse.Namespace(project="test", zone="test-b", mig="test-mig",
                             backend_service="backend", commit="a" * 40, template="new",
                             health_timeout=60, soak_seconds=0))
        self.group, self.instances, self.backends = state()

    def fake_live(self):
        self.d.safe_policy = Mock()
        self.d.wait_ready = Mock(return_value=(self.group, self.instances))
        self.d.ssh = Mock(return_value="b" * 40)
        self.d.deploy_instance = Mock()

    def test_failed_restart_rolls_back_and_does_not_touch_next_vm(self):
        self.fake_live()
        self.d.deploy_instance.side_effect = [subprocess.CalledProcessError(1, "ssh"), None]
        with self.assertRaisesRegex(m.DeploymentError, "restored"):
            self.d.live()
        self.assertEqual(self.d.deploy_instance.call_args_list,
                         [unittest.mock.call("vm-0", "a" * 40),
                          unittest.mock.call("vm-0", "b" * 40, rollback=True)])

    def test_lb_failure_after_successful_deploy_also_rolls_back(self):
        self.fake_live()
        healthy = (self.group, self.instances)
        self.d.wait_ready.side_effect = [healthy, m.DeploymentError("LB unhealthy"), healthy]
        with self.assertRaisesRegex(m.DeploymentError, "restored"):
            self.d.live()
        self.assertEqual(self.d.deploy_instance.call_count, 2)
        self.assertTrue(self.d.deploy_instance.call_args.kwargs["rollback"])

    def test_rollback_failure_stops_without_next_vm(self):
        self.fake_live()
        self.d.deploy_instance.side_effect = subprocess.CalledProcessError(1, "ssh")
        with self.assertRaises(subprocess.CalledProcessError):
            self.d.live()
        self.assertEqual([c.args[0] for c in self.d.deploy_instance.call_args_list], ["vm-0", "vm-0"])

    def test_membership_change_is_not_skipped(self):
        self.d.state = Mock(return_value=(self.group, self.instances, self.backends))
        with self.assertRaisesRegex(m.DeploymentError, "membership changed"):
            self.d.wait_ready(expected=["vm-0", "vanished"])

    def test_local_database_failure_blocks_even_if_lb_is_healthy(self):
        self.d.state = Mock(return_value=(self.group, self.instances, self.backends))
        self.d.ssh = Mock(side_effect=subprocess.CalledProcessError(22, "curl"))
        self.d.public_health = Mock()
        with patch.object(m.time, "monotonic", side_effect=[0, 1, 2, 2, 70]), patch.object(m.time, "sleep"):
            with self.assertRaisesRegex(m.DeploymentError, "timed out"):
                self.d.wait_ready()
        self.d.public_health.assert_called_once()

    def test_healthy_gate_does_not_repeat_ssh_during_soak(self):
        self.d.args.soak_seconds = 30
        self.d.state = Mock(return_value=(self.group, self.instances, self.backends))
        self.d.ssh = Mock(return_value="")
        self.d.public_health = Mock()
        with patch.object(m.time, "monotonic", side_effect=[0, 1, 2, 2, 12, 12, 33, 33]), patch.object(m.time, "sleep"):
            self.d.wait_ready()
        self.assertEqual(self.d.ssh.call_count, 2)

    def test_live_reuses_previous_post_deploy_gate(self):
        self.fake_live()
        self.d.live()
        self.assertEqual(self.d.wait_ready.call_count, 3)  # Initial + one after each VM.

    def test_diagnostic_names_recreating_vm(self):
        self.group["status"]["isStable"] = False
        self.instances[1]["currentAction"] = "RECREATING"
        issues = m.readiness_issues(self.group, self.instances, self.backends, 2)
        self.assertIn("vm-1: action=RECREATING", issues)
        self.assertFalse(any("load balancer" in s for s in issues))

    def test_aggressive_repair_check_blocks_deploy(self):
        import json
        self.d.mig = Mock()
        health = {"type": "HTTP", "httpHealthCheck": {"port": 8001, "requestPath": "/api/keepalive"},
                  "checkIntervalSec": 10, "unhealthyThreshold": 3}
        with patch.object(m, "run", return_value=json.dumps(health)):
            with self.assertRaisesRegex(m.DeploymentError, "too aggressive"):
                self.d.safe_policy()
        self.d.mig.assert_not_called()

    def test_replacement_failure_restores_template_with_zero_unavailable(self):
        self.d.safe_policy = Mock()
        self.d.wait_ready = Mock(return_value=(self.group, self.instances))
        self.d.mig = Mock(side_effect=["", subprocess.CalledProcessError(1, "wait"), "", ""])
        with self.assertRaisesRegex(m.DeploymentError, "replacement failed"):
            self.d.replace()
        calls = self.d.mig.call_args_list
        self.assertIn("--max-unavailable=0", calls[0].args)
        self.assertIn("--max-surge=1", calls[0].args)
        self.assertIn("--version=template=old", calls[2].args)
        self.assertIn("--max-unavailable=0", calls[2].args)
        self.assertGreaterEqual(self.d.safe_policy.call_count, 3)

    def test_refresh_failure_restores_previous_target_without_rollout(self):
        self.d.safe_policy = Mock()
        self.d.wait_ready = Mock(side_effect=[(self.group, self.instances), m.DeploymentError("health")])
        self.d.mig = Mock()
        self.d.args.template = "candidate"
        with self.assertRaises(m.DeploymentError): self.d.template()
        self.assertEqual(self.d.mig.call_args.args, ("set-instance-template", "--template=new"))
        self.assertFalse(any("rolling-action" in c.args for c in self.d.mig.call_args_list))

    def test_gcloud_rolling_action_argument_order(self):
        with patch.object(m, "run", return_value="") as run:
            self.d.mig("rolling-action", "replace", "--max-unavailable=0")
        self.assertEqual(run.call_args.args[:7],
                         ("gcloud", "compute", "instance-groups", "managed", "rolling-action", "replace", "test-mig"))

    def test_successful_replacement_does_not_redeploy_main_on_new_vms(self):
        self.d.safe_policy = Mock()
        replacements = copy.deepcopy(self.instances)
        for vm in replacements:
            vm["id"] += "new"
            vm["version"]["instanceTemplate"] = "new"
        self.d.wait_ready = Mock(side_effect=[(self.group, self.instances), (self.group, replacements)])
        self.d.mig = Mock()
        self.d.deploy_instance = Mock()
        self.d.replace()
        self.d.deploy_instance.assert_not_called()
        self.assertEqual(self.d.safe_policy.call_count, 2)

    def test_generated_remote_script_is_valid_and_does_not_pass_lock_to_backend(self):
        self.d.ssh = Mock(return_value="")
        self.d.deploy_instance("vm-0", "a" * 40)
        import shlex
        script = shlex.split(self.d.ssh.call_args.args[1])[2]
        subprocess.run(["bash", "-n"], input=script, text=True, check=True)
        self.assertIn('bash "$runner" 9>&-', script)
        self.assertIn("export DEPLOY_COMMIT=" + "a" * 40, script)


class PinnedCommitTests(unittest.TestCase):
    def test_deploy_and_rollback_use_exact_commit_when_main_has_moved(self):
        # Execute the actual git-selection section against a disposable remote.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args, cwd=root):
                return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True).strip()
            git("init", "-b", "main")
            git("config", "user.email", "test@example.com")
            git("config", "user.name", "Deploy Test")
            (root / "value").write_text("first")
            git("add", "."); git("commit", "-m", "first")
            first = git("rev-parse", "HEAD")
            (root / "value").write_text("later")
            git("commit", "-am", "later")
            latest = git("rev-parse", "HEAD")
            checkout = root / "checkout"
            git("clone", str(root), str(checkout))
            script = (SCRIPTS / "deploy-release.sh").read_text().split("# Optional: trigger")[0]
            import os
            for commit in (first, latest, first):
                env = dict(os.environ, APP_ROOT=str(checkout), DEPLOY_COMMIT=commit)
                subprocess.run(["bash", "-c", script], env=env, check=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                self.assertEqual(git("rev-parse", "HEAD", cwd=checkout), commit)


if __name__ == "__main__":
    unittest.main()
