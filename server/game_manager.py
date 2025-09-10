# server/game_manager.py
import requests
import settings
import random

class GameManager:
    def __init__(self, room_code):
        self.room_code = room_code
        self.players = {}
        self.running = False
        self.theme = "General"
        self.questions = []
        self.current_question = None
        self.answer_index = None
        self.round = 0

    def add_player(self, sid, name):
        self.players[sid] = {"name": name, "score": 0, "answered": False}

    def remove_player(self, sid):
        if sid in self.players:
            del self.players[sid]

    def set_theme(self, theme):
        self.theme = theme

    def get_leaderboard(self):
        return sorted(
            [{"name": p["name"], "score": p["score"]} for p in self.players.values()],
            key=lambda x: x["score"],
            reverse=True,
        )

    def fetch_question(self):
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        response = requests.get(url)
        data = response.json()
        if data["response_code"] == 0:
            q = data["results"][0]
            options = q["incorrect_answers"] + [q["correct_answer"]]
            random.shuffle(options)
            self.answer_index = options.index(q["correct_answer"])
            return {
                "question": q["question"],
                "options": options,
                "correct_index": self.answer_index,
            }
        return None

    def start_round(self):
        self.round += 1
        self.current_question = self.fetch_question()
        for p in self.players.values():
            p["answered"] = False
        return self.current_question
