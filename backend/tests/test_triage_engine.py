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
        result = classify_urgency([], species="cat")
        self.assertEqual(result["urgency"], "soon")
        self.assertIn("symptom", result["missing_info"])

    def test_red_flag_triggers_emergency(self):
        result = classify_urgency(
            [{"symptom": "vomiting", "duration": "today", "severity_cues": ["blood in vomit"]}],
            species="cat",
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
            species="cat",
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
            species="cat",
        )
        self.assertEqual(result["urgency"], "home")
        self.assertEqual(result["missing_info"], [])

    def test_missing_duration_and_severity_flags_missing_info(self):
        result = classify_urgency([{"symptom": "vomiting"}], species="cat")
        self.assertIn("duration_or_severity:vomiting", result["missing_info"])
        self.assertEqual(result["urgency"], "soon")

    def test_unrecognized_symptom_is_cautious_soon_and_flagged(self):
        result = classify_urgency([{"symptom": "glowing fur"}], species="cat")
        self.assertEqual(result["urgency"], "soon")
        self.assertTrue(any(m.startswith("unrecognized_symptom:") for m in result["missing_info"]))

    def test_worst_case_wins_across_multiple_symptoms(self):
        result = classify_urgency(
            [
                {"symptom": "vomiting", "duration": "once", "severity_cues": ["ate grass"]},
                {"symptom": "seizure", "duration": "just now", "severity_cues": ["convulsions"]},
            ],
            species="cat",
        )
        self.assertEqual(result["urgency"], "emergency")

    def test_alias_resolves_before_classification(self):
        result = classify_urgency(
            [{"symptom": "throwing up", "duration": "since morning", "severity_cues": []}],
            species="cat",
        )
        self.assertIn("vomiting", result["matched_kb_entries"])

    def test_urinary_obstruction_no_output_is_emergency(self):
        # Demo scenario: urinary obstruction is the flagship cat emergency -
        # a male cat straining with no urine output must never resolve to
        # anything less than "emergency".
        result = classify_urgency(
            [
                {
                    "symptom": "can't pee",
                    "duration": "since this morning",
                    "severity_cues": ["straining with little or no urine", "crying while trying to urinate"],
                }
            ],
            species="cat",
        )
        self.assertEqual(result["urgency"], "emergency")
        self.assertIn("urinary_obstruction", result["matched_kb_entries"])

    def test_urinary_obstruction_alias_resolves(self):
        self.assertEqual(normalize_symptom("straining to pee"), "urinary_obstruction")

    def test_constipation_distinct_from_urinary_obstruction(self):
        # A common real-world mix-up: owners can't always tell straining to
        # urinate from straining to defecate. Both should be recognized as
        # distinct KB entries rather than one swallowing the other.
        self.assertEqual(normalize_symptom("can't poop"), "constipation")
        self.assertNotEqual(normalize_symptom("can't poop"), normalize_symptom("can't pee"))

    def test_lily_ingestion_is_emergency_even_without_other_symptoms(self):
        result = classify_urgency(
            [{"symptom": "poisoning_ingestion", "duration": "an hour ago", "severity_cues": ["ate a lily"]}],
            species="cat",
        )
        self.assertEqual(result["urgency"], "emergency")

    def test_denied_symptom_cue_does_not_falsely_trigger_its_own_red_flag(self):
        # Regression: found via real Intake Agent extraction. When an owner
        # explicitly denies a symptom ("no vomiting", "no hiding"), the
        # fuzzy word-overlap fallback used to still match those words
        # against red flags like "not eating and hiding" or "not eating at
        # all combined with vomiting" - turning an explicit denial into a
        # false emergency trigger.
        result = classify_urgency(
            [
                {
                    "symptom": "not_eating",
                    "duration": "about a day and a half",
                    "severity_cues": ["overweight", "no vomiting", "no hiding"],
                }
            ],
            species="cat",
        )
        self.assertEqual(result["urgency"], "soon")

    def test_seizure_is_emergency_even_when_cues_dont_restate_the_word(self):
        # Regression: "seizure" is itself a red flag on the seizure entry
        # (yellow_flags is empty - any seizure warrants emergency care), but
        # real Intake Agent extraction won't always restate "seizure" or
        # "convulsions" verbatim in duration/severity_cues (e.g. it might
        # say "convulsing" instead). Providing *some* duration/cue used to
        # skip the missing_info->soon safety net without the red flag
        # actually matching, silently falling through to "home" - the
        # least cautious outcome for what should always be an emergency.
        result = classify_urgency(
            [{"symptom": "seizure", "duration": "a minute ago", "severity_cues": ["convulsing"]}],
            species="cat",
        )
        self.assertEqual(result["urgency"], "emergency")

    def test_open_mouth_breathing_in_cat_is_emergency(self):
        result = classify_urgency(
            [{"symptom": "difficulty_breathing", "duration": "just noticed", "severity_cues": ["open mouth breathing in a cat"]}],
            species="cat",
        )
        self.assertEqual(result["urgency"], "emergency")

    def test_fever_resolves_to_a_known_kb_entry(self):
        # Regression: "fever" had no KB entry at all (not even in the
        # original dog-era KB), so a real Intake Agent extraction of
        # symptom="fever" always fell into the unrecognized_symptom branch.
        # That branch has no questions_to_ask to ground the Conversation
        # Agent, so every follow-up turn - even the user repeatedly
        # confirming "yes" - produced a fresh, near-duplicate clarifying
        # question about the same thing instead of ever resolving,
        # observed live burning all 3 of the clarify-count budget on
        # variations of "is your cat warm to the touch?".
        self.assertEqual(normalize_symptom("fever"), "fever")
        self.assertEqual(normalize_symptom("body was hot"), "fever")

    def test_high_fever_with_lethargy_is_emergency(self):
        result = classify_urgency(
            [{"symptom": "fever", "duration": "since this morning", "severity_cues": ["fever with lethargy"]}],
            species="cat",
        )
        self.assertEqual(result["urgency"], "emergency")


class ClarifyCapFallbackTests(unittest.TestCase):
    def test_home_bumps_to_soon(self):
        result = apply_clarify_cap_fallback({"urgency": "home", "matched_kb_entry": None, "matched_kb_entries": [], "missing_info": ["x"]})
        self.assertEqual(result["urgency"], "soon")

    def test_emergency_stays_emergency(self):
        result = apply_clarify_cap_fallback({"urgency": "emergency", "matched_kb_entry": None, "matched_kb_entries": [], "missing_info": ["x"]})
        self.assertEqual(result["urgency"], "emergency")


if __name__ == "__main__":
    unittest.main()
