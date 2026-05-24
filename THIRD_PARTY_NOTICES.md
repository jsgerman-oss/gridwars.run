# Third-Party Notices

GridWars.run is licensed under AGPL-3.0-or-later. It vendors and depends on the
following third-party components, whose licenses and copyrights are reproduced or
referenced below.

---

## Evennia

| Field         | Value                                                        |
| ------------- | ------------------------------------------------------------ |
| Upstream      | <https://github.com/evennia/evennia>                         |
| Pinned tag    | `v6.0.0`                                                     |
| Pinned commit | `966301fc1f0318224f7c78c3702131126075429b`                   |
| Released      | 2026-02-15                                                   |
| License       | BSD-3-Clause                                                 |
| License file  | [`vendor/evennia/LICENSE.txt`](vendor/evennia/LICENSE.txt)   |
| Purpose       | MU\* engine providing networking, sessions, typeclasses, web client, and database. |

The Evennia source is vendored as a git submodule at `vendor/evennia/`. Its BSD-3-Clause
license and copyright notice are preserved verbatim in `vendor/evennia/LICENSE.txt`.

---

<!--
## Future entries — copy this block for each new vendored or bundled dependency

## <Component Name>

| Field         | Value                                           |
| ------------- | ----------------------------------------------- |
| Upstream      | <https://github.com/org/repo>                   |
| Pinned tag    | `vX.Y.Z`                                        |
| Pinned commit | `<full 40-char SHA>`                            |
| Released      | YYYY-MM-DD                                      |
| License       | <SPDX identifier, e.g. MIT / Apache-2.0>        |
| License file  | `vendor/<name>/LICENSE` (or `LICENSE.txt`)      |
| Purpose       | One sentence describing what this component provides. |

<Optional short prose: any special attribution requirement, patent clause, or notice
the upstream LICENSE mandates beyond name + license identifier.>

---
-->
