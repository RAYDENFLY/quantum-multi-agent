using System.Text.Json.Serialization;

namespace QuantumDesktop.Models;

public class AccountStateModel
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("timestamp_ms")]
    public long TimestampMs { get; set; }

    [JsonPropertyName("equity")]
    public double Equity { get; set; } = 10000.0;

    [JsonPropertyName("cash")]
    public double Cash { get; set; } = 10000.0;

    [JsonPropertyName("unrealized_pnl")]
    public double UnrealizedPnl { get; set; }

    [JsonPropertyName("realized_pnl")]
    public double RealizedPnl { get; set; }

    [JsonPropertyName("peak_equity")]
    public double PeakEquity { get; set; } = 10000.0;

    [JsonPropertyName("max_drawdown_pct")]
    public double MaxDrawdownPct { get; set; }

    [JsonPropertyName("gross_exposure")]
    public double GrossExposure { get; set; }

    [JsonPropertyName("gross_exposure_pct")]
    public double GrossExposurePct { get; set; }

    [JsonPropertyName("is_kill_switch_active")]
    public bool IsKillSwitchActive { get; set; }
}
