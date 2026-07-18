# Qimo Multi-domain Benchmark

- Benchmark: `qimo-multidomain-v1`
- Validator protocol: `1.0.0`
- Base-model control: same base model and decoding; only the runtime mode changes
- Base model: `Qwen/Qwen3-1.7B`
- Runtime: 211.97 seconds
- Tasks: 6
- Domains: multi_step_planning, smart_contract_audit, software_repair

## Summary

| Mode | Closed | Closure rate | Final score | Avg epochs | Model calls | False closure claims |
|---|---:|---:|---:|---:|---:|---:|
| one_shot | 3/6 | 50.0% | 0.789 | 1.00 | 6 | 0 |
| generic_retry | 3/6 | 50.0% | 0.789 | 2.00 | 12 | 0 |
| qimo | 4/6 | 66.7% | 0.844 | 1.83 | 11 | 0 |

## Task outcomes

### `one_shot`

- `software.clamp-boundaries`: **closed**, score=1.000, epochs=1
- `software.off-by-one`: **not_closed**, score=0.800, epochs=1
- `contracts.withdraw-order`: **not_closed**, score=0.467, epochs=1
- `contracts.owner-validation`: **not_closed**, score=0.467, epochs=1
- `planning.release-order`: **closed**, score=1.000, epochs=1
- `planning.data-pipeline`: **closed**, score=1.000, epochs=1

### `generic_retry`

- `software.clamp-boundaries`: **closed**, score=1.000, epochs=1
- `software.off-by-one`: **not_closed**, score=0.800, epochs=3
- `contracts.withdraw-order`: **not_closed**, score=0.467, epochs=3
- `contracts.owner-validation`: **not_closed**, score=0.467, epochs=3
- `planning.release-order`: **closed**, score=1.000, epochs=1
- `planning.data-pipeline`: **closed**, score=1.000, epochs=1

### `qimo`

- `software.clamp-boundaries`: **closed**, score=1.000, epochs=1
- `software.off-by-one`: **closed**, score=1.000, epochs=2
- `contracts.withdraw-order`: **not_closed**, score=0.600, epochs=3
- `contracts.owner-validation`: **not_closed**, score=0.467, epochs=3
- `planning.release-order`: **closed**, score=1.000, epochs=1
- `planning.data-pipeline`: **closed**, score=1.000, epochs=1

## Interpretation boundary

This benchmark does not demonstrate consciousness, AGI, weight-level learning, or unlimited self-evolution. It tests whether explicit verified gaps improve task closure for an unchanged base model.
