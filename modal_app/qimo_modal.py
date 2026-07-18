"""Cost-bounded Modal deployment for live Qimo closure proposals."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import modal

from modal_app.closure_core import (
    RequestError,
    build_prompt,
    normalize_request,
    parse_model_json,
    validate_candidate,
)


APP_NAME = "qimo-closure-model"
MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_CACHE = "/cache/huggingface"
DAILY_REQUEST_LIMIT = 4
MAX_NEW_TOKENS = 192

app = modal.App(APP_NAME)

api_image = modal.Image.debian_slim(python_version="3.12").uv_pip_install(
    "fastapi[standard]>=0.115,<1"
)
model_image = modal.Image.debian_slim(python_version="3.12").uv_pip_install(
    "accelerate>=1.5,<2",
    "huggingface_hub[hf_xet]>=0.30,<1",
    "transformers[torch]>=4.51,<5",
)

model_cache = modal.Volume.from_name("qimo-model-cache", create_if_missing=True)
quota_store = modal.Dict.from_name("qimo-demo-quota", create_if_missing=True)


@app.cls(
    image=model_image,
    gpu="T4",
    volumes={MODEL_CACHE: model_cache},
    min_containers=0,
    max_containers=1,
    scaledown_window=5,
    timeout=180,
    startup_timeout=600,
)
class ProposalModel:
    @modal.enter()
    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_CACHE,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_CACHE,
            torch_dtype="auto",
            device_map="cuda",
        )
        self.model.eval()
        model_cache.commit()

    @modal.method()
    def generate(self, request: dict) -> str:
        messages = [
            {"role": "system", "content": "Return only the requested JSON object."},
            {"role": "user", "content": build_prompt(request)},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        model_inputs = self.tokenizer(prompt, return_tensors="pt").to(
            self.model.device
        )
        with self.torch.inference_mode():
            generated = self.model.generate(
                **model_inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated_tokens = generated[0][model_inputs.input_ids.shape[-1] :]
        return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()


@app.function(
    image=api_image,
    min_containers=0,
    max_containers=1,
    scaledown_window=5,
    timeout=30,
)
@modal.fastapi_endpoint()
def health() -> dict:
    return {
        "ok": True,
        "app": APP_NAME,
        "model": MODEL_ID,
        "gpu": "T4",
        "daily_request_limit": DAILY_REQUEST_LIMIT,
        "closure_authority": "deterministic_external_validator",
    }


@app.function(
    image=api_image,
    min_containers=0,
    max_containers=1,
    scaledown_window=5,
    timeout=210,
)
@modal.concurrent(max_inputs=1)
@modal.fastapi_endpoint(method="POST")
def qimo_step(payload: dict) -> dict:
    try:
        request = normalize_request(payload)
    except RequestError as exc:
        return {"ok": False, "error": "invalid_request", "detail": str(exc)}

    quota_key = datetime.now(UTC).strftime("calls:%Y-%m-%d")
    used = int(quota_store.get(quota_key, 0))
    if used >= DAILY_REQUEST_LIMIT:
        return {
            "ok": False,
            "error": "daily_demo_quota_exhausted",
            "detail": "The public GPU guard has stopped additional requests today.",
            "quota": {"used": used, "limit": DAILY_REQUEST_LIMIT},
        }
    quota_store.put(quota_key, used + 1)

    raw_output = ProposalModel().generate.remote(request)
    try:
        candidate = parse_model_json(raw_output)
    except ValueError as exc:
        return {
            "ok": True,
            "model": MODEL_ID,
            "request": request,
            "model_output": raw_output,
            "validation": {
                "verdict": "rejected",
                "errors": [str(exc)],
                "accepted_candidate": None,
            },
            "closure_status": "not_closed",
            "quota": {"used": used + 1, "limit": DAILY_REQUEST_LIMIT},
        }

    validation = validate_candidate(candidate, request)
    return {
        "ok": True,
        "model": MODEL_ID,
        "request": request,
        "model_output": candidate,
        "validation": validation,
        "closure_status": "not_closed",
        "closure_note": (
            "An accepted proposal is still only a candidate update. Closure requires "
            "separate evidence and a complete deterministic audit."
        ),
        "quota": {"used": used + 1, "limit": DAILY_REQUEST_LIMIT},
    }


@app.local_entrypoint()
def main() -> None:
    request = normalize_request({"epoch": 1})
    raw_output = ProposalModel().generate.remote(request)
    try:
        candidate = parse_model_json(raw_output)
        validation = validate_candidate(candidate, request)
    except ValueError as exc:
        candidate = raw_output
        validation = {
            "verdict": "rejected",
            "errors": [str(exc)],
            "accepted_candidate": None,
        }
    print(
        json.dumps(
            {
                "request": request,
                "model_output": candidate,
                "validation": validation,
                "closure_status": "not_closed",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
