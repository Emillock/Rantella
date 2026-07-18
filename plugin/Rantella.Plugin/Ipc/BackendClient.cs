using System;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Rantella.Ipc
{
    /// <summary>
    /// WebSocket connection to the Rantella backend, run on a background
    /// thread. Script code (which runs on the game's script thread and must
    /// never block) talks to it only through the two queues.
    /// </summary>
    public sealed class BackendClient : IDisposable
    {
        private readonly Uri _uri;
        private readonly ConcurrentQueue<Envelope> _incoming = new ConcurrentQueue<Envelope>();
        private readonly BlockingCollection<string> _outgoing = new BlockingCollection<string>();
        private readonly CancellationTokenSource _cts = new CancellationTokenSource();
        private readonly Task _pump;

        public volatile bool Connected;

        public BackendClient(string url = "ws://127.0.0.1:8024/game")
        {
            _uri = new Uri(url);
            _pump = Task.Run(PumpAsync);
        }

        public void Send(string type, object payload)
        {
            var frame = new JObject
            {
                ["type"] = type,
                ["payload"] = payload == null ? new JObject() : JObject.FromObject(payload),
            };
            _outgoing.Add(frame.ToString(Formatting.None));
        }

        /// <summary>Called from the script tick; never blocks.</summary>
        public bool TryReceive(out Envelope msg) => _incoming.TryDequeue(out msg);

        private async Task PumpAsync()
        {
            while (!_cts.IsCancellationRequested)
            {
                using (var ws = new ClientWebSocket())
                {
                    try
                    {
                        await ws.ConnectAsync(_uri, _cts.Token);
                        Connected = true;
                        var recv = ReceiveLoopAsync(ws);
                        var send = SendLoopAsync(ws);
                        await Task.WhenAny(recv, send);
                    }
                    catch
                    {
                        // Backend not running yet, or dropped — retry below.
                    }
                    finally
                    {
                        Connected = false;
                    }
                }
                try { await Task.Delay(3000, _cts.Token); } catch (TaskCanceledException) { break; }
            }
        }

        private async Task ReceiveLoopAsync(ClientWebSocket ws)
        {
            var buffer = new byte[64 * 1024];
            var text = new StringBuilder();
            while (ws.State == WebSocketState.Open && !_cts.IsCancellationRequested)
            {
                var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), _cts.Token);
                if (result.MessageType == WebSocketMessageType.Close) return;
                text.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
                if (!result.EndOfMessage) continue;
                var json = text.ToString();
                text.Clear();
                try
                {
                    var envelope = JsonConvert.DeserializeObject<Envelope>(json);
                    if (envelope?.Type != null) _incoming.Enqueue(envelope);
                }
                catch (JsonException)
                {
                    // Malformed frame from backend; drop it.
                }
            }
        }

        private async Task SendLoopAsync(ClientWebSocket ws)
        {
            while (ws.State == WebSocketState.Open && !_cts.IsCancellationRequested)
            {
                string json;
                try { json = _outgoing.Take(_cts.Token); }
                catch (OperationCanceledException) { return; }
                var bytes = Encoding.UTF8.GetBytes(json);
                await ws.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, _cts.Token);
            }
        }

        public void Dispose()
        {
            _cts.Cancel();
            try { _pump.Wait(1000); } catch { }
            _cts.Dispose();
            _outgoing.Dispose();
        }
    }
}
