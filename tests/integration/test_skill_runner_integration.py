"""Execute-path tests with real runner/contracts and mocked external boundaries."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from evo_platform.harness.contracts import AgentContext, AgentRequest, AuthorizationTier
from evo_platform.harness.skill_loader import SkillBinding, SkillLoader
from evo_platform.harness.skill_runner import SkillAgentRunner
from evo_platform.llm.providers import LLMResponse


class SkillRunnerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        directory = self.root / "audit-skill"
        directory.mkdir()
        self.source = directory / "SKILL.md"
        self.raw = b"---\nname: audit-skill\ndescription: Audit\n---\nInspect supplied data only.\n"
        self.source.write_bytes(self.raw)
        self.digest = hashlib.sha256(self.raw).hexdigest()
        self.loader = SkillLoader(self.root, {
            "auditor": SkillBinding("audit-skill", self.digest),
        })
        self.provider = Mock()
        self.provider.model = "offline-test"
        self.provider.call.return_value = LLMResponse("ok", 2, 1, "offline-test", "mock", 0.0)
        self.audit = Mock()
        self.queue = Mock()
        self.runner = SkillAgentRunner(
            skill_loader=self.loader, system_prompt="BASE POLICY",
            llm_provider=self.provider, sandbox=Mock(),
            audit_log=self.audit, approval_queue=self.queue,
        )

    def request(self, tier, agent_id="auditor"):
        return AgentRequest(agent_id, "test-user", "test-session", "Review data",
                            context=AgentContext(authorization_tier=tier))

    def test_allowed_execute_merges_context_and_audits_digest(self):
        result = self.runner.execute(self.request(AuthorizationTier.ACT_AND_REPORT))
        self.assertTrue(result.success)
        messages = self.provider.call.call_args.args[0]
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        self.assertIn("BASE POLICY", messages[0]["content"])
        self.assertIn("Inspect supplied data only.", messages[0]["content"])
        records = [c.kwargs for c in self.audit.append.call_args_list]
        loaded = next(r for r in records if r["action"] == "skill_context_loaded")
        self.assertEqual(loaded["metadata"]["skill_sha256"], self.digest)

    def test_denied_execute_does_not_load_context_or_call_model(self):
        self.loader.for_agent = Mock(wraps=self.loader.for_agent)
        result = self.runner.execute(self.request(AuthorizationTier.OBSERVE))
        self.assertFalse(result.success)
        self.loader.for_agent.assert_not_called()
        self.provider.call.assert_not_called()

    def test_pending_execute_does_not_load_context_or_call_model(self):
        self.loader.for_agent = Mock(wraps=self.loader.for_agent)
        result = self.runner.execute(self.request(AuthorizationTier.RECOMMEND))
        self.assertFalse(result.success)
        self.queue.submit.assert_called_once()
        self.loader.for_agent.assert_not_called()
        self.provider.call.assert_not_called()

    def test_unbound_agent_fails_without_calling_model(self):
        with self.assertRaises(ValueError):
            self.runner.execute(self.request(AuthorizationTier.ACT_AND_REPORT, "other"))
        self.provider.call.assert_not_called()

    def test_wrong_digest_rejected(self):
        with self.assertRaises(ValueError):
            SkillLoader(self.root, {"auditor": SkillBinding("audit-skill", "0" * 64)})

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError):
            SkillLoader(self.root, {"auditor": SkillBinding("../audit-skill", self.digest)})

    def test_empty_base_prompt_rejected(self):
        with self.assertRaises(ValueError):
            SkillAgentRunner(skill_loader=self.loader, system_prompt=" ")


if __name__ == "__main__":
    unittest.main()
