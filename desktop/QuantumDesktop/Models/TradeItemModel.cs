using System;
using System.Text.Json.Serialization;

namespace QuantumDesktop.Models;

public class TradeItemModel
{
    [JsonPropertyName("trade_id")]
    public string TradeId { get; set; } = string.Empty;

    [JsonPropertyName("symbol")]
    public string Symbol { get; set; } = string.Empty;

    [JsonPropertyName("side")]
    public string Side { get; set; } = "LONG";

    [JsonPropertyName("quantity")]
    public double Quantity { get; set; }

    [JsonPropertyName("entry_price")]
    public double EntryPrice { get; set; }

    [JsonPropertyName("exit_price")]
    public double ExitPrice { get; set; }

    [JsonPropertyName("entry_time_ms")]
    public long EntryTimeMs { get; set; }

    [JsonPropertyName("exit_time_ms")]
    public long ExitTimeMs { get; set; }

    [JsonPropertyName("exit_reason")]
    public string ExitReason { get; set; } = string.Empty;

    [JsonPropertyName("gross_pnl")]
    public double GrossPnl { get; set; }

    [JsonPropertyName("fee")]
    public double Fee { get; set; }

    [JsonPropertyName("slippage")]
    public double Slippage { get; set; }

    [JsonPropertyName("net_pnl")]
    public double NetPnl { get; set; }

    [JsonPropertyName("net_return_bps")]
    public double NetReturnBps { get; set; }

    [JsonPropertyName("bars_held")]
    public int BarsHeld { get; set; }

    // UI Formatting Helpers
    public string SideColor => Side.ToUpperInvariant() == "LONG" ? "#00E676" : "#FF5252";

    public string FormattedNetPnl => NetPnl >= 0 ? $"+${NetPnl:F2}" : $"-${Math.Abs(NetPnl):F2}";

    public string PnlColor => NetPnl >= 0 ? "#00E676" : "#FF5252";

    public string FormattedReturnBps => $"{NetReturnBps:+0.0;-0.0;0.0} bps";

    public string FormattedEntryPrice => EntryPrice >= 1.0 ? $"${EntryPrice:F2}" : $"${EntryPrice:F4}";
    public string FormattedExitPrice => ExitPrice >= 1.0 ? $"${ExitPrice:F2}" : $"${ExitPrice:F4}";

    public string ExitReasonBadge => ExitReason switch
    {
        "TAKE_PROFIT" => "TP HIT",
        "STOP_LOSS" => "SL HIT",
        "TIMEOUT_24BAR" => "HORIZON EXIT",
        "KILL_SWITCH" => "KILL SWITCH",
        _ => ExitReason.Replace("_", " ")
    };

    public string ExitReasonColor => ExitReason switch
    {
        "TAKE_PROFIT" => "#00E676",
        "STOP_LOSS" => "#FF5252",
        "TIMEOUT_24BAR" => "#2979FF",
        "KILL_SWITCH" => "#D50000",
        _ => "#78909C"
    };
}
