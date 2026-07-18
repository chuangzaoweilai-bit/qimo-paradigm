# Qimo Paradigm

Qimo Paradigm is an experimental computing paradigm that attempts to redefine how computation should be organized from the bottom up.

It does not treat programs, files, processes, memory, instruction sets, operating systems, or applications as the first foundation of computing. Instead, it starts from origin, terminal state, complete semantics, structural rules, quality gates, feedback, and closure.

Qimo Paradigm is a universal-domain paradigm. It is not specific to blockchain, AI, a programming language, a workflow engine, or a container architecture. The blockchain semantic training loop in this repository is an early case study that shows how the paradigm can be applied in a complex domain.

This project is published for free. The goal is not to own or close the idea, but to make this new bottom-up computing paradigm visible to the public and encourage people to use it responsibly.

No person or organization may use Qimo Paradigm, its documents, examples, structures, or direct derivative technologies to apply for, obtain, or enforce exclusive patent rights that would prevent others from freely learning, using, implementing, improving, or extending it. Direct technologies derived from this computing paradigm must remain available for free use.

We hope more people will improve and maintain it. A new computing paradigm cannot be completed by one person alone.

## Executable Evidence

The repository now contains a first executable base-model runtime and a frozen
multi-domain pilot benchmark:

- [Qimo Structured Model](docs/qimo-structured-model.en.md): architecture,
  closure authority, feedback, and verified rule memory.
- [Multi-domain Benchmark v1](docs/multidomain-benchmark-v1.en.md): protocol,
  results, limitations, and interpretation.
- [Full audit record](artifacts/qimo-multidomain-v1.json): every raw model
  output, validation result, gap, feedback task, and rule snapshot.
