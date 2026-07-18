using Rantella.Ipc;
using RDR2;

namespace Rantella.Game
{
    public enum ConversationState
    {
        Idle,
        Active, // NPC held in conversation stance; PTT drives listening
    }

    /// <summary>
    /// Owns the conversation lifecycle on the game side:
    /// target ped -> start -> stream context -> execute backend messages -> end.
    /// </summary>
    public class ConversationController
    {
        private readonly BackendClient _backend;
        private Ped _npc;

        public ConversationState State { get; private set; } = ConversationState.Idle;

        public ConversationController(BackendClient backend)
        {
            _backend = backend;
        }

        public void OnTalkKeyDown()
        {
            if (State == ConversationState.Idle)
            {
                _npc = PedTargeting.FindConversationTarget();
                if (_npc == null) return;

                // TODO(M0): conversation stance —
                //   SET_BLOCKING_OF_NON_TEMPORARY_EVENTS, task turn-to-face,
                //   STOP_CURRENT_PLAYING_AMBIENT_SPEECH.
                State = ConversationState.Active;
                _backend.Send(MessageTypes.ConversationStart, new
                {
                    ped = ContextCollector.DescribePed(_npc),
                    context = ContextCollector.Collect(_npc),
                });
            }

            // Mic capture happens backend-side; we just signal the gesture.
            _backend.Send(MessageTypes.PushToTalk, new { pressed = true });
        }

        public void OnTalkKeyUp()
        {
            if (State == ConversationState.Active)
                _backend.Send(MessageTypes.PushToTalk, new { pressed = false });
        }

        public void Update()
        {
            if (State != ConversationState.Active || _npc == null) return;

            if (!_npc.Exists() || ContextCollector.DistanceToPlayer(_npc) > 12f)
            {
                End("player_left");
                return;
            }

            // TODO(M1): throttle to ~1 Hz.
            _backend.Send(MessageTypes.ContextUpdate, ContextCollector.Collect(_npc));
        }

        public void Handle(Envelope msg)
        {
            switch (msg.Type)
            {
                case MessageTypes.Subtitle:
                    var sub = msg.Payload.ToObject<SubtitleMsg>();
                    Subtitles.Show(sub.Speaker, sub.Text);
                    break;
                case MessageTypes.SpeechStart:
                    // TODO(M2): play talking gestures on _npc for the
                    // payload's duration while the backend plays the audio.
                    break;
                case MessageTypes.SpeechEnd:
                    break;
                case MessageTypes.Action:
                    ActionExecutor.Execute(_npc, msg.Payload.ToObject<ActionMsg>());
                    break;
                case MessageTypes.EndConversation:
                    End("backend_ended");
                    break;
            }
        }

        public void End(string reason)
        {
            if (State == ConversationState.Idle) return;
            State = ConversationState.Idle;
            // TODO(M0): release conversation stance, resume ambient behavior.
            _backend.Send(MessageTypes.EndConversation, new { reason });
            _npc = null;
        }
    }
}
