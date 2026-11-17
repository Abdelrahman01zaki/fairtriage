"""One flat, JSON-serializable row per (spec name, seed, policy) run.

A row identifies the spec it came from by name and by a hash of its exact
content, so a renamed spec and a changed spec are both visible later. Adding
a metric means adding a field with a default: existing records stay valid.
"""

import hashlib
import json
from dataclasses import dataclass

from ai_intelligence_lab.fairtriage.fairness.metrics import CategoryFairness
from ai_intelligence_lab.fairtriage.scenarios.generator import ScenarioSpec

SCHEMA_VERSION = 1


def spec_hash(spec: ScenarioSpec) -> str:
    """A stable id for a spec's content, independent of field or weight order."""
    payload = {
        "casualties": spec.casualties,
        "hospitals": spec.hospitals,
        "beds_per_hospital": spec.beds_per_hospital,
        "ambulances": spec.ambulances,
        "junctions": spec.junctions,
        "extra_roads": spec.extra_roads,
        "report_window": spec.report_window,
        "category_weights": sorted(
            [category.name, weight] for category, weight in spec.category_weights
        ),
    }
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RunRecord:
    """Everything measured from one simulation run, flat enough to store as a row."""

    schema_version: int
    spec_name: str
    spec_hash: str
    seed: int
    policy_name: str
    served: int
    unserved_total: int
    end_time: float
    categories: tuple[CategoryFairness, ...]

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unknown schema_version {self.schema_version}")
        for name in ("spec_name", "spec_hash", "policy_name"):
            if not getattr(self, name):
                raise ValueError(f"a run record needs a {name}")
        if self.seed < 0:
            raise ValueError("seed cannot be negative")
        if self.served < 0 or self.unserved_total < 0:
            raise ValueError("served and unserved_total cannot be negative")
        object.__setattr__(self, "categories", tuple(self.categories))


def to_json_dict(record: RunRecord) -> dict[str, object]:
    """``record`` as plain dicts, lists and primitives: ``json.dumps``-ready."""
    return {
        "schema_version": record.schema_version,
        "spec_name": record.spec_name,
        "spec_hash": record.spec_hash,
        "seed": record.seed,
        "policy_name": record.policy_name,
        "served": record.served,
        "unserved_total": record.unserved_total,
        "end_time": record.end_time,
        "categories": [
            {
                "category": item.category.name,
                "transported": item.transported,
                "unserved": item.unserved,
                "mean_wait": item.mean_wait,
                "median_wait": item.median_wait,
                "worst_wait": item.worst_wait,
                "gini": item.gini,
                "mean_to_hospital": item.mean_to_hospital,
                "worst_to_hospital": item.worst_to_hospital,
            }
            for item in record.categories
        ],
    }
