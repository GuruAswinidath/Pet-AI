"""The Triage Engine - a deterministic function, not an LLM call.

README section 1 is explicit about this: the urgency decision must stay a
deterministic function, called BY an agent as a tool, not decided BY an
agent's judgment. Nothing in this module makes a network call or reads
anything at runtime other than the in-code TRIAGE_KB - that's what makes
it independently testable (see tests/test_triage_engine.py) and auditable.
"""

import re

from triage_kb import SYMPTOM_ALIASES, TRIAGE_KB

URGENCY_RANK = {"home": 0, "soon": 1, "emergency": 2}

# Filler words excluded when checking flag-phrase/free-text keyword overlap
# below. Deliberately short - see _phrase_matches for why. Generic time/
# frequency words (hours, days, morning, ...) are included on purpose: they
# show up in almost any duration text AND inside frequency-based flag
# phrases like "3+ times in a few hours", which caused unrelated duration
# text to falsely trigger that red flag via a shared "hours".
_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "of", "for", "with", "and", "or",
    "is", "are", "was", "were", "be", "been", "being", "this", "that", "these",
    "those", "since", "after", "before", "during", "few", "some", "any", "no",
    "not", "than", "then", "very", "more", "most", "less", "least", "just",
    "only", "up", "down", "out", "off", "over", "under", "again", "once", "it",
    "its", "his", "her", "their", "our", "your", "my", "has", "have", "had",
    "hour", "hours", "day", "days", "minute", "minutes", "week", "weeks",
    "month", "months", "year", "years", "today", "morning", "evening",
    "night", "ago", "past",
}


def _more_cautious(a: str, b: str) -> str:
    return a if URGENCY_RANK[a] >= URGENCY_RANK[b] else b


def _significant_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) >= 4 and w not in _STOPWORDS}


def _phrase_matches(flag_phrase: str, text_blob: str) -> bool:
    """True if a KB flag phrase (e.g. "blood in vomit") should be considered
    triggered by free text (e.g. Intake Agent severity_cues like "blood").

    Exact substring containment first (either direction), then falls back to
    keyword overlap: real user/LLM phrasing almost never matches a KB phrase
    word-for-word ("blood" vs. "blood in vomit"), and this is the
    safety-critical red-flag check - a missed match here is far more
    dangerous than an over-cautious one, so the fallback deliberately errs
    toward sensitivity over precision."""
    if not text_blob:
        return False
    flag_lower = flag_phrase.lower()
    text_lower = text_blob.lower()
    if flag_lower in text_lower or text_lower in flag_lower:
        return True
    flag_words = _significant_words(flag_phrase)
    if not flag_words:
        return False
    return bool(flag_words & _significant_words(text_blob))


def normalize_symptom(raw: str | None) -> str | None:
    """Map free text (from the Intake Agent or a user) onto a canonical
    TRIAGE_KB key. Exact match -> alias table -> loose substring match."""
    if not raw:
        return None
    key = raw.strip().lower()
    if key in TRIAGE_KB:
        return key
    if key in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[key]
    for kb_key, kb_entry in TRIAGE_KB.items():
        label = kb_entry["label"].lower()
        spaced_key = kb_key.replace("_", " ")
        if key in label or label in key or key in spaced_key or spaced_key in key:
            return kb_key
    return None


def classify_urgency(extracted_symptoms: list[dict], species: str | None = None) -> dict:
    """The safety-critical decision.

    Input: extracted_symptoms - a list of {"symptom", "duration",
    "severity_cues"} dicts, as produced by the Intake Agent (README
    section 4's extracted_symptoms field).

    Output: {urgency, matched_kb_entry, matched_kb_entries, missing_info}
    matching README section 3's Triage Engine contract.
    """
    if not extracted_symptoms:
        return {
            "urgency": "soon",
            "matched_kb_entry": None,
            "matched_kb_entries": [],
            "missing_info": ["symptom"],
        }

    worst_urgency = "home"
    matched_entries: list[str] = []
    missing_info: list[str] = []

    for item in extracted_symptoms:
        raw_symptom = (item or {}).get("symptom")
        duration = (item or {}).get("duration")
        severity_cues = [c.lower() for c in (item or {}).get("severity_cues") or []]

        kb_key = normalize_symptom(raw_symptom)

        if kb_key is None:
            if raw_symptom:
                missing_info.append(f"unrecognized_symptom:{raw_symptom}")
            worst_urgency = _more_cautious(worst_urgency, "soon")
            continue

        entry = TRIAGE_KB[kb_key]
        if kb_key not in matched_entries:
            matched_entries.append(kb_key)

        text_blob = " ".join(severity_cues + ([duration] if duration else [])).lower()
        red_flags = [f.lower() for f in entry["red_flags"]]
        yellow_flags = [f.lower() for f in entry["yellow_flags"]]

        hit_red = any(_phrase_matches(rf, text_blob) for rf in red_flags)
        hit_yellow = any(_phrase_matches(yf, text_blob) for yf in yellow_flags)

        if hit_red:
            worst_urgency = _more_cautious(worst_urgency, "emergency")
        elif hit_yellow:
            worst_urgency = _more_cautious(worst_urgency, "soon")
        elif not duration and not severity_cues:
            missing_info.append(f"duration_or_severity:{kb_key}")
            worst_urgency = _more_cautious(worst_urgency, "soon")
        else:
            worst_urgency = _more_cautious(worst_urgency, "home")

    return {
        "urgency": worst_urgency,
        "matched_kb_entry": matched_entries[0] if matched_entries else None,
        "matched_kb_entries": matched_entries,
        "missing_info": missing_info,
    }


def apply_clarify_cap_fallback(triage_result: dict) -> dict:
    """README section 3: cap the clarifying-question loop at 2-3 turns,
    then fall back to the most cautious applicable urgency level rather
    than staying stuck. Called once MAX_CLARIFYING_QUESTIONS is hit while
    missing_info is still non-empty."""
    result = dict(triage_result)
    result["urgency"] = _more_cautious(result["urgency"], "soon")
    return result
