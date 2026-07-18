"""Gradio application for the Qimo Paradigm Closure Lab."""

from __future__ import annotations

import gradio as gr

from simulation import run_comparison


DEFAULT_ORIGIN = "AI wants to improve its own semantic competence."
DEFAULT_TERMINAL = (
    "AI reaches a verified closed structure containing complete semantic units, "
    "quality gates, feedback, memory updates, rule updates, and transfer."
)

TABLE_HEADERS = [
    "Mode",
    "Epoch",
    "Semantic %",
    "Gate %",
    "Missing units",
    "Missing gates",
    "Status",
    "Generated feedback",
]

CSS = """
:root {
  --qimo-green: #16794a;
  --qimo-yellow: #e2b93b;
  --qimo-red: #b94a48;
  --qimo-ink: #18211d;
  --qimo-line: #d8dfdb;
  --qimo-paper: #f7f9f8;
}
.gradio-container {
  width: 100% !important;
  max-width: 1420px !important;
  min-width: 0 !important;
  margin-inline: auto !important;
  padding-inline: 18px !important;
  box-sizing: border-box !important;
}
.qimo-header {
  border-left: 5px solid var(--qimo-green);
  padding: 12px 16px;
  margin: 4px 0 18px;
  background: var(--qimo-paper);
}
.qimo-header h1 { margin: 0 0 4px; font-size: 26px; letter-spacing: 0; color: var(--qimo-ink); }
.qimo-header p { margin: 0; color: #4b5951; }
.qimo-flow {
  display: grid;
  grid-template-columns: repeat(6, minmax(92px, 1fr));
  gap: 6px;
  margin: 0 0 16px;
}
.qimo-flow span {
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: 1px solid var(--qimo-line);
  border-radius: 6px;
  background: white;
  color: var(--qimo-ink);
  font-size: 13px;
  font-weight: 600;
}
.qimo-flow span:nth-child(1), .qimo-flow span:nth-child(6) { border-color: var(--qimo-green); }
.qimo-flow span:nth-child(3) { border-color: var(--qimo-yellow); }
.qimo-run button { background: var(--qimo-green) !important; border-color: var(--qimo-green) !important; }
.qimo-links { margin-top: 12px; color: #4b5951; font-size: 13px; }
.qimo-links a { color: var(--qimo-green); font-weight: 600; }
.block, .form { border-radius: 6px !important; }
@media (max-width: 760px) {
  .gradio-container {
    width: 100vw !important;
    max-width: 100vw !important;
    padding-inline: 10px !important;
    overflow-x: hidden !important;
  }
  .qimo-workbench {
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
  }
  .qimo-inputs, .qimo-results {
    width: 100% !important;
    min-width: 0 !important;
  }
  .qimo-flow {
    width: 100% !important;
    min-width: 0 !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .qimo-flow span { min-width: 0; overflow-wrap: anywhere; }
  .qimo-table {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    overflow-x: auto !important;
  }
  .qimo-header h1 { font-size: 22px; }
}
"""


def run_ui(origin: str, terminal: str, max_epochs: int):
    result = run_comparison(origin, terminal, max_epochs)
    return result["summary"], result["rows"], result["details"]


with gr.Blocks(
    title="Qimo Paradigm Closure Lab",
) as demo:
    gr.HTML(
        """
        <header class="qimo-header">
          <h1>Qimo Paradigm Closure Lab</h1>
          <p>Bounded structural self-evolution through explicit gaps, feedback tasks, and closure verification.</p>
        </header>
        <div class="qimo-flow" aria-label="Qimo closure sequence">
          <span>Origin</span><span>Gap audit</span><span>Feedback task</span>
          <span>Learning update</span><span>Quality gates</span><span>Verified terminal</span>
        </div>
        """
    )

    with gr.Row(equal_height=False, elem_classes="qimo-workbench"):
        with gr.Column(scale=4, min_width=320, elem_classes="qimo-inputs"):
            origin = gr.Textbox(label="Origin", value=DEFAULT_ORIGIN, lines=3)
            terminal = gr.Textbox(label="Terminal", value=DEFAULT_TERMINAL, lines=4)
            max_epochs = gr.Slider(
                minimum=1,
                maximum=6,
                value=6,
                step=1,
                label="Maximum epochs",
            )
            run_button = gr.Button("Run closure comparison", variant="primary", elem_classes="qimo-run")
        with gr.Column(scale=6, min_width=360, elem_classes="qimo-results"):
            summary = gr.Markdown()

    table = gr.Dataframe(
        headers=TABLE_HEADERS,
        datatype=["str", "number", "number", "number", "number", "number", "str", "str"],
        interactive=False,
        wrap=True,
        column_widths=[190, 72, 105, 90, 115, 115, 105, 440],
        label="Epoch audit",
        elem_classes="qimo-table",
    )
    with gr.Accordion("Full closure record", open=False):
        details = gr.JSON(label="Audit trace")

    gr.HTML(
        """
        <div class="qimo-links">
          Source and specification:
          <a href="https://github.com/chuangzaoweilai-bit/qimo-paradigm" target="_blank" rel="noreferrer">Qimo Paradigm on GitHub</a>
        </div>
        """
    )

    inputs = [origin, terminal, max_epochs]
    outputs = [summary, table, details]
    run_button.click(fn=run_ui, inputs=inputs, outputs=outputs)
    demo.load(fn=run_ui, inputs=inputs, outputs=outputs)


if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Soft(
            primary_hue="green",
            secondary_hue="yellow",
            neutral_hue="zinc",
        ),
        css=CSS,
    )
