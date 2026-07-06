import json
import math
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QLocale, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None


APP_NAME = "Focus Breaks"
APP_VERSION = "0.1.2"


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base_path / relative_path


def settings_path():
    appdata = os.environ.get("APPDATA")
    base_dir = Path(appdata) if appdata else Path.home() / ".config"
    config_dir = base_dir / "FocusBreaks"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


SETTINGS_PATH = settings_path()
ICON_PATH = resource_path("assets/app.ico")

DEFAULT_SETTINGS = {
    "focus_minutes": 20,
    "break_minutes": 5,
    "sound": True,
    "auto_start_next_focus": True,
}

TRANSLATIONS = {
    "ru": {
        "window_title": "Помидоро-перерывы",
        "title": "Фокус и зрение",
        "subtitle": "20 минут работы, 5 минут перерыва. Когда пора отдохнуть, приложение затемняет весь экран.",
        "status_focus_running": "Фокус идет",
        "status_focus_ready": "Готов к фокусу",
        "status_break_running": "Перерыв",
        "status_break_paused": "Перерыв на паузе",
        "phase_next_break": "Следующий перерыв: {minutes} минут",
        "phase_break": "Отдохни, посмотри вдаль, не проверяй уведомления",
        "until_break": "до перерыва",
        "until_focus": "до фокуса",
        "start": "Старт",
        "pause": "Пауза",
        "continue": "Продолжить",
        "reset": "Сброс",
        "skip": "Пропустить",
        "settings": "Настройки",
        "language": "Язык",
        "focus_minutes": "Работа, минут",
        "break_minutes": "Перерыв, минут",
        "sound": "Звуковой сигнал",
        "auto_start": "Автоматически начинать следующий фокус",
        "note": (
            "Во время перерыва лучше встать, размять плечи и посмотреть вдаль. "
            "Для 12-часового дня это не роскошь, а техобслуживание человека."
        ),
        "overlay_title_default": "ОТДОХНИ 5 МИНУТ",
        "overlay_title": "ОТДОХНИ {minutes} МИН.",
        "overlay_hint": "Посмотри вдаль, расслабь глаза, встань из-за стола.",
        "overlay_shortcut": "Esc - пауза    Space - завершить перерыв",
        "overlay_finish": "Завершить перерыв",
    },
    "en": {
        "window_title": "Focus Breaks",
        "title": "Focus and Eyes",
        "subtitle": "20 minutes of focus, 5 minutes of rest. When it is time to pause, the app dims the whole screen.",
        "status_focus_running": "Focus running",
        "status_focus_ready": "Ready to focus",
        "status_break_running": "Break time",
        "status_break_paused": "Break paused",
        "phase_next_break": "Next break: {minutes} minutes",
        "phase_break": "Rest your eyes, look into the distance, skip notifications",
        "until_break": "until break",
        "until_focus": "until focus",
        "start": "Start",
        "pause": "Pause",
        "continue": "Continue",
        "reset": "Reset",
        "skip": "Skip",
        "settings": "Settings",
        "language": "Language",
        "focus_minutes": "Focus, minutes",
        "break_minutes": "Break, minutes",
        "sound": "Sound alert",
        "auto_start": "Automatically start next focus session",
        "note": (
            "During a break, stand up, loosen your shoulders, and look into the distance. "
            "For a 12-hour day, this is human maintenance, not a luxury."
        ),
        "overlay_title_default": "REST FOR 5 MINUTES",
        "overlay_title": "REST FOR {minutes} MIN.",
        "overlay_hint": "Look into the distance, relax your eyes, stand up from the desk.",
        "overlay_shortcut": "Esc - pause    Space - end break",
        "overlay_finish": "End break",
    },
}


def system_language():
    return "ru" if QLocale.system().name().lower().startswith("ru") else "en"


def translate(language, key, **kwargs):
    value = TRANSLATIONS.get(language, TRANSLATIONS["en"])[key]
    return value.format(**kwargs) if kwargs else value

COLORS = {
    "bg": "#0f1115",
    "panel": "#171b22",
    "panel2": "#202631",
    "line": "#2d3440",
    "text": "#f4f7fb",
    "muted": "#94a1b2",
    "green": "#4ade80",
    "green_dim": "#102419",
    "orange": "#f6ad55",
    "red": "#fb7185",
    "blue": "#60a5fa",
}


