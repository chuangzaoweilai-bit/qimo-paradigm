# Qimo Native Model v2

## Status

Qimo Native Model v2 is a bounded experiment that moves Qimo behavior closer
to the model layer. It combines:

1. a Qwen3-1.7B base model;
2. a Qimo-specific LoRA adapter trained on origin/terminal trajectories; and
3. a deterministic Qimo kernel that retains closure authority.

This is not a foundation model trained from scratch, and it does not erase all
behavior learned by the base model. It tests whether Qimo-specific training and
runtime structure can change observable behavior under a declared protocol.

## Native Structural Kernel

The kernel treats each inference as typed state rather than free-form retry.
It provides:

- an explicit origin and externally verifiable terminal contract;
- validator-owned closure, so a model claim cannot mark a task complete;
- typed gaps that become the next executable feedback tasks;
- deterministic repair operators that can use only public task data and
  validator evidence;
- repeated-state detection and path escalation;
- explicit `not_closed` termination when the path budget is exhausted; and
- rule memory that commits only after verified closure.

The current operators cover Python syntax completion, removal of externally
rejected security identifiers, and stable precedence projection for workflow
plans. They are intentionally narrow and auditable.

## Training Protocol

The training set contains 120 generated tasks and 240 supervised trajectories:

- 40 software-repair tasks;
- 40 smart-contract audit tasks;
- 40 multi-step planning tasks; and
- two examples per task: an origin candidate and a gap-correction candidate.

The adapter was trained on Modal with these principal settings:

| Item | Value |
|---|---:|
| Base model | `Qwen/Qwen3-1.7B` |
| LoRA rank / alpha | `16 / 32` |
| Trainable parameters | `17,432,576` |
| Total parameters | `1,738,007,552` |
| Trainable ratio | `1.003%` |
| Epochs | `2` |
| Optimizer learning rate | `2e-4` |
| Effective batch size | `8` |
| Training steps | `60` |
| Final reported train loss | `0.0581` |

Training loss approached zero early. That is a warning about possible
overfitting, not evidence of general intelligence.

## Frozen Holdout Protocol

The holdout contains 30 tasks generated with a different seed: 10 tasks in
each of the same three domains. Holdout task IDs and public-contract
fingerprints are disjoint from training. The training JSONL contains no
`holdout` identifiers.

All three paths receive the same public task contract. Hidden expected answers
remain inside the external validator and are not included in model prompts.

The comparison is:

1. original Qwen, one shot;
2. original Qwen plus the Qimo native kernel; and
3. Qimo LoRA plus the same Qimo native kernel.

## Results

| Path | Closed | Closure rate | Model calls | Operator steps | Structural invariants |
|---|---:|---:|---:|---:|---:|
| Original Qwen, one shot | 16/30 | 53.33% | 30 | 0 | 100% |
| Original Qwen + native kernel | 27/30 | 90.00% | 45 | 8 | 100% |
| Qimo LoRA + native kernel | 30/30 | 100.00% | 30 | 0 | 100% |

The final path closed all ten tasks in each tested domain. Every terminal was
marked `verified_terminal` by the external validator. There were no parse
errors, no explicit path exhaustions, and no model-side `closure_claim=true`
values.

The full audit record is
[`artifacts/qimo-native-holdout-v2.json`](../artifacts/qimo-native-holdout-v2.json).
It includes every raw model output, candidate, validation result, feedback task,
operator action, termination reason, and structural invariant.

## What This Result Supports

Under this frozen synthetic protocol:

- the native kernel raised the original model from 53.33% to 90.00%;
- Qimo-specific LoRA training plus the kernel reached 100%; and
- closure remained external and auditable rather than self-declared.

This is evidence that both the structural kernel and model adaptation changed
behavior on unseen instances of the tested task families.

## What This Result Does Not Support

The holdout uses new instances of the same generator families used for
training. It is therefore an in-distribution synthetic holdout, not an
open-world or independently curated benchmark.

The result does not prove:

- 100% correctness on arbitrary tasks or domains;
- replacement of all legacy behavior in the base model;
- autonomous self-evolution or AGI;
- superiority over all existing computer architectures; or
- guaranteed terminal reachability when reality makes the terminal impossible.

In Qimo, an impossible or under-specified terminal must remain explicitly
`not_closed` with evidenced gaps. Honest non-closure is part of structural
correctness.

## Reproduction

Generate the frozen data:

```powershell
$env:PYTHONPATH = "src"
python scripts\generate_qimo_dataset.py
```

Train and deploy the adapter through Modal:

```powershell
python -m modal run -m modal_app.qimo_native_training --train --epochs 2
python -m modal deploy -m modal_app.qimo_native_training
```

Run the A/B/C holdout evaluation:

```powershell
$env:PYTHONPATH = "src"
python -m modal_app.run_native_holdout `
  --output artifacts/qimo-native-holdout-v2 `
  --per-domain 10
```

Run the local regression suite:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Next Falsification Test

The next meaningful test is a pre-registered, independently authored suite
whose task schemas and validators are frozen before any additional training.
It should include new task families, adversarial cases, impossible terminals,
and noisy real-world inputs. Failure cases must be published with the same
detail as successful closures.
