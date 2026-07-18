# Rantella — RDR2 Architecture

Rantella is a fork of [Pantella](https://github.com/Pathos14489/Pantella) that
brings AI NPC conversations to Red Dead Redemption 2: multilingual STT → LLM →
TTS, where the LLM knows the NPC's biography, remembers past conversations, is
aware of the current game state, and can trigger in-game actions (befriend, get
angry and attack, follow the player, flee, …). Conversations can move from NPC
to NPC.

This document describes the RDR2-specific design. The generic backend
(inference engines, TTS, memory, characters, behaviors) is upstream Pantella —
see the main README.

---

## 1. System overview

Two processes on the player's machine:

```
┌────────────────────────────┐        WebSocket (localhost)        ┌──────────────────────────────┐
│  RDR2 + game plugin (C#)   │ ◄─────────────────────────────────► │  Rantella backend (Python)   │
│  plugin/Rantella.Plugin    │                                     │                              │
│                            │  game → backend:                    │  • STT (faster-whisper)      │
│  • detect / target NPC     │    conversation events, context     │  • persona resolver / DB     │
│  • collect game context    │                                     │  • prompt builder + memory   │
│  • hold NPC in convo pose  │  backend → game:                    │  • LLM (OpenAI-compatible)   │
│  • play gestures           │    subtitles, actions, audio cues   │  • action parser (behaviors) │
│  • execute actions (natives)│                                    │  • TTS (Piper / XTTS / …)    │
│  • draw subtitles          │                                     │  • audio playback (3D-ish)   │
└────────────────────────────┘                                     └──────────────────────────────┘
```

Principle: **the game plugin stays thin** (sensing + acting only); all AI logic
lives in the backend. This mirrors Pantella's Skyrim split and keeps the part
that breaks on game updates as small as possible.

### Why this is *easier* than Skyrim in one way

Skyrim must squeeze communication through Papyrus + file I/O hacks. An RDR2
plugin is native code — a real WebSocket client with streaming, no file
polling. Latency and reliability should be better.

### Why it is *harder* in others

| Skyrim has | RDR2 equivalent | Consequence |
|---|---|---|
| SKSE, mature mod APIs | ScriptHookRDR2 (closed-source ASI loader) + natives | Everything via [native DB](https://alloc8or.re/rdr3/nativedb/); fewer helpers |
| Mostly named NPCs with wiki bios | Mostly *generic* peds; ~few dozen story NPCs | Need procedural persona generation with stable identity |
| Modder-generated lip files (FaceFX tooling) | No public facial-animation tooling | No true lip sync; use talking gestures/facial animations instead |
| ESP records to identify NPCs | Ped model hash + script metadata | Identity system built on decorators + model hash + region |

### Prior art: Talk to Strangers (Red Dead Voice Input)

[Talk to Strangers](https://www.nexusmods.com/reddeadredemption2/mods/7485) is
the closest existing RDR2 mod: hold RMB/L2, speak, and a background Python
script (Vosk STT → intent matching) injects the game's own interaction inputs
via a virtual gamepad (`vgamepad`) / keyboard to fire RDR2's built-in
Greet / Antagonize / Rob prompts. No ScriptHook involved. What we take from it:

- **Push-to-talk UX is proven**: hold the game's own focus button (L2/RMB) at
  an NPC and speak; end-of-speech detected by mic silence. We adopt the same
  gesture — it composes naturally with RDR2's targeting.
- **Input injection as a second action channel**: for actions the game already
  implements with real voiced reactions and mechanics (greet, antagonize,
  rob), injecting the native interaction can complement our `TASK_*` natives —
  e.g. the game's actual robbery flow instead of a scripted imitation.
- **Vosk** is a lightweight STT option for fast intent-only commands, though
  free-form multilingual dialogue still wants Whisper-class models.
- Caveat: check the mod's Nexus permissions before reusing any of its *code*;
  the techniques themselves (mic capture, `vgamepad`) are standard libraries.

## 2. Game plugin (`plugin/Rantella.Plugin`)

**Stack (settled 2026-07-18): C# / .NET Framework 4.8** on
[ScriptHookRDR2DotNet-V2](https://github.com/Halen84/ScriptHookRDR2DotNet-V2)
(zlib license, source available — we vendor/fix it ourselves if needed).
Chosen over raw C++ ASI for iteration speed: WebSocket, JSON, and audio are
trivial in C#. RDR2 has had no title updates in years, so the wrapper being
unmaintained since 2023 carries little practical risk.

Responsibilities:

1. **Targeting** — player aims at / stands near a ped and presses the talk
   hotkey. Raycast from camera → ped, fall back to nearest ped in a cone.
2. **Context packet** — on conversation start and periodically during it:
   ped model hash + name (if story character), gender, is-lawman/gang flags,
   player location (region/town name via `MAP` natives), in-game clock,
   weather, player honor, wanted state, nearby peds (for group conversations),
   recent world events the plugin observed (gunshots, player crimes).
3. **Conversation stance** — `SET_BLOCKING_OF_NON_TEMPORARY_EVENTS` so the NPC
   doesn't wander/panic, task the ped to face the player, play idle talking
   gestures while TTS audio plays, suppress ambient barks
   (`STOP_CURRENT_PLAYING_AMBIENT_SPEECH`).
4. **Subtitles** — draw NPC replies (and optionally the player's transcribed
   words) with UI natives, streamed sentence by sentence.
5. **Action execution** — apply structured actions from the backend via
   `TASK_*` / relationship natives (see §5).
6. **Identity tagging** — stamp each conversed ped with a persona ID decorator
   (`DECOR_SET_INT`) so re-approaching the same ped resumes the same persona
   within a session; persistence across sessions keyed by persona ID in the
   backend DB.

## 3. Backend (`src/game_interfaces/rdr2_websocket.py`)

Pipeline per conversation turn (all generic parts are stock Pantella):

1. **Push-to-talk capture** → **STT**: `faster-whisper` (multilingual, local,
   fast).
2. **Persona resolution**:
   - Story NPC (known model hash / name) → curated bio from
     `characters/rdr2/*.json` (name, backstory, speech style, TTS voice,
     relationships, knowledge cutoffs — a 1899 rancher knows nothing of the
     modern world).
   - Generic ped → **procedurally generated persona**, seeded deterministically
     (model hash + spawn region) and then persisted, so "the tall fellow outside
     the Valentine saloon" stays the same person.
3. **Prompt assembly**: `prompt_styles/rdr2_en_gemma4.json` (1899 frontier
   setting) + persona bio + retrieved memories (ChromaDB) + live game context
   packet + conversation history.
4. **LLM call**: any OpenAI-compatible endpoint (OpenRouter, OpenAI, LM Studio,
   llama.cpp server, koboldcpp). Streaming; actions via Pantella's behavior
   system.
5. **TTS**: Piper as the fast local default (voice per persona); optional
   XTTS-v2 / GPT-SoVITS profiles for cloning story-character voices from files
   the *user* extracts locally (we never distribute game assets).
6. **Playback**: backend plays audio, attenuated from ped-to-player distance
   (plugin streams positions); plugin triggers talking gestures for the
   duration.
7. **Memory write-back**: on conversation end, memories embed into the
   persona's ChromaDB store, including *what happened* (actions, fights,
   gifts), not just what was said.

## 4. Conversation model

- **State machine** per conversation: `idle → greeting → listening →
  thinking → speaking → (action) → listening … → farewell`.
- **Ending**: LLM signals farewell intent, player presses end-hotkey, or player
  walks out of range (NPC gets a goodbye line).
- **NPC-to-NPC handoff**: a shared short-term "recent events" buffer travels
  with the player, so the next NPC can be told "the player just talked to X
  about Y nearby" when plausible (same location, NPC could have overheard).
- **Group conversations**: multiple peds registered in one conversation; the
  LLM decides who replies — Pantella's multi-NPC support.
- **Radiant (NPC↔NPC) conversations**: stretch goal.

## 5. Actions

Routed through Pantella's behavior system → `queue_actor_method` → `action`
messages to the plugin. Initial action set (all implementable with documented
natives):

| Action | Natives (sketch) |
|---|---|
| Attack player / target | `TASK_COMBAT_PED` |
| Flee | `TASK_SMART_FLEE_PED` |
| Follow player | `TASK_FOLLOW_TO_OFFSET_OF_ENTITY` |
| Stop following / leave | `CLEAR_PED_TASKS`, wander task |
| Emotes: wave, greet, tip hat, point, laugh, cry | speech-gesture / scenario natives |
| Give or take item/money | inventory natives + animation |
| Mount horse & ride off | `TASK_MOUNT_ANIMAL` |
| Disposition change (friendly ↔ hostile) | relationship-group natives; persisted in persona memory |
| Call the law on the player | dispatch/wanted natives |
| Native interactions: greet / antagonize / rob | input injection into the game's own interaction system (Talk to Strangers technique) |

Disposition is **persistent**: insult a shopkeeper today and the memory + a
stored disposition score makes him cold tomorrow.

## 6. Latency budget (target: first spoken word < ~2.5 s after player stops talking)

- STT (faster-whisper small/medium, GPU): ~0.3–0.8 s
- LLM first sentence (streaming): ~0.5–1.5 s (endpoint-dependent)
- TTS first sentence (Piper): ~0.2–0.5 s
- Pantella already pipelines sentence-by-sentence (TTS starts on the first
  complete sentence while the LLM is still generating); we keep it.

## 7. Milestones

- **M0 — spike**: plugin targets a ped, freezes him into conversation stance,
  sends context over WebSocket, displays a subtitle from the backend, backend
  plays a canned WAV. *Proves the whole integration path.*
- **M1 — text conversations**: LLM + curated personas for a few story NPCs +
  procedural personas for generics; keyboard text input; subtitles.
- **M2 — voice loop**: push-to-talk STT in, Piper TTS out, gesture playback.
- **M3 — memory**: persona persistence, disposition, RDR2 character generator.
- **M4 — actions**: full action table above, honor/law integration.
- **M5 — social**: group conversations, NPC-to-NPC handoff, config UI/installer.

## 8. Licensing & legal

- Rantella is a GPLv3 fork of Pantella, with upstream attribution preserved.
  The whole repository, including the C# plugin, is GPLv3.
- ScriptHookRDR2 is closed-source, free for non-commercial use, and disables
  Red Dead Online — this mod is **single-player only** by construction.
- We distribute **no Rockstar assets**. Voice cloning of story characters, if
  ever, happens from files the user extracts locally.
- RDR2 character bios in `characters/rdr2/` are written by this project (not
  copied from wikis); if wiki-sourced data is ever added, it must keep
  CC-BY-SA attribution like upstream's Skyrim data.
