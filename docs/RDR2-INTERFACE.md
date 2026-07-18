# The `rdr2_websocket` game interface

Pantella discovers game interfaces dynamically — modules in
`src/game_interfaces/` registered by their `interface_slug` and `valid_games`
attributes and selected via `interface_configs/<game_id>.json`. RDR2 support is
therefore **additive**: new modules + configs, near-zero changes to upstream
files — easy to rebase on upstream and easy to offer back as a PR.

## RDR2 modules

| File | Purpose |
|---|---|
| `src/game_interfaces/rdr2_websocket.py` | WebSocket server the C# plugin connects to; implements `BaseGameInterface` |
| `src/conversation_managers/rdr2_websocket.py` | Conversation loop for RDR2 (modeled on the `gradio` manager) |
| `interface_configs/rdr2.json` | Selects the RDR2 modules for `game_id: rdr2` |
| `prompt_styles/rdr2_en_gemma4.json` | 1899 frontier prompt style |
| `characters/rdr2/*.json` | Curated NPC bios (project-written) |
| `plugin/Rantella.Plugin/` | C# game plugin (ScriptHookRDR2DotNet-V2) |

## Base interface mapping

| `BaseGameInterface` method | RDR2 implementation |
|---|---|
| `send_audio_to_external_software(queue_output)` | Play TTS output locally; send `subtitle` + `speech_start` (with duration) to the plugin for gestures |
| `get_player_response(...)` | Base implementation: mic + STT when enabled, console text input otherwise (plugin sends `push_to_talk` state) |
| `is_conversation_ended()` | Tracks `end_conversation` messages from the plugin |
| `end_conversation()` | Sends `end_conversation` to the plugin (release conversation stance) |
| `remove_from_conversation(character)` | Group-conversation bookkeeping (M5) |
| `queue_actor_method(actor, method, *args)` | Sends `action` messages (attack/flee/follow/emote/…) executed by the plugin via natives |
| `load_game_state()` | Blocks until the plugin sends `conversation_start`; builds `character_info` from the ped packet (curated bio by name if present in `characters/rdr2/`, minimal synthesized persona otherwise) |
| `get_current_location(...)` | From latest `context_update` packet |
| `get_current_game_time()` | From the context packet's in-game clock (1899 calendar) |
| `check_mic_status()` | True when a transcriber is configured |
| `is_radiant_dialogue()` | False until NPC↔NPC conversations (M5) |

## Wire protocol

One JSON object per WebSocket text frame: `{"type": ..., "payload": {...}}`,
server at `ws://127.0.0.1:8024`. Canonical definition on the plugin side:
[`plugin/Rantella.Plugin/Ipc/Messages.cs`](../plugin/Rantella.Plugin/Ipc/Messages.cs)
— keep both ends in sync.

| Type | Direction | Payload |
|---|---|---|
| `conversation_start` | game → backend | `ped` (persona_id, model_hash, story_name, is_male, is_lawman), `context` |
| `context_update` | game → backend | region, clock, weather, honor, wanted, distances, recent_events |
| `push_to_talk` | game → backend | `pressed: bool` (mic capture happens backend-side) |
| `end_conversation` | both | `reason` (from game) |
| `subtitle` | backend → game | `speaker`, `text` |
| `speech_start` / `speech_end` | backend → game | `duration` (seconds) for gesture timing |
| `action` | backend → game | `method`, `args[]`, `target` (from `queue_actor_method`) |

## Status

Skeleton — untested against a running game/backend. M0 (first end-to-end
message exchange) is the next milestone; expect field adjustments once the
plugin runs against the real ScriptHookRDR2DotNet API.
