# Qimo Multi-domain Benchmark v1

## Frozen Protocol

- Benchmark ID: `qimo-multidomain-v1`
- Validator protocol: `1.0.0`
- Base model: `Qwen/Qwen3-1.7B`
- Compute: NVIDIA T4 on Modal
- Decoding: deterministic, `do_sample=false`
- Output limit: 320 new tokens per generation
- Tasks: 6 across 3 domains
- Maximum epochs: 1 for one-shot; 3 for generic retry and Qimo
- Runtime: 211.97 seconds

The task contracts, answer schemas, validators, and feedback protocol were
frozen before this recorded run.

## Result

| Mode | Closed | Closure rate | Final score | Avg epochs | Model calls |
|---|---:|---:|---:|---:|---:|
| One shot | 3/6 | 50.0% | 0.789 | 1.00 | 6 |
| Generic retry | 3/6 | 50.0% | 0.789 | 2.00 | 12 |
| Qimo | 4/6 | 66.7% | 0.844 | 1.83 | 11 |

In this pilot, Qimo closed one additional task while using one fewer model call
than generic retry. The improvement was 16.7 percentage points in closure rate
and 0.055 in mean final score.

## Task-level Result

| Task | Domain | One shot | Generic retry | Qimo |
|---|---|---|---|---|
| `software.clamp-boundaries` | Software repair | closed | closed | closed |
| `software.off-by-one` | Software repair | not closed | not closed | closed at epoch 2 |
| `contracts.withdraw-order` | Smart-contract audit | not closed | not closed | not closed |
| `contracts.owner-validation` | Smart-contract audit | not closed | not closed | not closed |
| `planning.release-order` | Multi-step planning | closed | closed | closed |
| `planning.data-pipeline` | Multi-step planning | closed | closed | closed |

The Qimo-specific gain came from an explicit syntax gap. The first software
candidate had the correct loop bound but omitted the required Python colon.
Generic retry repeated the same incomplete answer for three epochs. Qimo
received the precise validator gap and returned a syntactically complete patch
in epoch 2.

The two smart-contract tasks remained open. Qimo partially removed unsupported
findings in one task but did not reach the exact evidence-backed finding set
within three epochs. The runtime preserved those failures as `not_closed`.

## Verifier Development Disclosure

Two development runs were performed before protocol `1.0.0` was frozen. They
revealed that one software gap was too vague and that one security gap code
contained an expected label. Both defects were removed, regression tests were
added, and the final benchmark was run from the frozen protocol without further
changes. Development runs are not included in the reported result.

## Reproduce

Run the deterministic validator and runtime tests:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Run the real base-model benchmark after deploying the Modal app:

```powershell
$env:PYTHONPATH = "src"
python -m modal deploy -m modal_app.qimo_modal
python -m modal_app.run_multidomain_benchmark --output artifacts/qimo-multidomain-v1
```

The complete 79 KB audit record is available at
[`artifacts/qimo-multidomain-v1.json`](../artifacts/qimo-multidomain-v1.json).
It includes every raw generation, candidate, parse result, external validation,
gap, feedback task, rule snapshot, and closure decision.

## Limitations

- Six tasks are not statistically sufficient for a general performance claim.
- All tasks are small and have deterministic validators.
- Only one 1.7B-parameter base model was tested.
- The benchmark tests inference-time structural adaptation, not weight updates.
- The domains are represented by two tasks each and do not measure full domain expertise.
- Independent reproduction has not yet been completed.

The correct conclusion is narrow: under this frozen pilot protocol, explicit
verified gaps improved closure for one task without increasing model calls over
generic retry. A 100-task pre-registered benchmark is the next evidence target.
