# Coding Conventions

Coding conventions for GridWars.run source files.

---

## SPDX license headers

Every new GridWars source file MUST begin with an `SPDX-License-Identifier` comment
using the identifier `AGPL-3.0-or-later`, written in a style appropriate to the file
format.

Vendored files inside `vendor/evennia/` retain their original SPDX headers
(BSD-3-Clause) and MUST NOT be modified. Do not add, remove, or alter license
identifiers in any file under `vendor/`.

---

## Examples

### Python

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Jay German
```

### YAML

```yaml
# SPDX-License-Identifier: AGPL-3.0-or-later
```

---

## Related files

- `THIRD_PARTY_NOTICES.md` — full inventory of third-party licenses used by vendored
  dependencies.
- `CONTRIBUTING.md` (Epic 10) — will link here for the full convention list once
  written.
