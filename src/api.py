from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.llm import extract_candidate
from src.db import Db
from src.cache import Cache
from src.graph import GraphDb

db = Db()
cache = Cache()
graph = GraphDb()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.connect()
    await cache.connect()
    await graph.connect()
    yield
    await db.close()
    await cache.close()
    await graph.close()


app = FastAPI(
    title="Decision API",
    version="0.1.0",
    description="API de matching candidat vs poste. Utility-based agent avec extraction LLM, scoring formel et graphe de dependances.",
    lifespan=lifespan,
)


class DecideRequest(BaseModel):
    job: str
    cv: str


class DecideResponse(BaseModel):
    decision_id: str
    candidate: str
    utility_score: float
    criteria: list[dict]
    graph_adjustments: dict[str, list[str]] = {}


@app.post("/api/decide", response_model=DecideResponse)
async def decide(req: DecideRequest):
    cached = await cache.get(req.job, req.cv)
    if cached:
        return DecideResponse(
            decision_id="cached",
            candidate=cached.get("candidate", "?"),
            utility_score=cached.get("utility_score", 0),
            criteria=cached.get("criteria", []),
            graph_adjustments=cached.get("graph_adjustments", {}),
        )

    profile = extract_candidate(req.job, req.cv)

    scores = {c.name: c.score for c in profile.criteria}
    adjustments = await graph.get_adjustments(scores)
    await graph.apply_adjustments(profile.criteria, adjustments)

    decision_id = await db.save_decision(req.job, profile)

    data_for_cache = profile.to_dict()
    data_for_cache["graph_adjustments"] = adjustments
    await cache.set(req.job, req.cv, data_for_cache)

    return DecideResponse(
        decision_id=decision_id,
        candidate=profile.name,
        utility_score=profile.utility_score,
        criteria=profile.to_dict()["criteria"],
        graph_adjustments=adjustments,
    )


@app.get("/api/decide/{decision_id}")
async def get_decision(decision_id: str):
    decision = await db.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {
        "id": decision.id,
        "job": decision.job,
        "candidate": decision.candidate.to_dict(),
        "created_at": decision.created_at.isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
