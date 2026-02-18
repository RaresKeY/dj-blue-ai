from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui_ux_team.blue_ui import settings as app_settings
from ui_ux_team.blue_ui.app.api_usage_guard import current_usage_state
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.widgets.settings_section import SettingsSection


def _parse_color(value: str, fallback: str) -> QColor:
    color = QColor((value or "").strip())
    if color.isValid():
        return color
    fallback_color = QColor(fallback)
    return fallback_color if fallback_color.isValid() else QColor("#FFFFFF")


def _color_with_alpha(value: str, alpha: float, fallback: str) -> str:
    c = _parse_color(value, fallback)
    a = max(0.0, min(1.0, float(alpha)))
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a:.3f})"


def _is_light_color(value: str, fallback: str = "#1E1E1E") -> bool:
    return _parse_color(value, fallback).lightnessF() >= 0.55


class APIUsageLimitsForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("apiUsageLimitsForm")

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(8)

        title = QLabel("API Usage Limits")
        title.setObjectName("apiUsageLimitsTitle")
        subtitle = QLabel(
            "Set conservative caps for local runtime usage. "
            "These values are persisted in app settings and can be tuned per environment."
        )
        subtitle.setObjectName("apiUsageLimitsSubtitle")
        subtitle.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(subtitle)

        self._request_section = SettingsSection(
            "Request Throughput",
            "Protect against runaway request loops and overly aggressive polling.",
        )
        request_form = QFormLayout()
        request_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        request_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        request_form.setHorizontalSpacing(14)
        request_form.setVerticalSpacing(6)
        self._request_section.content_layout().addLayout(request_form)

        self._rpm = QSpinBox()
        self._rpm.setRange(
            app_settings.API_USAGE_MIN_REQUESTS_PER_MINUTE,
            app_settings.API_USAGE_MAX_REQUESTS_PER_MINUTE,
        )
        self._rpm.setFixedHeight(34)
        self._rpm.setKeyboardTracking(False)
        self._rpm.setSuffix(" req/min")
        request_form.addRow("Requests per minute", self._rpm)

        self._rpd = QSpinBox()
        self._rpd.setRange(
            app_settings.API_USAGE_MIN_REQUESTS_PER_DAY,
            app_settings.API_USAGE_MAX_REQUESTS_PER_DAY,
        )
        self._rpd.setFixedHeight(34)
        self._rpd.setKeyboardTracking(False)
        self._rpd.setSuffix(" req/day")
        request_form.addRow("Requests per day", self._rpd)

        self._budget_section = SettingsSection(
            "Budget Guardrail",
            "Set a soft monthly cap to catch accidental overuse early.",
        )
        budget_form = QFormLayout()
        budget_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        budget_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        budget_form.setHorizontalSpacing(14)
        budget_form.setVerticalSpacing(6)
        self._budget_section.content_layout().addLayout(budget_form)

        self._monthly_budget = QDoubleSpinBox()
        self._monthly_budget.setRange(
            app_settings.API_USAGE_MIN_MONTHLY_BUDGET_USD,
            app_settings.API_USAGE_MAX_MONTHLY_BUDGET_USD,
        )
        self._monthly_budget.setDecimals(2)
        self._monthly_budget.setSingleStep(1.0)
        self._monthly_budget.setFixedHeight(34)
        self._monthly_budget.setKeyboardTracking(False)
        self._monthly_budget.setPrefix("$")
        self._monthly_budget.setSuffix(" /month")
        budget_form.addRow("Monthly budget", self._monthly_budget)

        self._usage_section = SettingsSection(
            "Current Usage",
            "Monitor real-time consumption against configured limits.",
        )
        usage_form = QFormLayout()
        usage_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        usage_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        usage_form.setHorizontalSpacing(14)
        usage_form.setVerticalSpacing(6)
        self._usage_section.content_layout().addLayout(usage_form)

        self._current_rpm = QLabel("0 / --")
        self._current_rpd = QLabel("0 / --")
        self._current_spend = QLabel("$0.00 / --")
        usage_form.addRow("RPM (Current Minute)", self._current_rpm)
        usage_form.addRow("RPD (Current Day)", self._current_rpd)
        usage_form.addRow("Monthly Spend", self._current_spend)

        self._free_tier_note = QLabel(
            "* Note: This is an estimated cost. If your API key is on a free tier (e.g. Gemini Flash free limits), "
            "you will not actually be charged by the provider for that usage."
        )
        self._free_tier_note.setObjectName("apiUsageFreeTierNote")
        self._free_tier_note.setWordWrap(True)
        self._usage_section.content_layout().addWidget(self._free_tier_note)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(6)
        self._reset_btn = QPushButton("Reset to Defaults")
        self._reset_btn.clicked.connect(self._reset_defaults)
        actions.addWidget(self._reset_btn, 0, Qt.AlignLeft)
        actions.addStretch(1)

        self._status = QLabel("")
        self._status.setObjectName("apiUsageLimitsStatus")
        self._status.setWordWrap(True)
        self._status.setText("Saved usage caps are active for this app profile.")

        root.addWidget(self._request_section)
        root.addWidget(self._budget_section)
        root.addWidget(self._usage_section)
        root.addLayout(actions)
        root.addWidget(self._status)

        self._rpm.valueChanged.connect(self._persist_limits)
        self._rpd.valueChanged.connect(self._persist_limits)
        self._monthly_budget.valueChanged.connect(self._persist_limits)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(5000)
        self._refresh_timer.timeout.connect(self._update_usage_display)
        self._refresh_timer.start()

        self._load_from_settings()
        self.refresh_theme()

    def _update_usage_display(self) -> None:
        state = current_usage_state()
        limits = app_settings.api_usage_limits()
        
        self._current_rpm.setText(f"{state['minute_count']} / {limits['requests_per_minute']}")
        self._current_rpd.setText(f"{state['day_count']} / {limits['requests_per_day']}")
        self._current_spend.setText(f"${state['month_spend_usd']:.4f} / ${float(limits['monthly_budget_usd']):.2f}")

    def _load_from_settings(self) -> None:
        limits = app_settings.api_usage_limits()
        self._rpm.blockSignals(True)
        self._rpd.blockSignals(True)
        self._monthly_budget.blockSignals(True)
        self._rpm.setValue(int(limits["requests_per_minute"]))
        self._rpd.setValue(int(limits["requests_per_day"]))
        self._monthly_budget.setValue(float(limits["monthly_budget_usd"]))
        self._rpm.blockSignals(False)
        self._rpd.blockSignals(False)
        self._monthly_budget.blockSignals(False)
        self._update_usage_display()

    def _persist_limits(self) -> None:
        saved = app_settings.set_api_usage_limits(
            requests_per_minute=self._rpm.value(),
            requests_per_day=self._rpd.value(),
            monthly_budget_usd=self._monthly_budget.value(),
        )
        self._status.setText(
            "Saved: "
            f"{int(saved['requests_per_minute'])} req/min, "
            f"{int(saved['requests_per_day'])} req/day, "
            f"${float(saved['monthly_budget_usd']):.2f}/month."
        )
        self._update_usage_display()

    def _reset_defaults(self) -> None:
        defaults = app_settings.api_usage_defaults()
        self._rpm.setValue(int(defaults["requests_per_minute"]))
        self._rpd.setValue(int(defaults["requests_per_day"]))
        self._monthly_budget.setValue(float(defaults["monthly_budget_usd"]))
        self._persist_limits()

    def refresh_theme(self) -> None:
        bg_main = getattr(tokens, "COLOR_BG_MAIN", "#1E1E1E")
        accent = getattr(tokens, "ACCENT", "#FF9B54")
        text_primary = getattr(tokens, "TEXT_PRIMARY", "#D4D4D4")
        is_light_theme = _is_light_color(bg_main, "#1E1E1E")
        button_bg_idle = _color_with_alpha(accent, 0.11 if is_light_theme else 0.14, accent)
        button_bg_hover = _color_with_alpha(accent, 0.19 if is_light_theme else 0.24, accent)
        button_border = _color_with_alpha(accent, 0.66 if is_light_theme else 0.62, accent)
        status_color = _color_with_alpha(accent, 0.90 if is_light_theme else 0.94, accent)
        self.setStyleSheet(
            f"""
            QWidget#apiUsageLimitsForm {{
                background: transparent;
            }}
            QLabel#apiUsageLimitsTitle {{
                font-size: 18px;
                font-weight: 700;
                color: {tokens.TEXT_PRIMARY};
            }}
            QLabel#apiUsageLimitsSubtitle {{
                font-size: 12px;
                color: {tokens.TEXT_MUTED};
            }}
            QLabel {{
                color: {tokens.TEXT_PRIMARY};
            }}
            QSpinBox, QDoubleSpinBox {{
                background: {tokens.BG_INPUT};
                color: {text_primary};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 0px 10px;
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                width: 18px;
                border: none;
                background: transparent;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {accent};
            }}
            QPushButton {{
                background: {button_bg_idle};
                color: {accent};
                border: 1px solid {button_border};
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {button_bg_hover};
            }}
            QLabel#apiUsageLimitsStatus {{
                font-size: 12px;
                color: {status_color};
                padding-top: 2px;
            }}
            QLabel#apiUsageFreeTierNote {{
                font-size: 11px;
                color: {tokens.TEXT_MUTED};
                font-style: italic;
                padding-top: 4px;
            }}
            """
        )
        self._request_section.refresh_theme()
        self._budget_section.refresh_theme()
        self._usage_section.refresh_theme()
