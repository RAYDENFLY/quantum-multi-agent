using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using QuantumDesktop.Models;
using QuantumDesktop.Services;

namespace QuantumDesktop.ViewModels;

public partial class MainViewModel : ViewModelBase, IDisposable
{
    private readonly QuantumDaemonClient _client;
    private readonly DispatcherTimer _pollTimer;

    // Header State
    [ObservableProperty]
    private bool _isConnected = false;

    [ObservableProperty]
    private string _connectionText = "CONNECTING TO DAEMON...";

    [ObservableProperty]
    private string _connectionColor = "#FFA726";

    [ObservableProperty]
    private string _clockMode = "HISTORICAL REPLAY STREAM";

    [ObservableProperty]
    private bool _isPaused = true;

    [ObservableProperty]
    private string _pauseButtonText = "RESUME";

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(KillSwitchStatusText))]
    [NotifyPropertyChangedFor(nameof(KillSwitchStatusColor))]
    private bool _isKillSwitchActive = false;

    public string KillSwitchStatusText => IsKillSwitchActive ? "LOCKED (TRIGGERED)" : "ARMED (NORMAL)";
    public string KillSwitchStatusColor => IsKillSwitchActive ? "#FF5252" : "#00E676";

    // Account Metrics
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedEquity))]
    private double _equity = 10000.0;

    [ObservableProperty]
    private double _cash = 10000.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedUnrealizedPnl))]
    [NotifyPropertyChangedFor(nameof(UnrealizedPnlColor))]
    private double _unrealizedPnl = 0.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedRealizedPnl))]
    [NotifyPropertyChangedFor(nameof(RealizedPnlColor))]
    private double _realizedPnl = 0.0;

    [ObservableProperty]
    private double _peakEquity = 10000.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedMaxDrawdown))]
    private double _maxDrawdownPct = 0.0;

    [ObservableProperty]
    private double _grossExposure = 0.0;

    [ObservableProperty]
    private double _grossExposurePct = 0.0;

    [ObservableProperty]
    private double _grossExposureProgress = 0.0;

    [ObservableProperty]
    private string _grossExposureColor = "#00E676";

    [ObservableProperty]
    private string _grossExposureText = "0.0% / 30.0% Max Cap";

    public string FormattedEquity => $"${Equity:N2}";
    public string FormattedUnrealizedPnl => UnrealizedPnl >= 0 ? $"+${UnrealizedPnl:F2}" : $"-${Math.Abs(UnrealizedPnl):F2}";
    public string UnrealizedPnlColor => UnrealizedPnl >= 0 ? "#00E676" : "#FF5252";
    public string FormattedRealizedPnl => RealizedPnl >= 0 ? $"+${RealizedPnl:F2}" : $"-${Math.Abs(RealizedPnl):F2}";
    public string RealizedPnlColor => RealizedPnl >= 0 ? "#00E676" : "#FF5252";
    public string FormattedMaxDrawdown => $"{MaxDrawdownPct:F2}%";

    // KPI Summary
    [ObservableProperty]
    private int _totalTradesCount = 0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedWinRate))]
    private double _winRatePct = 0.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedProfitFactor))]
    private double _profitFactor = 0.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedExpectancy))]
    private double _netExpectancyBps = 0.0;

    public string FormattedWinRate => $"{WinRatePct:F1}%";
    public string FormattedProfitFactor => $"{ProfitFactor:F3}";
    public string FormattedExpectancy => $"{NetExpectancyBps:+0.0;-0.0;0.0} bps";

    // Tab 1: Specialists
    public ObservableCollection<SpecialistCardModel> Tier1Specialists { get; } = new();
    public ObservableCollection<SpecialistCardModel> Tier2Specialists { get; } = new();
    public ObservableCollection<SpecialistCardModel> Tier3Specialists { get; } = new();
    public ObservableCollection<SpecialistCardModel> AllSpecialists { get; } = new();

    // Tab 2: Positions & Trades
    public ObservableCollection<PositionItemModel> ActivePositions { get; } = new();
    public ObservableCollection<TradeItemModel> RecentTrades { get; } = new();

    // Tab 3: Governance Explorer
    public ResearchSummaryModel ResearchSummary { get; } = new();

    // Event Log
    public ObservableCollection<string> EventLogEntries { get; } = new();

    public MainViewModel()
    {
        _client = new QuantumDaemonClient();
        _client.OnConnectionStatusChanged += HandleConnectionStatusChanged;
        _client.OnTelemetryReceived += HandleTelemetryReceived;

        InitializeDefaultSpecialists();

        // 3-second portfolio poll timer
        _pollTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(3)
        };
        _pollTimer.Tick += async (s, e) => await RefreshPortfolioAsync();
        _pollTimer.Start();

        _client.StartTelemetryStream();
    }

    private void InitializeDefaultSpecialists()
    {
        var specialists = new[]
        {
            // Tier 1 (Active Alpha Core)
            new SpecialistCardModel { Symbol = "LINKUSDT", Tier = 1, TierName = "Active Alpha Core", VolThresholdBps = 160.0, ProbMarginThreshold = 0.20, ExpectedProfitFactor = 4.702, IsEnabled = true, LastPrice = 18.50, SigmaBps = 168.0, Margin = 0.24, GateStatus = "OPEN", ProbLong = 0.58, ProbNeutral = 0.28, ProbShort = 0.14 },
            new SpecialistCardModel { Symbol = "AVAXUSDT", Tier = 1, TierName = "Active Alpha Core", VolThresholdBps = 160.0, ProbMarginThreshold = 0.20, ExpectedProfitFactor = 1.931, IsEnabled = true, LastPrice = 28.40, SigmaBps = 172.0, Margin = 0.22, GateStatus = "OPEN", ProbLong = 0.55, ProbNeutral = 0.31, ProbShort = 0.14 },
            new SpecialistCardModel { Symbol = "SOLUSDT",  Tier = 1, TierName = "Active Alpha Core", VolThresholdBps = 120.0, ProbMarginThreshold = 0.30, ExpectedProfitFactor = 1.458, IsEnabled = true, LastPrice = 175.20, SigmaBps = 135.0, Margin = 0.32, GateStatus = "OPEN", ProbLong = 0.62, ProbNeutral = 0.26, ProbShort = 0.12 },
            new SpecialistCardModel { Symbol = "ADAUSDT",  Tier = 1, TierName = "Active Alpha Core", VolThresholdBps = 120.0, ProbMarginThreshold = 0.30, ExpectedProfitFactor = 1.075, IsEnabled = true, LastPrice = 0.45, SigmaBps = 125.0, Margin = 0.31, GateStatus = "OPEN", ProbLong = 0.61, ProbNeutral = 0.27, ProbShort = 0.12 },
            new SpecialistCardModel { Symbol = "BNBUSDT",  Tier = 1, TierName = "Active Alpha Core", VolThresholdBps = 160.0, ProbMarginThreshold = 0.20, ExpectedProfitFactor = 1.071, IsEnabled = true, LastPrice = 612.0, SigmaBps = 165.0, Margin = 0.21, GateStatus = "OPEN", ProbLong = 0.54, ProbNeutral = 0.32, ProbShort = 0.14 },

            // Tier 2 (Macro Expansion Core)
            new SpecialistCardModel { Symbol = "BTCUSDT",  Tier = 2, TierName = "Macro Core", VolThresholdBps = 80.0,  ProbMarginThreshold = 0.30, ExpectedProfitFactor = 1.182, IsEnabled = true, LastPrice = 72450.0, SigmaBps = 88.0, Margin = 0.33, GateStatus = "OPEN", ProbLong = 0.63, ProbNeutral = 0.25, ProbShort = 0.12 },
            new SpecialistCardModel { Symbol = "ETHUSDT",  Tier = 2, TierName = "Macro Core", VolThresholdBps = 120.0, ProbMarginThreshold = 0.30, ExpectedProfitFactor = 1.104, IsEnabled = true, LastPrice = 2650.0, SigmaBps = 124.0, Margin = 0.31, GateStatus = "OPEN", ProbLong = 0.61, ProbNeutral = 0.27, ProbShort = 0.12 },

            // Tier 3 (Shadow Monitor-Only)
            new SpecialistCardModel { Symbol = "XRPUSDT",  Tier = 3, TierName = "Shadow Monitor", VolThresholdBps = 200.0, ProbMarginThreshold = 0.30, ExpectedProfitFactor = 0.980, IsEnabled = false, LastPrice = 0.52, SigmaBps = 95.0, Margin = 0.12, GateStatus = "TIER_BLOCKED", ProbLong = 0.38, ProbNeutral = 0.36, ProbShort = 0.26 },
            new SpecialistCardModel { Symbol = "DOGEUSDT", Tier = 3, TierName = "Shadow Monitor", VolThresholdBps = 200.0, ProbMarginThreshold = 0.30, ExpectedProfitFactor = 0.637, IsEnabled = false, LastPrice = 0.16, SigmaBps = 110.0, Margin = 0.08, GateStatus = "TIER_BLOCKED", ProbLong = 0.36, ProbNeutral = 0.38, ProbShort = 0.26 },
            new SpecialistCardModel { Symbol = "LTCUSDT",  Tier = 3, TierName = "Shadow Monitor", VolThresholdBps = 200.0, ProbMarginThreshold = 0.30, ExpectedProfitFactor = 0.671, IsEnabled = false, LastPrice = 68.40, SigmaBps = 85.0, Margin = 0.05, GateStatus = "TIER_BLOCKED", ProbLong = 0.34, ProbNeutral = 0.40, ProbShort = 0.26 },
            new SpecialistCardModel { Symbol = "XMRUSDT",  Tier = 3, TierName = "Shadow Monitor", VolThresholdBps = 200.0, ProbMarginThreshold = 0.30, ExpectedProfitFactor = 0.000, IsEnabled = false, LastPrice = 162.0, SigmaBps = 75.0, Margin = 0.02, GateStatus = "TIER_BLOCKED", ProbLong = 0.33, ProbNeutral = 0.42, ProbShort = 0.25 },
        };

        foreach (var s in specialists)
        {
            AllSpecialists.Add(s);
            if (s.Tier == 1) Tier1Specialists.Add(s);
            else if (s.Tier == 2) Tier2Specialists.Add(s);
            else Tier3Specialists.Add(s);
        }
    }

    private void HandleConnectionStatusChanged(bool connected)
    {
        Dispatcher.UIThread.Post(() =>
        {
            IsConnected = connected;
            if (connected)
            {
                ConnectionText = "CONNECTED TO DAEMON (1Hz TELEMETRY)";
                ConnectionColor = "#00E676"; // Emerald
                AddEvent("IPC WebSocket Connected to http://127.0.0.1:8000");
            }
            else
            {
                ConnectionText = "DISCONNECTED (AUTO-RECONNECTING...)";
                ConnectionColor = "#FF5252"; // Crimson
                AddEvent("IPC WebSocket Disconnected. Retrying...");
            }
        });
    }

    private void HandleTelemetryReceived(TelemetrySnapshotModel snapshot)
    {
        Dispatcher.UIThread.Post(() =>
        {
            ClockMode = snapshot.ClockMode.Replace("_", " ");
            IsPaused = snapshot.IsPaused;
            PauseButtonText = snapshot.IsPaused ? "RESUME" : "PAUSE";
            IsKillSwitchActive = snapshot.IsKillSwitchActive;

            // Account metrics
            Equity = snapshot.Account.Equity;
            Cash = snapshot.Account.Cash;
            UnrealizedPnl = snapshot.Account.UnrealizedPnl;
            RealizedPnl = snapshot.Account.RealizedPnl;
            PeakEquity = snapshot.Account.PeakEquity;
            MaxDrawdownPct = snapshot.Account.MaxDrawdownPct;
            GrossExposure = snapshot.Account.GrossExposure;
            GrossExposurePct = snapshot.Account.GrossExposurePct;

            // Progress bar capped to 30.0% max
            GrossExposureProgress = Math.Clamp((GrossExposurePct / 30.0) * 100.0, 0.0, 100.0);
            GrossExposureText = $"{GrossExposurePct:F1}% / 30.0% Max Cap";

            if (GrossExposurePct >= 28.0)
                GrossExposureColor = "#FF5252"; // Crimson (near cap)
            else if (GrossExposurePct >= 20.0)
                GrossExposureColor = "#FFA726"; // Amber
            else
                GrossExposureColor = "#00E676"; // Emerald

            // Update specialist cards
            if (snapshot.Specialists != null)
            {
                foreach (var kvp in snapshot.Specialists)
                {
                    var card = AllSpecialists.FirstOrDefault(s => s.Symbol == kvp.Key);
                    if (card != null)
                    {
                        var data = kvp.Value;
                        card.ProbLong = data.ProbLong;
                        card.ProbNeutral = data.ProbNeutral;
                        card.ProbShort = data.ProbShort;
                        card.Margin = data.Margin;
                        card.SigmaBps = data.SigmaBps;
                        card.GateStatus = data.GateStatus;
                        card.LastPrice = data.LastPrice;
                        card.HasActivePosition = data.HasActivePosition;
                        card.HasPendingOrder = data.HasPendingOrder;
                    }
                }
            }

            // Sync recent event messages
            if (snapshot.RecentEvents != null)
            {
                foreach (var evt in snapshot.RecentEvents)
                {
                    if (!EventLogEntries.Contains(evt))
                    {
                        AddEvent(evt);
                    }
                }
            }
        });
    }

    private async Task RefreshPortfolioAsync()
    {
        if (!IsConnected)
            return;

        var portfolio = await _client.GetPortfolioAsync();
        if (portfolio == null)
            return;

        Dispatcher.UIThread.Post(() =>
        {
            // Sync positions
            ActivePositions.Clear();
            foreach (var pos in portfolio.ActivePositions)
            {
                ActivePositions.Add(pos);
            }

            // Sync trades
            RecentTrades.Clear();
            foreach (var trd in portfolio.RecentTrades)
            {
                RecentTrades.Add(trd);
            }

            // Recompute summary metrics
            TotalTradesCount = RecentTrades.Count;
            if (TotalTradesCount > 0)
            {
                var winningTrades = RecentTrades.Count(t => t.NetPnl > 0);
                WinRatePct = (double)winningTrades / TotalTradesCount * 100.0;

                var grossWins = RecentTrades.Where(t => t.NetPnl > 0).Sum(t => t.NetPnl);
                var grossLosses = Math.Abs(RecentTrades.Where(t => t.NetPnl < 0).Sum(t => t.NetPnl));
                ProfitFactor = grossLosses > 0 ? (grossWins / grossLosses) : (grossWins > 0 ? 99.9 : 0.0);

                NetExpectancyBps = RecentTrades.Average(t => t.NetReturnBps);
            }
        });
    }

    [RelayCommand]
    public async Task EmergencyKillSwitchAsync()
    {
        AddEvent("[CRITICAL] EMERGENCY KILL-SWITCH INITIATED BY OPERATOR!");
        var ok = await _client.SendControlCommandAsync("EMERGENCY_KILL_SWITCH");
        if (ok)
        {
            IsKillSwitchActive = true;
            AddEvent("[KILL-SWITCH] Executed: All positions liquidated, orders cancelled, account locked.");
            await RefreshPortfolioAsync();
        }
        else
        {
            AddEvent("[ERROR] Failed to deliver kill-switch command to daemon.");
        }
    }

    [RelayCommand]
    public async Task TogglePauseAsync()
    {
        var cmd = IsPaused ? "RESUME" : "PAUSE";
        var ok = await _client.SendControlCommandAsync(cmd);
        if (ok)
        {
            IsPaused = !IsPaused;
            PauseButtonText = IsPaused ? "RESUME" : "PAUSE";
            AddEvent($"Daemon execution state toggled: {cmd}");
        }
    }

    [RelayCommand]
    public async Task StartReplayModeAsync()
    {
        var ok = await _client.SendControlCommandAsync("START_REPLAY", new { max_bars = 500, delay_seconds = 0.05 });
        if (ok)
        {
            ClockMode = "HISTORICAL REPLAY STREAM";
            IsPaused = false;
            PauseButtonText = "PAUSE";
            AddEvent("Mode changed: HISTORICAL REPLAY STREAM (500 bars, 50ms interval)");
        }
    }

    [RelayCommand]
    public async Task StartLivePaperModeAsync()
    {
        var ok = await _client.SendControlCommandAsync("START_LIVE_PAPER", new { poll_interval_seconds = 5.0 });
        if (ok)
        {
            ClockMode = "LIVE WEBSOCKET PAPER";
            IsPaused = false;
            PauseButtonText = "PAUSE";
            AddEvent("Mode changed: LIVE WEBSOCKET PAPER (5.0s candle polling)");
        }
    }

    [RelayCommand]
    public async Task ResetAccountAsync()
    {
        var ok = await _client.SendControlCommandAsync("RESET_ACCOUNT");
        if (ok)
        {
            IsKillSwitchActive = false;
            Equity = 10000.0;
            Cash = 10000.0;
            UnrealizedPnl = 0.0;
            RealizedPnl = 0.0;
            GrossExposure = 0.0;
            GrossExposurePct = 0.0;
            AddEvent("Paper ledger account reset to initial $10,000.00 cash.");
            await RefreshPortfolioAsync();
        }
    }

    [RelayCommand]
    public async Task RefreshAllAsync()
    {
        await RefreshPortfolioAsync();
        AddEvent("Manual refresh requested.");
    }

    private void AddEvent(string msg)
    {
        var timestamp = DateTime.Now.ToString("HH:mm:ss");
        EventLogEntries.Insert(0, $"[{timestamp}] {msg}");
        while (EventLogEntries.Count > 100)
        {
            EventLogEntries.RemoveAt(EventLogEntries.Count - 1);
        }
    }

    public void Dispose()
    {
        _pollTimer.Stop();
        _client.Dispose();
    }
}
