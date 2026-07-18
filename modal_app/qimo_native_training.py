"""Train and serve the Qimo-native LoRA adapter on Modal."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import modal


APP_NAME = "qimo-native-model"
MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_CACHE = "/cache/huggingface"
ADAPTER_ROOT = "/adapters"
ADAPTER_PATH = f"{ADAPTER_ROOT}/qimo-v2"

app = modal.App(APP_NAME)

training_image = modal.Image.debian_slim(python_version="3.12").uv_pip_install(
    "accelerate>=1.5,<2",
    "huggingface_hub[hf_xet]>=0.30,<1",
    "peft>=0.15,<1",
    "transformers[torch]>=4.51,<5",
)

model_cache = modal.Volume.from_name("qimo-model-cache", create_if_missing=True)
adapter_volume = modal.Volume.from_name("qimo-native-adapter", create_if_missing=True)


def _encode_example(tokenizer, example: dict[str, Any], max_length: int = 1024) -> dict:
    messages = [
        {
            "role": "system",
            "content": "Follow the supplied benchmark protocol and return only one JSON object.",
        },
        {"role": "user", "content": example["prompt"]},
    ]
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    target_ids = tokenizer(
        example["target"] + tokenizer.eos_token,
        add_special_tokens=False,
    )["input_ids"][:320]
    prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    prompt_budget = max_length - len(target_ids)
    if len(prompt_ids) > prompt_budget:
        head = min(560, prompt_budget // 2)
        prompt_ids = prompt_ids[:head] + prompt_ids[-(prompt_budget - head) :]
    input_ids = prompt_ids + target_ids
    return {
        "input_ids": input_ids,
        "attention_mask": [1] * len(input_ids),
        "labels": [-100] * len(prompt_ids) + target_ids,
    }


@app.function(
    image=training_image,
    gpu="T4",
    volumes={MODEL_CACHE: model_cache, ADAPTER_ROOT: adapter_volume},
    min_containers=0,
    max_containers=1,
    scaledown_window=5,
    timeout=1800,
    startup_timeout=600,
)
def train_adapter(examples: list[dict[str, Any]], epochs: float = 2.0) -> dict:
    import torch
    from peft import LoraConfig, get_peft_model
    from torch.nn.utils.rnn import pad_sequence
    from torch.utils.data import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=MODEL_CACHE)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    encoded = [_encode_example(tokenizer, example) for example in examples]

    class TrajectoryDataset(Dataset):
        def __len__(self) -> int:
            return len(encoded)

        def __getitem__(self, index: int) -> dict:
            return encoded[index]

    def collate(batch: list[dict]) -> dict:
        input_ids = [torch.tensor(item["input_ids"], dtype=torch.long) for item in batch]
        attention = [
            torch.tensor(item["attention_mask"], dtype=torch.long) for item in batch
        ]
        labels = [torch.tensor(item["labels"], dtype=torch.long) for item in batch]
        return {
            "input_ids": pad_sequence(
                input_ids, batch_first=True, padding_value=tokenizer.pad_token_id
            ),
            "attention_mask": pad_sequence(
                attention, batch_first=True, padding_value=0
            ),
            "labels": pad_sequence(labels, batch_first=True, padding_value=-100),
        }

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        cache_dir=MODEL_CACHE,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    model = get_peft_model(model, lora_config)
    model.enable_input_require_grads()

    arguments = TrainingArguments(
        output_dir="/tmp/qimo-native-training",
        num_train_epochs=float(epochs),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_strategy="no",
        fp16=True,
        bf16=False,
        gradient_checkpointing=True,
        optim="adamw_torch",
        report_to=[],
        remove_unused_columns=False,
        seed=20260718,
        data_seed=20260718,
    )
    trainer = Trainer(
        model=model,
        args=arguments,
        train_dataset=TrajectoryDataset(),
        data_collator=collate,
    )
    result = trainer.train()
    model.save_pretrained(ADAPTER_PATH)
    tokenizer.save_pretrained(ADAPTER_PATH)
    adapter_volume.commit()

    trainable, total = model.get_nb_trainable_parameters()
    return {
        "status": "trained",
        "model_id": MODEL_ID,
        "adapter_path": ADAPTER_PATH,
        "examples": len(examples),
        "epochs": float(epochs),
        "trainable_parameters": trainable,
        "total_parameters": total,
        "trainable_ratio": trainable / total,
        "metrics": {
            key: value
            for key, value in result.metrics.items()
            if isinstance(value, (int, float, str, bool))
        },
    }


@app.cls(
    image=training_image,
    gpu="T4",
    volumes={MODEL_CACHE: model_cache, ADAPTER_ROOT: adapter_volume},
    min_containers=0,
    max_containers=1,
    scaledown_window=5,
    timeout=180,
    startup_timeout=600,
)
class TrainedModel:
    @modal.enter()
    def load(self) -> None:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)
        base = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_CACHE,
            dtype="auto",
            device_map="cuda",
        )
        self.model = PeftModel.from_pretrained(base, ADAPTER_PATH)
        self.model.eval()

    @modal.method()
    def complete(self, prompt: str, max_new_tokens: int = 320) -> str:
        messages = [
            {
                "role": "system",
                "content": "Follow the supplied benchmark protocol and return only one JSON object.",
            },
            {"role": "user", "content": str(prompt)[:12000]},
        ]
        rendered = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        model_inputs = self.tokenizer(rendered, return_tensors="pt").to(
            self.model.device
        )
        with self.torch.inference_mode():
            generated = self.model.generate(
                **model_inputs,
                max_new_tokens=max(64, min(int(max_new_tokens), 384)),
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated_tokens = generated[0][model_inputs.input_ids.shape[-1] :]
        return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()


@app.local_entrypoint()
def main(train: bool = False, epochs: float = 2.0) -> None:
    if train:
        dataset_path = Path(__file__).resolve().parents[1] / "training_data" / "qimo_train.jsonl"
        examples = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines()]
        print(json.dumps(train_adapter.remote(examples, epochs), indent=2))
        return

    smoke_prompt = "/no_think\nReturn JSON only: {\"closure_claim\": false}"
    print(TrainedModel().complete.remote(smoke_prompt, max_new_tokens=96))
