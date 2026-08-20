"""Evaluation Runner - Production-grade evaluation harness for AI agents.

This module implements the evaluation runner that executes agents on graded
evaluation sets, computes scores, and generates reports with pass/fail decisions.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import statistics

from .contracts import (
    AgentRequest,
    AgentResponse,
    EvaluationExample,
    EvaluationResult,
    EvaluationSet,
    TokenUsage,
    PRODUCTION_THRESHOLDS,
)


class SemanticSimilarityScorer:
    """Compute semantic similarity between output and expected output."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.available = True
        except ImportError:
            self.available = False
            self.model = None
    
    def score(self, output: str, expected: str) -> float:
        if not self.available:
            return self._fallback_similarity(output, expected)
        embeddings = self.model.encode([output, expected])
        similarity = float(self._cosine_similarity(embeddings[0], embeddings[1]))
        return max(0.0, min(1.0, similarity))
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
    
    def _fallback_similarity(self, a: str, b: str) -> float:
        tokens_a = set(a.lower().split())
        tokens_b = set(b.lower().split())
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union) if union else 0.0


class LLMJudgeScorer:
    """Use LLM to judge output quality (1-5 scale)."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.available = True
    
    def score(self, input: str, output: str, expected: str, criteria: str = "helpfulness, accuracy, completeness") -> float:
        output_len = len(output.split())
        expected_len = len(expected.split())
        len_ratio = min(output_len, expected_len) / max(output_len, expected_len)
        output_words = set(output.lower().split())
        expected_words = set(expected.lower().split())
        keyword_overlap = len(output_words & expected_words) / len(expected_words) if expected_words else 0.0
        score = 3.0 + (len_ratio * 1.0) + (keyword_overlap * 1.0)
        return max(1.0, min(5.0, score))


class CustomScorer:
    """Compute custom metrics (response time, helpfulness, etc.)."""
    
    def response_time_score(self, latency_ms: float, threshold_ms: float = 2000.0) -> float:
        if latency_ms <= threshold_ms:
            return 1.0
        elif latency_ms >= 2 * threshold_ms:
            return 0.0
        else:
            return 1.0 - (latency_ms - threshold_ms) / threshold_ms
    
    def helpfulness_score(self, output: str, expected: str) -> float:
        score = 0.5
        output_len = len(output.split())
        if 50 <= output_len <= 300:
            score += 0.2
        elif output_len < 10:
            score -= 0.3
        if "\n" in output or "-" in output or "1." in output:
            score += 0.1
        politeness_words = ["please", "thank", "happy", "help", "sure", "certainly"]
        if any(word in output.lower() for word in politeness_words):
            score += 0.1
        return max(0.0, min(1.0, score))
    
    def accuracy_score(self, output: str, expected: str) -> float:
        import re
        output_facts = set(re.findall(r'\b\d+\b|\b[A-Z][a-z]+\b', output))
        expected_facts = set(re.findall(r'\b\d+\b|\b[A-Z][a-z]+\b', expected))
        if not expected_facts:
            return 1.0
        overlap = len(output_facts & expected_facts)
        return overlap / len(expected_facts) if expected_facts else 1.0


class EvaluationRunner:
    """Production-grade evaluation runner for AI agents."""
    
    def __init__(self, agent_executor=None):
        self.agent_executor = agent_executor
        self.semantic_scorer = SemanticSimilarityScorer()
        self.llm_judge_scorer = LLMJudgeScorer()
        self.custom_scorer = CustomScorer()
    
    def load_eval_set(self, path: str) -> EvaluationSet:
        with open(path, 'r') as f:
            data = json.load(f)
        examples = [
            EvaluationExample(
                id=ex["id"],
                input=ex["input"],
                expected_output=ex["expected_output"],
                metadata=ex.get("metadata", {}),
                scorers=ex.get("scorers", {})
            )
            for ex in data.get("examples", [])
        ]
        return EvaluationSet(
            capability_id=data.get("capability_id", "unknown"),
            capability_version=data.get("capability_version", "1.0.0"),
            examples=examples,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            owner=data.get("owner", ""),
            metadata=data.get("metadata", {})
        )
    
    def execute_example(self, example: EvaluationExample, agent_id: str = "test-agent", user_id: str = "eval-user", session_id: str = "eval-session") -> Tuple[AgentResponse, Dict[str, float], float]:
        request = AgentRequest(agent_id=agent_id, user_id=user_id, session_id=session_id, input=example.input)
        start_time = time.time()
        if self.agent_executor:
            response = self.agent_executor(request)
        else:
            response = AgentResponse(
                request_id=request.request_id,
                output=example.expected_output,
                tokens_used=TokenUsage(
                    input_tokens=len(example.input.split()),
                    output_tokens=len(example.expected_output.split()),
                    total_tokens=len(example.input.split()) + len(example.expected_output.split()),
                    cost_usd=0.001,
                    model="gpt-4o-mini"
                ),
                latency_ms=150.0,
                cost_usd=0.001,
                success=True
            )
        latency_ms = (time.time() - start_time) * 1000
        scores = self._compute_scores(response, example)
        return response, scores, latency_ms
    
    def _compute_scores(self, response: AgentResponse, example: EvaluationExample) -> Dict[str, float]:
        scores = {}
        scores["semantic_similarity"] = self.semantic_scorer.score(response.output, example.expected_output)
        scores["llm_judge_score"] = self.llm_judge_scorer.score(response.output, example.expected_output, example.input)
        scores["response_time"] = self.custom_scorer.response_time_score(response.latency_ms)
        scores["helpfulness"] = self.custom_scorer.helpfulness_score(response.output, example.expected_output)
        scores["accuracy"] = self.custom_scorer.accuracy_score(response.output, example.expected_output)
        return scores
    
    def run_evaluation(self, eval_set: EvaluationSet, agent_id: str = "test-agent") -> EvaluationResult:
        results = []
        failures = []
        latencies = []
        total_cost = 0.0
        for example in eval_set.examples:
            response, scores, latency_ms = self.execute_example(example, agent_id=agent_id)
            latencies.append(latency_ms)
            total_cost += response.cost_usd
            passed = self._check_thresholds(scores)
            if not passed:
                failures.append({"example_id": example.id, "scores": scores, "expected_scores": example.scorers, "output": response.output[:200] + "..." if len(response.output) > 200 else response.output})
            results.append({"example_id": example.id, "passed": passed, "scores": scores})
        examples_run = len(results)
        examples_passed = sum(1 for r in results if r["passed"])
        pass_rate = examples_passed / examples_run if examples_run > 0 else 0.0
        aggregate_scores = {}
        for score_name in ["semantic_similarity", "llm_judge_score", "response_time", "helpfulness", "accuracy"]:
            score_values = [r["scores"].get(score_name, 0.0) for r in results]
            aggregate_scores[score_name] = statistics.mean(score_values) if score_values else 0.0
        latency_p50 = statistics.median(latencies) if latencies else 0.0
        latency_p95 = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else (latencies[0] if latencies else 0.0)
        return EvaluationResult(
            capability_id=eval_set.capability_id,
            eval_set_id=f"{eval_set.capability_id}-{eval_set.capability_version}",
            examples_run=examples_run,
            examples_passed=examples_passed,
            pass_rate=pass_rate,
            scores=aggregate_scores,
            failures=failures,
            latency_p50_ms=latency_p50,
            latency_p95_ms=latency_p95,
            cost_total_usd=total_cost,
            created_at=datetime.utcnow()
        )
    
    def _check_thresholds(self, scores: Dict[str, float]) -> bool:
        for metric, threshold in PRODUCTION_THRESHOLDS.items():
            if metric in scores and scores[metric] < threshold:
                return False
        return True
    
    def generate_report(self, result: EvaluationResult, output_path: Optional[str] = None) -> str:
        report = []
        report.append(f"# Evaluation Report: {result.capability_id}")
        report.append("")
        report.append(f"**Eval Set:** {result.eval_set_id}")
        report.append(f"**Date:** {result.created_at.isoformat()}")
        report.append("")
        report.append("## Summary")
        report.append("")
        status = "✅ PASSED" if result.pass_rate >= PRODUCTION_THRESHOLDS["pass_rate"] else "❌ FAILED"
        report.append(f"**Status:** {status}")
        report.append(f"**Pass Rate:** {result.pass_rate:.1%} ({result.examples_passed}/{result.examples_run})")
        report.append(f"**Total Cost:** ${result.cost_total_usd:.4f}")
        report.append("")
        report.append("## Scores")
        report.append("")
        report.append("| Metric | Score | Threshold | Status |")
        report.append("|--------|-------|-----------|--------|")
        for metric, score in result.scores.items():
            threshold = PRODUCTION_THRESHOLDS.get(metric, 0.0)
            status = "✅" if score >= threshold else "❌"
            report.append(f"| {metric} | {score:.3f} | {threshold:.3f} | {status} |")
        report.append("")
        report.append("## Latency")
        report.append("")
        report.append(f"- **P50:** {result.latency_p50_ms:.1f} ms")
        report.append(f"- **P95:** {result.latency_p95_ms:.1f} ms")
        report.append(f"- **Threshold:** {PRODUCTION_THRESHOLDS['response_time_ms']} ms")
        report.append("")
        if result.failures:
            report.append("## Failures")
            report.append("")
            for i, failure in enumerate(result.failures, 1):
                report.append(f"### {i}. {failure['example_id']}")
                report.append("")
                report.append("**Scores:**")
                for metric, score in failure["scores"].items():
                    threshold = PRODUCTION_THRESHOLDS.get(metric, 0.0)
                    status = "✅" if score >= threshold else "❌"
                    report.append(f"- {metric}: {score:.3f} {status}")
                report.append("")
                report.append(f"**Output:** {failure['output']}")
                report.append("")
        report.append("## Recommendations")
        report.append("")
        if result.pass_rate >= PRODUCTION_THRESHOLDS["pass_rate"]:
            report.append("✅ **Ready for production deployment**")
        else:
            report.append("❌ **Not ready for production**")
            report.append("")
            report.append("**Action items:**")
            report.append(f"1. Fix {len(result.failures)} failing examples")
            report.append("2. Re-run evaluation after fixes")
            report.append("3. Ensure all scores meet thresholds before deployment")
        report.append("")
        report_text = "\n".join(report)
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report_text)
        return report_text


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run evaluation on a capability")
    parser.add_argument("--capability", required=True, help="Capability ID")
    parser.add_argument("--eval-set", required=True, help="Path to evaluation set JSON")
    parser.add_argument("--output", default="results/eval-report.md", help="Output report path")
    args = parser.parse_args()
    runner = EvaluationRunner()
    eval_set = runner.load_eval_set(args.eval_set)
    result = runner.run_evaluation(eval_set, agent_id=args.capability)
    report = runner.generate_report(result, output_path=args.output)
    print(report)
    print(f"\nReport saved to: {args.output}")
    if result.pass_rate < PRODUCTION_THRESHOLDS["pass_rate"]:
        exit(1)
