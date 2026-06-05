import pytest
from src.domain import Criterion, CandidateProfile, Decision
from datetime import datetime


class TestCriterion:
    def test_create(self):
        c = Criterion(name="skills_match", score=8.0, weight=0.35, justification="Good")
        assert c.name == "skills_match"
        assert c.score == 8.0
        assert c.weight == 0.35
        assert c.justification == "Good"


class TestCandidateProfile:
    def make_profile(self) -> CandidateProfile:
        return CandidateProfile(
            name="Alice",
            criteria=[
                Criterion("skills_match", 10.0, 0.35, "Perfect"),
                Criterion("years_experience", 8.0, 0.20, "Solid"),
                Criterion("leadership", 5.0, 0.15, "Okay"),
            ],
        )

    def test_utility_score(self):
        p = self.make_profile()
        expected = 10.0 * 0.35 + 8.0 * 0.20 + 5.0 * 0.15
        assert p.utility_score == expected

    def test_to_dict(self):
        p = self.make_profile()
        d = p.to_dict()
        assert d["name"] == "Alice"
        assert d["utility_score"] == pytest.approx(10.0 * 0.35 + 8.0 * 0.20 + 5.0 * 0.15, 0.01)
        assert len(d["criteria"]) == 3
        for c in d["criteria"]:
            assert "name" in c
            assert "score" in c
            assert "weight" in c
            assert "contribution" in c
            assert "justification" in c

    def test_breakdown_lines(self):
        p = self.make_profile()
        lines = p.breakdown_lines()
        assert len(lines) == 5
        assert "SCORE FINAL" in lines[-1]


class TestDecision:
    def test_create(self):
        d = Decision(
            id="dec_abc123",
            job="Senior Engineer",
            candidate=CandidateProfile("Bob", []),
            created_at=datetime(2026, 6, 5),
        )
        assert d.id == "dec_abc123"
        assert d.job == "Senior Engineer"
        assert d.candidate.name == "Bob"
