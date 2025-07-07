import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QFileDialog, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QTextCursor, QFont, QColor, QTextCharFormat
from PyQt5.QtCore import Qt
import ollama
from PyQt5.QtGui import QIcon

MODEL = "mistral"

def query_llm(prompt, history):
    conversation = ""
    for turn in history:
        role = turn["role"].capitalize()
        content = turn["content"]
        conversation += f"{role}: {content}\n\n"
    full_prompt = conversation + f"Assistant: {prompt}"
    result = ollama.generate(model=MODEL, prompt=full_prompt)
    return result.response

class AdventureApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Infinite Adventure")
        self.setWindowIcon(QIcon("adventure_icon.png"))
        self.resize(850, 600)

        self.font_family = "Segoe UI"
        self.text_fg = QColor("#E1E1E1")
        self.player_fg = QColor("#4CAF50")
        self.bg_color = "#1e1e1e"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.bg_color};
            }}
        """)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # Title label
        self.title_label = QLabel("Infinite Adventure")
        self.title_label.setFont(QFont(self.font_family, 20, QFont.Bold))
        self.title_label.setStyleSheet("color: #F0F0F0;")
        layout.addWidget(self.title_label)

        # Story display
        self.story_area = QTextEdit()
        self.story_area.setReadOnly(True)
        self.story_area.setFont(QFont(self.font_family, 13))
        self.story_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: #2A2D2E;
                color: {self.text_fg.name()};
                border: 1px solid #3A3A3A;
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        layout.addWidget(self.story_area)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.input_entry = QLineEdit()
        self.input_entry.setFont(QFont(self.font_family, 12))
        self.input_entry.setStyleSheet("""
            QLineEdit {
                background-color: #3A3D3E;
                color: #EEEEEE;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        input_row.addWidget(self.input_entry)

        self.submit_button = QPushButton("Submit")
        self.submit_button.setFont(QFont(self.font_family, 11))
        self.submit_button.setCursor(Qt.PointingHandCursor)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2494E6;
            }
        """)
        self.submit_button.clicked.connect(self.on_submit)
        input_row.addWidget(self.submit_button)

        layout.addLayout(input_row)

        # Control buttons row
        control_row = QHBoxLayout()
        control_row.setSpacing(10)

        self.start_button = QPushButton("Start Game")
        self.start_button.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        self.start_button.clicked.connect(self.start_game)
        control_row.addWidget(self.start_button)

        self.export_button = QPushButton("Export Transcript")
        self.export_button.setFont(QFont(self.font_family, 11))
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        self.export_button.clicked.connect(self.export_transcript)
        control_row.addWidget(self.export_button)

        layout.addLayout(control_row)

        # Game state
        self.history = []
        self.prompt = (
            "You are the narrator of an interactive fiction game. "
            "Invent a unique world, main character, and opening scene. "
            "Describe the setting and present two choices for the player."
        )
        self.running = False

    def start_game(self):
        self.start_button.setEnabled(False)
        self.append_text("Loading model, please wait...\n")
        threading.Thread(target=self.initialize_game).start()

    def initialize_game(self):
        _ = query_llm("Hello.", [])
        self.running = True
        self.append_text("Model loaded! The adventure begins.\n\n")
        self.get_story()

    def append_text(self, text, player=False):
        cursor = self.story_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setFont(QFont(self.font_family, 12))
        fmt.setForeground(self.player_fg if player else self.text_fg)
        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n\n")
        self.story_area.setTextCursor(cursor)
        self.story_area.ensureCursorVisible()

    def get_story(self):
        threading.Thread(target=self.generate_story).start()

    def generate_story(self):
        output = query_llm(self.prompt, self.history)
        self.history.append({"role": "assistant", "content": output})
        if len(self.history) > 6:
            self.history = self.history[-6:]
        self.append_text("Narrator:\n" + output)

    def on_submit(self):
        if not self.running:
            return
        user_input = self.input_entry.text().strip()
        if not user_input:
            return
        if user_input.lower() == "quit":
            self.append_text("\nThanks for playing!")
            self.running = False
            return
        self.append_text(f"Player: {user_input}", player=True)
        self.history.append({"role": "user", "content": user_input})
        if len(self.history) > 6:
            self.history = self.history[-6:]
        self.prompt = (
            f"The player chose: {user_input}. "
            "Continue the story in 3-4 sentences, describe the consequences briefly, and present exactly two short choices."
        )
        self.input_entry.clear()
        self.get_story()

    def export_transcript(self):
        content = self.story_area.toPlainText().strip()
        if not content:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Transcript", "", "Text Files (*.txt)"
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Export Successful", "Transcript saved!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdventureApp()
    window.show()
    sys.exit(app.exec_())