def clamp(value, low, high):
    return max(low, min(high, value))


def format_seconds(seconds):
    seconds = max(0, int(math.ceil(seconds)))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def load_settings():
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}

    settings = DEFAULT_SETTINGS | {key: data.get(key, DEFAULT_SETTINGS[key]) for key in DEFAULT_SETTINGS}
    settings["focus_minutes"] = int(clamp(int(settings["focus_minutes"]), 1, 180))
    settings["break_minutes"] = int(clamp(int(settings["break_minutes"]), 1, 60))
    settings["sound"] = bool(settings["sound"])
    settings["auto_start_next_focus"] = bool(settings["auto_start_next_focus"])
    language = data.get("language", system_language())
    settings["language"] = language if language in TRANSLATIONS else system_language()
    return settings


def save_settings(settings):
    try:
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        pass


def set_font(widget, size, weight=QFont.Normal):
    font = QFont("Segoe UI", size)
    font.setWeight(weight)
    widget.setFont(font)


class CircleTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remaining = 20 * 60
        self.duration = 20 * 60
        self.mode = "focus"
        self.language = "en"
        self.setMinimumSize(QSize(250, 250))
        self.setMaximumHeight(280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_state(self, remaining, duration, mode, language=None):
        self.remaining = remaining
        self.duration = max(1, duration)
        self.mode = mode
        if language:
            self.language = language
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        size = max(180, min(width, height) - 42)
        left = (width - size) / 2
        top = (height - size) / 2
        rect = QRect(int(left), int(top), int(size), int(size))

        painter.setPen(QPen(QColor(COLORS["panel2"]), 18, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(rect)

        progress = clamp(1 - self.remaining / self.duration, 0, 1)
        accent = COLORS["green"] if self.mode == "focus" else COLORS["orange"]
        painter.setPen(QPen(QColor(accent), 18, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * progress))

        painter.setPen(QColor(COLORS["text"]))
        timer_font = QFont("Segoe UI", 44, QFont.DemiBold)
        painter.setFont(timer_font)
        painter.drawText(rect.adjusted(0, -16, 0, 0), Qt.AlignCenter, format_seconds(self.remaining))

        painter.setPen(QColor(COLORS["muted"]))
        sub_font = QFont("Segoe UI", 12)
        painter.setFont(sub_font)
        label = translate(self.language, "until_break" if self.mode == "focus" else "until_focus")
        painter.drawText(rect.adjusted(0, 62, 0, 0), Qt.AlignCenter, label)


class BreakOverlay(QWidget):
    def __init__(self, geometry, finish_callback, pause_callback, language):
        super().__init__(None)
        self.remaining = 5 * 60
        self.duration = 5 * 60
        self.finish_callback = finish_callback
        self.pause_callback = pause_callback
        self.language = language

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowOpacity(0.97)
        self.setGeometry(geometry)
        self.setStyleSheet(
            f"""
            QWidget {{
                background: #050608;
                color: {COLORS["text"]};
            }}
            QPushButton {{
                background: #111821;
                color: {COLORS["text"]};
                border: 1px solid #263241;
                border-radius: 10px;
                padding: 12px 20px;
                font: 600 11pt "Segoe UI";
            }}
            QPushButton:hover {{
                background: #17212d;
                border-color: #334255;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addStretch(1)

        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        set_font(self.title, 34, QFont.DemiBold)
        layout.addWidget(self.title)

        self.hint = QLabel()
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet(f"color: {COLORS['muted']};")
        set_font(self.hint, 15)
        layout.addWidget(self.hint)

        self.circle = CircleTimer()
        self.circle.setMinimumSize(QSize(320, 320))
        self.circle.setMaximumSize(QSize(520, 520))
        layout.addWidget(self.circle, alignment=Qt.AlignCenter)

        self.shortcut = QLabel()
        self.shortcut.setAlignment(Qt.AlignCenter)
        self.shortcut.setStyleSheet("color: #697583;")
        set_font(self.shortcut, 10)
        layout.addWidget(self.shortcut)

        self.finish_button = QPushButton()
        self.finish_button.clicked.connect(self.finish_callback)
        layout.addWidget(self.finish_button, alignment=Qt.AlignCenter)

        layout.addStretch(1)
        self.apply_language()

    def apply_language(self):
        self.hint.setText(translate(self.language, "overlay_hint"))
        self.shortcut.setText(translate(self.language, "overlay_shortcut"))
        self.finish_button.setText(translate(self.language, "overlay_finish"))

    def update_timer(self, remaining, duration, break_minutes, language):
        self.remaining = remaining
        self.duration = max(1, duration)
        if language != self.language:
            self.language = language
            self.apply_language()
        if break_minutes == 5:
            self.title.setText(translate(self.language, "overlay_title_default"))
        else:
            self.title.setText(translate(self.language, "overlay_title", minutes=break_minutes))
        self.circle.set_state(remaining, duration, "break", self.language)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.pause_callback()
            event.accept()
        elif event.key() == Qt.Key_Space:
            self.finish_callback()
            event.accept()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.state = "focus"
        self.running = False
        self.deadline = None
        self.remaining = self.settings["focus_minutes"] * 60
        self.overlays = []
        self.language = self.settings["language"]

        self.setMinimumSize(640, 880)
        self.resize(700, 900)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.tick)

        self.build_ui()
        self.apply_language()
        self.refresh()
        self.timer.start()

    @property
    def focus_seconds(self):
        return self.focus_spin.value() * 60

    @property
    def break_seconds(self):
        return self.break_spin.value() * 60

    def build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        self.setStyleSheet(self.stylesheet())

        shell = QVBoxLayout(root)
        shell.setContentsMargins(30, 26, 30, 26)
        shell.setSpacing(16)

        self.title_label = QLabel()
        set_font(self.title_label, 26, QFont.DemiBold)
        shell.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setObjectName("muted")
        set_font(self.subtitle_label, 10)
        shell.addWidget(self.subtitle_label)

        timer_card = self.card()
        timer_card.setMinimumHeight(386)
        timer_layout = QVBoxLayout(timer_card)
        timer_layout.setContentsMargins(24, 20, 24, 22)
        timer_layout.setSpacing(10)
        shell.addWidget(timer_card)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("mutedStrong")
        set_font(self.status_label, 12, QFont.DemiBold)
        timer_layout.addWidget(self.status_label)

        self.circle = CircleTimer()
        timer_layout.addWidget(self.circle, 1)

        self.phase_label = QLabel()
        self.phase_label.setAlignment(Qt.AlignCenter)
        self.phase_label.setWordWrap(True)
        self.phase_label.setMinimumHeight(24)
        set_font(self.phase_label, 14, QFont.DemiBold)
        timer_layout.addWidget(self.phase_label)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.setAlignment(Qt.AlignCenter)
        timer_layout.addLayout(controls)

        self.start_button = QPushButton()
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.toggle_running)
        controls.addWidget(self.start_button)

        self.reset_button = QPushButton()
        self.reset_button.clicked.connect(self.reset_timer)
        controls.addWidget(self.reset_button)

        self.skip_button = QPushButton()
        self.skip_button.clicked.connect(self.skip_phase)
        controls.addWidget(self.skip_button)

        settings_card = self.card()
        settings_card.setMinimumHeight(196)
        settings_layout = QGridLayout(settings_card)
        settings_layout.setContentsMargins(20, 18, 20, 18)
        settings_layout.setHorizontalSpacing(18)
        settings_layout.setVerticalSpacing(10)
        settings_layout.setColumnStretch(0, 1)
        settings_layout.setColumnMinimumWidth(1, 190)
        shell.addWidget(settings_card)

        self.settings_title = QLabel()
        set_font(self.settings_title, 13, QFont.DemiBold)
        settings_layout.addWidget(self.settings_title, 0, 0, 1, 2)

        self.focus_spin = self.spinbox(self.settings["focus_minutes"], 1, 180)
        self.break_spin = self.spinbox(self.settings["break_minutes"], 1, 60)
        self.language_combo = QComboBox()
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.addItem("English", "en")
        self.language_combo.setFixedWidth(190)
        self.language_combo.setCurrentIndex(0 if self.language == "ru" else 1)
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)

        self.setting_labels = {}
        self.add_setting_row(settings_layout, 1, "language", self.language_combo)
        self.add_setting_row(settings_layout, 2, "focus_minutes", self.focus_spin)
        self.add_setting_row(settings_layout, 3, "break_minutes", self.break_spin)

        self.sound_check = QCheckBox()
        self.sound_check.setChecked(self.settings["sound"])
        self.sound_check.stateChanged.connect(self.persist_settings)
        settings_layout.addWidget(self.sound_check, 4, 0, 1, 2)

        self.auto_check = QCheckBox()
        self.auto_check.setChecked(self.settings["auto_start_next_focus"])
        self.auto_check.stateChanged.connect(self.persist_settings)
        settings_layout.addWidget(self.auto_check, 5, 0, 1, 2)

        note = QFrame()
        note.setObjectName("note")
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(16, 14, 16, 14)
        self.note_text = QLabel()
        self.note_text.setWordWrap(True)
        self.note_text.setObjectName("noteText")
        set_font(self.note_text, 10)
        note_layout.addWidget(self.note_text)
        shell.addWidget(note)

    def stylesheet(self):
        return f"""
        #root {{
            background: {COLORS["bg"]};
            color: {COLORS["text"]};
        }}
        QLabel {{
            color: {COLORS["text"]};
        }}
        #muted, #mutedStrong {{
            color: {COLORS["muted"]};
        }}
        #card {{
            background: {COLORS["panel"]};
            border: 1px solid {COLORS["line"]};
            border-radius: 18px;
        }}
        #note {{
            background: {COLORS["green_dim"]};
            border: 1px solid #22543a;
            border-radius: 16px;
        }}
        #noteText {{
            color: #d7ffe5;
        }}
        QPushButton {{
            background: {COLORS["panel2"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["line"]};
            border-radius: 12px;
            padding: 12px 18px;
            font: 600 10pt "Segoe UI";
            min-width: 96px;
        }}
        QPushButton:hover {{
            background: #293241;
            border-color: #3b4656;
        }}
        QPushButton:pressed {{
            background: #11161d;
        }}
        QPushButton#primary {{
            background: {COLORS["green"]};
            color: #07120c;
            border: 0;
        }}
        QPushButton#primary:hover {{
            background: #6ee795;
        }}
        QSpinBox {{
            background: {COLORS["panel2"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["line"]};
            border-radius: 10px;
            padding: 8px 12px;
            min-width: 166px;
            font: 10pt "Segoe UI";
        }}
        QComboBox {{
            background: {COLORS["panel2"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["line"]};
            border-radius: 10px;
            padding: 8px 12px;
            min-width: 166px;
            font: 10pt "Segoe UI";
        }}
        QComboBox::drop-down {{
            border: 0;
            width: 30px;
        }}
        QComboBox QAbstractItemView {{
            background: {COLORS["panel2"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["line"]};
            selection-background-color: #293241;
        }}
        QCheckBox {{
            color: {COLORS["text"]};
            font: 10pt "Segoe UI";
            spacing: 10px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid {COLORS["line"]};
            background: {COLORS["panel2"]};
        }}
        QCheckBox::indicator:checked {{
            background: {COLORS["green"]};
            border-color: {COLORS["green"]};
        }}
        """

    def card(self):
        frame = QFrame()
        frame.setObjectName("card")
        return frame

    def spinbox(self, value, low, high):
        spin = QSpinBox()
        spin.setRange(low, high)
        spin.setValue(value)
        spin.setButtonSymbols(QSpinBox.NoButtons)
        spin.setFixedWidth(190)
        spin.valueChanged.connect(self.on_duration_changed)
        return spin

    def add_setting_row(self, layout, row, key, widget):
        text = QLabel()
        text.setObjectName("muted")
        set_font(text, 10)
        self.setting_labels[key] = text
        layout.addWidget(text, row, 0)
        layout.addWidget(widget, row, 1, alignment=Qt.AlignRight)

    def t(self, key, **kwargs):
        return translate(self.language, key, **kwargs)

    def apply_language(self):
        self.setWindowTitle(self.t("window_title"))
        self.title_label.setText(self.t("title"))
        self.subtitle_label.setText(self.t("subtitle"))
        self.settings_title.setText(self.t("settings"))
        self.setting_labels["language"].setText(self.t("language"))
        self.setting_labels["focus_minutes"].setText(self.t("focus_minutes"))
        self.setting_labels["break_minutes"].setText(self.t("break_minutes"))
        self.sound_check.setText(self.t("sound"))
        self.auto_check.setText(self.t("auto_start"))
        self.note_text.setText(self.t("note"))
        self.reset_button.setText(self.t("reset"))
        self.skip_button.setText(self.t("skip"))
        self.refresh()

    def on_language_changed(self, _index=None):
        language = self.language_combo.currentData()
        if language not in TRANSLATIONS or language == self.language:
            return
        self.language = language
        self.persist_settings()
        self.apply_language()

    def current_duration(self):
        return self.focus_seconds if self.state == "focus" else self.break_seconds

    def toggle_running(self):
        if self.running:
            self.pause_timer()
        else:
            self.start_timer()

    def start_timer(self):
        self.remaining = max(0.1, self.remaining)
        self.deadline = time.monotonic() + self.remaining
        self.running = True
        self.refresh()

    def pause_timer(self):
        if self.deadline is not None:
            self.remaining = max(0, self.deadline - time.monotonic())
        self.deadline = None
        self.running = False
        self.refresh()

    def reset_timer(self):
        self.running = False
        self.deadline = None
        self.state = "focus"
        self.remaining = self.focus_seconds
        self.hide_overlays()
        self.refresh()

    def skip_phase(self):
        if self.state == "focus":
            self.begin_break()
        else:
            self.begin_focus(auto=self.auto_check.isChecked())

    def begin_break(self):
        self.state = "break"
        self.remaining = self.break_seconds
        self.deadline = time.monotonic() + self.remaining
        self.running = True
        self.signal()
        self.show_overlays()
        self.refresh()

    def begin_focus(self, auto=True):
        self.hide_overlays()
        self.state = "focus"
        self.remaining = self.focus_seconds
        self.running = auto
        self.deadline = time.monotonic() + self.remaining if auto else None
        self.signal()
        self.refresh()

    def tick(self):
        if self.running and self.deadline is not None:
            self.remaining = max(0, self.deadline - time.monotonic())
            if self.remaining <= 0:
                if self.state == "focus":
                    self.begin_break()
                else:
                    self.begin_focus(auto=self.auto_check.isChecked())
        self.refresh()

    def refresh(self):
        duration = self.current_duration()
        self.circle.set_state(self.remaining, duration, self.state, self.language)

        if self.state == "focus":
            self.status_label.setText(self.t("status_focus_running" if self.running else "status_focus_ready"))
            self.phase_label.setText(self.t("phase_next_break", minutes=self.break_spin.value()))
        else:
            self.status_label.setText(self.t("status_break_running" if self.running else "status_break_paused"))
            self.phase_label.setText(self.t("phase_break"))

        if self.running:
            self.start_button.setText(self.t("pause"))
        else:
            self.start_button.setText(self.t("continue") if self.remaining < duration else self.t("start"))

        for overlay in self.overlays:
            overlay.update_timer(self.remaining, self.break_seconds, self.break_spin.value(), self.language)

    def show_overlays(self):
        self.hide_overlays()
        app = QApplication.instance()
        for screen in app.screens():
            overlay = BreakOverlay(screen.geometry(), self.end_break_from_overlay, self.pause_timer, self.language)
            overlay.showFullScreen()
            overlay.raise_()
            overlay.activateWindow()
            overlay.setFocus()
            self.overlays.append(overlay)

    def hide_overlays(self):
        for overlay in self.overlays:
            overlay.close()
        self.overlays = []

    def end_break_from_overlay(self):
        self.begin_focus(auto=self.auto_check.isChecked())

    def on_duration_changed(self):
        self.persist_settings()
        if not self.running:
            self.remaining = self.current_duration()
            self.refresh()

    def persist_settings(self):
        save_settings(
            {
                "focus_minutes": self.focus_spin.value(),
                "break_minutes": self.break_spin.value(),
                "sound": self.sound_check.isChecked(),
                "auto_start_next_focus": self.auto_check.isChecked(),
                "language": self.language,
            }
        )

    def signal(self):
        if not self.sound_check.isChecked():
            return
        if winsound:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            QApplication.beep()

    def closeEvent(self, event):
        self.persist_settings()
        self.hide_overlays()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
