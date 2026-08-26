from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from instant_chat_v2.career_graph_policy import CareerGraphPolicyStore  # noqa: E402
from instant_chat_v2.health_graph_policy import HealthGraphPolicyStore  # noqa: E402
from instant_chat_v2.marriage_graph_policy import MarriageGraphPolicyStore  # noqa: E402
from instant_chat_v2.question_taxonomy import LIFE_DOMAINS  # noqa: E402


RUNTIME = ROOT / "knowledge_graph" / "core" / "life-domain-runtime.json"


def test_shared_life_domain_ontology_compiles() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_life_domain_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "13 parents, 46 taxonomy topics, Muhurat separate" in result.stdout


def test_every_taxonomy_domain_has_exactly_one_parent_except_muhurat() -> None:
    document = json.loads(RUNTIME.read_text(encoding="utf-8"))
    mapping = document["runtime_key_to_parent"]
    assert set(mapping) == set(LIFE_DOMAINS) - {"muhurat"}
    assert document["parent_domain_count"] == 13
    assert document["topic_count"] == 46
    assert document["question_operations"] == [{
        "id": "domain:Muhurat",
        "label": "Muhurat and electional timing",
        "runtime_key": "muhurat",
    }]


def _domain_branch(policy) -> dict:
    question = policy.graph_tree["children"][0]
    life_domain = next(node for node in question["children"] if node["label"] == "Life domain")
    return life_domain["children"][0]


def test_career_graph_uses_shared_parent_and_exposes_domain_topics() -> None:
    domain = _domain_branch(CareerGraphPolicyStore().require("general"))
    assert domain["id"] == "domain:CareerWorkPublicRole"
    assert domain["label"] == "Career, work and public role"
    topics = next(node for node in domain["children"] if node["label"] == "Domain topics")
    assert {node["id"] for node in topics["children"]} >= {
        "domain:Career", "domain:Business", "domain:Employment", "domain:Government",
    }


def test_health_graph_uses_shared_parent_and_exposes_domain_topics() -> None:
    domain = _domain_branch(HealthGraphPolicyStore().require("health"))
    assert domain["id"] == "domain:HealthWellbeing"
    assert domain["label"] == "Health and wellbeing"
    topics = next(node for node in domain["children"] if node["label"] == "Domain topics")
    assert [node["id"] for node in topics["children"]] == [
        "domain:Health", "domain:MentalWellbeing", "domain:Surgery",
        "domain:Accident", "domain:Recovery",
    ]


def test_marriage_graph_uses_shared_parent_and_exposes_domain_topics() -> None:
    domain = _domain_branch(MarriageGraphPolicyStore().require("marriage_timing"))
    assert domain["id"] == "domain:MarriageRelationships"
    assert domain["label"] == "Marriage and relationships"
    topics = next(node for node in domain["children"] if node["label"] == "Domain topics")
    assert [node["id"] for node in topics["children"]] == [
        "domain:Marriage", "domain:Relationship", "domain:Separation",
    ]
