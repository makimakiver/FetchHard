# laptop_agent_human_chat_delay.py
from uagents import Agent, Context, Model
import asyncio
import threading
import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
import time

# -------------------------------
# Models
# -------------------------------
class Command(Model):
    direction: str
    reason: str
    obstacle_type: str

class Status(Model):
    old_pos: tuple
    new_pos: tuple
    obstacle_type: str
    bot_name: str   # NEW → identify spiderbot or wheelbot

# -------------------------------
# Configuration
# -------------------------------
SPIDERBOT_ADDRESS = "agent1qdakxxf9saqnmft032m4zfs8mj2cdnmehljv6jkw7yy6t92hq6cjj4mh2tn"
WHEELBOT_ADDRESS  = "agent1qg8urv8w302p9awuaf9xu7x50tjp2kaj089jpluwhed4dn8kty6pvy7lhme"

LAPTOP_IP = "10.64.173.208"
SEND_INTERVAL = 0.5
HUMAN_DELAY = 1.5

agent = Agent(
    name="laptop_agent",
    seed="laptop_agent_seed",
    port=8000,
    endpoint=[f"http://{LAPTOP_IP}:8000/submit"]
)

# -------------------------------
# Tkinter GUI Setup
# -------------------------------
root = tk.Tk()
root.title("Spiderbot + Wheelbot Simulation & Chat")
root.geometry("1100x500")

# CANVAS
canvas = tk.Canvas(root, width=400, height=400, bg="white")
canvas.grid(row=0, column=0, padx=10, pady=10)

GRID_SIZE = 10
BOT_SIZE = 40
spider_pos = [2,5]   # BLUE bot
wheel_pos  = [7,5]   # RED bot

def draw_bots():
    canvas.delete("all")
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x0, y0 = i*BOT_SIZE, j*BOT_SIZE
            x1, y1 = x0+BOT_SIZE, y0+BOT_SIZE
            canvas.create_rectangle(x0, y0, x1, y1, outline="gray")

    # Spiderbot = BLUE
    sx0, sy0 = spider_pos[0]*BOT_SIZE, spider_pos[1]*BOT_SIZE
    canvas.create_oval(sx0, sy0, sx0+BOT_SIZE, sy0+BOT_SIZE, fill="blue")

    # Wheelbot = RED
    wx0, wy0 = wheel_pos[0]*BOT_SIZE, wheel_pos[1]*BOT_SIZE
    canvas.create_oval(wx0, wy0, wx0+BOT_SIZE, wy0+BOT_SIZE, fill="red")

# -------------------------------
# CHAT SYSTEM
# -------------------------------
chat_frame = tk.Frame(root, bg="#efe7dd")
chat_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
chat_frame.grid_rowconfigure(0, weight=1)
chat_frame.grid_columnconfigure(0, weight=1)

