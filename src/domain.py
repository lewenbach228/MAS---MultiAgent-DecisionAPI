from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Criterion:
    name: str
    score: float
    weight: float
    justification: str


@dataclass
class CandidateProfile:
    name: str
    criteria: List[Criterion] = field(default_factory=list)

    @property
    def utility_score(self) -> float:
        return sum(c.score * c.weight for c in self.criteria)

    def breakdown_lines(self) -> list[str]:
        lines: list[str] = []
        for c in self.criteria:
            contrib = c.score * c.weight
            lines.append(f"  {c.name:25s} {c.score:.1f}/10 x poids {c.weight:.2f} = {contrib:.2f}")
        lines.append(f"  {'─' * 55}")
        lines.append(f"  {'SCORE FINAL':25s} {self.utility_score:.2f}/10")
        return lines

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "utility_score": round(self.utility_score, 2),
            "criteria": [
                {
                    "name": c.name,
                    "score": c.score,
                    "weight": c.weight,
                    "contribution": round(c.score * c.weight, 2),
                    "justification": c.justification,
                }
                for c in self.criteria
            ],
        }


@dataclass
class Decision:
    id: str
    job: str
    candidate: CandidateProfile
    created_at: datetime
