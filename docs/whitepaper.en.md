# Qimo Paradigm Whitepaper

## Abstract

Qimo Paradigm is a proposed bottom-up computing paradigm based on origin, terminal state, complete semantics, embedded rules, quality gates, feedback, and structural closure.

It challenges the assumption that computation should primarily be organized around program entry points, instruction execution, files, processes, and open-ended outputs. Instead, it treats computation as the process of transforming an origin into a verified terminal state through complete semantic structures and closed substructures.

The paradigm is universal-domain. Blockchain semantic training is used in this repository only as an early case study.

## 1. Motivation

Most current computing systems start from a predefined execution point:

```text
program starts
function is called
command is executed
request arrives
event is triggered
```

This is useful, but it is not the same as how real goals occur.

A human or system goal often begins as a missing state:

```text
I want an apple.
I need this task completed.
This state must change.
This problem must be solved.
```

Traditional systems usually compress the goal into an input, run a program, handle exceptions, add patches, and return a result. The process may finish, but the real terminal state may still not be true.

This creates a structural problem:

```text
fixed start -> execution -> skipped or patched errors -> output -> unknown terminal state
```

Qimo Paradigm is motivated by the need to make the terminal state explicit, verifiable, and structurally closed.

## 2. Core Definition

Qimo Paradigm reorganizes computation as:

```text
origin -> terminal model -> semantic structure -> path generation -> execution -> verification -> closure
```

### Origin

The origin is where computation happens from. It may be a goal, desire, missing state, external event, internal inconsistency, or semantic task.

### Terminal

The terminal is the final state that must become true. It is not merely a return value or output string.

### Terminal-Reaching Mechanism

The terminal-reaching mechanism generates, selects, executes, verifies, rejects, and revises paths until the terminal state is closed or a structural gap is recorded.

### Closure

Closure means the terminal state has been verified as true under the declared constraints. A completed process without terminal verification is not closure.

## 3. The Apple Example

```text
Origin: I want an apple.
Terminal: I will eventually have an apple.
```

A traditional system may return:

```text
search results
purchase links
delivery options
```

But returning links is not the same as having an apple.

Qimo Paradigm asks:

```text
What is the current state?
What terminal state must be true?
What allowed paths can reach it?
What forbidden paths must be excluded?
How is the terminal verified?
What happens if a path fails?
```

The system may consider:

```text
self-purchase
family assistance
friend assistance
delivery
voluntary gift
permitted picking
home inventory
exchange
```

It must also record and reject forbidden paths:

```text
steal an apple
rob an apple
pick from an orchard without permission
```

This is the difference between fragmented answers and complete semantics.

## 4. Foundational Axioms

### 4.1 Numeric and Symbolic Identity

At the bottom layer:

```text
1 is 1
1.2 is 1.2
```

Numbers and symbols should not silently become human meanings at the bottom layer.

If `1` means enabled, allowed, done, or true, that meaning must be declared in a semantic structure. It should not contaminate numeric identity.

### 4.2 Semantic Isolation

Human intention can become an origin, but it cannot directly overwrite bottom-layer rules.

It must be transformed into explicit structures:

```text
origin
terminal
state
constraints
allowed paths
forbidden paths
quality gates
verification
```

### 4.3 No Silent Handling

A system must not silently skip, swallow, default, or hide an unclosed state.

```text
unparsable -> not closed
unmatched -> gap
unverified -> quality-gate failure
terminal not reached -> feedback task
```

Silent handling hides structural failure and produces unknown results.

### 4.4 Rule Endogeneity

Rules should not be treated as external patches.

Rules belong inside the structure:

```text
structure = state + rules + paths + quality gates + closure condition
```

### 4.5 Substructure Closure

A whole structure is closed only if its substructures are closed.

```text
substructure closure -> substructure closure -> whole closure
```

If any substructure does not close, the whole structure must not be marked as closed.

## 5. Complete Semantics

Complete semantics is not a database of correct answers.

It is a structure that records:

