"""Agents & Models workspace shell (Alt+3) displaying agent telemetry cards and local model registry."""

from typing import Dict, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quantum.domain.enums import AgentId, ModelStatus
from quantum.ml.registry import ModelMetadata, ModelRegistry
from quantum.ui.widgets.empty_state import EmptyStateWidget


class AgentsPage(QWidget):
    """Workspace 3: Agents and Local ML Model Registry."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._agent_cards: Dict[str, Dict[str, QLabel]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        lbl_title = QLabel("Workspace 3: Agents & Local ML Models")
        lbl_title.setProperty("class", "title")
        lbl_subtitle = QLabel("Local CPU machine learning models, inference latency telemetry, and model registry.")
        lbl_subtitle.setProperty("class", "subtitle")
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # 2. 5-Agent Model Status Cards Row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        agent_configs = [
            ("SCOUT", "Agent 1: Opportunity Filter", "LightGBM + Anomaly Z", "FALLBACK_RULE_ONLY", "rule_baseline_v1"),
            ("ANALYST", "Agent 2: Regime Conditioner", "Multi-TF Regime + Meta", "FALLBACK_RULE_ONLY", "rule_baseline_v1"),
            ("SNIPER", "Agent 3: EV & Barrier Opt", "Triple-Barrier + ATR", "FALLBACK_RULE_ONLY", "rule_baseline_v1"),
            ("RISK", "Agent 4: Portfolio Veto", "Deterministic 12-Gate Python", "100% PYTHON RULE", "deterministic_v1"),
            ("BANKER", "Agent 5: Lifecycle & Exit", "State Machine + Hazard ML", "DETERMINISTIC", "state_machine_v1"),
        ]

        for name, role, algo, mode, default_model in agent_configs:
            card = QFrame()
            card.setProperty("class", "panel")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(12, 10, 12, 10)
            c_layout.setSpacing(4)

            lbl_name = QLabel(name)
            lbl_name.setStyleSheet("font-weight: 700; font-size: 13px; color: #22D3EE;")
            lbl_role = QLabel(role)
            lbl_role.setProperty("class", "muted")
            lbl_role.setStyleSheet("font-size: 10px; color: #94A3B8;")

            lbl_algo = QLabel(algo)
            lbl_algo.setProperty("class", "mono")
            lbl_algo.setStyleSheet("font-size: 10px; color: #CBD5E1;")

            lbl_mode = QLabel(f"[{mode}]")
            lbl_mode.setProperty("class", "mono")
            lbl_mode.setStyleSheet(
                "font-size: 10px; color: #FBBF24; background: #2E2108; padding: 2px 4px; border: 1px solid #FBBF24; border-radius: 3px;"
            )

            lbl_model = QLabel(f"Model: {default_model}")
            lbl_model.setProperty("class", "mono")
            lbl_model.setStyleSheet("font-size: 9px; color: #64748B;")

            metrics_layout = QVBoxLayout()
            metrics_layout.setSpacing(2)

            lbl_latency = QLabel("Latency: 0.0 ms")
            lbl_latency.setProperty("class", "mono")
            lbl_latency.setStyleSheet("font-size: 10px; color: #34D399;")

            lbl_runs = QLabel("Runs: 0 | Props: 0 | Vetos: 0")
            lbl_runs.setProperty("class", "mono")
            lbl_runs.setStyleSheet("font-size: 9px; color: #94A3B8;")

            metrics_layout.addWidget(lbl_latency)
            metrics_layout.addWidget(lbl_runs)

            c_layout.addWidget(lbl_name)
            c_layout.addWidget(lbl_role)
            c_layout.addWidget(lbl_algo)
            c_layout.addWidget(lbl_mode)
            c_layout.addWidget(lbl_model)
            c_layout.addLayout(metrics_layout)
            cards_layout.addWidget(card)

            self._agent_cards[name] = {
                "mode": lbl_mode,
                "model": lbl_model,
                "latency": lbl_latency,
                "runs": lbl_runs,
            }

        layout.addLayout(cards_layout)

        # 3. Model Registry Section (Table / Empty State Stack)
        self.registry_stack = QStackedWidget(self)

        # Page 0: Cold start empty state
        self.empty_state = EmptyStateWidget(
            badge_text="[MODEL REGISTRY: COLD START (RULE BASELINE)]",
            title="Zero Local LightGBM Artifacts Registered",
            description=(
                "The desk is currently operating in deterministic cold-start mode (FALLBACK_RULE_ONLY). "
                "The local ML training pipeline, purged walk-forward cross-validator, and train_worker.py "
                "subprocess will be implemented in Phase 5. Once historical datasets are harvested and "
                "trained locally, versioned boosters, Brier calibration curves, and feature contribution plots "
                "will populate here for evaluation and 1-click promotion."
            ),
        )
        self.registry_stack.addWidget(self.empty_state)

        # Page 1: Registered models table
        table_container = QWidget()
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(6)

        table_header = QLabel("Registered Model Artifacts")
        table_header.setStyleSheet("font-weight: 600; font-size: 12px; color: #E2E8F0;")
        tc_layout.addWidget(table_header)

        self.models_table = QTableWidget(0, 6)
        self.models_table.setHorizontalHeaderLabels(
            ["Model Version", "Target Agent", "Algorithm", "Status", "Threshold", "Schema Hash"]
        )
        self.models_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.models_table.setStyleSheet(
            "QTableWidget { background-color: #0F172A; gridline-color: #334155; color: #F8FAFC; }"
            "QHeaderView::section { background-color: #1E293B; color: #94A3B8; font-weight: 600; padding: 4px; }"
        )
        tc_layout.addWidget(self.models_table)

        self.registry_stack.addWidget(table_container)
        layout.addWidget(self.registry_stack, stretch=1)

    def update_agent_metrics(
        self,
        agent_name: str,
        latency_ms: float = 0.0,
        runs: int = 0,
        proposals: int = 0,
        vetos: int = 0,
        model_version: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> None:
        """Update live telemetry metrics displayed on the agent card."""
        card = self._agent_cards.get(agent_name.upper())
        if not card:
            return

        card["latency"].setText(f"Latency: {latency_ms:.1f} ms")
        card["runs"].setText(f"Runs: {runs} | Props: {proposals} | Vetos: {vetos}")

        if model_version:
            card["model"].setText(f"Model: {model_version}")

        if mode:
            card["mode"].setText(f"[{mode}]")

    def refresh_registry(self, registry: ModelRegistry) -> None:
        """Refresh table from registered models or display empty state if none."""
        models = registry.list_models()
        if not models:
            self.registry_stack.setCurrentIndex(0)
            return

        self.registry_stack.setCurrentIndex(1)
        self.models_table.setRowCount(len(models))

        for row, m in enumerate(models):
            self.models_table.setItem(row, 0, QTableWidgetItem(m.model_version))
            self.models_table.setItem(row, 1, QTableWidgetItem(m.agent_id.name))
            self.models_table.setItem(row, 2, QTableWidgetItem(m.algorithm))
            self.models_table.setItem(row, 3, QTableWidgetItem(m.status.name))
            self.models_table.setItem(row, 4, QTableWidgetItem(f"{m.decision_threshold:.3f}"))
            self.models_table.setItem(row, 5, QTableWidgetItem(m.feature_schema_hash[:12] + "..."))
