# `.github/scripts/` — Code Reference

This document describes every Python file in `.github/scripts/`, including all functions,
their purpose, inputs/outputs, and notes for future refactoring toward the
[`rocrate`](https://pypi.org/project/rocrate/) library.

---

## Dependencies

| Package | Version constraint | Purpose |
|---|---|---|
| `pygithub` | `==2.2.0` | GitHub API (all workflow entry-point scripts) |
| `rocrate` | (latest) | RO-Crate read/write/entity access — replaces manual JSON traversal |
| `pyyaml` | (any) | YAML dump for `CITATION.cff` output |
| `requests` | (transitive via pygithub) | `request_utils.py` |

> `ruamel.yaml` has been removed; its only remaining use (YAML frontmatter handling in
> `.website_material/index.md`) was already commented out. All RO-Crate JSON manipulation
> is now handled by the `rocrate` library.

All scripts receive configuration via **environment variables only** — no CLI arguments.
Scripts that communicate with GitHub create a `Github` client from `GITHUB_TOKEN` via
`Auth.Token`.

---

## Dependency graph

```
update_doi.py
  ├── parse_utils.py  (extract_doi_parts, format_citation, ro_crate_to_cff)
  └── file_utils.py   (update_csv_content)

request_utils.py    — standalone (currently unused by any other script)
```

---

## File: `parse_utils.py`

Pure utility functions. No side effects, no GitHub calls. Imports: `re`, `yaml` (PyYAML),
`rocrate.rocrate.ROCrate`.

### `extract_doi_parts(doi_string: str) -> str`

Extracts and cleans a DOI from arbitrary text (plain DOI, full URL, etc.).

- Uses regex `10\.[0-9]+/[^ \s]+` to match the DOI.
- Strips trailing punctuation: `` [\s,.:;|/?:@&=+$,] ``.
- Returns the cleaned DOI string, or `"No valid DOI found in the input string."` on failure.
- Used by: `update_doi.py`

### `format_citation(crate: ROCrate) -> str`

Builds an APA-style citation string from an `ROCrate` object.

- Navigates to the root data entity (`@id == "./"`) via `crate.root_dataset`.
- Resolves `creator` and `publisher` references using `crate.dereference()`.
- Format: `"Surname, I. (Year). Title [Data set]. Publisher. https://doi.org/suffix"`
- Returns the citation string.
- Used by: `update_doi.py`

### `ro_crate_to_cff(crate: ROCrate) -> str`

Converts an `ROCrate` object to a [CFF](https://citation-file-format.github.io/)-formatted
YAML string, ready to write directly to `CITATION.cff`.

- Reads `name`, `version`, `identifier`, `datePublished`, `url` from `crate.root_dataset`.
- Resolves `creator` author references using `crate.dereference()`, extracting
  `familyName`, `givenName`, and ORCID `@id`.
- Returns a YAML string via `yaml.dump()`.
- Used by: `update_doi.py`

---

## File: `file_utils.py`

Pure utility functions for CSV manipulation. No GitHub calls. Imports: `csv`, `io.StringIO`.

> **Note:** `create_or_update_json_entry`, `navigate_and_assign`, and `read_yaml_with_header`
> have been removed. Their work is now performed by the `rocrate` library in `update_doi.py`
> and `parse_utils.py`.

### `update_csv_content(file_path: str, field: str, value: str) -> str`

Reads a two-column CSV file and updates (or appends) the row where `row[0] == field`.

- If the field exists, its value (`row[1]`) is replaced with `value`.
- If the field does not exist, a new row `[field, value]` is appended.
- Returns the full updated CSV as a string (not written to disk — caller is responsible).
- Used by: `update_doi.py` to update `.metadata_trail/nci_iso.csv`.

---

## File: `request_utils.py`

Single utility function. No GitHub calls. Imports: `requests`.

> Currently **unused** by any workflow script or other module. Retained as a utility.

### `check_uri(uri: str) -> str`

Performs an HTTP GET request with a 10-second timeout.

- Returns `"OK"` on a successful 2xx response.
- Returns the exception message string on any failure.
- Intended use: validating that a URI resolves before committing it to the crate.

---

## File: `update_doi.py`

**Workflow entry point** — run by `copy-files.yml` (`update-doi` job).

**Environment variables:** `GITHUB_TOKEN`, `REPO_NAME`, `ISSUE_NUMBER`

**Flow:**

1. Fetches the triggering issue from GitHub by `ISSUE_NUMBER`.
2. Parses the issue body using regex
   `### *(?P<key>.*?)\s*[\r\n]+(?P<value>[\s\S]*?)(?=###|$)` to extract key-value pairs.
3. Extracts the DOI from the `-> doi` field using `extract_doi_parts()`.
4. If the DOI is **valid**:
   - Downloads `ro-crate-metadata.json` from the repo via PyGitHub.
   - Loads it into an `ROCrate` object using `ROCrate(metadata_dict)` (detached crate).
   - Sets `identifier` on the root dataset, `model_inputs`, and `model_outputs` entities
     using `entity.append_to("identifier", doi)`.
   - Generates a citation string via `format_citation()` and sets `creditText` on the root
     dataset.
   - Serializes the updated crate back to JSON via `json.dumps(crate.metadata.generate())`.
   - Commits the updated `ro-crate-metadata.json` to the repo.
   - Generates `CITATION.cff` via `ro_crate_to_cff()` and commits it.
   - Updates `.metadata_trail/nci_iso.csv` via `update_csv_content()` and commits it.
   - Prints `True` to stdout (consumed by workflow as `$GITHUB_OUTPUT`).
5. If the DOI is **invalid**:
   - Posts a comment on the issue with an error message.
   - Removes the `model published` label.
   - Prints `False` to stdout.

**Imports:** `os`, `re`, `json`, `github.Github`, `github.Auth`,
`parse_utils.extract_doi_parts`, `parse_utils.format_citation`,
`parse_utils.ro_crate_to_cff`, `file_utils.update_csv_content`,
`rocrate.rocrate.ROCrate`

---

## Removed / dead code

The following items existed in earlier versions and have been removed:

| Item | Was in | Reason |
|---|---|---|
| `create_or_update_json_entry()` | `file_utils.py` | Replaced by `rocrate` entity API |
| `navigate_and_assign()` | `file_utils.py` | Was already unused (commented-out call site) |
| `read_yaml_with_header()` | `file_utils.py` | Was already unused (commented-out call site) |
| `.website_material/ro-crate-metadata.json` copy | `update_doi.py` | Only root-level file is maintained now |
| `ruamel.yaml` imports | `file_utils.py`, `update_doi.py` | No longer needed after removing dead YAML code |
| `copy_files.py` | `.github/scripts/` | Website/cross-repo copy functionality removed |
| `create_branch.py` | `.github/scripts/` | Only served cross-repo copy workflows |
| `find_repos.py` | `.github/scripts/` | Only served `new-actions.yml` |
| `pull_request.py` | `.github/scripts/` | Only served `new-actions.yml` |
| `check_published.py` | `.github/scripts/` | Only served `new-files.yml` |
| `update_labels.py` | `.github/scripts/` | Only served the website copy job |
| `new-files.yml` | `.github/workflows/` | Entire purpose was copying to website repo |
| `new-actions.yml` | `.github/workflows/` | Entire purpose was copying `.github/` to derived repos |

---

## Remaining refactoring opportunities

| Issue | Location | Suggested fix |
|---|---|---|
| `request_utils.check_uri` is unused | `request_utils.py` | Either wire it into DOI validation or remove |
