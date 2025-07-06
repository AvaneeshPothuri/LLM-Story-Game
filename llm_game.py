import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QFileDialog, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QTextCursor, QFont, QColor, QTextCharFormat
from PyQt5.QtCore import Qt
import ollama

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
        self.resize(800, 600)

        self.font_family = "Consolas"
        self.text_fg = QColor("#dddddd")
        self.player_fg = QColor("#6A9955")
        self.bg_color = "#1e1e1e"

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Story display
        self.story_area = QTextEdit()
        self.story_area.setReadOnly(True)
        self.story_area.setFont(QFont(self.font_family, 12))
        self.story_area.setStyleSheet(f"""
            background-color: #252526;
            color: {self.text_fg.name()};
            border: none;
            padding: 10px;
        """)
        layout.addWidget(self.story_area)

        # Input row
        input_row = QHBoxLayout()

        self.input_entry = QLineEdit()
        self.input_entry.setFont(QFont(self.font_family, 12))
        self.input_entry.setStyleSheet("""
            background-color: #2d2d30;
            color: #dddddd;
            border: none;
            padding: 6px;
        """)
        input_row.addWidget(self.input_entry)

        self.submit_button = QPushButton("Submit")
        self.submit_button.setFont(QFont(self.font_family, 12))
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        self.submit_button.clicked.connect(self.on_submit)
        input_row.addWidget(self.submit_button)

        layout.addLayout(input_row)

        # Start button
        self.start_button = QPushButton("Start Game")
        self.start_button.setFont(QFont(self.font_family, 12, QFont.Bold))
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #388a34;
                color: white;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4caf50;
            }
        """)
        self.start_button.clicked.connect(self.start_game)
        layout.addWidget(self.start_button)

        # Export button
        self.export_button = QPushButton("Export Transcript")
        self.export_button.setFont(QFont(self.font_family, 10))
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        self.export_button.clicked.connect(self.export_transcript)
        layout.addWidget(self.export_button)

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
