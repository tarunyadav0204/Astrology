#!/usr/bin/env python3
"""Serialized production MIG deployment. No third-party Python dependencies.

Readiness requires a stable group, MIG liveness, LB health, local DB readiness,
and public API readiness. Failed updates stop before touching the next VM.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import threading
import time


class DeploymentError(RuntimeError):
    pass


def run(*args, timeout=120):
    try:
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise DeploymentError(f"{args[0]} timed out after {timeout}s") from None
    if result.returncode:
        print(result.stdout, flush=True)
        # SSH command arguments contain the encoded deployment runner. Avoid
        # dumping that entire payload into a traceback; stderr has the cause.
        raise DeploymentError(f"{args[0]} failed with exit code {result.returncode}")
    return result.stdout.strip()


def readiness_issues(group, instances, backends, minimum):
    """Fail closed on missing/unknown health, membership changes and ongoing repairs."""
    issues = []
    if not group.get("status", {}).get("isStable"):
        issues.append("MIG has an operation in progress")
    if group.get("targetSize", 0) < minimum:
        issues.append(f"requires at least {minimum} servers")
    if len(instances) != group["targetSize"]:
        issues.append("instance count differs from target size")
    healthy = {
        h.get("instance")
        for backend in backends
        for h in backend.get("status", {}).get("healthStatus", [])
        if h.get("healthState") == "HEALTHY"
    }
    for vm in instances:
        name = vm["instance"].rsplit("/", 1)[-1]
        if vm.get("currentAction") != "NONE":
            issues.append(f"{name}: action={vm.get('currentAction', 'unknown')}")
        if vm.get("instanceStatus") != "RUNNING":
            issues.append(f"{name}: status={vm.get('instanceStatus', 'unknown')}")
        health = vm.get("instanceHealth", [])
        if not health or any(h.get("detailedHealthState") != "HEALTHY" for h in health):
            issues.append(f"{name}: auto-repair health=" + ",".join(h.get("detailedHealthState", "unknown") for h in health or [{}]))
        if vm["instance"] not in healthy:
            issues.append(f"{name}: load balancer has not marked it healthy")
    return issues


def ready_instances(group, instances, backends, minimum):
    return not readiness_issues(group, instances, backends, minimum)


class Deployment:
    def __init__(self, args):
        self.args = args
        self.scope = [f"--project={args.project}", f"--zone={args.zone}", "--quiet"]
        self.ssh_key_lock = threading.Lock()

    def mig(self, action, *args):
        if action == "rolling-action":
            return run("gcloud", "compute", "instance-groups", "managed", action, args[0],
                       self.args.mig, *self.scope, *args[1:])
        return run("gcloud", "compute", "instance-groups", "managed", action,
                   self.args.mig, *self.scope, *args, timeout=960 if action in ("wait-until", "update") else 120)

    def state(self):
        group = json.loads(self.mig("describe", "--format=json"))
        instances = json.loads(self.mig("list-instances", "--format=json"))
        backends = json.loads(run("gcloud", "compute", "backend-services", "get-health",
                                 self.args.backend_service, f"--project={self.args.project}",
                                 "--global", "--format=json"))
        return group, instances, backends

    def ssh(self, instance, command, timeout=120):
        # Parallel gcloud calls must not both generate the same fresh runner key.
        key = Path.home() / ".ssh" / "google_compute_engine"
        with self.ssh_key_lock:
            if not key.exists():
                key.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                run("ssh-keygen", "-q", "-t", "rsa", "-b", "3072", "-N", "", "-f", str(key))
        return run("gcloud", "compute", "ssh", f"tarun_yadav@{instance}", *self.scope,
                   "--tunnel-through-iap", f"--ssh-key-file={key}", "--command", command, timeout=timeout)

    def public_health(self):
        run("curl", "--fail", "--silent", "--show-error", "--max-time", "20",
            "https://astroroshni.com/api/health")

    def wait_ready(self, expected=None, minimum=1):
        deadline = time.monotonic() + self.args.health_timeout
        healthy_since = None
        while time.monotonic() < deadline:
            group, instances, backends = self.state()
            names = sorted(vm["instance"].rsplit("/", 1)[-1] for vm in instances)
            if expected is not None and names != expected:
                raise DeploymentError("MIG membership changed during app deployment; stopping")
            issues = readiness_issues(group, instances, backends, minimum)
            if not issues:
                try:
                    self.public_health()
                    if healthy_since is None:
                        healthy_since = time.monotonic()
                    remaining = self.args.soak_seconds - (time.monotonic() - healthy_since)
                    if remaining <= 0:
                        # SSH is expensive over IAP. Check apps once per gate,
                        # in parallel, after the cheap cloud checks have settled.
                        def check_app(name):
                            try:
                                self.ssh(name, "curl -fsS --max-time 10 http://127.0.0.1:8001/api/keepalive >/dev/null && "
                                         "curl -fsS --max-time 10 http://127.0.0.1:8001/api/health >/dev/null")
                            except (subprocess.SubprocessError, DeploymentError) as error:
                                raise DeploymentError(f"{name}: local application readiness failed: {error}") from error
                        with ThreadPoolExecutor(max_workers=min(4, len(names))) as pool:
                            list(pool.map(check_app, names))
                        # A repair may begin during SSH; don't admit stale state.
                        final_group, final_instances, final_backends = self.state()
                        final_names = sorted(vm["instance"].rsplit("/", 1)[-1] for vm in final_instances)
                        issues = readiness_issues(final_group, final_instances, final_backends, minimum)
                        if names != final_names or issues:
                            raise DeploymentError("State changed during app checks: " + "; ".join(issues or ["membership changed"]))
                        print(f"Ready: {self.args.mig}; all servers, LB and app checks passed", flush=True)
                        return final_group, final_instances
                    issues = [f"all cloud/public checks healthy; observing for {remaining:.0f}s more"]
                except (subprocess.SubprocessError, DeploymentError) as error:
                    healthy_since = None
                    issues = [str(error)]
            else:
                healthy_since = None
            print(f"Waiting for {self.args.mig}: {'; '.join(issues)}", flush=True)
            time.sleep(10)
        raise DeploymentError(f"Readiness timed out for {self.args.mig}; no further servers will be updated")

    def safe_policy(self):
        check_name = "astroroshni-autohealing"
        health = json.loads(run("gcloud", "compute", "health-checks", "describe", check_name,
                                f"--project={self.args.project}", "--global", "--format=json"))
        if (health.get("type") != "HTTP" or health.get("httpHealthCheck", {}).get("port") != 8001
                or health.get("httpHealthCheck", {}).get("requestPath") != "/api/keepalive"
                or health.get("checkIntervalSec", 0) * health.get("unhealthyThreshold", 0) < 180):
            raise DeploymentError("Auto-repair check is too aggressive or invalid; run scripts/configure-mig-autohealing.sh first")
        group = json.loads(self.mig("describe", "--format=json"))
        policy = group.get("updatePolicy", {})
        healing = group.get("autoHealingPolicies", [])
        if (policy.get("type") == "OPPORTUNISTIC"
                and policy.get("maxUnavailable", {}).get("fixed") == 0
                and policy.get("maxSurge", {}).get("fixed") == 1
                and policy.get("replacementMethod") == "SUBSTITUTE"
                and len(healing) == 1
                and healing[0].get("healthCheck", "").endswith("/" + check_name)
                and healing[0].get("initialDelaySec", 0) >= 600):
            return  # Avoid a slow policy mutation when it is already correct.
        # Explicitly enforce policy even if a previous manual rollout left it proactive.
        self.mig("update", "--update-policy-type=opportunistic",
                 "--update-policy-max-unavailable=0", "--update-policy-max-surge=1",
                 "--update-policy-replacement-method=substitute",
                 f"--health-check={check_name}", "--initial-delay=600")

    def deploy_instance(self, name, commit, rollback=False):
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise DeploymentError("Deployment requires a full immutable commit SHA")
        # Use this pinned runner on rollback too: older deploy.sh versions fetch moving main.
        runner = base64.b64encode(Path(__file__).with_name("deploy-release.sh").read_bytes()).decode()
        env = {
            "APP_ROOT": "/home/tarun_yadav/AstrologyApp", "DEPLOY_COMMIT": commit,
            "SERVE_FRONTEND_LOCALLY": "false", "SYNC_GCP_SECRETS": "false" if rollback else "true",
            "FORCE_BACKEND_PIP": "true" if rollback else os.getenv("FORCE_BACKEND_PIP", "false"),
            "FORCE_FULL_DEPLOY": os.getenv("FORCE_FULL_DEPLOY", "false") if not rollback else "false",
            "GIT_SSH_COMMAND": "ssh -i /home/tarun_yadav/.ssh/astroroshni_startup_deploy_key -o IdentitiesOnly=yes",
        }
        exports = "\n".join(f"export {key}={shlex.quote(value)}" for key, value in env.items())
        command = f"""set -euo pipefail
