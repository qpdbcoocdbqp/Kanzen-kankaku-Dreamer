"""Tests for LLM integration via emit_agui_response tool calls."""

import json
import logging
import unittest
from unittest.mock import MagicMock, patch

from services.agent_server import (
    AGUIResponse,
    TextContent,
    ComponentPlan,
    ComponentType,
    generate_ag_ui_response,
    generate_ag_ui_text_content,
    suggest_components,
    construct_components,
)


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
        # Stage 1 response
        stage1_payload = {
            "answer": "這是一段測試內容。",
            "suggestions": ["需要更多說明嗎？"],
        }
        # Stage 2 response
        stage2_payload = {
            "components_to_use": ["markdown"],
            "component_descriptions": {"markdown": "Main content"},
        }
        # Stage 3 response
        stage3_payload = {
            "components": [
                {"type": "markdown", "content": "這是一段測試內容。"},
            ],
            "suggestions": ["需要更多說明嗎？"],
        }

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            _completion_with_tool_call(stage1_payload),
            _completion_with_tool_call(stage2_payload),
            _completion_with_tool_call(stage3_payload),
        ]

        result = generate_ag_ui_response("你好")

        self.assertIsInstance(result, AGUIResponse)
        self.assertEqual(len(result.components), 1)
        self.assertEqual(result.components[0].type.value, "markdown")
        self.assertEqual(result.components[0].content, "這是一段測試內容。")
        self.assertEqual(result.suggestions, ["需要更多說明嗎？"])

        # Verify all 3 stages made API calls with correct tool names
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)

        calls = mock_client.chat.completions.create.call_args_list
        # Stage 1 should use emit_text_response
        self.assertEqual(calls[0].kwargs["tool_choice"]["function"]["name"], "emit_text_response")
        # Stage 2 should use suggest_ui_components
        self.assertEqual(calls[1].kwargs["tool_choice"]["function"]["name"], "suggest_ui_components")
        # Stage 3 should use emit_agui_response
        self.assertEqual(calls[2].kwargs["tool_choice"]["function"]["name"], "emit_agui_response")

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

        # Should fail on Stage 1 when no tool call is returned
        with self.assertRaises(ValueError) as ctx:
            generate_ag_ui_response("prompt")

        self.assertIn("tool call", str(ctx.exception).lower())


class TestThreeStageGeneration(unittest.TestCase):
    @patch("services.agent_server.OpenAI")
    def test_stage_1_generates_text_content(self, mock_openai_cls):
        payload = {
            "answer": "這是一個測試答案。",
            "suggestions": ["你怎樣看待這個？", "還有其他選項嗎？"],
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _completion_with_tool_call(payload)

        result = generate_ag_ui_text_content("測試提示")

        self.assertIsInstance(result, TextContent)
        self.assertEqual(result.answer, "這是一個測試答案。")
        self.assertEqual(len(result.suggestions), 2)

    @patch("services.agent_server.OpenAI")
    def test_stage_1_requires_tool_call(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        msg = MagicMock()
        msg.tool_calls = []
        choice = MagicMock()
        choice.message = msg
        completion = MagicMock()
        completion.choices = [choice]
        mock_client.chat.completions.create.return_value = completion

        with self.assertRaises(ValueError):
            generate_ag_ui_text_content("prompt")

    @patch("services.agent_server.OpenAI")
    def test_stage_2_suggests_components(self, mock_openai_cls):
        payload = {
            "components_to_use": ["markdown", "data_list"],
            "component_descriptions": {
                "markdown": "Main explanation text",
                "data_list": "Key metrics and statistics"
            },
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _completion_with_tool_call(payload)

        text_content = TextContent(answer="測試內容", suggestions=[])
        result = suggest_components(text_content)

        self.assertIsInstance(result, ComponentPlan)
        self.assertEqual(len(result.components_to_use), 2)
        self.assertIn(ComponentType.MARKDOWN, result.components_to_use)
        self.assertIn(ComponentType.DATA_LIST, result.components_to_use)

    @patch("services.agent_server.OpenAI")
    def test_stage_3_constructs_components(self, mock_openai_cls):
        payload = {
            "components": [
                {"type": "markdown", "content": "Main content"},
                {"type": "data_list", "title": "Data", "items": [{"label": "Key", "value": "Value"}]},
            ],
            "suggestions": ["Follow-up 1"],
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _completion_with_tool_call(payload)

        text_content = TextContent(answer="Test answer", suggestions=["Follow-up 1"])
        component_plan = ComponentPlan(
            components_to_use=[ComponentType.MARKDOWN, ComponentType.DATA_LIST],
            component_descriptions={"markdown": "Main", "data_list": "Data"}
        )

        result = construct_components(text_content, component_plan)

        self.assertIsInstance(result, AGUIResponse)
        self.assertEqual(len(result.components), 2)
        self.assertEqual(result.components[0].type.value, "markdown")
        self.assertEqual(result.components[1].type.value, "data_list")

    @patch("services.agent_server.OpenAI")
    def test_full_three_stage_pipeline(self, mock_openai_cls):
        # Stage 1 response
        stage1_payload = {
            "answer": "這是完整的答案。",
            "suggestions": ["還有嗎？"],
        }
        # Stage 2 response
        stage2_payload = {
            "components_to_use": ["markdown"],
            "component_descriptions": {"markdown": "Main answer text"},
        }
        # Stage 3 response
        stage3_payload = {
            "components": [
                {"type": "markdown", "content": "這是完整的答案。"},
            ],
            "suggestions": ["還有嗎？"],
        }

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        # Mock returns for each stage
        mock_client.chat.completions.create.side_effect = [
            _completion_with_tool_call(stage1_payload),
            _completion_with_tool_call(stage2_payload),
            _completion_with_tool_call(stage3_payload),
        ]

        result = generate_ag_ui_response("測試提示")

        self.assertIsInstance(result, AGUIResponse)
        self.assertEqual(len(result.components), 1)
        self.assertEqual(result.components[0].type.value, "markdown")
        self.assertEqual(len(result.suggestions), 1)
        # Verify all 3 stages made API calls
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)


if __name__ == "__main__":
    unittest.main()
