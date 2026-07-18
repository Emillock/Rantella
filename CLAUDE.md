# CLAUDE.md

Rantella = fork of [Pantella](https://github.com/Pathos14489/Pantella) (GPLv3)
adding **Red Dead Redemption 2** support: voice conversations with any NPC
(multilingual STT → LLM → TTS), per-NPC bios, long-term memory, game-state
awareness, in-game actions. Fork: https://github.com/Emillock/Rantella
(`origin`; `upstream` = Pathos14489/Pantella).

## Where things are

- `docs/RDR2-ARCHITECTURE.md` — full RDR2 design, action table, milestones M0–M5
- `docs/RDR2-INTERFACE.md` — game-interface mapping + wire protocol
- `plugin/Rantella.Plugin/` — C# game plugin (.NET Framework 4.8,
  ScriptHookRDR2DotNet-V2; drop `ScriptHookRDRNetAPI.dll` in `plugin/lib/` to
  build). Canonical protocol DTOs: `plugin/Rantella.Plugin/Ipc/Messages.cs`
- `src/game_interfaces/rdr2_websocket.py` — WebSocket server
  (ws://127.0.0.1:8024) the plugin connects to; implements BaseGameInterface
- `src/conversation_managers/rdr2_websocket.py` — RDR2 conversation loop
  (modeled on the gradio manager)
- `interface_configs/rdr2.json`, `prompt_styles/rdr2_en_gemma4.json`,
  `characters/rdr2/` — RDR2 config, 1899-frontier prompt style, curated bios

## Working rules

- All changes in this repo; commit frequently in small logical chunks; don't
  push without being asked.
- Keep RDR2 support **additive** (new modules/files, minimal edits to upstream
  files) so rebases on upstream and upstream PRs stay easy. Pantella discovers
  modules dynamically by `interface_slug`/`manager_slug` + `valid_games`.
- `interface_configs/*.json` is gitignored upstream — `git add -f` for shipped
  game configs (matches how upstream tracks skyrim.json etc.).
- RDR2 character bios are project-written (no wiki copy-paste); wiki-sourced
  data would need CC-BY-SA attribution.

## Local clone gotchas

This working copy is a **blobless sparse clone** — the full repo is ~7 GB
(`data/` 5.5 GB, `addons/` 2 GB of binaries). Cone: src, interface_configs,
prompt_styles, behavior_styles, characters, docs, plugin. Need another dir?
`git sparse-checkout add <dir>`. Plain `git clone` of this repo hangs for a
long time — don't.

## State (2026-07-18) and next step

Skeleton committed and syntax-checked, **untested against the real
game/backend**. Next milestone is **M0**: implement the plugin's TODO stubs
against the real ScriptHookRDR2DotNet-V2 API (ped targeting, conversation
stance natives, subtitles), run the backend with `game_id: rdr2`, and get one
end-to-end subtitle + canned WAV in game. Expect protocol/field adjustments —
keep Messages.cs and rdr2_websocket.py in sync.
