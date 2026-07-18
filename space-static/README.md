---
title: Qimo Paradigm Closure Lab
colorFrom: green
colorTo: yellow
sdk: static
app_file: index.html
pinned: false
license: other
short_description: A bounded closure simulation for the Qimo Paradigm.
---

# Qimo Paradigm Closure Lab

This free static Space compares a fixed-output baseline with the Qimo feedback
loop. The deterministic comparison executes entirely in the visitor's browser.

The optional **Generate next proposal** action sends the entered origin and
terminal to a cost-bounded Modal endpoint. Qwen3-1.7B generates a candidate
feedback step, and a deterministic validator accepts or rejects its structure.
The model cannot mark the system closed. The public endpoint is limited to four
GPU requests per UTC day and the browser permits one request per page session.

The page also publishes the frozen `qimo-multidomain-v1` pilot. Using the same
Qwen3-1.7B weights and deterministic decoding, one-shot inference and generic
retry each closed 3/6 tasks, while Qimo structured feedback closed 4/6 with one
fewer model call than generic retry. Six tasks are not sufficient for a general
performance claim; the full method, limitations, and audit JSON are linked from
the page.

The default scenario demonstrates bounded structural self-evolution. It does
not claim to prove consciousness, AGI, or unlimited autonomous evolution.

Project source and specification:
[Qimo Paradigm](https://github.com/chuangzaoweilai-bit/qimo-paradigm)
