# Experimentation and rollouts

Experiments are versioned artifacts, not informal traffic switches. Each
experiment declares a hypothesis, baseline, variants, primary metric, minimum
detectable effect, guardrails, traffic steps, and rollback conditions.

## Stages

```text
Offline -> Shadow -> Canary -> A/B -> Full rollout
```

Offline evaluation blocks unsafe or invalid candidates. Shadow traffic measures
real behavior without user-visible side effects. Canary increases exposure in
controlled steps. A/B compares variants against a stable baseline. Full rollout
requires passing quality, safety, cost, latency, and regression guardrails.

## Rollback

Roll back immediately on critical safety violations, unauthorized tool actions,
material quality regression, budget breaches, or sustained latency breaches.

Rollback decisions should create an audit record linked to the experiment,
capability, trace sample, and policy version.
