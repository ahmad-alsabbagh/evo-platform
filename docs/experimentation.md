# Experimentation and Rollouts

Experiments are versioned artifacts, not informal traffic switches. Each experiment declares a hypothesis, baseline, variants, primary metric, minimum detectable effect, guardrails, traffic steps, and rollback conditions.

## Stages

```text
Offline -> Shadow -> Canary -> A/B -> Full rollout
```

Offline evaluation blocks obviously unsafe or invalid candidates. Shadow traffic measures realistic behavior without user-visible side effects. Canary increases exposure in controlled steps. A/B compares variants against a stable baseline. Full rollout requires passing quality, safety, cost, latency, and regression guardrails.

## Rollback

Rollback immediately on critical safety violations, unauthorized tool actions, material quality regression, budget breach, or sustained latency breach. Rollback decisions must produce an audit record linked to the experiment, capability, trace sample, and policy version.
