# Spherical Runtime Space

## Positioning

Spherical Runtime Space is a proposed low-level runtime environment design for Qimo Paradigm.

It is not a traditional heavy virtual machine and not a conventional independent virtual disk design. It uses the real local physical disk as the bottom foundation, creates a flexible isolated runtime boundary, and embeds resource rules, quality gates, and closure checks into the runtime space itself.

This design was previously considered as a patent direction. It is now published for free as part of the public Qimo Paradigm project.

## 1. Bottom Foundation

Spherical Runtime Space rejects the assumption that an isolated environment must begin from a heavy VM or a separated virtual disk.

It uses the real physical disk as the only bottom foundation:

```text
no forced repartitioning
no fragmentation of the original disk
no heavy virtual disk as the primary base
no destructive split between existing data and runtime space
```

The base image is minimal and blank. It keeps only the core runtime kernel needed to maintain the virtual space.

That kernel is expected to remain resident, maintaining space rules, resource boundaries, isolation strategy, and closure state.

## 2. Glove Model Isolation

The isolation model is similar to a glove.

The physical hardware is the body.

The spherical virtual space is the glove:

```text
directly connected to the physical disk
does not destroy the original disk structure
does not occupy used data areas
allocates only from free space
forms an isolated runtime boundary
```

Instead of cutting the entire disk into new partitions, the space dynamically allocates a specified capacity from idle storage.

Example:

```text
allocate 4 TB from current free space
isolate and lock that allocation
do not overwrite existing data
do not break original drive letters or directory structures
```

## 3. Resource Customization

The user can precisely limit hardware resources:

```text
disk: percentage of free space or fixed capacity
memory: explicit quota
CPU: explicit quota
```

The goal is to avoid waste, resource grabbing, and uncontrolled expansion.

Resources enter a structured configuration:

```text
resource origin
resource limit
allocation rule
runtime monitoring
overflow handling
closure verification
```

## 4. Single-Path Runtime

Traditional virtualization often introduces multiple layers of paths, mounts, checks, and mappings.

Spherical Runtime Space aims for a single direct path:

```text
physical disk path -> spherical space mapping path -> program runtime path
```

The runtime space keeps one main path wherever possible.

This reduces nested mounts, mapping drift, path conflicts, and multi-layer validation failures.

In Qimo Paradigm terms:

```text
fewer paths make closure clearer
direct mapping makes quality gates more explicit
```

## 5. Native System Compatibility

The runtime space should automatically map existing device structures.

On Windows:

```text
A:
B:
C:
D:
```

On Linux:

```text
/
/home
/mnt
/var
/opt
```

If a required file or directory does not exist, the runtime should generate it adaptively according to the current system environment.

This makes command-line operations lighter and improves cross-device adaptation.

## 6. Security and Encrypted Closure

The spherical space keeps one explicit entrance.

No hidden bypass is designed.

The entrance uses an end-to-end encrypted private-cloud channel for:

```text
access
snapshots
backups
cross-device sync
configuration sync
image pull
```

The security target is to reduce the exposed surface:

```text
single entrance
end-to-end encryption
minimal visible ports
no hidden bypass
all transfer through encrypted channels
```

This public document does not claim absolute unbreakability. It defines a minimal-exposure and closure-based security boundary.

## 7. Cross-Device Roaming

Space rules, resource configuration, and isolation policies can be preset and fixed inside the image.

When the user signs in from another device, the private cloud can pull the dedicated image.

The new device detects:

```text
local physical disks
remaining storage
existing drive letters or directory structures
available CPU and memory
allocatable resources
```

Then it deploys the space using the original rules.

The goal is:

```text
carry the environment across devices
preserve rules
avoid resource-boundary drift
avoid rewriting isolation strategy
```

## 8. Two Usage Modes

### General Mode

For ordinary users:

```text
standard preset image
ready to use
no need to understand isolation internals
automatic resource allocation and path mapping
```

### Professional Mode

For engineers and advanced users:

```text
custom rules
custom isolation policy
custom permissions
custom resource parameters
extensible runtime structure
```

## Relationship to Qimo Paradigm

Spherical Runtime Space is not just another virtualization system.

It reflects core Qimo Paradigm principles:

```text
terminal first: the runtime space must become a verifiable isolated state
single-path terminal reaching: reduce structural drift caused by multiple paths
embedded rules: resource, permission, isolation, and sync rules live inside the space
no silent handling: path, resource, sync, and encryption failures must be explicit
substructure closure: disk, memory, CPU, entrance, sync, and image each close independently
whole closure: if any substructure does not close, the runtime space is not usable
```

## Core Definition

Spherical Runtime Space is a low-level runtime environment design based on real physical disks, flexible spherical isolation, single-path mapping, encrypted entrance, and cross-device roaming.

Its goal is not to reproduce traditional virtual machines, but to provide a lighter, more direct, and more closed runtime base for Qimo Paradigm.

