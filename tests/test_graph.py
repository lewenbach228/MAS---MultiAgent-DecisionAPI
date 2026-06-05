import pytest
from src.graph import GraphDb


@pytest.fixture
async def graph():
    g = GraphDb()
    await g.connect()
    return g


class TestGraphDb:
    async def test_connect(self, graph):
        assert graph._graph is not None
        assert graph._graph.number_of_edges() == 4

    async def test_no_adjustments_when_all_medium(self, graph):
        scores = {"skills_match": 5.0, "years_experience": 5.0, "leadership": 5.0, "domain_fit": 5.0}
        adj = await graph.get_adjustments(scores)
        assert adj == {}

    async def test_boost_when_high_score(self, graph):
        scores = {"skills_match": 3.0, "years_experience": 8.0, "leadership": 8.0, "domain_fit": 3.0}
        adj = await graph.get_adjustments(scores)
        assert "BOOST" in adj.get("leadership", [""])[0]
        assert "BOOST" in adj.get("years_experience", [""])[0]

    async def test_block_when_prerequisite_zero(self, graph):
        scores = {"skills_match": 5.0, "years_experience": 5.0, "leadership": 5.0, "domain_fit": 0.0}
        adj = await graph.get_adjustments(scores)
        assert any("BLOQUE" in m for m in adj.get("communication", []))

    async def test_penalize_when_low_score(self, graph):
        scores = {"skills_match": 2.0, "years_experience": 5.0, "leadership": 5.0, "domain_fit": 5.0}
        adj = await graph.get_adjustments(scores)
        assert any("PENALISE" in m for m in adj.get("education", []))

    async def test_apply_adjustments_boost(self, graph):
        scores = {"skills_match": 3.0, "years_experience": 8.0, "leadership": 8.0, "domain_fit": 3.0}
        adj = await graph.get_adjustments(scores)

        from src.domain import Criterion
        criteria = [Criterion("years_experience", 10.0, 0.20, "")]
        await graph.apply_adjustments(criteria, adj)
        assert criteria[0].weight == pytest.approx(0.20 * 1.3, 0.001)

    async def test_apply_adjustments_block(self, graph):
        scores = {"skills_match": 5.0, "years_experience": 5.0, "leadership": 5.0, "domain_fit": 0.0}
        adj = await graph.get_adjustments(scores)

        from src.domain import Criterion
        criteria = [Criterion("communication", 5.0, 0.10, "")]
        await graph.apply_adjustments(criteria, adj)
        assert criteria[0].weight == 0.0