exec 9>/tmp/astroroshni-app-deploy.lock
flock -w 1800 9
{exports}
cd "$APP_ROOT"
export DEPLOY_PREV_HEAD=$(git rev-parse HEAD)
runner=$(mktemp /tmp/astroroshni-deploy.XXXXXX)
trap 'rm -f "$runner"' EXIT
printf '%s' '{runner}' | base64 -d > "$runner"
# Keep the lock in this shell only; the long-lived backend must not inherit it.
bash "$runner" 9>&-
test "$(git rev-parse HEAD)" = "$DEPLOY_COMMIT"
"""
        print(f"{'Restoring' if rollback else 'Deploying'} {name} -> {commit}", flush=True)
        # Do not replay a potentially successful mutation on an SSH error.
        print(self.ssh(name, "bash -c " + shlex.quote(command), timeout=3600), flush=True)

    def live(self):
        self.safe_policy()
        _, instances = self.wait_ready(minimum=2)
        names = sorted(vm["instance"].rsplit("/", 1)[-1] for vm in instances)
        for name in names:
            # Initial readiness, then the preceding server's post-deploy gate,
            # already protects the next update. Do not run the same gate twice.
            previous = self.ssh(name, "cd /home/tarun_yadav/AstrologyApp && git rev-parse HEAD")
            if not re.fullmatch(r"[0-9a-f]{40}", previous):
                raise DeploymentError(f"Cannot capture rollback commit on {name}")
            try:
                self.deploy_instance(name, self.args.commit)
                self.wait_ready(expected=names, minimum=2)
            except (subprocess.SubprocessError, DeploymentError) as error:
                print(f"Deployment failed on {name}: {error}. Attempting rollback; stopping this rollout.", flush=True)
                self.deploy_instance(name, previous, rollback=True)
                self.wait_ready(expected=names, minimum=2)
                raise DeploymentError(f"{name} restored to {previous}; rollout failed and stopped") from error

    def template(self):
        self.safe_policy()
        group, instances = self.wait_ready()
        names = sorted(vm["instance"].rsplit("/", 1)[-1] for vm in instances)
        try:
            self.mig("set-instance-template", f"--template={self.args.template}")
            self.wait_ready(expected=names)
        except (subprocess.SubprocessError, DeploymentError):
            self.safe_policy()
            self.mig("set-instance-template", f"--template={group['instanceTemplate']}")
            raise

    def replace(self):
        self.safe_policy()
        group, instances = self.wait_ready()
        previous = {vm.get("version", {}).get("instanceTemplate") for vm in instances}
        if len(previous) != 1 or None in previous:
            raise DeploymentError("Replacement needs a single known rollback template; MIG has mixed versions")
        previous_template = previous.pop()
        target = group["instanceTemplate"]
        try:
            self.mig("rolling-action", "replace", "--max-unavailable=0", "--max-surge=1",
                     "--replacement-method=substitute")
            # An asynchronous API success is not rollout success.
            self.mig("wait-until", "--stable", "--timeout=900")
            _, replacements = self.wait_ready()
            original_ids = {vm["id"] for vm in instances}
            if any(vm["id"] in original_ids or vm.get("version", {}).get("instanceTemplate") != target
                   for vm in replacements):
                raise DeploymentError("Replacement has not reached the requested template on every new VM")
        except (subprocess.SubprocessError, DeploymentError) as error:
            self.safe_policy()  # Stop scheduling new replacements before attempting recovery.
            if previous_template != target:
                print(f"Restoring previous template {previous_template}", flush=True)
                self.mig("rolling-action", "start-update", f"--version=template={previous_template}",
                         "--max-unavailable=0", "--max-surge=1", "--type=proactive")
                try:
                    self.mig("wait-until", "--stable", "--timeout=900")
                    self.wait_ready()
                finally:
                    self.safe_policy()
            raise DeploymentError("VM replacement failed; rollout stopped. Inspect recovery before retrying.") from error
        finally:
            self.safe_policy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["live", "replace", "template", "check"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--mig", required=True)
    parser.add_argument("--zone", required=True)
    parser.add_argument("--backend-service", required=True)
    parser.add_argument("--commit")
    parser.add_argument("--template")
    parser.add_argument("--health-timeout", type=int, default=600)
    parser.add_argument("--soak-seconds", type=int, default=30)
    args = parser.parse_args()
    if args.mode == "live" and not re.fullmatch(r"[0-9a-f]{40}", args.commit or ""):
        parser.error("live requires --commit with a full SHA")
    if args.mode == "template" and not args.template:
        parser.error("template requires --template")
    deployment = Deployment(args)
    if args.mode == "check":
        deployment.wait_ready()
    else:
        getattr(deployment, args.mode)()


if __name__ == "__main__":
    main()
