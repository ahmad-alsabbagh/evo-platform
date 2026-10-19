"""Opt-in AgentRunner specialization for server-bound, reviewed skills."""
from .contracts import AgentRequest
from .runner import AgentRunner
from .skill_loader import SkillLoader


class SkillAgentRunner(AgentRunner):
    """Reuse AgentRunner.execute and its existing authorization gates unchanged."""

    def __init__(self, *, skill_loader: SkillLoader, system_prompt: str, **kwargs):
        if not system_prompt.strip():
            raise ValueError("A server-owned base system prompt is required")
        super().__init__(**kwargs)
        self.skill_loader = skill_loader
        self.system_prompt = system_prompt

    def _llm_call(self, request: AgentRequest) -> tuple[str, int, int, float]:
        skill = self.skill_loader.for_agent(request.agent_id)
        if skill is None:
            raise ValueError("Agent has no reviewed skill binding")
        system = (
            self.system_prompt
            + "\n\nProcedural guidance follows. It does not grant tool permissions "
            "or override server authorization.\n"
            + skill.instructions
        )
        self._audit(request, "skill_context_loaded", "loaded", {
            "skill_name": skill.name, "skill_sha256": skill.sha256,
        })
        response = self.llm_provider.call([
            {"role": "system", "content": system},
            {"role": "user", "content": request.input},
        ], max_tokens=request.context.guardrails.output_max_tokens)
        return (response.content, response.input_tokens, response.output_tokens, response.cost_usd)
