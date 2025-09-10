import pygame
import socketio
import requests
import html
import random
import time
import os

# ---------------- Socket.IO Setup ----------------
sio = socketio.Client(logger=False, engineio_logger=False)

ROOM_CODE = ""
PLAYER_NAME = input("Enter your player name: ")

player_score = 0
sio.leaderboard_items = []

# Load sounds
pygame.mixer.init()
CORRECT_SOUND = pygame.mixer.Sound(os.path.join("assets", "correct.wav"))
WRONG_SOUND = pygame.mixer.Sound(os.path.join("assets", "wrong.wav"))
TICK_SOUND = pygame.mixer.Sound(os.path.join("assets", "tick.wav"))

@sio.event
def connect():
    print("✅ Connected to server")
    action = input("Type 'create' to create a room or 'join' to join a room: ").lower()
    global ROOM_CODE
    if action == "create":
        sio.emit("create_room", {"name": PLAYER_NAME})
    elif action == "join":
        ROOM_CODE = input("Enter room code to join: ")
        sio.emit("join_room", {"room_code": ROOM_CODE, "name": PLAYER_NAME})

@sio.on("join_success")
def join_success(data):
    global ROOM_CODE
    ROOM_CODE = data["room_code"]
    print(f"🙌 Joined room: {ROOM_CODE}, Theme: {data['theme']}")

@sio.on("room_created")
def room_created(data):
    global ROOM_CODE
    ROOM_CODE = data["room_code"]
    print(f"🎮 Room created with code: {ROOM_CODE}")

@sio.on("server_msg")
def server_msg(data):
    print("📢", data["text"])

@sio.on("leaderboard")
def update_leaderboard(data):
    sio.leaderboard_items = data["items"]

@sio.event
def disconnect():
    print("❌ Disconnected from server")

# Connect to server
sio.connect("http://localhost:5000")

# ---------------- Pygame Setup ----------------
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("QuizMaster Multiplayer")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (100, 149, 237)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)

font = pygame.font.SysFont("Arial", 28)
big_font = pygame.font.SysFont("Arial", 36)
clock = pygame.time.Clock()

# Countdown bar settings
BAR_WIDTH = 600
BAR_HEIGHT = 20
BAR_X = 150
BAR_Y = 140

# ---------------- Theme Selection ----------------
THEMES = ["General Knowledge", "Science", "History", "Sports", "Geography"]
theme_selected = None
selecting_theme = True
question_index = 0
questions = []
TIME_LIMIT = 10  # seconds
timer_start = None

def fetch_questions(category="General Knowledge", amount=5):
    category_mapping = {
        "General Knowledge": 9,
        "Science": 17,
        "History": 23,
        "Sports": 21,
        "Geography": 22
    }
    cat_id = category_mapping.get(category, 9)
    url = f"https://opentdb.com/api.php?amount={amount}&category={cat_id}&type=multiple"
    response = requests.get(url)
    data = response.json()
    results = data.get("results", [])
    formatted = []
    for q in results:
        answers = q["incorrect_answers"] + [q["correct_answer"]]
        random.shuffle(answers)
        formatted.append({
            "question": html.unescape(q["question"]),
            "correct": html.unescape(q["correct_answer"]),
            "options": [html.unescape(a) for a in answers]
        })
    return formatted

# ---------------- Animations ----------------
def fade_out():
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill(WHITE)
    for alpha in range(0, 300, 15):
        fade.set_alpha(alpha)
        screen.blit(fade, (0,0))
        pygame.display.update()
        pygame.time.delay(20)

