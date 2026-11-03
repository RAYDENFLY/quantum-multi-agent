using System;
using System.IO;
using System.Net.Http;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using QuantumDesktop.Models;

namespace QuantumDesktop.Services;

public class QuantumDaemonClient : IDisposable
{
    private readonly string _baseHttpUrl;
    private readonly string _baseWsUrl;
    private readonly HttpClient _httpClient;
    private ClientWebSocket? _webSocket;
    private CancellationTokenSource? _streamCts;
    private bool _isDisposed;

    public event Action<TelemetrySnapshotModel>? OnTelemetryReceived;
    public event Action<bool>? OnConnectionStatusChanged;

    public bool IsConnected { get; private set; }

    public QuantumDaemonClient(string baseHost = "127.0.0.1", int port = 8000)
    {
        _baseHttpUrl = $"http://{baseHost}:{port}";
        _baseWsUrl = $"ws://{baseHost}:{port}/ws/v1/telemetry";
        _httpClient = new HttpClient
        {
            BaseAddress = new Uri(_baseHttpUrl),
            Timeout = TimeSpan.FromSeconds(5)
        };
    }

    public async Task<bool> CheckHealthAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/api/v1/health");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<PortfolioResponseModel?> GetPortfolioAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/api/v1/paper/portfolio");
            if (!response.IsSuccessStatusCode)
                return null;

            var json = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<PortfolioResponseModel>(json);
        }
        catch
        {
            return null;
        }
    }

    public async Task<bool> SendControlCommandAsync(string command, object? parameters = null)
    {
        try
        {
            var payload = new
            {
                command = command.ToUpperInvariant(),
                @params = parameters ?? new { }
            };

            var json = JsonSerializer.Serialize(payload);
            using var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync("/api/v1/paper/control", content);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public void StartTelemetryStream()
    {
        if (_streamCts != null)
            return;

        _streamCts = new CancellationTokenSource();
        Task.Run(() => StreamLoopAsync(_streamCts.Token));
    }

    public void StopTelemetryStream()
    {
        _streamCts?.Cancel();
        _streamCts = null;

        try
        {
            if (_webSocket?.State == WebSocketState.Open)
            {
                _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None).Wait(1000);
            }
        }
        catch
        {
            // Ignore close exceptions during shutdown
        }
    }

    private async Task StreamLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested && !_isDisposed)
        {
            try
            {
                _webSocket = new ClientWebSocket();
                await _webSocket.ConnectAsync(new Uri(_baseWsUrl), ct);

                IsConnected = true;
                OnConnectionStatusChanged?.Invoke(true);

                var buffer = new byte[65536];
                using var ms = new MemoryStream();

                while (_webSocket.State == WebSocketState.Open && !ct.IsCancellationRequested)
                {
                    ms.SetLength(0);
                    WebSocketReceiveResult result;
                    do
                    {
                        result = await _webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), ct);
                        if (result.MessageType == WebSocketMessageType.Close)
                        {
                            await _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Acknowledge Close", ct);
                            break;
                        }
                        ms.Write(buffer, 0, result.Count);
                    }
                    while (!result.EndOfMessage);

                    if (result.MessageType == WebSocketMessageType.Text && ms.Length > 0)
                    {
                        ms.Seek(0, SeekOrigin.Begin);
                        var snapshot = await JsonSerializer.DeserializeAsync<TelemetrySnapshotModel>(ms, cancellationToken: ct);
                        if (snapshot != null)
                        {
                            OnTelemetryReceived?.Invoke(snapshot);
                        }
                    }
                }
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
                // Connection failed or dropped
            }
            finally
            {
                if (IsConnected)
                {
                    IsConnected = false;
                    OnConnectionStatusChanged?.Invoke(false);
                }

                try
                {
                    _webSocket?.Dispose();
                }
                catch
                {
                    // Ignore dispose errors
                }
                _webSocket = null;
            }

            // Retry after delay
            if (!ct.IsCancellationRequested)
            {
                try
                {
                    await Task.Delay(2000, ct);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
            }
        }
    }

    public void Dispose()
    {
        if (_isDisposed)
            return;

        _isDisposed = true;
        StopTelemetryStream();
        _httpClient.Dispose();
    }
}
