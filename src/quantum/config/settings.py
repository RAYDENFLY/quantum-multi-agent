"""Application configuration models and persistence for QUANTUM Trading Desk."""

import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AppConfig(BaseModel):
    """Core desktop application settings."""
    model_config = ConfigDict(validate_assignment=True)

    app_name: str = "QUANTUM Multi-Agent Trading Desk"
    version: str = "0.1.0"
    log_level: str = "INFO"
    theme_mode: str = "obsidian"  # "obsidian" or "daylight"
    ui_refresh_hz: int = Field(default=4, ge=1, le=10)
    window_width: int = Field(default=1440, ge=1024)
    window_height: int = Field(default=900, ge=700)


class SingleExchangeConfig(BaseModel):
    """Configuration for an individual exchange adapter."""
    model_config = ConfigDict(validate_assignment=True)

    enabled: bool = True
    rest_base_url: str = ""
    ws_base_url: str = ""
    rate_limit_rps: float = Field(default=10.0, ge=1.0, le=50.0)
    timeout_s: float = Field(default=10.0, ge=1.0, le=60.0)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_backoff_s: float = Field(default=1.0, ge=0.1, le=10.0)
    ping_interval_s: float = Field(default=20.0, ge=5.0, le=60.0)
    ping_timeout_s: float = Field(default=10.0, ge=2.0, le=30.0)
    max_reconnect_attempts: int = Field(default=10, ge=1, le=50)
    initial_backoff_s: float = Field(default=1.0, ge=0.1, le=10.0)
    max_backoff_s: float = Field(default=60.0, ge=5.0, le=300.0)


class ExchangeConfig(BaseModel):
    """Exchange adapter and connectivity parameters."""
    model_config = ConfigDict(validate_assignment=True)

    bybit_enabled: bool = True
    aster_enabled: bool = True
    rest_poll_interval_s: int = Field(default=60, ge=10, le=300)
    max_ws_subscriptions: int = Field(default=25, ge=5, le=100)

    bybit: SingleExchangeConfig = Field(
        default_factory=lambda: SingleExchangeConfig(
            enabled=True,
            rest_base_url="https://api.bybit.com",
            ws_base_url="wss://stream.bybit.com/v5/public/linear",
            rate_limit_rps=10.0,
        )
    )
    aster: SingleExchangeConfig = Field(
        default_factory=lambda: SingleExchangeConfig(
            enabled=True,
            rest_base_url="https://fapi.asterdex.com",
            ws_base_url="wss://fstream.asterdex.com/ws",
            rate_limit_rps=10.0,
        )
    )

    candle_retention_days: int = Field(default=30, ge=7, le=180)
    ticker_retention_days: int = Field(default=7, ge=1, le=30)
    orderbook_retention_hours: int = Field(default=24, ge=1, le=168)
    batch_flush_interval_s: float = Field(default=1.0, ge=0.1, le=10.0)
    batch_max_size: int = Field(default=500, ge=10, le=5000)
    freshness_stale_threshold_s: float = Field(default=5.0, ge=1.0, le=30.0)
    freshness_invalid_threshold_s: float = Field(default=15.0, ge=5.0, le=60.0)


class ScannerConfig(BaseModel):
    """Stage A-D dynamic market scanner thresholds."""
    model_config = ConfigDict(validate_assignment=True)

    min_24h_turnover_usdt: float = Field(default=5_000_000.0, ge=500_000.0)
    max_spread_bps: float = Field(default=12.0, ge=2.0, le=50.0)
    min_scanner_score: float = Field(default=68.0, ge=40.0, le=95.0)
    symbol_cooldown_minutes: int = Field(default=15, ge=5, le=120)


class RiskConfig(BaseModel):
    """Deterministic risk limits enforced by Agent 4."""
    model_config = ConfigDict(validate_assignment=True)

    starting_paper_equity_usdt: float = Field(default=10_000.0, ge=1_000.0)
    risk_per_trade_pct: float = Field(default=0.005, ge=0.001, le=0.02)
    max_concurrent_positions: int = Field(default=3, ge=1, le=8)
    max_symbol_exposure_pct: float = Field(default=0.15, ge=0.05, le=0.30)
    max_total_exposure_pct: float = Field(default=0.45, ge=0.10, le=1.00)
    max_leverage_per_position: float = Field(default=3.0, ge=1.0, le=5.0)
    max_daily_loss_pct: float = Field(default=0.025, ge=0.01, le=0.05)
    max_total_drawdown_pct: float = Field(default=0.08, ge=0.03, le=0.15)
    min_net_reward_risk: float = Field(default=1.80, ge=1.50, le=4.00)
    max_spread_bps: float = Field(default=12.0, ge=3.0, le=25.0)
    max_estimated_slippage_bps: float = Field(default=10.0, ge=2.0, le=25.0)
    loss_streak_cooldown_count: int = Field(default=3, ge=2, le=5)
    per_symbol_loss_cooldown_min: int = Field(default=45, ge=15, le=240)