# ---------------- Main Loop ----------------
running = True
while running:
    screen.fill(WHITE)
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if selecting_theme:
        text = big_font.render(f"Connected as {PLAYER_NAME}", True, BLACK)
        screen.blit(text, (50, 20))
        y_offset = 100
        for theme in THEMES:
            rect = pygame.Rect(300, y_offset, 250, 50)
            color = BLUE if rect.collidepoint(mouse_pos) else GRAY
            pygame.draw.rect(screen, color, rect)
            label = font.render(theme, True, WHITE)
            screen.blit(label, (rect.x + 10, rect.y + 10))
            if rect.collidepoint(mouse_pos) and mouse_clicked:
                theme_selected = theme
                selecting_theme = False
                questions = fetch_questions(theme_selected)
                timer_start = time.time()
                sio.emit("set_theme", {"room_code": ROOM_CODE, "theme": theme_selected})
                time.sleep(0.2)
            y_offset += 80
    else:
        if question_index < len(questions):
            q = questions[question_index]
            screen.blit(font.render(q["question"], True, BLACK), (50, 50))

            # Countdown Bar
            elapsed = time.time() - timer_start
            remaining_ratio = max(0, (TIME_LIMIT - elapsed) / TIME_LIMIT)
            bar_color = GREEN if remaining_ratio > 0.6 else YELLOW if remaining_ratio > 0.3 else RED
            pygame.draw.rect(screen, GRAY, (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT))
            pygame.draw.rect(screen, bar_color, (BAR_X, BAR_Y, int(BAR_WIDTH * remaining_ratio), BAR_HEIGHT))

            if remaining_ratio <= 0:
                fade_out()
                question_index += 1
                timer_start = time.time()

            # Options
            y_offset = 180
            option_rects = []
            for opt in q["options"]:
                rect = pygame.Rect(150, y_offset, 600, 50)
                option_rects.append((rect, opt))
                color = YELLOW if rect.collidepoint(mouse_pos) else GRAY
                pygame.draw.rect(screen, color, rect)
                screen.blit(font.render(opt, True, BLACK), (rect.x + 10, rect.y + 10))
                y_offset += 80

            # Click detection
            if mouse_clicked:
                for rect, opt in option_rects:
                    if rect.collidepoint(mouse_pos):
                        correct = (opt == q["correct"])
                        if correct:
                            player_score += 1
                            CORRECT_SOUND.play()
                        else:
                            WRONG_SOUND.play()

                        # Flash feedback
                        feedback_color = GREEN if correct else RED
                        pygame.draw.rect(screen, feedback_color, rect)
                        screen.blit(font.render(opt, True, WHITE), (rect.x + 10, rect.y + 10))
                        pygame.display.flip()
                        pygame.time.delay(600)

                        sio.emit("update_score", {"room_code": ROOM_CODE, "name": PLAYER_NAME, "score": player_score})
                        fade_out()
                        question_index += 1
                        timer_start = time.time()
                        break
        else:
            # Final Score Animation
            final_score = 0
            while final_score <= player_score:
                screen.fill(WHITE)
                screen.blit(big_font.render("Quiz Finished!", True, BLACK), (WIDTH//2 - 150, HEIGHT//2 - 50))
                screen.blit(font.render(f"Your Score: {final_score}/{len(questions)}", True, GREEN),
                            (WIDTH//2 - 100, HEIGHT//2 + 20))
                pygame.display.flip()
                final_score += 1
                pygame.time.delay(200)

            # Confetti
            confetti = [{"x": random.randint(0, WIDTH), "y": random.randint(-50, 0),
                         "color": random.choice([RED, GREEN, BLUE, YELLOW])} for _ in range(100)]
            for _ in range(60):
                screen.fill(WHITE)
                for c in confetti:
                    pygame.draw.circle(screen, c["color"], (c["x"], c["y"]), 5)
                    c["y"] += 5
                    if c["y"] > HEIGHT:
                        c["y"] = random.randint(-50, 0)
                pygame.display.flip()
                pygame.time.delay(50)

    # Leaderboard
    lb_y = 50
    screen.blit(big_font.render("Leaderboard", True, BLACK), (WIDTH - 250, 50))
    for item in sio.leaderboard_items:
        color = GREEN if item["name"] == PLAYER_NAME else BLACK
        screen.blit(font.render(f"{item['name']}: {item['score']}", True, color), (WIDTH - 250, lb_y + 100))
        lb_y += 40

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sio.disconnect()
