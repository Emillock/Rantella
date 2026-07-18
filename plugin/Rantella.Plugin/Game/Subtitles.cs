namespace Rantella.Game
{
    public static class Subtitles
    {
        public static void Show(string speaker, string text)
        {
            // TODO(M0): verify PrintSubtitle vs DisplaySubtitle in game and
            // whether long lines need splitting; style speaker name later.
            RDR2.UI.Screen.DisplaySubtitle(speaker + ": " + text);
        }
    }
}
