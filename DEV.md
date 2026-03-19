# DEV.md — Developer Reference for il_conv

## Running the Tests Locally

### Linux / WSL

```bash
./run_tests.sh        # all tests, normal output
./run_tests.sh -v     # verbose (one line per test)
```

### Windows (native cmd)

```bat
run_tests.cmd         :: all tests
run_tests.cmd -v      :: verbose
```

> **Note:** `run_tests.cmd` changes to `%TEMP%` before running to avoid SQLite locking
> issues when the project lives on a WSL/network path.

### Running a single test file

```bash
python3 -m unittest tests/test_parse.py -v
python3 -m unittest tests/test_parse_testlog.py -v
python3 -m unittest tests/test_issuedb_rn.py -v
python3 -m unittest tests/test_export_xlsx.py -v
```

---

## Test Files

| File | Type | Requires | Description |
|---|---|---|---|
| `tests/test_parse.py` | public | — | Regex pattern unit tests and `LogDB` with synthetic temp-file input |
| `tests/test_parse_testlog.py` | public | `test.log` | End-to-end `LogDB.parse_log_file` against the committed `test.log` — all detection variants, counts, field values, path normalisation |
| `tests/test_export_xlsx.py` | public | — | `_map_dtype_2_auto_judgement` for all detectiontype combinations |
| `tests/test_issuedb_rn.py` | public | `RELEASENOTES/*.html` | `IssueDB` release-note import and queries using committed HTML files; no XML needed |
| `tests/test_issuedb_private.py` | private | `XML/` + `RELEASENOTES/` | Full `IssueDB` integration tests — skipped automatically when XML files are absent |
| `tests/test_export_xlsx_private.py` | private | `XML/` + `RELEASENOTES/` | `generateExcel` / `_addOneSheet` integration tests — skipped when absent |
| `tests/test_il_conv_private.py` | private | `XML/` + `RELEASENOTES/` + `test.log` | CLI entry-point end-to-end tests — skipped when absent |

Private test data (`XML/`) is not committed and is excluded via `.gitignore`.
`RELEASENOTES/*.html` files are committed and used by the public tests.

---

## GitHub Actions Workflows

### CI — Automated Tests (`.github/workflows/ci.yml`)

Triggered automatically on:
- Push to `main`, `feature_*`, `fix_*` branches
- Pull requests targeting `main`

Runs the full test suite with coverage on both platforms:

| Runner | Shell | Notes |
|---|---|---|
| `ubuntu-latest` | bash | Runs from the project root; `.coveragerc` auto-discovered |
| `windows-latest` | cmd | Runs from `%TEMP%` to avoid SQLite locking issues; `--rcfile` passed explicitly |

No manual action needed — the workflow runs automatically on every push.

---

### Release Builds — Nuitka Executables (`.github/workflows/release.yml`)

Triggered by pushing a **version tag** (`v*`). Builds onefile binaries on both
platforms and publishes a GitHub Release with both binaries attached.

```bash
git tag v3.0
git push origin v3.0
```

| Platform | Runner | Release asset |
|---|---|---|
| Linux | `ubuntu-latest` | `il_conv-linux-x64` |
| Windows | `windows-latest` | `il_conv-windows-x64.exe` |

The GitHub Release is created automatically with:
- Name: `il_conv <tag>`
- Auto-generated release notes from commit/PR history
- Both binaries as downloadable assets

---

### Build Branch — Manual Onefile Build (`.github/workflows/build-branch.yml`)

Manually triggered from the GitHub Actions UI. Useful for testing a build from a
feature or fix branch before tagging a release.

**How to trigger:**
1. Go to **Actions → Build branch → Run workflow**
2. Enter the branch name (default: `main`)
3. Click **Run workflow**

Artifacts are uploaded with a branch-specific name (`il_conv-linux-x64-<branch>`,
`il_conv-windows-x64.exe-<branch>`) and kept for **30 days**.
No GitHub Release is created.

---

## Nuitka Build Details

All three workflows that invoke Nuitka share the same build configuration:

#### Extra packages installed

```
nuitka   ordered-set   zstandard
```

`ordered-set` is required by Nuitka internally; `zstandard` is required for
`--onefile` compression.

#### Platform-specific compiler setup

| Platform | Compiler | Setup |
|---|---|---|
| Linux | gcc | `sudo apt-get install -y gcc patchelf` |
| Windows | MinGW64 (gcc) | `C:\msys64\mingw64\bin` added to `PATH`; `--mingw64` flag passed to Nuitka |

`patchelf` is required by Nuitka `--onefile` on Linux to patch the ELF bootstrap.

#### Bundled resource files

```
res/default.css
res/functions.js
res/logo_base64.txt
res/logo.png
```

Passed via `--include-data-file=src=dest` so they are accessible at runtime
through `resources.py` regardless of whether running from source or a bundled exe.

#### Local build (Windows)

```bat
create_nuitka_exe.bat
```
