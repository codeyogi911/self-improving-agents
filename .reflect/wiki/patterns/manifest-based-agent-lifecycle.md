---
created: 2026-04-13
updated: 2026-04-13
sources: [commit 94ffe62]
tags: [agent-lifecycle, manifest, cleanup, init-upgrade]
status: active
---

# Manifest-Based Agent Lifecycle Management

A manifest file tracks which agents should be installed, enabling automatic cleanup of stale agents during `reflect init` and `reflect upgrade` operations. When init or upgrade runs, it compares the manifest against agents actually present in the `.claude/` directory and removes any agents not listed in the manifest (commit 94ffe62).

## Pattern

Instead of manually tracking which agents to keep or remove, maintain a manifest that declares the desired set of agents. The init/upgrade workflow uses this manifest as the source of truth:

1. **Record desired agents** in a manifest file (e.g., `.claude/agents.manifest`)
2. **Compare on init/upgrade**: Read manifest and scan the actual agent directory
3. **Remove stale agents**: Delete any agents found on disk but not in the manifest
4. **Update manifest**: After successful upgrade, update manifest to reflect new state

## Why This Works

This approach solves the problem of agent accumulation. When upgrading reflect or changing which agents should be bundled, old agent code can persist on disk and cause conflicts or unexpected behavior. By using a manifest, cleanup happens automatically without requiring users to manually delete outdated files.

The manifest acts as a declarative source of truth: each init/upgrade operation produces a predictable, deterministic state with no orphaned agents.

## When to Apply

- Initializing environments that must start in a known state
- Upgrading reflect or changing agent versions across projects
- Preventing deprecated agent implementations from lingering
- Ensuring consistency across team repositories

The cleanup is transparent to users—it happens automatically as part of standard init/upgrade operations, with no additional configuration or manual steps required.