class MLConfig(BaseModel):
    """Local CPU ML inference, offline training, and tunable agent decision parameters.

    NOTE: Default thresholds are initial uncalibrated engineering baselines,
    NOT statistically validated optima. Precise thresholds must be empirically
    selected on cross-validation folds in Phase 5 without in-sample overfitting.
    """
    model_config = ConfigDict(validate_assignment=True)

    fallback_policy: str = "FALLBACK_RULE_ONLY"  # "FALLBACK_RULE_ONLY" or "STRICT_ML_ONLY"
    scout_min_prob: float = Field(default=0.56, ge=0.50, le=0.80)
    scout_max_wick_trap: float = Field(default=0.55, ge=0.20, le=0.80)
    analyst_min_prob: float = Field(default=0.58, ge=0.50, le=0.85)
    analyst_invalidation_atr_mult: float = Field(default=1.75, ge=1.0, le=3.0)
    sniper_min_expected_r: float = Field(default=0.25, ge=0.10, le=1.00)
    sniper_min_gross_rr: float = Field(default=1.80, ge=1.50, le=3.00)
    sniper_tp1_r_multiple: float = Field(default=2.0, ge=1.2, le=3.5)
    sniper_tp2_r_multiple: float = Field(default=3.2, ge=2.0, le=6.0)
    sniper_tp1_close_pct: float = Field(default=0.50, ge=0.20, le=0.80)
    banker_hazard_exit_prob: float = Field(default=0.78, ge=0.65, le=0.95)
    banker_trailing_stop_activation_r: float = Field(default=2.0, ge=1.0, le=4.0)
    banker_trailing_stop_distance_atr: float = Field(default=1.0, ge=0.5, le=2.5)
    max_training_cpu_threads: int = Field(default=2, ge=1, le=8)
    lookback_days: int = Field(default=90, ge=30, le=365)


class Settings(BaseModel):
    """Root configuration holding all sub-configurations."""
    data_dir_path: str = Field(default_factory=lambda: str(Path.home() / ".quantum"))
    app: AppConfig = Field(default_factory=AppConfig)
    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    ml: MLConfig = Field(default_factory=MLConfig)

    @property
    def data_dir(self) -> Path:
        """Return the resolved data directory Path."""
        path = Path(os.environ.get("QUANTUM_DATA_DIR", self.data_dir_path)).expanduser().resolve()
        return path

    @property
    def db_path(self) -> Path:
        """Return the SQLite database file path."""
        env_db = os.environ.get("QUANTUM_DB_PATH")
        if env_db:
            return Path(env_db).expanduser().resolve()
        return self.data_dir / "quantum_desk.db"

    @property
    def config_path(self) -> Path:
        """Return the config.json file path."""
        return self.data_dir / "config.json"

    @property
    def log_path(self) -> Path:
        """Return the rotating log file path."""
        return self.data_dir / "logs" / "quantum.log"

    def ensure_directories(self) -> None:
        """Create required data, log, and artifact directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        """Persist current settings to config.json."""
        self.ensure_directories()
        payload = self.model_dump(exclude={"data_dir_path"})
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @classmethod
    def load(cls, custom_data_dir: Optional[Path] = None) -> "Settings":
        """Load settings from config.json or initialize defaults."""
        data_dir_val = custom_data_dir or Path(os.environ.get("QUANTUM_DATA_DIR", str(Path.home() / ".quantum")))
        resolved_data_dir = Path(data_dir_val).expanduser().resolve()
        config_file = resolved_data_dir / "config.json"

        settings = cls(data_dir_path=str(resolved_data_dir))
        settings.ensure_directories()

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                settings = cls(data_dir_path=str(resolved_data_dir), **data)
            except Exception:
                # If config is invalid or corrupt, preserve existing defaults
                pass
        else:
            settings.save()

        return settings


_GLOBAL_SETTINGS: Optional[Settings] = None


def get_settings(custom_data_dir: Optional[Path] = None) -> Settings:
    """Return the global Settings singleton or a custom instance."""
    global _GLOBAL_SETTINGS
    if custom_data_dir is not None:
        return Settings.load(custom_data_dir=custom_data_dir)
    if _GLOBAL_SETTINGS is None:
        _GLOBAL_SETTINGS = Settings.load()
    return _GLOBAL_SETTINGS
