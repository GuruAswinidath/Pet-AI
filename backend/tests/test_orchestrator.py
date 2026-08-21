import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import route_turn


class RouteTurnFastPathTests(unittest.TestCase):
    def test_awaiting_clarification_status_forces_triage(self):
        session = {"status": "awaiting_clarification", "extracted_symptoms": []}
        result = route_turn(session, "yes")
        self.assertEqual(result["route"], "triage")

    def test_short_reply_with_existing_symptoms_forces_triage_without_llm(self):
        # Regression: found via a real conversation. A session's status
        # flips to "complete" after every final reply - even an
        # underspecified "home" verdict the user goes on to add detail to -
        # so the awaiting_clarification fast path alone doesn't protect the
        # very next turn. A bare "yes" confirming something safety-relevant
        # (e.g. a fever) was observed being misrouted to "knowledge" by the
        # LLM router, which then replied "I don't have that in the
        # knowledge base" instead of ever triaging the confirmation - three
        # times in a row in the same session. This must resolve to "triage"
        # deterministically, without depending on a live Groq call, so the
        # test session intentionally omits any config needed for that call.
        session = {"status": "complete", "extracted_symptoms": [{"symptom": "fever"}]}
        result = route_turn(session, "yes")
        self.assertEqual(result["route"], "triage")

    @patch("agents.orchestrator.chat_json")
    def test_short_reply_without_prior_symptoms_does_not_force_triage(self, mock_chat_json):
        # No established symptom context - nothing for a short reply to be
        # "continuing", so this should fall through to the LLM router
        # rather than being force-routed. chat_json is mocked so this stays
        # offline/deterministic like the rest of the suite.
        mock_chat_json.return_value = {"route": "knowledge", "reasoning": "mocked"}
        session = {"status": "complete", "extracted_symptoms": []}
        result = route_turn(session, "yes")
        mock_chat_json.assert_called_once()
        self.assertEqual(result["route"], "knowledge")

    @patch("agents.orchestrator.chat_json")
    def test_short_reply_phrased_as_a_question_is_not_force_routed(self, mock_chat_json):
        # A "?" signals a genuine (if short) question rather than a
        # continuation reply, so this should be left to the LLM router.
        mock_chat_json.return_value = {"route": "knowledge", "reasoning": "mocked"}
        session = {"status": "complete", "extracted_symptoms": [{"symptom": "fever"}]}
        result = route_turn(session, "why?")
        mock_chat_json.assert_called_once()
        self.assertEqual(result["route"], "knowledge")


if __name__ == "__main__":
    unittest.main()
