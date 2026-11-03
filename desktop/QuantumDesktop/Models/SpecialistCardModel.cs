using System;
using System.Text.Json.Serialization;
using CommunityToolkit.Mvvm.ComponentModel;

namespace QuantumDesktop.Models;

public partial class SpecialistCardModel : ObservableObject
{
    [ObservableProperty]
    private string _symbol = string.Empty;

    [ObservableProperty]
    private int _tier = 1;

    [ObservableProperty]
    private string _tierName = "Active Alpha Core";

    [ObservableProperty]
    private bool _isEnabled = true;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ProbLongPct))]
    [NotifyPropertyChangedFor(nameof(ProbLongText))]
    private double _probLong = 0.33;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ProbNeutralPct))]
    [NotifyPropertyChangedFor(nameof(ProbNeutralText))]
    private double _probNeutral = 0.34;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ProbShortPct))]
    [NotifyPropertyChangedFor(nameof(ProbShortText))]
    private double _probShort = 0.33;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedMargin))]
    [NotifyPropertyChangedFor(nameof(IsMarginPassing))]
    private double _margin = 0.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedMargin))]
    [NotifyPropertyChangedFor(nameof(IsMarginPassing))]
    private double _probMarginThreshold = 0.20;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedVol))]
    [NotifyPropertyChangedFor(nameof(IsVolPassing))]
    private double _sigmaBps = 0.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedVol))]
    [NotifyPropertyChangedFor(nameof(IsVolPassing))]
    private double _volThresholdBps = 160.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(IsGateOpen))]
    [NotifyPropertyChangedFor(nameof(GateBadgeText))]
    [NotifyPropertyChangedFor(nameof(GateBadgeColor))]
    private string _gateStatus = "FILTERED_VOLATILITY";

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedPrice))]
    private double _lastPrice = 0.0;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FormattedExpectedPf))]
    private double _expectedProfitFactor = 1.0;

    public string FormattedExpectedPf => $"Exp. PF: {ExpectedProfitFactor:F3}";

    [ObservableProperty]
    private bool _hasActivePosition = false;

    [ObservableProperty]
    private bool _hasPendingOrder = false;

    // Computed UI helper properties
    public string DisplayName => Symbol.Replace("USDT", " / USDT");

    public string FormattedPrice => LastPrice >= 1.0 ? $"${LastPrice:F2}" : $"${LastPrice:F4}";

    public string FormattedMargin => $"{Margin:+0.00;-0.00;0.00} (Gate: \u2265 {ProbMarginThreshold:F2})";

    public bool IsMarginPassing => Margin >= ProbMarginThreshold;

    public string FormattedVol => $"{SigmaBps:F1} bps (Gate: \u2265 {VolThresholdBps:F1})";

    public bool IsVolPassing => SigmaBps >= VolThresholdBps;

    public bool IsGateOpen => string.Equals(GateStatus, "OPEN", StringComparison.OrdinalIgnoreCase);

    public string GateBadgeText => GateStatus switch
    {
        "OPEN" => "GATE OPEN",
        "FILTERED_VOLATILITY" => "VOL FILTERED",
        "FILTERED_MARGIN" => "MARGIN FILTERED",
        "TIER_BLOCKED" => "SHADOW BLOCKED",
        "ACCOUNT_LOCKED" => "KILL SWITCH",
        "MAX_EXPOSURE_REACHED" => "CAP REACHED",
        _ => GateStatus.Replace("_", " ")
    };

    public string GateBadgeColor => GateStatus switch
    {
        "OPEN" => "#00E676",               // Emerald
        "FILTERED_VOLATILITY" => "#FFA726", // Amber
        "FILTERED_MARGIN" => "#FFCA28",     // Yellow-Amber
        "TIER_BLOCKED" => "#546E7A",        // Gray-Muted
        "ACCOUNT_LOCKED" => "#FF5252",      // Red
        "MAX_EXPOSURE_REACHED" => "#FF7043",// Orange
        _ => "#78909C"
    };

    public string TierBadgeColor => Tier switch
    {
        1 => "#00E676", // Emerald (Alpha Core)
        2 => "#2979FF", // Blue (Macro Core)
        _ => "#78909C"  // Muted (Shadow)
    };

    public double ProbLongPct => Math.Clamp(ProbLong * 100.0, 0.0, 100.0);
    public double ProbNeutralPct => Math.Clamp(ProbNeutral * 100.0, 0.0, 100.0);
    public double ProbShortPct => Math.Clamp(ProbShort * 100.0, 0.0, 100.0);

    public string ProbLongText => $"L: {ProbLong:P0}";
    public string ProbNeutralText => $"N: {ProbNeutral:P0}";
    public string ProbShortText => $"S: {ProbShort:P0}";
}
