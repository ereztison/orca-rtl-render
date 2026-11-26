---
name: rtl-render
description: Show Orca chat replies right-to-left when requested or while RTL mode is active in this chat.
---

- A request to load the skill without a mode selects `on keep` for this chat. An explicit mode takes precedence. Installing or discovering the skill alone does not activate it.
- `$rtl-render` renders the previous reply verbatim, or the content specified, without changing the mode.
- `$rtl-render on` streams the complete Markdown in commentary, then renders that same Markdown and returns the script output as the final reply.
- `$rtl-render on keep` renders first, then streams the original Markdown in the final reply with the visual directive appended on its own line. Use `--keep-original` since the original carries its local links.
- `$rtl-render off` resumes normal replies. Remember the selected mode from conversation context.

On load or mode change, confirm in one short plain-text line with the active mode and the other two options. For example: מצב פעיל `on keep` · אפשרויות נוספות `on`, `off`.

Skip the script for clearly LTR-only prose. Hebrew or Arabic confined to code, paths, or link destinations does not need a card. If unsure, call the script: empty successful output means no card. In either case, send the regular reply or briefly confirm a one-off request.

Resolve `scripts/render.py` relative to this skill. In one Python 3 tool call, pass the Markdown verbatim as UTF-8 stdin or as a safely single-quoted argument after `--`, escaping embedded single quotes. Return the directive and any local file links outside code blocks. On failure, return the original if needed and report the error briefly.
