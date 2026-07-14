# Bilingual README Installation and Usage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish one accurate Chinese-English README that lets Blender users install, use, and safely clean up Quick Language Switcher.

**Architecture:** Keep a single `README.md`. Chinese appears first and English follows with equivalent installation, usage, bilingual-pack safety, troubleshooting, and verification guidance.

**Tech Stack:** GitHub-flavored Markdown, Blender 5.0+ extension installation workflow.

## Global Constraints

- Keep a single `README.md` as the project homepage documentation.
- State that Blender 5.0 or newer is required.
- Present `Get Extensions > Install from Disk` as the preferred ZIP installation workflow.
- Treat bilingual packs as an optional advanced feature that writes under Blender `datafiles/locale`.
- State that disabling or unregistering attempts best-effort cleanup of generated bilingual packs.
- Do not modify plugin Python code, manifest metadata, tests, or release artifacts.

---

### Task 1: Replace README With Equivalent Bilingual User Guidance

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: `blender_manifest.toml` metadata and current add-on behavior.
- Produces: GitHub-ready Chinese and English installation and usage documentation.

- [x] **Step 1: Run a failing documentation acceptance check**

The original README did not contain `## 中文说明`.

- [x] **Step 2: Replace README content**

The README now uses Chinese-first and English-second sections covering Release ZIP installation, manual installation, quick switching, favorites, optional bilingual packs, cleanup boundaries, troubleshooting, development checks, and licensing.

- [x] **Step 3: Run documentation acceptance checks**

```powershell
$content = Get-Content README.md -Raw
@('# Quick Language Switcher', '## 中文说明', '## English', 'Get Extensions', 'Install from Disk', 'Shift + Ctrl + L', 'Blender 5.0', 'datafiles/locale', 'Emergency Cleanup') | ForEach-Object { if (-not $content.Contains($_)) { throw "Missing README content: $_" } }
git diff --check
```

Expected: both commands exit 0.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/compose/plans/2026-07-15-bilingual-readme-installation-and-usage.md
git commit -m "docs: add bilingual installation and usage guide"
```

---

## Self-Review

- The README contains a single bilingual documentation source.
- The text documents existing behavior and does not change runtime functionality.
