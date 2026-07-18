print("Importing game_interfaces/rdr2_websocket.py")
from src.logging import logging, time
from src.game_interfaces.base_interface import BaseGameInterface
import src.utils as utils
import asyncio
import json
import os
import threading
try:
    import winsound
except ImportError:  # non-Windows dev environment
    winsound = None
logging.info("Imported required libraries in game_interfaces/rdr2_websocket.py")

valid_games = ["rdr2"]
interface_slug = "rdr2_websocket"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8024


class GameInterface(BaseGameInterface):
    """Talks to the Rantella C# game plugin (plugin/Rantella.Plugin) over a
    localhost WebSocket. One JSON object per text frame:
    {"type": ..., "payload": {...}} — see docs/RDR2-INTERFACE.md for the
    protocol and plugin/Rantella.Plugin/Ipc/Messages.cs for the canonical
    definition."""

    def __init__(self, conversation_manager, valid_games=valid_games, interface_slug=interface_slug):
        super().__init__(conversation_manager, valid_games, interface_slug)
        self.audio_supported = True
        self.text_supported = True
        self.host = getattr(self.config, "rdr2_ws_host", DEFAULT_HOST)
        self.port = int(getattr(self.config, "rdr2_ws_port", DEFAULT_PORT))
        self._loop = None
        self._client = None
        self._client_lock = threading.Lock()
        self.pending_conversation = None  # payload of the last unconsumed conversation_start
        self.latest_context = {}
        self.conversation_ended_flag = False
        self.ptt_pressed = threading.Event()
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        logging.info(f"RDR2 WebSocket interface listening on ws://{self.host}:{self.port}")

    # --- WebSocket server (background thread, own asyncio loop) ---

    def _run_server(self):
        import websockets
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def start():
            await websockets.serve(self._handler, self.host, self.port)

        self._loop.run_until_complete(start())
        self._loop.run_forever()

    async def _handler(self, websocket, path=None):
        logging.info("RDR2 plugin connected")
        with self._client_lock:
            self._client = websocket
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    logging.error(f"Malformed frame from RDR2 plugin: {raw[:200]}")
                    continue
                self._dispatch(msg.get("type"), msg.get("payload") or {})
        except Exception as e:
            logging.error(f"RDR2 plugin connection error: {e}")
        finally:
            with self._client_lock:
                if self._client is websocket:
                    self._client = None
            logging.info("RDR2 plugin disconnected")

    def _dispatch(self, msg_type, payload):
        if msg_type == "conversation_start":
            self.latest_context = payload.get("context") or {}
            self.pending_conversation = payload
            self.conversation_ended_flag = False
        elif msg_type == "context_update":
            self.latest_context = payload
            # TODO(M1): feed payload["recent_events"] into new_game_events once
            # the render_game_event format is settled for RDR2.
        elif msg_type == "push_to_talk":
            if payload.get("pressed"):
                self.ptt_pressed.set()
            else:
                self.ptt_pressed.clear()
        elif msg_type == "end_conversation":
            self.conversation_ended_flag = True
        else:
            logging.warning(f"Unknown message type from RDR2 plugin: {msg_type}")

    def send_to_game(self, msg_type, payload=None):
        with self._client_lock:
            client = self._client
        if client is None or self._loop is None:
            logging.warning(f"No RDR2 plugin connected; dropping '{msg_type}' message")
            return
        frame = json.dumps({"type": msg_type, "payload": payload or {}})
        asyncio.run_coroutine_threadsafe(client.send(frame), self._loop)

    # --- BaseGameInterface implementation ---

    @utils.time_it
    def load_game_state(self):
        """Blocks until the plugin reports the player started a conversation."""
        logging.info("Waiting for the player to start a conversation in RDR2...")
        while self.pending_conversation is None:
            time.sleep(0.1)
        start = self.pending_conversation
        self.pending_conversation = None
        ped = start.get("ped") or {}
        character_info = self._character_info_from_ped(ped)
        location = self.get_current_location(presume="the American frontier")
        player_name = getattr(self.config, "player_name", "Arthur")
        player_race = getattr(self.config, "player_race", "American")
        player_gender = getattr(self.config, "player_gender", "Male")
        return character_info, location, player_name, player_race, player_gender

    def _character_info_from_ped(self, ped):
        """Resolve a ped packet into character_info: curated bio if the story
        name is in characters/rdr2/, otherwise a minimal synthesized persona.
        TODO(M3): procedural persona generation seeded by model hash + region,
        persisted per persona_id."""
        name = ped.get("story_name")
        db = getattr(self.conversation_manager, "character_database", None)
        if name and db is not None:
            record = getattr(db, "named_index", {}).get(name)
            if record is not None:
                logging.info(f"Found curated RDR2 character: {name}")
                return record
        gender = "Male" if ped.get("is_male", True) else "Female"
        display_name = name or "Stranger"
        persona_id = ped.get("persona_id") or f"rdr2_ped_{ped.get('model_hash', 0)}"
        role = "a lawman" if ped.get("is_lawman") else "an ordinary local"
        pronoun = "He" if gender == "Male" else "She"
        return {
            "name": display_name,
            "ref_id": persona_id,
            "base_id": f"{ped.get('model_hash', 0):08X}",
            "gender": gender,
            "race": "American",
            "in_game_race": "Human",
            "species": "Human",
            "age": "adult",
            "voice_model": "maleeventoned" if gender == "Male" else "femaleeventoned",
            "location": self.get_current_location(presume="the American frontier"),
            "bio": f"{display_name} is {role} living near {self.get_current_location(presume='the American frontier')} in 1899. {pronoun} doesn't know the person approaching them.",
            "knows": [],
        }

    def get_current_location(self, presume=''):
        region = (self.latest_context or {}).get("region")
        if region and region != "unknown":
            return region
        return presume or "the American frontier"

    def get_current_game_time(self):
        clock = (self.latest_context or {}).get("clock")
        if not clock:
            return self.get_dummy_game_time()
        hour24 = int(clock.get("hour24", 12))
        minute = int(clock.get("minute", 0))
        hour12 = hour24 % 12
        ampm = 'AM' if hour24 < 12 else 'PM'
        return {
            "year": int(clock.get("year", 1899)),
            "month": int(clock.get("month", 5)),
            "day": int(clock.get("day", 14)),
            "hour24": hour24,
            "hour12": hour12,
            "minute": minute,
            "time24": f"{hour24:02}:{minute:02}",
            "time12": f"{hour12:02}:{minute:02} {ampm}",
            "ampm": ampm,
        }

    def is_conversation_ended(self):
        return self.conversation_ended_flag

    def end_conversation(self):
        self.send_to_game("end_conversation", {})
        self.conversation_ended_flag = True
        return True

    def remove_from_conversation(self, character):
        # TODO(M5): group conversations
        logging.info(f"remove_from_conversation({character}) not implemented for RDR2 yet")

    def check_mic_status(self):
        return self.transcriber is not None

    def queue_actor_method(self, actor_character, method_name, *args):
        target = getattr(actor_character, "name", None)
        logging.info(f"RDR2 action: {method_name}({args}) on {target}")
        self.send_to_game("action", {
            "method": method_name,
            "args": [str(a) for a in args],
            "target": target,
        })

    async def send_audio_to_external_software(self, queue_output):
        """Play the TTS line on the backend side and cue subtitles + talking
        gestures in game. The base class waits out the audio duration before
        sending the next sentence."""
        audio_file, sentence = queue_output[0], queue_output[1]
        logging.info(f"Dialogue to play: {audio_file} — {sentence}")
        duration = await self.get_audio_duration(audio_file)
        speaker = self.active_character.name if self.active_character is not None else ""
        self.send_to_game("subtitle", {"speaker": speaker, "text": sentence})
        self.send_to_game("speech_start", {"duration": duration})
        # TODO(M2): positional attenuation from context distance/bearing;
        # for now play the wav flat. The plugin times gestures off `duration`.
        if winsound is not None and audio_file and os.path.exists(audio_file):
            winsound.PlaySound(audio_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            logging.warning(f"Cannot play audio file locally: {audio_file}")
