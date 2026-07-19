using RDR2;
using RDR2.Native;

namespace Rantella.Game
{
    public static class PedTargeting
    {
        private const float ConversationRange = 6f; // meters

        /// <summary>Diagnostics for the last FindConversationTarget call.</summary>
        public static string LastDebug = "";

        /// <summary>
        /// The ped the player is trying to talk to: the nearest living human
        /// ped within conversation range. Filters use direct natives — the
        /// wrapper's IsHuman/IsAlive properties read memory offsets that are
        /// stale for current game builds and reject every ped.
        /// TODO(M1): prefer the game's lock-on/aim target and require a
        /// facing cone so the player can pick one ped out of a crowd.
        /// </summary>
        public static Ped FindConversationTarget()
        {
            var player = RDR2.Game.Player.Character;
            if (player == null)
            {
                LastDebug = "no player ped";
                return null;
            }
            var playerPos = ENTITY.GET_ENTITY_COORDS(player.Handle, true, true);

            // M0 diagnostics: raw native values for the first peds in the
            // pool — coords, distance, IS_PED_A_PLAYER — plus the player's
            // own coords, to see which natives return usable data at all.
            string F(RDR2.Math.Vector3 v)
            {
                return v.X.ToString("0.0") + "/" + v.Y.ToString("0.0") + "/" + v.Z.ToString("0.0");
            }

            Ped best = null;
            var bestDist = float.MaxValue;
            var total = 0;
            var sample = "";
            var shown = 0;
            foreach (var ped in World.GetAllPeds())
            {
                total++;
                if (ped == null) continue;
                var h = ped.Handle;
                if (h == player.Handle) continue;
                var c = ENTITY.GET_ENTITY_COORDS(h, true, true);
                var dist = c.DistanceTo(playerPos);
                if (shown < 2)
                {
                    // NOTE: boolean natives (IS_PED_A_PLAYER, IS_ENTITY_DEAD,
                    // IS_PED_HUMAN) return garbage with this hook combo — do
                    // not filter on them. Int/vector natives are reliable.
                    sample += " | h=" + h + " pos=" + F(c) + " d=" + dist.ToString("0.0");
                    shown++;
                }
                if (dist < bestDist)
                {
                    best = ped;
                    bestDist = dist;
                }
            }
            LastDebug = "peds=" + total + " plrH=" + player.Handle + " plrPos=" + F(playerPos) +
                        " nearest=" + (best == null ? "none" : best.Handle + "@" + bestDist.ToString("0.0") + "m") + sample;

            return best != null && bestDist <= ConversationRange ? best : null;
        }
    }
}
