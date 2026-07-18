using System.Collections.Generic;
using Newtonsoft.Json;

namespace Rantella.Ipc
{
    // Wire protocol between the game plugin and the Rantella backend.
    // One JSON object per WebSocket text frame, with "type" as the
    // discriminator. Keep in sync with the backend's
    // src/game_interfaces/rdr2_websocket.py.

    public static class MessageTypes
    {
        // game -> backend
        public const string ConversationStart = "conversation_start";
        public const string ContextUpdate = "context_update";
        public const string PushToTalk = "push_to_talk"; // pressed/released; mic capture happens backend-side

        // both directions
        public const string EndConversation = "end_conversation";

        // backend -> game
        public const string Subtitle = "subtitle";
        public const string Action = "action";
        public const string SpeechStart = "speech_start"; // begin talking gestures; payload carries duration
        public const string SpeechEnd = "speech_end";
    }

    public class Envelope
    {
        [JsonProperty("type")] public string Type;
        [JsonProperty("payload")] public Newtonsoft.Json.Linq.JObject Payload;
    }

    public class PedInfo
    {
        [JsonProperty("persona_id")] public string PersonaId; // stable id (decorator); backend keys memory on this
        [JsonProperty("model_hash")] public uint ModelHash;
        [JsonProperty("story_name")] public string StoryName; // null for generic peds
        [JsonProperty("is_male")] public bool IsMale;
        [JsonProperty("is_lawman")] public bool IsLawman;
    }

    public class GameClock
    {
        [JsonProperty("year")] public int Year;
        [JsonProperty("month")] public int Month;
        [JsonProperty("day")] public int Day;
        [JsonProperty("hour24")] public int Hour24;
        [JsonProperty("minute")] public int Minute;
    }

    public class GameContext
    {
        [JsonProperty("region")] public string Region;
        [JsonProperty("clock")] public GameClock Clock;
        [JsonProperty("weather")] public string Weather;
        [JsonProperty("player_honor")] public int PlayerHonor;
        [JsonProperty("player_wanted")] public bool PlayerWanted;
        [JsonProperty("nearby_persona_ids")] public List<string> NearbyPersonaIds;
        [JsonProperty("distance_to_player")] public float DistanceToPlayer;
        [JsonProperty("bearing_to_player")] public float BearingToPlayer;
        [JsonProperty("recent_events")] public List<string> RecentEvents;
    }

    public class SubtitleMsg
    {
        [JsonProperty("speaker")] public string Speaker;
        [JsonProperty("text")] public string Text;
    }

    public class SpeechStartMsg
    {
        [JsonProperty("duration")] public double Duration; // seconds; time gestures off this
    }

    public class ActionMsg
    {
        // Mirrors the backend's queue_actor_method(actor, method_name, *args):
        // e.g. method "attack", "flee", "follow", "stop_following", "emote",
        // "give_item", "mount_and_leave", "set_disposition", "call_law",
        // "native_interaction" (greet/antagonize/rob via input injection)
        [JsonProperty("method")] public string Method;
        [JsonProperty("args")] public List<string> Args;
        [JsonProperty("target")] public string Target; // character name; null = the active NPC
    }
}
