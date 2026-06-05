import networkx as nx

"""
Graphe de dependances entre criteres (NetworkX).

Stocke les relations suivantes :
  BOOSTS              → multiplie le poids de target par (1 + factor) si source.score > 5
  PENALIZES           → multiplie le poids de target par factor si source.score < 3
  PREREQUISITE_FOR    → le poids de target est 0 si source.score == 0

Construction :
  G.add_edge(source, target, type="BOOSTS", factor=0.3)
"""

SEED_EDGES = [
    ("leadership",     "years_experience", {"type": "BOOSTS",          "factor": 0.3}),
    ("domain_fit",     "communication",    {"type": "PREREQUISITE_FOR", "factor": 0.0}),
    ("skills_match",   "education",        {"type": "PENALIZES",        "factor": 0.5}),
    ("years_experience", "leadership",     {"type": "BOOSTS",          "factor": 0.2}),
]


class GraphDb:
    def __init__(self) -> None:
        self._graph: nx.DiGraph | None = None

    async def connect(self) -> None:
        g = nx.DiGraph()
        for source, target, attrs in SEED_EDGES:
            g.add_edge(source, target, **attrs)
        self._graph = g
        print(f"Neo4j: graphe initialise avec {g.number_of_edges()} dependances")

    async def get_adjustments(self, scores: dict[str, float]) -> dict[str, list[str]]:
        if not self._graph:
            return {}

        adjustments: dict[str, list[str]] = {}

        for source, score in scores.items():
            if source not in self._graph:
                continue

            for _, target, data in self._graph.out_edges(source, data=True):
                etype = data.get("type")
                factor = data.get("factor", 0.0)

                if etype == "PREREQUISITE_FOR" and score == 0:
                    adjustments.setdefault(target, []).append(
                        f"BLOQUE: {source}=0 (prerequis non rempli)"
                    )

                elif etype == "BOOSTS" and score > 5:
                    pct = int(factor * 100)
                    adjustments.setdefault(target, []).append(
                        f"BOOST: +{pct}% car {source}={score:.0f}/10"
                    )

                elif etype == "PENALIZES" and score < 3:
                    pct = int((1 - factor) * 100)
                    adjustments.setdefault(target, []).append(
                        f"PENALISE: -{pct}% car {source}={score:.0f}/10 (< 3)"
                    )

        return adjustments

    async def apply_adjustments(self, criteria: list, adjustments: dict[str, list[str]]) -> list:
        if not adjustments:
            return criteria

        for c in criteria:
            msgs = adjustments.get(c.name, [])
            for msg in msgs:
                if msg.startswith("BLOQUE"):
                    c.weight = 0.0
                elif msg.startswith("BOOST"):
                    c.weight *= 1.3
                elif msg.startswith("PENALISE"):
                    c.weight *= 0.5
        return criteria

    async def close(self) -> None:
        self._graph = None
