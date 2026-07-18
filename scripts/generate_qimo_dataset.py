"""Generate deterministic Qimo training trajectories and holdout metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qimo_model.dataset import (  # noqa: E402
    build_training_examples,
    generate_holdout_tasks,
    generate_training_tasks,
)


def main() -> None:
    output_dir = ROOT / "training_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    training_tasks = generate_training_tasks()
    examples = build_training_examples(training_tasks)
    holdout = generate_holdout_tasks()

    with (output_dir / "qimo_train.jsonl").open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False) + "\n")

    (output_dir / "qimo_holdout_manifest.json").write_text(
        json.dumps(
            {
                "training_task_count": len(training_tasks),
                "training_example_count": len(examples),
                "holdout_task_count": len(holdout),
                "holdout_task_ids": [task.task_id for task in holdout],
                "holdout_domains": sorted({task.domain for task in holdout}),
                "note": "Holdout tasks are regenerated from a disjoint seed at evaluation time.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "training_tasks": len(training_tasks),
                "training_examples": len(examples),
                "holdout_tasks": len(holdout),
            }
        )
    )


if __name__ == "__main__":
    main()
