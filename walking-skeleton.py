"""
P3 — Decision API (Utility-based Agent)
Walking Skeleton : prouve le cœur agentique sans infrastructure.

Ce script :
  1. Prend un CV texte + une description de poste
  2. Extrait un profil structuré via LLM
  3. Calcule un score via une utility function formelle
  4. Produit un breakdown expliqué

Usage : python walking-skeleton.py
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List

try:
    from google import genai
except ImportError:
    print("Erreur : google-genai non installe. Lance : pip install google-genai python-dotenv")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── Domain model ───────────────────────────────────────────────

@dataclass
class Criterion:
    name: str
    raw: str
    score: float        # normalisé 0–10
    weight: float       # poids dans la utility function
    justification: str  # pourquoi ce score

@dataclass
class CandidateProfile:
    name: str
    criteria: List[Criterion] = field(default_factory=list)

    @property
    def utility_score(self) -> float:
        return sum(c.score * c.weight for c in self.criteria)

    @property
    def breakdown(self) -> str:
        lines = []
        for c in self.criteria:
            contribution = c.score * c.weight
            lines.append(f"  {c.name:20s}  {c.score:.1f}/10 × poids {c.weight:.2f} = {contribution:.2f}")
        lines.append(f"  {'─' * 50}")
        lines.append(f"  {'SCORE FINAL':20s}  {self.utility_score:.2f}/10")
        return "\n".join(lines)

# ─── Data ────────────────────────────────────────────────────────

JOB_DESCRIPTION = """
Poste : Senior Software Engineer (full-stack)
Stack : React, TypeScript, Node.js, GraphQL, PostgreSQL
Mission : Lead une équipe de 4 devs, architecturer une feature de recommandation temps réel
Contrat : CDI, Paris ou full remote
"""

CVS = {
    "alice": """
Alice Dubois — Senior Full-Stack Engineer
7 ans d'expérience
Stack : React, TypeScript, Node.js, GraphQL, PostgreSQL, AWS
A leadé une équipe de 5 devs pendant 3 ans chez Doctolib
Ex-Co-founder d'une startup SaaS (levée 2M€) — lead technique full-stack
Master en informatique (CentraleSupélec)
Bilingue français/anglais
""",
    "bob": """
Bob Martin — Développeur Full-Stack
12 ans d'expérience
Stack : React, Node.js, Express, MongoDB, PHP
A travaillé chez 3 agences web différentes (5ans), puis freelance (4ans)
Projets : sites e-commerce, CRM sur mesure
Pas d'expérience de management d'équipe
Master MIAGE
Anglais technique
""",
    "charlie": """
Charlie Zhang — Software Engineer
3 ans d'expérience
Stack : React, TypeScript, NestJS, Prisma, GraphQL
Dernière mission : API GraphQL pour une app fintech (1.2M users)
Lead technique d'une feature de bout en bout (squad de 3)
Bachelor en informatique + bootcamp Le Wagon
Trilingue FR/EN/Mandarin
""",
}

# ─── Weights ─────────────────────────────────────────────────────

WEIGHTS: dict[str, float] = {
    "skills_match":    0.35,
    "years_experience":0.20,
    "leadership":      0.15,
    "domain_fit":      0.15,
    "communication":   0.10,
    "education":       0.05,
}

# ─── LLM client (Gemini) ─────────────────────────────────────────

_client = None

def get_client():
    global _client
    if _client is None:
        import google.genai as genai
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

EXTRACTION_PROMPT = """Tu es un recruteur technique qui analyse des CVs.

Poste :
{job}

CV du candidat :
{cv}

Évalue ce candidat selon les critères ci-dessous.
Pour chaque critère :
- Donne le score (0-10) basé sur le CV et le poste
- Justifie le score en 1 phrase max

Critères et leurs définitions :
- skills_match : adéquation de la stack technique avec le poste (React, TypeScript, Node.js, GraphQL, PostgreSQL)
- years_experience : années d'expérience professionnelle pertinente (10+ → 10/10)
- leadership : expérience de lead technique, management d'équipe, mentoring
- domain_fit : expérience dans le domaine (SaaS, startup, scale-up)
- communication : langues, capacité à communiquer en contexte international
- education : diplômes, formations, certifications

Réponds UNIQUEMENT en JSON (sans markdown) :
{{
  "name": "Prénom Nom",
  "criteria": [
    {{"name": "skills_match", "score": <0-10>, "justification": "..."}},
    ...
  ]
}}
"""

def extract_candidate(cv_text: str) -> dict:
    prompt = EXTRACTION_PROMPT.format(job=JOB_DESCRIPTION, cv=cv_text)
    resp = get_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.3,
        },
    )
    return json.loads(resp.text)

# ─── Utility function ────────────────────────────────────────────

def build_profile(cv_key: str, cv_text: str) -> CandidateProfile:
    data = extract_candidate(cv_text)
    criteria = []
    for c in data["criteria"]:
        weight = WEIGHTS.get(c["name"], 0)
        criteria.append(Criterion(
            name=c["name"],
            raw=c.get("justification", ""),
            score=float(c["score"]),
            weight=weight,
            justification=c.get("justification", ""),
        ))
    return CandidateProfile(name=cv_key, criteria=criteria)

# ─── Main ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("P3 — Decision API (Utility-based Agent)")
    print("Walking Skeleton : Matching Candidat ≙ Poste")
    print("=" * 60)

    if not os.getenv("GEMINI_API_KEY"):
        print("\nErreur : GEMINI_API_KEY non definie")
        print("   Cree un fichier .env avec : GEMINI_API_KEY=ta_cle")
        exit(1)

    profiles: list[CandidateProfile] = []
    for key, cv in CVS.items():
        print(f"\nAnalyse de {key}...")
        try:
            profile = build_profile(key, cv)
            profiles.append(profile)
            print(f"  OK Score: {profile.utility_score:.2f}/10")
        except Exception as e:
            print(f"  FAIL Erreur: {e}")

    # ── Classement ───────────────────────────────────────────
    profiles.sort(key=lambda p: p.utility_score, reverse=True)

    print("\n" + "=" * 60)
    print("CLASSEMENT FINAL")
    print("=" * 60)
    for i, p in enumerate(profiles, 1):
        print(f"\n  #{i} — {p.name.upper():30s} {p.utility_score:.2f}/10")
        print(p.breakdown)

    # ── Recommandation ───────────────────────────────────────
    if profiles:
        best = profiles[0]
        print(f"\n{'=' * 60}")
        print(f"✅ RECOMMANDATION : {best.name} ({best.utility_score:.2f}/10)")
        print(f"{'=' * 60}\n")

    # ── JSON output ──────────────────────────────────────────
    output = []
    for p in profiles:
        output.append({
            "candidate": p.name,
            "utility_score": round(p.utility_score, 2),
            "criteria": [
                {
                    "name": c.name,
                    "score": c.score,
                    "weight": c.weight,
                    "normalized_contribution": round(c.score * c.weight, 2),
                    "justification": c.justification,
                }
                for c in p.criteria
            ],
        })

    print("─" * 60)
    print("OUTPUT JSON :")
    print(json.dumps({"job": JOB_DESCRIPTION.strip(), "ranking": output}, indent=2))


if __name__ == "__main__":
    main()
