using RDR2;

namespace Rantella.Game
{
    public static class PedTargeting
    {
        private const float ConversationRange = 4f; // meters

        /// <summary>
        /// The ped the player is trying to talk to: the nearest living human
        /// ped within conversation range. TODO(M1): prefer the game's
        /// lock-on/aim target and require a facing cone so the player can
        /// pick one ped out of a crowd.
        /// </summary>
        public static Ped FindConversationTarget()
        {
            var player = RDR2.Game.Player.Character;
            if (player == null || !player.Exists()) return null;

            Ped best = null;
            var bestDist = ConversationRange;
            foreach (var ped in World.GetAllPeds())
            {
                if (ped == null || !ped.Exists() || !ped.IsAlive || !ped.IsHuman) continue;
                if (ped.Handle == player.Handle) continue;
                var dist = ped.Position.DistanceTo(player.Position);
                if (dist < bestDist)
                {
                    bestDist = dist;
                    best = ped;
                }
            }
            return best;
        }
    }
}
