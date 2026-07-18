# Qimo Modal model endpoint

This directory adds a cost-bounded live-model experiment to the deterministic
Closure Lab. Qwen generates candidate feedback tasks, while
`closure_core.py` validates the schema and retains closure authority.

## Cost and safety boundaries

- GPU: one NVIDIA T4 container maximum.
- Idle scale-down: 5 seconds.
- Output: at most 192 new tokens per request.
- Public quota: 4 model requests per UTC day.
- Closure: the model is never allowed to mark the structure closed.
- Billing: do not add a payment method for this experiment.

## Local verification

```powershell
python -m unittest modal_app.test_closure_core -v
python -m py_compile modal_app\closure_core.py modal_app\qimo_modal.py
```

## Modal commands

```powershell
python -m modal setup
python -m modal deploy modal_app\qimo_modal.py
```

Run one direct model validation after deployment:

```powershell
python -m modal run modal_app\qimo_modal.py
```

The first model request downloads `Qwen/Qwen3-1.7B` into the persistent Modal
volume named `qimo-model-cache`. Subsequent cold starts reuse that cache.

## Multi-domain benchmark

The deployed `ProposalModel.complete` method exposes the same deterministic
base model to the controlled benchmark runner. It is not part of the public
four-request endpoint quota.

```powershell
$env:PYTHONPATH = "src"
python -m modal_app.run_multidomain_benchmark --output artifacts/qimo-multidomain-v1
```

The runner compares one-shot inference, generic retry, and Qimo structured
feedback on the same tasks and writes both a complete JSON audit record and a
Markdown summary.
