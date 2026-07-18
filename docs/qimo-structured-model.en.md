# Qimo Structured Model

## Scope

`QimoStructuredModel` is the first executable model runtime in this repository.
It restructures how an unchanged base model is used; it does not modify the
base model's architecture or weights.

This distinction creates a controlled experiment:

```text
constant: model weights, decoding, tasks, validators, token limit
variable: inference runtime
```

Any measured difference can therefore be attributed to the runtime protocol
within the declared benchmark, rather than to a different model or hidden
fine-tuning data.

## Runtime Structure

```text
origin contract
  -> terminal contract
  -> candidate generation
  -> deterministic domain validator
  -> explicit evidence and gaps
  -> feedback tasks
  -> new candidate
  -> external closure decision
  -> verified rule memory
```

The base model can generate candidates and evidence. It cannot declare the
terminal closed. A candidate remains `not_closed` whenever parsing fails, a
declared check fails, evidence is missing, or an unsupported result appears.

## Three Controlled Modes

### `one_shot`

The base model receives the task contract once. The external validator checks
the result, and the run ends.

### `generic_retry`

The base model may try up to three times. After failure it receives only a
generic message that the previous candidate failed. It does not receive the
validator's structured gaps.

### `qimo`

The base model may try up to three times. Every failed candidate becomes an
explicit list of gap codes, repair tasks, and required evidence. The next epoch
must resolve those gaps. Closure still belongs exclusively to the external
validator.

## Verified Rule Memory

Universal rules are present from the start:

```text
no_silent_success
external_validator_controls_closure
failed_candidate_must_remain_not_closed
```

Domain rules are committed only after verified closure. A failed candidate
cannot write rules into memory. This prevents an unverified model statement
from becoming a future system rule.

The current pilot includes these verified domain rules:

```text
software_patch_must_satisfy_declared_behavior
security_finding_requires_code_evidence
plan_must_cover_steps_and_respect_precedence
```

## Machine-verifiable Domains

The initial suite contains two tasks in each domain:

- Software repair: exact replacement lines plus declared behavior checks.
- Smart-contract audit: normalized finding identifiers with code evidence.
- Multi-step planning: complete step coverage and precedence constraints.

No evaluator asks another language model whether an answer is correct. Terminal
closure is calculated by deterministic Python code.

## Repository Modules

```text
src/qimo_model/contracts.py   shared task, gap, validation, epoch, and run records
src/qimo_model/tasks.py       domain tasks and deterministic validators
src/qimo_model/runtime.py     three runtime modes and verified rule memory
src/qimo_model/benchmark.py   controlled suite execution and summary metrics
src/qimo_model/reports.py     Markdown report rendering
modal_app/qimo_modal.py       Qwen3-1.7B generation on Modal T4
```

## Interpretation Boundary

This runtime demonstrates bounded structural inference. It does not yet
demonstrate weight-level learning, consciousness, AGI, unlimited autonomous
evolution, or universal superiority. Those claims require substantially larger
pre-registered experiments and independent reproduction.
