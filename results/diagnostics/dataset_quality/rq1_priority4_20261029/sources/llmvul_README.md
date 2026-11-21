# LLMVul: A Vulnerability-Labeled Dataset of LLM-Generated C/C++ Functions from Production Repositories

This is an RQ-focused excerpt of the [upstream dataset documentation](https://github.com/Wahed08/LLMVul-Dataset/tree/29313663fe2a575123adf552fd339c93c345e43d).
Upstream dataset and labeling claims are retained for provenance; see the
[RQ dataset-quality audit](../../rq1_priority4_diagnostics.md)
for the validation limits found in this study.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22668216.svg)](https://doi.org/10.5281/zenodo.22668216)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
![Functions](https://img.shields.io/badge/Functions-21%2C430-green.svg)
![Vulnerable](https://img.shields.io/badge/Vulnerable-1%2C540-red.svg)

---

## Overview

LLMVul is the **first vulnerability-labeled  dataset of LLM generated C/C++ functions mined from real  production GitHub repositories** where developers used AI coding assistants including GitHub Copilot, ChatGPT, Claude Code, Cursor, and Gemini.

LLMVul mines AI-attributed C/C++ code from authentic developer workflows and public software repositories. It preserves code contribution context through AI-tool attribution and commit metadata while removing duplicate function instances. The extracted functions are analyzed using a multi-tool vulnerability detection pipeline with CWE classification and manual validation. This enables the study of vulnerabilities that arise incidentally during routine AI-assisted development rather than through explicitly security-focused code generation.


## What It Provides
✨ **Real production code** — mined from 1,200 GitHub repositories, not researcher-directed prompts

✨ **AI tool attribution** — records which assistant generated the code (9 tools covered)

✨ **Validated labels** — three-tool ensemble with human validation (Cohen's κ = 0.79)

✨ **Full provenance** — commit ID, URL, message, date, file hash per function

### Key Statistics

| Metric | Value |
|--------|-------|
| Total functions | 21,430 |
| Vulnerable functions | 1,540 (7.2%) |
| Safe functions | 17,211 (80.3%) |
| Uncertain functions | 2,679 (12.5%) |
| Source repositories | 226 |
| LLM-attributed commits | 1,684 |
| Repositories scanned | 1,200 |
| Commits scanned | 321,080 |
| Date range | Nov 2022 – Sep 2026 |
| Languages | C, C++ |
| AI tools covered | 9 |
| Inter-rater agreement | κ = 0.79 |
| Columns per function | 34 |

---


## Dataset Columns (34 Total)

| Category | Column | Description |
|----------|--------|-------------|
| **Function Identity** | `unique_id` | 16-length hexadecimal string identifier. Format: `ID_XXXB7F0FA3BCEXXX` |
| **Project** | `project_name` | GitHub repository in `owner/repo` format |
| **Project** | `project_url` | Full URL of the GitHub repository |
| **Commit** | `commit_id` | Full 40-character Git commit |
| **Commit** | `commit_url` | Direct URL to the commit on GitHub |
| **Commit** | `commit_message` | Full commit message |
| **Commit** | `commit_date` | ISO 8601 commit timestamp, e.g. `2024-03-15T10:22:31` |
| **Source** | `file_name` | Relative path of the source file within the repository |
| **Source** | `file_hash` | SHA-256 hash of the file at commit time, prefixed `sha256:` |
| **Source** | `language` | Programming language: `c` or `cpp` |
| **Function** | `function_body` | Extracted source code of the function |
| **Function** | `function_start_line` | Starting line number in the source file |
| **Function** | `function_end_line` | Ending line number in the source file |
| **Function** | `function_lines` | Total number of lines in the function body |
| **AI Provenance** | `ai_tool` | AI assistant: `copilot`, `chatgpt`, `claude`, `claude_code`, `cursor`, `gemini`, `openai_codex`, `devin`, `generic_llm` |
| **AI Provenance** | `signal_strength` | Attribution confidence: `strong` (co-author tag) or `medium` (commit message) |
| **AI Provenance** | `signal_type` | Attribution source: `coauthor` or `commit_message` |
| **Repository** | `repo_stars` | Number of GitHub stars at mining time |
| **Repository** | `repo_forks` | Number of GitHub forks at mining time |
| **Repository** | `repo_primary_language` | Primary language of the repository as reported by GitHub |
| **Dataset** | `mined_at` | ISO 8601 timestamp when this function was collected |
| **Label** | `vuln_label` | Final binary label: `1` = vulnerable, `0` = safe, `null` = uncertain |
| **Label** | `ensemble_label` | Ensemble verdict: `vulnerable`, `safe`, or `uncertain` |
| **Tool Result** | `tool_semgrep` | Semgrep result: `1` = flagged, `0` = clean |
| **Tool Result** | `tool_flawfinder` | Flawfinder result: `1` = flagged, `0` = clean |
| **Tool Result** | `pattern_match` | Pattern matching result: `1` = flagged, `0` = clean |
| **CWE** | `cwe_id` | Final CWE assigned, e.g. `CWE-120`. Null if safe or uncertain |
| **CWE** | `cwe_description` | Human-readable CWE description from MITRE CWE catalogue |
| **CWE** | `cwe_url` | MITRE CWE reference URL, e.g. `https://cwe.mitre.org/data/definitions/120.html` |
| **Tool CWE** | `cwe_semgrep_raw` | CWE reported by Semgrep. Null if not flagged |
| **Tool CWE** | `cwe_flawfinder_raw` | CWE reported by Flawfinder. Null if not flagged |
| **Tool CWE** | `cwe_pattern_match_raw` | CWE reported by pattern matching. Null if not flagged |
| **Tool Meta** | `semgrep_rule` | Semgrep rule ID that triggered the finding, e.g. `dangerous-strcpy` |
| **Tool Meta** | `flawfinder_risk` | Flawfinder risk level: `1` (lowest) to `5` (highest). `0` if not flagged |

---

## Labeling Methodology

Functions are labeled using a **three-tool majority 
vote ensemble**:

```
Tool 1: Semgrep      — CWE-mapped rules
Tool 2: Flawfinder   — dangerous function database
Tool 3: Pattern Match — 54 NIST SARD-derived patterns

Majority vote:
  ≥ 2 tools flag → VULNERABLE (vuln_label = 1)
  0 tools flag   → SAFE       (vuln_label = 0)
  1 tool flags   → UNCERTAIN  (excluded from labels)
```

**Human validation:** Two independent raters 
manually labeled 100 randomly sampled 
ensemble-vulnerable functions.
Inter-rater agreement: **Cohen's κ = 0.79** 
(substantial agreement, Landis & Koch 1977).
The upstream review CSV is included as
[llmvul_manual_review.csv](llmvul_manual_review.csv).
It is source evidence; this study did not independently adjudicate the evaluation labels.

---

## AI Attribution Signals

Commits are classified as LLM-attributed using 
two signal categories:

**Strong signals** (co-authorship tags):
```
Co-authored-by: GitHub Copilot
Co-authored-by: cursor-noreply
Co-authored-by: claude-code
Co-authored-by: anthropic
```

**Medium signals** (commit message keywords):
```
"generated with ChatGPT"
"copilot suggested"
"via cursor ai"
"generated by claude"
"ai-assisted"
```

---

## Quick Start

Run this example from the public repository root after the
[local environment setup](../../../../../localScripts/README.md). The source CSV
has a title row before its header; `skiprows=1` is required.

```python
import pandas as pd

# Load the supplied source snapshot; skip its title line.
df = pd.read_csv('datasets/raw/LLMVul/LLMVul_v3-Updated.csv', skiprows=1)

# Vulnerable functions only
vuln = df[df['vuln_label'] == 1]

# By AI tool
copilot = df[df['ai_tool'] == 'copilot']

# By CWE
cwe120 = df[df['cwe_id'] == 'CWE-120']

# Strong signal only (high confidence)
strong = df[df['signal_strength'] == 'strong']

# For frozen-model evaluation — binary labeled only
labeled = df[df['vuln_label'].isin([0, 1])]
assert len(df) == 21430 and len(labeled) == 18751

print(f"Total:      {len(df):,}")
print(f"Vulnerable: {(df['vuln_label']==1).sum():,}")
print(f"Safe:       {(df['vuln_label']==0).sum():,}")
```

---

## Use in RQ

RQ compares the frozen LineVul and VulBERTa checkpoints on PrimeVul and the
18,751 binary-labeled LLMVul records. The 2,679 uncertain records are excluded.
See the [prepared dataset protocol](../../../../../datasets/pruned/README.md) and
[RQ findings](../../../../findings/rq1_answer.md) for the evaluated
cohorts and interpretation.

## Note on Reproducibility

> The underlying repository data may change over time as repositories, commits, and files are updated, removed, or rewritten. Therefore, re-mining the same repositories and time range may not reproduce the exact contents of LLMVul. In addition, vulnerability findings and CWE assignments may differ as analysis tools, rules, and versions evolve. The released dataset represents the snapshot collected and analyzed during our study period.


---

## Download

The full dataset is hosted on Zenodo:

**DOI:** [10.5281/zenodo.22668216](https://doi.org/10.5281/zenodo.22668216)

Files available on Zenodo:
- `LLMVul_v3-Updated.csv` — full dataset (21,430 functions)


---

## Manual Validation File

[llmvul_manual_review.csv](llmvul_manual_review.csv)
contains 100 randomly sampled ensemble-vulnerable functions with:

| Column | Description |
|--------|-------------|
| `row_num` | Row number (1–100) |
| `unique_id` | Links back to main dataset |
| `language` | C or C++ |
| `cwe_id` | Assigned CWE |
| `ai_tool` | AI tool that generated the code |
| `project_name` | Source repository |
| `function_body` | Function source code |
| `rater1_label` | First rater value: 0, 1, or undocumented `-1` |
| `rater2_label` | Second rater value: 0, 1, or undocumented `-1` |

---

## License

Dataset: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)

Scripts: [MIT License](https://github.com/Wahed08/LLMVul-Dataset/blob/29313663fe2a575123adf552fd339c93c345e43d/LICENSE)

---


## Citation

If you use LLMVul in your research, please cite:

```bibtex
@article{llmvul2026Farhad,
  author    = {Farhad, Mohammad and Dass, Shuvalaxmi},
  title     = {LLMVul: A Vulnerability-Labeled Dataset of LLM-Generated C/C++ Functions from Production Repositories},
  journal={arXiv preprint arXiv:2609.10945},
  year      = {2026},
}
```
---
