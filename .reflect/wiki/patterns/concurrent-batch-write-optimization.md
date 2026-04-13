---
created: 2026-04-13
updated: 2026-04-13
sources: [commit 90a5cde, commit 4359625]
tags: [concurrency, batch-operations, threadpool]
status: active
---

# Concurrent Batch Write with ThreadPoolExecutor

Use Python's `concurrent.futures.ThreadPoolExecutor` to parallelize multiple write operations in batch workflows. This pattern replaces sequential writes with concurrent execution, improving throughput for I/O-bound operations (commit 90a5cde, 2026-04-09).

## Pattern Overview

ThreadPoolExecutor enables writing multiple independent records in parallel by distributing work across a managed pool of threads. Each write operation is submitted as a task and executes concurrently, rather than waiting for the previous write to complete.

## Implementation Decision

**Chosen**: `concurrent.futures.ThreadPoolExecutor` for batch write refactoring

**Why adopted**: Sequential batch writes create unnecessary latency when write operations are I/O-bound. Parallelization allows multiple writes to progress simultaneously, hiding wait times and reducing total ingest duration.

**Context**: Introduced in v0.7.0 (commit 4359625) alongside concurrent ingest, repo-scoped collections, and high-water mark tracking—a comprehensive shift toward non-blocking batch operations.

## Use Cases

- **Batch ingestion**: Writing multiple records during incremental ingest cycles
- **Collection updates**: Concurrent writes to repo-scoped collection namespaces
- **Tracking updates**: Parallel writes of content and high-water mark records
- **Session evidence persistence**: Multiple evidence documents written without blocking

## Pattern Benefits

- **Reduced total latency**: Exploits parallelism in I/O-bound write operations
- **Non-blocking pipelines**: Frees threads while writes complete
- **Resource bounded**: Thread pool limits concurrent resource consumption
- **Clean semantics**: `submit()` and `as_completed()` provide intuitive concurrent patterns

## Considerations

- Thread pool size must account for database connection limits
- Exception handling requires aggregation across concurrent tasks
- May require connection pooling tuned to thread count
- Validate whether strict ordering guarantees are needed across concurrent writes

## Related Patterns

Complementary to:
- Incremental ingest with high-water marks (commit 2f5ad53)
- Repo-scoped collection naming to prevent collisions under concurrent load (commit 7b17590)
