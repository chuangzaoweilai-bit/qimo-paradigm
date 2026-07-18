# Qimo Native Holdout v2

Frozen run date: 2026-07-18

| Path | Closed | Closure rate | Model calls | Operator steps | Structural invariants |
|---|---:|---:|---:|---:|---:|
| Original Qwen, one shot | 16/30 | 53.33% | 30 | 0 | 100% |
| Original Qwen + native kernel | 27/30 | 90.00% | 45 | 8 | 100% |
| Qimo LoRA + native kernel | 30/30 | 100.00% | 30 | 0 | 100% |

Domain results for the final path:

- software repair: 10/10;
- smart-contract audit: 10/10; and
- multi-step planning: 10/10.

All 30 final-path runs terminated as `verified_terminal`. The model never set
`closure_claim=true`; external validators retained closure authority.

This is a synthetic, in-distribution holdout. Training and holdout instances
are disjoint, but they share generator families. See
[`docs/qimo-native-model-v2.en.md`](../docs/qimo-native-model-v2.en.md) for the
method, limitations, and reproduction commands.
