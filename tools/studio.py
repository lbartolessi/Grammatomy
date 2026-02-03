import logging
import random
import signal
import sys
from pathlib import Path

import yaml
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Import Grammatomy Core
from grammatomy import from_ptb, get_syntax_tree
from grammatomy.logger import setup_logging
from grammatomy.ui.syntax_editor import SyntaxEditor
from grammatomy.validation import validate_ghosts, validate_structure


class QLogHandler(logging.Handler, QObject):
    """Custom logging handler sending logs to a PyQt signal."""

    log_signal = pyqtSignal(str, str)  # level, message

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(record.levelname, msg)


class LogViewer(QPlainTextEdit):
    """Widget to display logs with colors."""

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")


class GrammatomyStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grammatomy Studio - Syntax Editor")
        self.resize(1200, 800)

        # Initialize Logger (No file logging for Studio to save disk)
        self.logger = setup_logging(
            name="grammatomy_studio", log_file=None, console_level=logging.INFO
        )
        self.setup_gui_logging()

        # Main Container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Content Layout (Horizontal: Tabs | Sidebar)
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)

        # --- Tabs ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        content_layout.addWidget(self.tabs, stretch=3)

        # Tab 1: Visual Editor
        self.editor = SyntaxEditor()
        self.tabs.addTab(self.editor, "Editor Visual 🌳")

        # Tab 2: Raw PTB (Optional/Debug)
        self.ptb_view = QTextEdit()
        self.ptb_view.setReadOnly(True)
        self.ptb_view.setFont(QFont("Consolas", 10))
        self.tabs.addTab(self.ptb_view, "Estructura PTB 📄")

        # Tab 3: Telemetry & Logs
        self.log_view = LogViewer()
        self.tabs.addTab(self.log_view, "Telemetría & Logs 📟")

        # --- Sidebar (Right) ---
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(350)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(15)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(sidebar)

        # 1. Title
        title_lbl = QLabel("Grammatomy\nStudio")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_lbl)

        # 2. Language Selector
        lang_layout = QVBoxLayout()
        lang_lbl = QLabel("Idioma / Language:")
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["es", "en", "fr", "it", "pt", "de"])
        lang_layout.addWidget(lang_lbl)
        lang_layout.addWidget(self.combo_lang)
        sidebar_layout.addLayout(lang_layout)

        # Input Box
        input_lbl = QLabel("Entrada / Input:")
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Escribe una frase o pega un árbol PTB...")
        self.input_text.setMaximumHeight(150)

        sidebar_layout.addWidget(input_lbl)
        sidebar_layout.addWidget(self.input_text)

        # Buttons
        btn_render = QPushButton("Analizar / Render 🌳")
        btn_render.setFixedHeight(40)
        btn_render.setStyleSheet(
            "background-color: #007ACC; color: white; font-weight: bold;"
        )
        btn_render.clicked.connect(self.render_from_input)

        btn_clear = QPushButton("Limpiar / Clear 🗑️")
        btn_clear.clicked.connect(self.clear_tree)

        btn_random = QPushButton("Frase Aleatoria / Random 🎲")
        btn_random.clicked.connect(self.set_random_sentence)

        btn_save = QPushButton("Save Image 📷")
        btn_save.clicked.connect(self.save_image)

        btn_copy_logs = QPushButton("Copiar Logs / Copy 📋")
        btn_copy_logs.clicked.connect(self.copy_logs_to_clipboard)

        sidebar_layout.addWidget(btn_render)
        sidebar_layout.addWidget(btn_clear)
        sidebar_layout.addWidget(btn_copy_logs)
        sidebar_layout.addWidget(btn_random)
        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(btn_save)
        sidebar_layout.addStretch()

        # Load Examples
        self.examples = {}
        self.load_examples()

        # --- Signals & Shortcuts ---
        self.editor.treeChanged.connect(self.on_tree_changed)

        self.undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        self.undo_shortcut.activated.connect(self.editor.undo)

        self.redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        self.redo_shortcut.activated.connect(self.editor.redo)

    def setup_gui_logging(self):
        """Connects the python logger to the GUI widget."""
        handler = QLogHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(message)s", "%H:%M:%S")
        )
        handler.log_signal.connect(self.append_log)
        self.logger.addHandler(handler)  # Attach to specific logger (propagate=False)

    def append_log(self, level, message):
        colors = {
            "DEBUG": "#808080",
            "INFO": "#56B4E9",
            "WARNING": "#E69F00",
            "ERROR": "#D55E00",
            "CRITICAL": "#CC79A7",
        }
        color = colors.get(level, "#FFFFFF")
        self.log_view.appendHtml(f'<span style="color:{color}">{message}</span>')

    def load_examples(self):
        """Loads example sentences from YAML asset."""
        try:
            path = (
                Path(__file__).parents[1]
                / "src"
                / "grammatomy"
                / "assets"
                / "examples.yaml"
            )
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self.examples = yaml.safe_load(f)
            else:
                self.logger.warning("Examples file not found at %s", path)
        except (OSError, yaml.YAMLError) as e:
            self.logger.error("Error loading examples: %s", e)

    def set_random_sentence(self):
        """Picks a random sentence for the selected language."""
        lang = self.combo_lang.currentText()
        if lang in self.examples and self.examples[lang]:
            sentence = random.choice(self.examples[lang])
            self.input_text.setText(sentence)
        else:
            QMessageBox.information(
                self, "Info", f"No hay ejemplos disponibles para '{lang}'."
            )

    def render_from_input(self):
        """Parses input text and loads it into the editor."""
        text = self.input_text.toPlainText().strip()
        if not text:
            return

        lang = self.combo_lang.currentText()
        try:
            if text.startswith("("):
                self.logger.info("Parsing from raw PTB input...")
                root = from_ptb(text)
            else:
                self.logger.info("Requesting syntax tree for lang='%s'...", lang)
                root = get_syntax_tree(text, params={"lang": lang})

            if root:
                self.editor.load_tree(root)
                self.logger.info("Tree rendered successfully.")

                # Auto-validate (Flexible Mode)
                self.validate_current_tree(silent_success=True, root=root)

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("Parsing failed: %s", e, exc_info=True)
            QMessageBox.critical(
                self, "Error de Parsing", f"Ocurrió un error:\n{str(e)}"
            )

    def on_tree_changed(self, ptb_string):
        """Syncs the editor state back to the input box and PTB view."""
        self.input_text.setText(ptb_string)
        self.ptb_view.setText(ptb_string)

    def clear_tree(self):
        self.editor.clear()
        self.input_text.clear()
        self.ptb_view.clear()

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "tree.png", "Images (*.png *.jpg)"
        )
        if file_path:
            self.editor.save_image(file_path)

    def copy_logs_to_clipboard(self):
        """Copies the content of the log viewer to the system clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.log_view.toPlainText())
            self.logger.info(
                "Logs copied to clipboard / Logs copiados al portapapeles."
            )

    def validate_current_tree(self, silent_success=False, root=None):
        """Runs validation logic on the current tree."""
        # We get the tree back from the editor (or the PTB string)
        # For now, we re-parse the PTB string from the text view as the source of truth

        if root is None:
            ptb_content = self.ptb_view.toPlainText().strip()
            if not ptb_content:
                if not silent_success:
                    self.logger.warning("No tree to validate.")
                return

            try:
                root = from_ptb(ptb_content)
            except Exception as e:
                self.logger.error("Validation parsing error: %s", e)
                return

        try:
            # 1. Strict Check: Ghosts
            ghosts = validate_ghosts(root)
            if ghosts:
                for g in ghosts:
                    self.logger.critical(g)
                QMessageBox.warning(
                    self,
                    "Validation Failed",
                    "Se detectaron Nodos Fantasma (Ghost Nodes).\nEl árbol está incompleto.",
                )
                return

            # 2. Flexible Check: Structure
            warnings = validate_structure(root)
            for w in warnings.values():
                self.logger.warning(w)

            if not ghosts and not warnings and not silent_success:
                self.logger.info("Validation Passed: Tree is structurally sound.")
                QMessageBox.information(
                    self,
                    "Validación",
                    "El árbol es válido y cumple las reglas metasintácticas.",
                )

        except Exception as e:
            self.logger.error("Validation error: %s", e)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = GrammatomyStudio()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
