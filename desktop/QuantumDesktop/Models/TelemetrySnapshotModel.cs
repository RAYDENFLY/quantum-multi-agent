using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace QuantumDesktop.Models;

public class SpecialistSnapshotItem
{
    [JsonPropertyName("symbol")]
    public string Symbol { get; set; } = string.Empty;

    [JsonPropertyName("tier")]
    public int Tier { get; set; } = 1;

    [JsonPropertyName("is_enabled")]
    public bool IsEnabled { get; set; } = true;

    [JsonPropertyName("prob_long")]
    public double ProbLong { get; set; } = 0.33;

    [JsonPropertyName("prob_short")]
    public double ProbShort { get; set; } = 0.33;

    [JsonPropertyName("prob_neutral")]
    public double ProbNeutral { get; set; } = 0.34;

    [JsonPropertyName("margin")]
    public double Margin { get; set; } = 0.0;

    [JsonPropertyName("prob_margin_threshold")]
    public double ProbMarginThreshold { get; set; } = 0.20;

    [JsonPropertyName("sigma_bps")]
    public double SigmaBps { get; set; } = 0.0;

    [JsonPropertyName("vol_threshold_bps")]
    public double VolThresholdBps { get; set; } = 160.0;

    [JsonPropertyName("gate_status")]
    public string GateStatus { get; set; } = "FILTERED_VOLATILITY";

    [JsonPropertyName("last_price")]
    public double LastPrice { get; set; } = 0.0;

    [JsonPropertyName("has_active_position")]
    public bool HasActivePosition { get; set; }

    [JsonPropertyName("has_pending_order")]
    public bool HasPendingOrder { get; set; }
}

public class TelemetrySnapshotModel
{
    [JsonPropertyName("timestamp_ms")]
    public long TimestampMs { get; set; }

    [JsonPropertyName("clock_mode")]
    public string ClockMode { get; set; } = "HISTORICAL_REPLAY_STREAM";

    [JsonPropertyName("is_paused")]
    public bool IsPaused { get; set; } = true;

    [JsonPropertyName("is_kill_switch_active")]
    public bool IsKillSwitchActive { get; set; } = false;

    [JsonPropertyName("account")]
    public AccountStateModel Account { get; set; } = new();

    [JsonPropertyName("active_positions_count")]
    public int ActivePositionsCount { get; set; }

    [JsonPropertyName("pending_orders_count")]
    public int PendingOrdersCount { get; set; }

    [JsonPropertyName("specialists")]
    public Dictionary<string, SpecialistSnapshotItem> Specialists { get; set; } = new();

    [JsonPropertyName("recent_events")]
    public List<string> RecentEvents { get; set; } = new();
}

public class PortfolioResponseModel
{
    [JsonPropertyName("account")]
    public AccountStateModel Account { get; set; } = new();

    [JsonPropertyName("active_positions")]
    public List<PositionItemModel> ActivePositions { get; set; } = new();

    [JsonPropertyName("recent_trades")]
    public List<TradeItemModel> RecentTrades { get; set; } = new();
}
