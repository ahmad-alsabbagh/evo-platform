"""Hierarchical multi-agent orchestration.

Routes complex requests to specialized sub-agents based on intent classification.
Each sub-agent has its own governance, cost tracking, and audit trail.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

from ..harness.contracts import AgentRequest, AgentResponse, AgentContext, Guardrails, AuthorizationTier
from ..harness.runner import AgentRunner, AgentRunnerConfig
from ..llm.providers import LLMProviderBase


class IntentType(Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    GENERAL = "general"


@dataclass
class SubAgent:
    name: str
    description: str
    intent_patterns: List[str]
    runner: AgentRunner
    default_action_type: str = "generate_response"
    authorization_tier: AuthorizationTier = AuthorizationTier.ACT_AND_REPORT
    spending_cap_usd: float = 1.0


class OrchestratorAgent:
    def __init__(self, llm_provider: LLMProviderBase, config: Optional[AgentRunnerConfig] = None):
        self.llm_provider = llm_provider
        self.config = config or AgentRunnerConfig()
        self.sub_agents: Dict[IntentType, SubAgent] = {}
        self._setup_default_sub_agents()

    def _setup_default_sub_agents(self):
        # Billing Agent
        billing_runner = AgentRunner(
            llm_provider=self.llm_provider,
            config=AgentRunnerConfig(
                default_action_type="billing_inquiry",
                cost_per_1k_input_tokens=self.config.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=self.config.cost_per_1k_output_tokens,
            )
        )
        self.sub_agents[IntentType.BILLING] = SubAgent(
            name="billing-agent",
            description="Handles refunds, payments, invoices",
            intent_patterns=[r"refund", r"payment", r"invoice", r"bill", r"charge"],
            runner=billing_runner,
            default_action_type="billing_inquiry",
            authorization_tier=AuthorizationTier.REQUIRE_APPROVAL,
            spending_cap_usd=0.50,
        )

        # Technical Support Agent
        tech_runner = AgentRunner(
            llm_provider=self.llm_provider,
            config=AgentRunnerConfig(
                default_action_type="technical_support",
                cost_per_1k_input_tokens=self.config.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=self.config.cost_per_1k_output_tokens,
            )
        )
        self.sub_agents[IntentType.TECHNICAL] = SubAgent(
            name="technical-agent",
            description="Handles bugs, errors, troubleshooting",
            intent_patterns=[r"bug", r"error", r"issue", r"problem", r"how to", r"broken"],
            runner=tech_runner,
            default_action_type="technical_support",
            authorization_tier=AuthorizationTier.ACT_AND_REPORT,
            spending_cap_usd=0.50,
        )

        # Account Agent
        account_runner = AgentRunner(
            llm_provider=self.llm_provider,
            config=AgentRunnerConfig(
                default_action_type="account_management",
                cost_per_1k_input_tokens=self.config.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=self.config.cost_per_1k_output_tokens,
            )
        )
        self.sub_agents[IntentType.ACCOUNT] = SubAgent(
            name="account-agent",
            description="Handles password reset, profile, deletion",
            intent_patterns=[r"password", r"account", r"profile", r"reset"],
            runner=account_runner,
            default_action_type="account_management",
            authorization_tier=AuthorizationTier.ACT_AND_REPORT,
            spending_cap_usd=0.50,
        )

        # General Agent (fallback)
        general_runner = AgentRunner(
            llm_provider=self.llm_provider,
            config=AgentRunnerConfig(
                default_action_type="general_inquiry",
                cost_per_1k_input_tokens=self.config.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=self.config.cost_per_1k_output_tokens,
            )
        )
        self.sub_agents[IntentType.GENERAL] = SubAgent(
            name="general-agent",
            description="Handles general questions and fallback",
            intent_patterns=[r".*"],
            runner=general_runner,
            default_action_type="general_inquiry",
            authorization_tier=AuthorizationTier.ACT_AND_REPORT,
            spending_cap_usd=0.50,
        )

    def _classify_intent(self, user_input: str) -> IntentType:
        user_input_lower = user_input.lower()
        for intent_type, sub_agent in self.sub_agents.items():
            if intent_type == IntentType.GENERAL:
                continue
            for pattern in sub_agent.intent_patterns:
                if re.search(pattern, user_input_lower):
                    return intent_type
        return IntentType.GENERAL

    def _create_sub_agent_request(self, user_request: AgentRequest, sub_agent: SubAgent) -> AgentRequest:
        return AgentRequest(
            agent_id=sub_agent.name,
            user_id=user_request.user_id,
            session_id=user_request.session_id,
            input=user_request.input,
            context=AgentContext(
                tools=user_request.context.tools,
                guardrails=Guardrails(
                    spending_cap_usd=sub_agent.spending_cap_usd,
                    tool_allowlist=user_request.context.guardrails.tool_allowlist,
                    tool_denylist=user_request.context.guardrails.tool_denylist,
                ),
                authorization_tier=sub_agent.authorization_tier,
                session_metadata={
                    **user_request.context.session_metadata,
                    "orchestrator_routed": True,
                    "routed_to": sub_agent.name,
                },
            ),
            request_id=user_request.request_id,
        )

    def execute(self, user_request: AgentRequest) -> AgentResponse:
        intent = self._classify_intent(user_request.input)
        sub_agent = self.sub_agents[intent]
        sub_request = self._create_sub_agent_request(user_request, sub_agent)
        response = sub_agent.runner.execute(sub_request, action_type=sub_agent.default_action_type)
        response.output = f"[{sub_agent.name}]: {response.output}"
        return response


def create_orchestrator(llm_provider: LLMProviderBase) -> OrchestratorAgent:
    return OrchestratorAgent(llm_provider=llm_provider)
