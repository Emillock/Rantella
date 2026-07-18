using Rantella.Ipc;
using RDR2;
using RDR2.Math;

namespace Rantella.Game
{
    public static class ActionExecutor
    {
        public static void Execute(Ped npc, ActionMsg msg)
        {
            if (npc == null || !npc.Exists() || msg == null) return;
            var player = RDR2.Game.Player.Character;

            switch (msg.Method)
            {
                case "attack":
                    npc.BlockPermanentEvents = false;
                    npc.AlwaysKeepTask = false;
                    npc.Task.ClearTasks(false);
                    if (player != null) npc.Task.Combat(player, -1);
                    break;

                case "flee":
                    npc.BlockPermanentEvents = false;
                    npc.AlwaysKeepTask = false;
                    npc.Task.ClearTasks(false);
                    if (player != null) npc.Task.Flee(player, -1, eFleeStyle.MajorThreat);
                    break;

                case "follow":
                    npc.Task.ClearTasks(false);
                    // Walk just behind the player's right shoulder, stop ~1.5 m out.
                    if (player != null)
                        npc.Task.FollowToOffsetOfEntity(player, new Vector3(0.5f, -1.0f, 0f), 1.0f, -1, 1.5f, true);
                    break;

                case "stop_following":
                    npc.Task.ClearTasks(false);
                    npc.Task.WanderAround();
                    break;

                case "cower":
                    if (player != null) npc.Task.Cower(-1, player);
                    break;

                case "hands_up":
                    if (player != null) npc.Task.HandsUp(-1, player, -1);
                    break;

                case "mount_and_leave":
                    npc.BlockPermanentEvents = false;
                    npc.AlwaysKeepTask = false;
                    npc.Task.ClearTasks(false);
                    var mount = npc.CurrentMount;
                    if (mount != null && mount.Exists())
                        npc.Task.MountAnimal(mount, -1, eVehicleSeat.Driver, 2.0f, 0);
                    else
                        npc.Task.WanderAround(); // no horse nearby; just leave
                    break;

                // TODO(M4): emote (gesture natives), give_item, set_disposition
                // (relationship groups), call_law, native_interaction (input
                // injection for greet/antagonize/rob).
                default:
                    Subtitles.Show("Rantella", "[action not implemented: " + msg.Method + "]");
                    break;
            }
        }
    }
}
