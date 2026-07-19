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

## State (2026-07-19): M0 COMPLETE — first live voice conversations work

Full loop verified in game (Horseshoe Overlook camp): mic → faster-whisper →
Gemma 4 E4B (GPU, RTX 5070) → Piper → subtitle/gesture cue to plugin. ~4 s
per turn after the first (~60 s prompt-cache warmup). NPC stays in character
(1899, English-only, western dialect). Setup that works: game root has
dinput8.dll (Ultimate ASI Loader) + ScriptHookRDR2.dll (community V2 2.0) +
ScriptHookRDRDotNet 2.2 files; `scripts/` has Rantella.Plugin.dll +
Newtonsoft. Backend: `.venv` py3.10 + `requirements-rdr2.txt` +
machine-local `configs/rdr2_config.json` (all dialog-triggering keys must be
pre-seeded — any `None` opens a blocking Tk dialog). Insert = hot-reload
scripts in game.

**Critical finding: boolean-returning natives (and wrapper properties on
them) return garbage** with this hook combo — IS_PED_HUMAN, IS_ENTITY_DEAD,
IS_PED_A_PLAYER, Exists(). Never filter on them. Int/vector natives
(GET_ENTITY_COORDS, handles, GET_PED_TYPE) are reliable. Targeting is
nearest-ped-by-distance (6 m) via coords natives only.

Known rough edges / next (M1): per-sentence WAV filename collision
(voiceline.wav overwritten while playing), subtitle display in game
unverified (DisplaySubtitle vs PrintSubtitle), conversation stance tuning,
region/clock/honor context still stubbed ("the American frontier"), persona
persistence + rdr2 character generator (M3), actions untested in game (M4).
Six upstream-worthy bug fixes are in git history (piper ×2, logger, base
transcriber init, torch index, speechbrain pin) — PR candidates.
