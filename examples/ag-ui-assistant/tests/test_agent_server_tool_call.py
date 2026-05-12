"""Tests for LLM integration via emit_agui_response tool calls."""

import json
import logging
import unittest
from unittest.mock import MagicMock, patch

from services.agent_server import AGUIResponse, generate_ag_ui_response


def setUpModule():
    logging.disable(logging.CRITICAL)


def tearDownModule():
    logging.disable(logging.NOTSET)


def _completion_with_tool_call(arguments: dict) -> MagicMock:
    tc = MagicMock()
    tc.function.arguments = json.dumps(arguments, ensure_ascii=False)
    msg = MagicMock()
    msg.tool_calls = [tc]
    choice = MagicMock()
    choice.message = msg
    completion = MagicMock()
    completion.choices = [choice]
    return completion


class TestGenerateAgUiResponseToolCall(unittest.TestCase):
    @patch("services.agent_server.OpenAI")
    def test_parses_emit_agui_response_tool_arguments(self, mock_openai_cls):
        payload = {
            "components": [
                {"type": "markdown", "content": "這是一段測試內容。"},
            ],
            "suggestions": ["需要更多說明嗎？"],
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _completion_with_tool_call(
            payload
        )

        result = generate_ag_ui_response("你好")

        self.assertIsInstance(result, AGUIResponse)
        self.assertEqual(len(result.components), 1)
        self.assertEqual(result.components[0].type.value, "markdown")
        self.assertEqual(result.components[0].content, "這是一段測試內容。")
        self.assertEqual(result.suggestions, ["需要更多說明嗎？"])

        call_kw = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(call_kw["tool_choice"]["function"]["name"], "emit_agui_response")
        tools = call_kw["tools"]
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["function"]["name"], "emit_agui_response")

    @patch("services.agent_server.OpenAI")
    def test_raises_when_model_returns_no_tool_calls(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        msg = MagicMock()
        msg.tool_calls = []
        choice = MagicMock()
        choice.message = msg
        completion = MagicMock()
        completion.choices = [choice]
        mock_client.chat.completions.create.return_value = completion

        with self.assertRaises(ValueError) as ctx:
            generate_ag_ui_response("prompt")

        self.assertIn("tool call", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
