using System;
using System.Windows.Forms;
using Rantella.Game;
using Rantella.Ipc;
using RDR2;

namespace Rantella
{
    /// <summary>
    /// Script entry point, loaded by ScriptHookRDR2DotNet from RDR2/scripts/.
    /// Keep this thin: routes tick + input to the conversation controller.
    /// </summary>
    public class Main : Script
    {
        private readonly BackendClient _backend = new BackendClient();
        private readonly ConversationController _conversation;

        // M0 defaults; move to an .ini later.
        private const Keys TalkKey = Keys.T;
        private const Keys EndKey = Keys.Y;

        public Main()
        {
            _conversation = new ConversationController(_backend);
            Tick += OnTick;
            KeyDown += OnKeyDown;
            KeyUp += OnKeyUp;
            Aborted += (s, e) => _backend.Dispose();
        }

        private void OnTick(object sender, EventArgs e)
        {
            _conversation.Update();

            // Drain backend messages on the script thread.
            while (_backend.TryReceive(out var msg))
                _conversation.Handle(msg);
        }

        private void OnKeyDown(object sender, KeyEventArgs e)
        {
            switch (e.KeyCode)
            {
                case TalkKey:
                    _conversation.OnTalkKeyDown();
                    break;
                case EndKey:
                    _conversation.End("player_ended");
                    break;
            }
        }

        private void OnKeyUp(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == TalkKey)
                _conversation.OnTalkKeyUp();
        }
    }
}
