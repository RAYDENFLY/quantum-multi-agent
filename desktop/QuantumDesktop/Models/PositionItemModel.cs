using System;
using System.Text.Json.Serialization;

namespace QuantumDesktop.Models;

public class PositionItemModel
{
    [JsonPropertyName("position_id")]
    public string PositionId { get; set; } = string.Empty;

    [JsonPropertyName("symbol")]
    public string Symbol { get; set; } = string.Empty;

    [JsonPropertyName("side")]
    public string Side { get; set; } = "LONG";

    [JsonPropertyName("quantity")]
    public double Quantity { get; set; }

    [JsonPropertyName("entry_price")]
    public double EntryPrice { get; set; }

    [JsonPropertyName("mark_price")]
    public double MarkPrice { get; set; }

    [JsonPropertyName("current_sl")]
    public double CurrentSl { get; set; }

    [JsonPropertyName("current_tp")]
    public double CurrentTp { get; set; }

    [JsonPropertyName("entry_time_ms")]
    public long EntryTimeMs { get; set; }

    [JsonPropertyName("bars_held")]
    public int BarsHeld { get; set; } = 1;

    [JsonPropertyName("volatility_sigma")]
    public double VolatilitySigma { get; set; }

    [JsonPropertyName("notional")]
    public double Notional { get; set; }

    [JsonPropertyName("unrealized_pnl")]
    public double UnrealizedPnl { get; set; }

    [JsonPropertyName("updated_at_ms")]
    public long UpdatedAtMs { get; set; }

    // UI Formatting Helpers
    public string SideColor => Side.ToUpperInvariant() == "LONG" ? "#00E676" : "#FF5252";

    public string HorizonCountdown => $"Bar {BarsHeld} / 24";

    public string FormattedEntryPrice => EntryPrice >= 1.0 ? $"${EntryPrice:F2}" : $"${EntryPrice:F4}";
    public string FormattedMarkPrice => MarkPrice >= 1.0 ? $"${MarkPrice:F2}" : $"${MarkPrice:F4}";
    public string FormattedTp => CurrentTp >= 1.0 ? $"${CurrentTp:F2}" : $"${CurrentTp:F4}";
    public string FormattedSl => CurrentSl >= 1.0 ? $"${CurrentSl:F2}" : $"${CurrentSl:F4}";
    public string FormattedNotional => $"${Notional:F2}";

    // Maker fee: 8.0 bps round trip (4 bps in + 4 bps out)
    public double EstimatedNetPnl => UnrealizedPnl - (Notional * 0.0008);

    public string FormattedNetPnl => EstimatedNetPnl >= 0
        ? $"+${EstimatedNetPnl:F2}"
        : $"-${Math.Abs(EstimatedNetPnl):F2}";

    public string PnlColor => EstimatedNetPnl >= 0 ? "#00E676" : "#FF5252";
}
