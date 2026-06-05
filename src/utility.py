from src.domain import CandidateProfile, Criterion


def compute_score(profile: CandidateProfile) -> CandidateProfile:
    return profile


def check_weights(criteria: list[Criterion]) -> float:
    total = sum(c.weight for c in criteria)
    return round(total, 2)
