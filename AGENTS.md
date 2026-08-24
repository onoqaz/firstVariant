# AGENTS.md

Docs-only repo: a Russian-language course on automotive electrics («курс по автоэлектрике»). No code, builds, lint, tests, or CI — verification means keeping the Markdown internally consistent.

## Layout

- All content lives in `курс по автоэлектрике/` (Cyrillic path with spaces — quote it in shell commands).
- `План обучения автоэлектрика.md` is the master index (TOC + per-module lesson outlines). Any new/renamed module must be reflected in its Оглавление; each TOC entry combines a GitHub anchor and a relative file link on one line.
- Each of the 20 modules is a file pair:
  - `Module_NN_<Тема>.md` — lesson content
  - `Module_NN_<Тема>_questions.md` — exactly 20 numbered questions titled `# Вопросы к модулю NN — Тема`
- Follow the naming scheme exactly: zero-padded `NN` (01–20), topic words joined by underscores.

## Gotchas

- `План обучения автоэлектрика.md` (lines ~26–50) contains unresolved merge-conflict markers (`<<<<<<< ours` … `>>>>>>> theirs`). The "theirs" block links to `Quiz_NN_*.md` files that **do not exist** — real question files are suffixed `_questions`. Do not create `Quiz_*` files or reuse those links.
- Content is entirely in Russian; keep edits in Russian. Existing files contain Latin/Cyrillic typo artifacts (e.g., «interpretarовать», «Клerk Maxwell») — don't propagate them when editing nearby text.
- Module files often share sections (`Ликбез`, `Историческая справка`, `Нестандартные решения вендоров`, `Практические задания`), but the structure isn't rigid — match the target file's own layout instead of imposing a template.

## Git

- History uses Conventional Commits, e.g. `docs(course): update introductory module documentation`.
- Work branches follow `session/agent_*`; there is no `main`.
