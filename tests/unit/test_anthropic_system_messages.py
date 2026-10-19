"""Regression tests using the complete provider module and an offline SDK mock."""
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[2] / "src/evo_platform/llm/providers.py"
SPEC = importlib.util.spec_from_file_location("provider_regression_target", SOURCE)
providers = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = providers
SPEC.loader.exec_module(providers)


class SystemMessageTests(unittest.TestCase):
    def setUp(self):
        self.provider = providers.AnthropicProvider.__new__(providers.AnthropicProvider)
        self.provider.model = "claude-3-haiku-20240307"
        response = SimpleNamespace(content=[SimpleNamespace(text="answer")],
                                   usage=SimpleNamespace(input_tokens=10, output_tokens=5))
        self.create = Mock(return_value=response)
        self.provider.client = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def test_merges_in_order(self):
        result = self.provider.call([
            {"role": "system", "content": "Base policy"},
            {"role": "system", "content": "Skill instructions"},
            {"role": "user", "content": "Question"},
        ], max_tokens=123)
        payload = self.create.call_args.kwargs
        self.assertEqual(payload["system"], "Base policy\n\nSkill instructions")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "Question"}])
        self.assertEqual(payload["max_tokens"], 123)
        self.assertEqual(result.content, "answer")
        self.assertEqual((result.input_tokens, result.output_tokens), (10, 5))

    def test_single_system(self):
        self.provider.call([{"role": "system", "content": "Policy"}])
        self.assertEqual(self.create.call_args.kwargs["system"], "Policy")

    def test_no_system(self):
        self.provider.call([{"role": "user", "content": "Question"}])
        self.assertEqual(self.create.call_args.kwargs["system"], "")

    def test_chat_and_input_preserved(self):
        messages = [
            {"role": "system", "content": "First"},
            {"role": "user", "content": "One"},
            {"role": "assistant", "content": "Two"},
            {"role": "system", "content": "Second"},
            {"role": "user", "content": "Three"},
        ]
        original = copy.deepcopy(messages)
        self.provider.call(messages)
        payload = self.create.call_args.kwargs
        self.assertEqual(payload["system"], "First\n\nSecond")
        self.assertEqual(payload["messages"], [messages[1], messages[2], messages[4]])
        self.assertEqual(messages, original)

    def test_empty_section_preserved(self):
        self.provider.call([
            {"role": "system", "content": "First"},
            {"role": "system", "content": ""},
            {"role": "system", "content": "Third"},
        ])
        self.assertEqual(self.create.call_args.kwargs["system"], "First\n\n\n\nThird")


if __name__ == "__main__":
    unittest.main()
