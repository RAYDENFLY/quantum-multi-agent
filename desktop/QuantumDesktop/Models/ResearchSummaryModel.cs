using System.Collections.Generic;

namespace QuantumDesktop.Models;

public class SpecialistBenchmarkModel
{
    public string Symbol { get; set; } = string.Empty;
    public string TierName { get; set; } = string.Empty;
    public double VolThresholdBps { get; set; }
    public double ProbMargin { get; set; }
    public double ProfitFactor { get; set; }
    public double NetExpectancyBps { get; set; }
    public double WinRatePct { get; set; }
    public string Status { get; set; } = "APPROVED";
    public string StatusColor => Status.Contains("APPROVED") ? "#00E676" : "#78909C";
    public string FormattedProfitFactor => $"{ProfitFactor:F3}";
    public string FormattedExpectancy => $"{NetExpectancyBps:+0.0;-0.0;0.0} bps";
    public string FormattedVolThreshold => $"{VolThresholdBps:F0} bps";
    public string FormattedProbMargin => $"{ProbMargin:F2}";
    public string FormattedWinRate => $"{WinRatePct:F1}%";
}

public class ResearchSummaryModel
{
    public string Phase55Status { get; set; } = "COMPLETED / REJECTED (MODE 1 UNCONDITIONAL)";
    public string Phase55FrictionAnalysis { get; set; } = "Round-trip taker friction (44.0 bps) exceeds typical barrier width (15-31 bps) on 90%+ of bars.";
    public string Phase56Verdict { get; set; } = "QUALIFIED / ASYMMETRIC MAKER OVERLAY";
    public string Phase56OverlayMechanics { get; set; } = "2.5 : 1.0 Asymmetric Barriers reduce breakeven win rate to 28.6%. 8.0 bps Maker-Passive fee unlocks sustained positive expectancy.";

    public List<SpecialistBenchmarkModel> SpecialistBenchmarks { get; set; } = new()
    {
        new SpecialistBenchmarkModel { Symbol = "LINKUSDT", TierName = "Tier 1: Alpha Core", VolThresholdBps = 160, ProbMargin = 0.20, ProfitFactor = 4.702, NetExpectancyBps = 186.2, WinRatePct = 65.5, Status = "TIER 1 APPROVED" },
        new SpecialistBenchmarkModel { Symbol = "AVAXUSDT", TierName = "Tier 1: Alpha Core", VolThresholdBps = 160, ProbMargin = 0.20, ProfitFactor = 1.931, NetExpectancyBps = 105.4, WinRatePct = 48.0, Status = "TIER 1 APPROVED" },
        new SpecialistBenchmarkModel { Symbol = "SOLUSDT",  TierName = "Tier 1: Alpha Core", VolThresholdBps = 120, ProbMargin = 0.30, ProfitFactor = 1.458, NetExpectancyBps = 46.1,  WinRatePct = 39.5, Status = "TIER 1 APPROVED" },
        new SpecialistBenchmarkModel { Symbol = "BTCUSDT",  TierName = "Tier 2: Macro Core", VolThresholdBps = 80,  ProbMargin = 0.30, ProfitFactor = 1.182, NetExpectancyBps = 14.2,  WinRatePct = 33.3, Status = "TIER 2 APPROVED" },
        new SpecialistBenchmarkModel { Symbol = "ETHUSDT",  TierName = "Tier 2: Macro Core", VolThresholdBps = 120, ProbMargin = 0.30, ProfitFactor = 1.104, NetExpectancyBps = 8.5,   WinRatePct = 32.1, Status = "TIER 2 APPROVED" },
        new SpecialistBenchmarkModel { Symbol = "ADAUSDT",  TierName = "Tier 1: Alpha Core", VolThresholdBps = 120, ProbMargin = 0.30, ProfitFactor = 1.075, NetExpectancyBps = 10.8,  WinRatePct = 31.8, Status = "TIER 1 APPROVED" },
        new SpecialistBenchmarkModel { Symbol = "BNBUSDT",  TierName = "Tier 1: Alpha Core", VolThresholdBps = 160, ProbMargin = 0.20, ProfitFactor = 1.071, NetExpectancyBps = 6.3,   WinRatePct = 31.4, Status = "TIER 1 APPROVED" },
        new SpecialistBenchmarkModel { Symbol = "XRPUSDT",  TierName = "Tier 3: Shadow",     VolThresholdBps = 200, ProbMargin = 0.30, ProfitFactor = 0.980, NetExpectancyBps = -2.1,  WinRatePct = 26.2, Status = "TIER 3 BLOCKED" },
        new SpecialistBenchmarkModel { Symbol = "LTCUSDT",  TierName = "Tier 3: Shadow",     VolThresholdBps = 200, ProbMargin = 0.30, ProfitFactor = 0.671, NetExpectancyBps = -35.4, WinRatePct = 21.0, Status = "TIER 3 BLOCKED" },
        new SpecialistBenchmarkModel { Symbol = "DOGEUSDT", TierName = "Tier 3: Shadow",     VolThresholdBps = 200, ProbMargin = 0.30, ProfitFactor = 0.637, NetExpectancyBps = -42.8, WinRatePct = 19.5, Status = "TIER 3 BLOCKED" },
        new SpecialistBenchmarkModel { Symbol = "XMRUSDT",  TierName = "Tier 3: Shadow",     VolThresholdBps = 200, ProbMargin = 0.30, ProfitFactor = 0.000, NetExpectancyBps = 0.0,    WinRatePct = 0.0,  Status = "TIER 3 BLOCKED" },
    };
}
