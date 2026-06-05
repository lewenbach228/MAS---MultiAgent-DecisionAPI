import json
from google import genai
from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.domain import CandidateProfile, Criterion


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


EXTRACTION_PROMPT = """Tu es un recruteur technique qui analyse des CVs.

Poste :
{job}

CV du candidat :
{cv}

Evalue ce candidat selon les criteres ci-dessous.
Pour chaque critere :
- Donne le score (0-10) base sur le CV et le poste
- Justifie le score en 1 phrase max

Criteres et leurs definitions :
- skills_match : adequation de la stack technique avec le poste
- years_experience : annees d'experience professionnelle pertinente (10+ => 10/10)
- leadership : experience de lead technique, management d'equipe, mentoring
- domain_fit : experience dans le domaine (SaaS, startup, scale-up)
- communication : langues, capacite a communiquer en contexte international
- education : diplomes, formations, certifications

Reponds UNIQUEMENT en JSON (sans markdown) :
{{
  "name": "Prenom Nom",
  "criteria": [
    {{"name": "skills_match", "score": <0-10>, "justification": "..."}},
    ...
  ]
}}
"""

WEIGHTS: dict[str, float] = {
    "skills_match":     0.35,
    "years_experience": 0.20,
    "leadership":       0.15,
    "domain_fit":       0.15,
    "communication":    0.10,
    "education":        0.05,
}


def extract_candidate(job: str, cv_text: str) -> CandidateProfile:
    prompt = EXTRACTION_PROMPT.format(job=job, cv=cv_text)
    resp = _get_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.3,
        },
    )
    data = json.loads(resp.text)

    criteria = []
    for c in data["criteria"]:
        weight = WEIGHTS.get(c["name"], 0)
        criteria.append(Criterion(
            name=c["name"],
            score=float(c["score"]),
            weight=weight,
            justification=c.get("justification", ""),
        ))
    return CandidateProfile(name=data["name"], criteria=criteria)