- [Live Closure Lab](https://huggingface.co/spaces/qimo-paradigm/qimo-closure-lab):
  browser simulation and a bounded Modal-backed model proposal.

In the frozen six-task pilot, the same Qwen3-1.7B model closed 3/6 tasks with
one-shot inference, 3/6 with generic retry, and 4/6 with Qimo structured
feedback. This is initial evidence, not a general proof; the sample is too small
for a broad performance claim.

## Minimal Example

```text
Origin: I want an apple.
Terminal: I will eventually have an apple.
Middle: how the system makes that terminal state happen.
```

In this example, the origin is not a normal input parameter, and the terminal is not a normal output value.

The origin is the occurrence of a desire, goal, problem, or missing state.

The terminal is the final state that must become true.

The middle is the mechanism that continuously generates paths, executes actions, handles obstacles, verifies the result, and keeps evolving until the terminal state is closed.

## Core Claim

Traditional computing is usually organized like this:

```text
input -> program -> output
```

Qimo Paradigm reorganizes computation like this:

```text
origin -> terminal-reaching mechanism -> terminal -> verification -> closure
```

The difference is not cosmetic.

Traditional systems can execute a process and still fail to reach the real goal.

Qimo Paradigm does not treat "the process ran" as success. It only treats the terminal state as successful when it has been verified as true.

## Critique of Traditional Computing

Mainstream computing systems usually assume a fixed starting point:

```text
the program starts running
```

But real-world goals do not always begin as clean program entries, function calls, requests, commands, or events. Human goals often begin as missing states:

```text
I want an apple.
This task must be completed.
This state must change.
This problem must be resolved.
```

Traditional systems often compress these origins into inputs, execute existing programs, catch or skip errors, add patches, and eventually return an uncertain result.

```text
single start -> skipped errors -> completed process -> patches -> unknown result
```

Qimo Paradigm attempts to reverse that structure:

```text
Old systems: start from execution and accept an unknown result.
Qimo Paradigm: start from origin and organize around terminal closure.
```

## Foundational Axioms

### 1. Numeric Identity

In the digital world:

```text
1 is 1
1.2 is 1.2
```

A number should not be silently overloaded at the bottom layer to mean `true`, `enabled`, `done`, `allowed`, a role, a status, or an error code.

If a system needs those meanings, it must declare them in a semantic structure. Human interpretation should not directly contaminate the identity of numbers and symbols.

### 2. Semantic Isolation

Human intention is allowed to enter the system as an origin, but it must not directly overwrite bottom-layer rules.

It must be transformed into verifiable structures:

```text
origin
terminal
state
constraints
paths
quality gates
closure verification
```

### 3. No Silent Handling

Qimo Paradigm rejects silent handling at the bottom layer.

States that cannot be parsed, matched, verified, or closed must be recorded explicitly:

```text
unparsable -> not closed
unmatched -> structural gap
unverified -> quality-gate failure
terminal not reached -> feedback task
```

Silent handling is not reliability. It hides an unclosed state.

### 4. Structural Closure

Closure is not only a final system-level result.

Every small structure must embed its own rules, quality checks, failure conditions, and feedback path.

```text
small closed structure -> small closed structure -> small closed structure -> whole closure
```

If any small structure does not close, the whole structure does not close.

## Complete Semantics

Current AI semantics are often fragmented. A model may generate plausible answers, but that does not mean it has a complete semantic structure.

For the apple example, a complete semantic structure should record multiple scenes and paths:

```text
buy one yourself
ask a parent to buy one
ask a friend to buy one
order delivery
find one already at home
request one as a gift
pick one from an orchard with permission
steal or rob one
```

Wrong, dangerous, or illegal paths must also be recorded, but only as forbidden or rejected paths.

For example, stealing or robbing an apple may appear to satisfy the surface terminal state, but it violates higher constraints such as legality, safety, ownership, and harm prevention.

Complete semantics is not an answer list. It is a closed structure of objects, scenes, allowed paths, forbidden paths, constraints, failures, and verification rules.

## Path Expansion

"I will get an apple" does not mean one fixed path must succeed.

If the user has no money, the system must not immediately fail. It should treat the failure of the current path as a signal to expand paths:

```text
self-purchase failed -> try family assistance
family path failed -> try friend assistance
friend path failed -> try voluntary gift
gift path failed -> try permitted picking or production
```

Resource shortage is not the terminal failure. It is a path-expansion signal.

At the same time, path expansion never means "anything is allowed." Forbidden paths must be recorded and rejected.

## Universal-Domain Scope

Qimo Paradigm is not tied to one domain.

Any domain can be modeled if it has:

```text
origin
terminal
paths
rules
quality gates
failure feedback
closure verification
```

This includes software engineering, AI semantics, blockchain, education, medicine, law, manufacturing, finance, research, personal tasks, and social collaboration.

The domain is the application object, not the paradigm boundary.

## Spherical Runtime Space

Spherical Runtime Space is a proposed low-level runtime environment design for Qimo Paradigm.

It uses the real local physical disk as the bottom foundation instead of relying on heavy virtual machines or independent virtual disks. Through a glove-like flexible isolation model, it allocates capacity from free storage on demand and forms a single-entrance, single-path, encrypted, cross-device runtime space.

Its goal is not to reproduce traditional virtualization, but to provide a lighter, more direct, and more closed runtime base for Qimo Paradigm.

See [Spherical Runtime Space](docs/spherical-runtime-space.en.md).

## Case Study: Three-Container Semantic Loop

An early experiment used three containers to construct blockchain semantics:

```text
Origin: I want complete blockchain semantics.
Terminal: I will obtain complete blockchain semantics.

Container 1: pull on-chain smart contracts and generate staged task lists.
Container 2: read the task list and generate staged corpus entries.
Container 3: read the corpus and infer semantic entries.
Container 1: read semantic entries and verify whether the task list was executed.
```

This is not a loose pipeline.

It is a gated loop:

```text
on-chain contracts
  -> staged tasks
  -> staged corpus
  -> semantic entries
  -> reverse verification by Container 1
  -> gaps or errors
  -> new tasks
```

Each container can run only when the previous structure has produced the required artifact.

## Data Structures

The repository includes early schemas and examples:

```text
schemas/
  state.schema.json
  semantic_entries_payload.schema.json
  corpus_entry.schema.json
  corpus_entry_results.schema.json
  semantic_entry.schema.json

examples/
  state.example.json
  semantic_entries_payload.example.json
  corpus_entry.example.json
  corpus_entry_results.example.json
  corpus_entry_results_minimal.example.json
  corpus_entry_results_erc1155holder.example.json
  semantic_entry.example.json
```

These are not final implementations. They are early public structures for explaining how a closed semantic loop can be represented.

## Repository Map

```text
docs/
  public-intent.md
  universal-domain-paradigm.md
  foundations.md
  paradigm.md
  critique.md
  silent-handling.md
  semantic-completeness.md
  path-expansion.md
  program-construction.md
  structural-closure.md
  spherical-runtime-space.md
  spherical-runtime-space.en.md
  popularization.md
  multi-container-semantic-loop.md
  container1-master.md
  data-structures.md
  runtime.md
  whitepaper.en.md
examples/
schemas/
src/
tests/
LICENSE
CONTRIBUTING.md
README.md
README.en.md
```

## Status

This repository is an initial public draft.

The original implementation was mostly deleted before publication. This repository rebuilds the public version from the paradigm definition, examples, case-study structures, and early schemas.

## Contributing

Contributions are welcome.

When proposing a concept, example, or implementation, please try to explain:

```text
What is the origin?
What is the terminal?
How does the middle reach the terminal?
Where are the rules and quality gates?
How is closure verified?
```

## License

Qimo Paradigm Public Free License v1.0.
