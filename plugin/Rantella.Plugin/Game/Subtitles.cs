namespace Rantella.Game
{
    public static class Subtitles
    {
        public static void Show(string speaker, string text)
        {
            // TODO(M0): verify against the SHRDN2DN-V2 API surface; prefix
            // with speaker name until we draw proper styled subtitles.
            RDR2.UI.Screen.ShowSubtitle(speaker + ": " + text, 5000);
        }
    }
}
