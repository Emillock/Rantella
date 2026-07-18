using System.Collections.Generic;
using Rantella.Ipc;
using RDR2;

namespace Rantella.Game
{
    public static class ContextCollector
    {
        public static PedInfo DescribePed(Ped ped)
        {
            // TODO(M0): persona id via decorator (DECOR_SET_INT) so the same
            // ped keeps the same persona; story-NPC name from model hash map.
            return new PedInfo
            {
                PersonaId = "ped_" + ped.Handle,
                ModelHash = (uint)ped.Model.Hash,
                StoryName = null,
                IsMale = ped.Gender == Gender.Male,
                IsLawman = false // TODO: ped type / relationship group
            };
        }

        public static GameContext Collect(Ped npc)
        {
            // TODO(M1): region/district name, in-game clock natives, weather,
            // honor, wanted state, nearby conversed peds, recent world events.
            return new GameContext
            {
                Region = "unknown",
                Clock = null,
                Weather = "unknown",
                PlayerHonor = 0,
                PlayerWanted = false,
                NearbyPersonaIds = new List<string>(),
                DistanceToPlayer = DistanceToPlayer(npc),
                BearingToPlayer = 0f,
                RecentEvents = new List<string>(),
            };
        }

        public static float DistanceToPlayer(Ped npc)
        {
            var player = RDR2.Game.Player.Character;
            return player == null || npc == null
                ? float.MaxValue
                : npc.Position.DistanceTo(player.Position);
        }
    }
}