chat_canvas = tk.Canvas(chat_frame, bg="#efe7dd", highlightthickness=0)
scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=chat_canvas.yview)
scrollable_frame = tk.Frame(chat_canvas, bg="#efe7dd")
scrollable_frame.bind("<Configure>", lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all")))
chat_canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
chat_canvas.configure(yscrollcommand=scrollbar.set)
chat_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


def add_message(text, sender, bot_type=None):
    """sender = sent | received  
       bot_type = None | 'spider' | 'wheel'"""

    time_str = time.strftime("%H:%M:%S")
    bubble_frame = tk.Frame(scrollable_frame, bg="#efe7dd")
    bubble_frame.pack(pady=4, anchor="e" if sender=="sent" else "w", padx=10)

    # COLORS
    if sender == "sent":
        bg = "#dcf8c6"
        fg = "black"
    else:
        if bot_type == "spider":
            bg = "#cce5ff"  # LIGHT BLUE
            fg = "black"
        elif bot_type == "wheel":
            bg = "#ffcccc"  # LIGHT RED
            fg = "black"
        else:
            bg = "white"
            fg = "black"

    bubble = tk.Label(
        bubble_frame, text=f"{text}  ", bg=bg, fg=fg,
        justify="left", wraplength=250, font=("Arial", 11),
        relief="flat", padx=12, pady=8
    )
    bubble.pack(side="right" if sender=="sent" else "left")

    tk.Label(
        bubble, text=time_str,
        fg="#555555", bg=bg, font=("Arial", 8)
    ).place(relx=1.0, rely=1.0, anchor="se")

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

# -------------------------------
# Obstacle Detection (unchanged)
# -------------------------------
COLOR_THRESHOLDS = {
    "RED": [([0,120,70],[10,255,255]), ([170,120,70],[180,255,255])],
    "GREEN": [([35,50,50],[85,255,255])],
    "BLUE": [([100,150,0],[140,255,255])]
}

def analyze_frame(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    largest_area = 0
    detected_color = None
    largest_contour = None

    for color, ranges in COLOR_THRESHOLDS.items():
        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for r in ranges:
            lower = np.array(r[0])
            upper = np.array(r[1])
            mask = cv2.inRange(hsv, lower, upper)
            mask_total = cv2.bitwise_or(mask_total, mask)
        contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area > largest_area and area > 500:
                largest_area = area
                detected_color = color
                largest_contour = c

    if largest_area == 0:
        return "FRONT", "no obstacle", "NONE"

    x, y, w, h = cv2.boundingRect(largest_contour)
    cx = x + w//2
    center = frame.shape[1]//2

    if cx < center/2:
        return "RIGHT", f"{detected_color} left", detected_color
    elif cx > center*1.5:
        return "LEFT", f"{detected_color} right", detected_color
    else:
        return "BACK", f"{detected_color} center", detected_color

# -------------------------------
# CAMERA LOOP → Send commands to BOTH robots
# -------------------------------
async def camera_loop(ctx: Context):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        add_message("Camera not found.", "sent")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            await asyncio.sleep(SEND_INTERVAL)
            continue

        direction, reason, obstacle = analyze_frame(frame)

        # SEND TO SPIDERBOT (normal)
        await ctx.send(SPIDERBOT_ADDRESS,
                       Command(direction=direction, reason=reason, obstacle_type=obstacle))

        add_message(f"[Spiderbot] move {direction} ({reason})", "sent")

        # SEND TO WHEELBOT (OPPOSITE)
        opposite = {"LEFT":"RIGHT","RIGHT":"LEFT","FRONT":"BACK","BACK":"FRONT"}
        dir_wheel = opposite[direction]

        await ctx.send(WHEELBOT_ADDRESS,
                       Command(direction=dir_wheel, reason=reason, obstacle_type=obstacle))

        add_message(f"[Wheelbot] move {dir_wheel} (opposite of spider)", "sent")

        await asyncio.sleep(HUMAN_DELAY)

# -------------------------------
# RECEIVE STATUS FROM BOTH BOTS
# -------------------------------
@agent.on_message(model=Status)
async def handle_status(ctx: Context, sender: str, msg: Status):
    global spider_pos, wheel_pos

    if msg.bot_name == "spider":
        spider_pos = list(msg.new_pos)
        add_message(
            f"[Spiderbot] moved {msg.old_pos} → {msg.new_pos}",
            "received",
            bot_type="spider"
        )

    elif msg.bot_name == "wheel":
        wheel_pos = list(msg.new_pos)
        add_message(
            f"[Wheelbot] moved {msg.old_pos} → {msg.new_pos}",
            "received",
            bot_type="wheel"
        )

    draw_bots()
    await asyncio.sleep(HUMAN_DELAY)

# -------------------------------
# STARTUP
# -------------------------------
@agent.on_event("startup")
async def startup(ctx: Context):
    asyncio.create_task(camera_loop(ctx))

# -------------------------------
# TKINTER LOOP
# -------------------------------
def gui_update():
    draw_bots()
    root.after(100, gui_update)

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    threading.Thread(target=lambda: agent.run(), daemon=True).start()
    gui_update()
    root.mainloop()
