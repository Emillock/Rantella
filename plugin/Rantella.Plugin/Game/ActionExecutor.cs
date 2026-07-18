using Rantella.Ipc;
using RDR2;

namespace Rantella.Game
{
    public static class ActionExecutor
    {
        public static void Execute(Ped npc, ActionMsg msg)
        {
            if (npc == null || msg == null) return;

            switch (msg.Method)
            {
                // TODO(M4): implement via natives — see docs/RDR2-ARCHITECTURE.md §5.
                case "attack":         // TASK_COMBAT_PED
                case "flee":           // TASK_SMART_FLEE_PED
                case "follow":         // TASK_FOLLOW_TO_OFFSET_OF_ENTITY
                case "stop_following": // CLEAR_PED_TASKS + wander
                case "emote":          // speech-gesture / scenario natives
                case "give_item":
                case "mount_and_leave":
                case "set_disposition":
                case "call_law":
                case "native_interaction": // input injection (greet/antagonize/rob)
                default:
                    Subtitles.Show("Rantella", "[action not implemented: " + msg.Method + "]");
                    break;
            }
        }
    }
}