```text
object
scenes
allowed paths
conditional paths
failed paths
forbidden paths
constraints
verification
feedback
terminal state
```

Wrong paths are part of complete semantics, but they are not executable suggestions. They are recorded so the system knows what must be rejected and why.

## 6. Path Expansion

When a path fails, the system should not immediately fail the terminal.

It should identify which path failed and expand to other allowed paths.

```text
self path failed -> family path
family path failed -> social path
social path failed -> request path
request path failed -> environmental or production path
```

The principle is:

```text
resource shortage is a path-expansion signal, not terminal failure.
```

However, path expansion must obey constraints. A forbidden path is still forbidden even if it appears to reach the terminal.

## 7. Program Construction

A program built under Qimo Paradigm should not begin from an entry function and then discover the final shape later.

It should begin by defining the terminal structure.

```text
origin -> terminal fixed -> complete semantics -> structural paths -> closure verification
```

If the final structure is not the originally defined terminal, the structure does not close.

This does not mean errors never happen. It means errors cannot be swallowed or disguised as success.

## 8. Universal-Domain Nature

Qimo Paradigm is not limited to blockchain or AI.

Any domain can be modeled with:

```text
origin
terminal
object
scene
allowed paths
forbidden paths
constraints
substructures
quality gates
feedback
closure verification
```

Examples:

```text
Education:
Origin: a student wants to master a concept.
Terminal: the student can understand, apply, and pass verification.
```

```text
Software engineering:
Origin: build a reliable program.
Terminal: the program satisfies its predefined terminal structure and closure checks.
```

```text
Medical assistance:
Origin: a patient has a health concern.
Terminal: the concern is safely and professionally evaluated and routed to an appropriate path.
```

The domain changes. The closure structure remains.

## 9. Case Study: Blockchain Semantic Loop

An early experiment used a three-container structure to build blockchain semantics.

### Container 1: Master

Container 1 pulls smart contracts, generates staged task lists, monitors task indexes, reads semantic entries, writes them to storage, and keeps a heartbeat.

It is both the origin generator and the feedback verifier.

### Container 2: Corpus Generator

Container 2 can run only after it reads the task list from Container 1.

It produces `corpus_entry` structures containing metrics, security notes, risk prefilters, executed actions, reasoning input, reasoning output, and closure status.

### Container 3: Semantic Generator

Container 3 can run only after it reads the corpus produced by Container 2.

It produces `semantic_entry` structures that can be traced back to the original task through `task_id`.

### Loop

```text
smart contracts
  -> task list
  -> corpus entries
  -> semantic entries
  -> reverse verification by Container 1
  -> gap or error
  -> new tasks
```

This is not a simple pipeline. It is a gated loop with reverse verification.

## 10. Data Structures

The repository currently includes early JSON schemas:

```text
state.schema.json
semantic_entries_payload.schema.json
corpus_entry.schema.json
corpus_entry_results.schema.json
semantic_entry.schema.json
```

These schemas are not final. They are public draft structures for turning the paradigm into verifiable artifacts.

## 11. Relation to Existing Systems

Qimo Paradigm is not simply:

```text
an AI agent
a workflow engine
a knowledge graph
a programming language
an operating system
a formal verification tool
a model fine-tuning method
```

It may use parts of these systems, but its organization principle is different:

```text
terminal closure over process completion
complete semantics over fragmented answers
embedded quality gates over external patches
explicit gaps over silent handling
substructure closure over loose modules
```

## 12. Current Status

This is an initial public draft.

The goal of the current repository is to make the paradigm visible, document its foundations, provide examples, and invite collaboration.

The next technical step is a minimal reference implementation that can read:

```text
task list
corpus entries
semantic entries
closure rules
```

and produce:

```text
closed
not closed
gap
rejected
waiting
error
```

## 13. Public Intent

Qimo Paradigm is published for free.

The hope is that it will be studied, questioned, improved, maintained, and used responsibly.

```text
Let a new computing paradigm appear.
Let more people understand it.
Let it be used well.
```

