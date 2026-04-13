---
created: 2026-04-13
updated: 2026-04-13
sources: [commit 28a6f97, commit e3d0c01, commit 244dc80]
tags: [distribution, curl, github-releases, installation]
status: active
---

# GitHub Releases Curl Installer Distribution

The project uses a curl-based installer pipeline that downloads artifacts directly from GitHub Releases. This approach provides a lightweight, zero-dependency distribution method for the `reflect` CLI.

## Distribution Model

The installer leverages GitHub Releases as the primary artifact repository. Users download and execute the installation script via curl, which then manages the full installation and future upgrades. This eliminates the need for package managers or other distribution channels while maintaining simplicity and ease of use.

## Technical Implementation

The curl-based approach uses direct GitHub Release asset downloads. A key implementation detail: the installer properly handles version redirects by capturing the redirect URL without following it (`-L` flag behavior), ensuring accurate version detection and artifact resolution (commit e3d0c01).

The tool supports self-upgrade functionality, allowing installed instances to update themselves via the same `reflect upgrade` command (commit 244dc80). This means the installer pattern not only handles initial distribution but also manages the full lifecycle of the CLI.

## Key Design Decisions

**No external dependencies**: Using curl (almost universally available) rather than package managers keeps the installation footprint minimal and avoids coupling to specific platforms or ecosystems.

**GitHub Releases as source of truth**: Release artifacts are the authoritative distribution point, enabling semantic versioning and changelog tracking alongside binary artifacts.

**Version redirect handling**: Careful handling of HTTP redirects ensures the installer correctly identifies and downloads the intended release version, preventing version mismatch issues.

## Use Cases

This distribution pattern is ideal for:
- CLI tools targeting multiple OS/architecture combinations
- Projects seeking rapid distribution without package manager approval/delays
- Self-contained tools where users value simplicity over integration with system package managers

The approach was introduced as part of the project's maturation toward production-ready distribution (commit 28a6f97).
