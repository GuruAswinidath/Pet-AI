import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from triage_engine import apply_clarify_cap_fallback, classify_urgency, normalize_symptom


class NormalizeSymptomTests(unittest.TestCase):
    def test_exact_key(self):
        self.assertEqual(normalize_symptom("vomiting"), "vomiting")

    def test_alias(self):
        self.assertEqual(normalize_symptom("throwing up"), "vomiting")

    def test_label_substring(self):
        self.assertEqual(normalize_symptom("Bloated / distended abdomen"), "bloated_abdomen")

    def test_unknown(self):
        self.assertIsNone(normalize_symptom("purple sparkles"))

    def test_none_input(self):
        self.assertIsNone(normalize_symptom(None))


class ClassifyUrgencyTests(unittest.TestCase):
    def test_empty_symptoms_returns_cautious_soon(self):
        result = classify_urgency([], species="dog")
        self.assertEqual(result["urgency"], "soon")
        self.assertIn("symptom", result["missing_info"])

    def test_red_flag_triggers_emergency(self):
        result = classify_urgency(
            [{"symptom": "vomiting", "duration": "today", "severity_cues": ["blood in vomit"]}],
            species="dog",
        )
        self.assertEqual(result["urgency"], "emergency")
        self.assertIn("vomiting", result["matched_kb_entries"])

    def test_red_flag_matches_on_partial_keyword_not_just_exact_phrase(self):
        # Regression test: the Intake Agent rarely extracts a KB red-flag
        # phrase verbatim - it extracted "blood" here, not "blood in vomit"
        # or "vomiting blood". This case previously fell through to "home"
        # because the matcher required near-exact phrase containment,
        # silently missing a real emergency (vomiting blood + lethargy).
        result = classify_urgency(
            [
                {"symptom": "vomiting", "duration": "since this morning", "severity_cues": ["blood"]},
                {"symptom": "lethargy", "duration": None, "severity_cues": ["very lethargic"]},
            ],
            species="dog",
        )
        self.assertEqual(result["urgency"], "emergency")

    def test_yellow_flag_triggers_soon(self):
        result = classify_urgency(
            [{"symptom": "vomiting", "duration": "persists past 24 hours", "severity_cues": []}],
            species="cat",
        )
        self.assertEqual(result["urgency"], "soon")

    def test_mild_case_with_info_present_is_home(self):
        result = classify_urgency(
            [{"symptom": "vomiting", "duration": "once this morning", "severity_cues": ["ate grass"]}],
            species="dog",
        )
        self.assertEqual(result["urgency"], "home")
        self.assertEqual(result["missing_info"], [])

    def test_missing_duration_and_severity_flags_missing_info(self):
        result = classify_urgency([{"symptom": "vomiting"}], species="dog")
        self.assertIn("duration_or_severity:vomiting", result["missing_info"])
        self.assertEqual(result["urgency"], "soon")

    def test_unrecognized_symptom_is_cautious_soon_and_flagged(self):
        result = classify_urgency([{"symptom": "glowing fur"}], species="dog")
        self.assertEqual(result["urgency"], "soon")
        self.assertTrue(any(m.startswith("unrecognized_symptom:") for m in result["missing_info"]))

    def test_worst_case_wins_across_multiple_symptoms(self):
        result = classify_urgency(
            [
                {"symptom": "vomiting", "duration": "once", "severity_cues": ["ate grass"]},
                {"symptom": "seizure", "duration": "just now", "severity_cues": ["convulsions"]},
            ],
            species="dog",
        )
        self.assertEqual(result["urgency"], "emergency")

    def test_alias_resolves_before_classification(self):
        result = classify_urgency(
            [{"symptom": "throwing up", "duration": "since morning", "severity_cues": []}],
            species="dog",
        )
        self.assertIn("vomiting", result["matched_kb_entries"])


class ClarifyCapFallbackTests(unittest.TestCase):
    def test_home_bumps_to_soon(self):
        result = apply_clarify_cap_fallback({"urgency": "home", "matched_kb_entry": None, "matched_kb_entries": [], "missing_info": ["x"]})
        self.assertEqual(result["urgency"], "soon")

    def test_emergency_stays_emergency(self):
        result = apply_clarify_cap_fallback({"urgency": "emergency", "matched_kb_entry": None, "matched_kb_entries": [], "missing_info": ["x"]})
        self.assertEqual(result["urgency"], "emergency")


if __name__ == "__main__":
    unittest.main()
