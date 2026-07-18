using RDR2;

namespace Rantella.Game
{
    public static class PedTargeting
    {
        /// <summary>
        /// The ped the player is trying to talk to: the game's current
        /// lock-on/focus target if it's a living human ped, else the nearest
        /// human ped within range in front of the player.
        /// </summary>
        public static Ped FindConversationTarget()
        {
            // TODO(M0): 1) try the game's interaction/lock-on target natives;
            //           2) fall back to World.GetNearbyPeds + facing cone;
            //           3) filter: human, alive, not the player, not in combat.
            return null;
        }
    }
}
