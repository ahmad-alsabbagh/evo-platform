# Evaluation Harness

## Golden Evaluation Sets

This directory contains graded evaluation sets for all capabilities.

### Structure

Each eval set follows this schema:

```json
{
  "capability_id": "string",
  "capability_version": "string",
  "examples": [
    {
      "id": "string",
      "input": "string",
      "expected_output": "string",
      "metadata": {
        "difficulty": "easy|medium|hard",
        "category": "string",
        "tags": ["string"]
      },
      "scorers": {
        "semantic_similarity": 0.95,
        "exact_match": false,
        "llm_judge_score": 4.5,
        "custom_scorers": {
          "response_time": 0.8,
          "helpfulness": 0.9
        }
      }
    }
  ],
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "owner": "string"
}
```

### Minimum Requirements

- **100-300 examples** per capability before production deployment
- **Graded difficulty**: 40% easy, 40% medium, 20% hard
- **Coverage**: All major use cases and edge cases
- **Regular updates**: Add failure cases from production weekly

### Available Eval Sets

- `customer-support-golden.json` - Customer support agent evaluation
- Coming soon: sales, hr, marketing, etc.

## Running Evaluations

```bash
# Run evals for a capability
python -m evo_platform.harness.eval_runner \
  --capability customer-support \
  --eval-set evals/customer-support-golden.json \
  --output results/customer-support-eval.json
```

## Scoring Thresholds

| Metric | Production Threshold | Warning Threshold |
|---|---|---|
| Semantic Similarity | >0.85 | 0.75-0.85 |
| LLM Judge Score | >4.0/5.0 | 3.5-4.0 |
| Response Time | <2s | 2-3s |
| Helpfulness | >0.8 | 0.7-0.8 |

## Continuous Improvement

1. Add production failures to eval set weekly
2. Re-run evals before every capability update
3. Track score trends over time
4. Block deployments that regress below thresholds
