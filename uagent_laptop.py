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

# -------------------------------
# Configuration
# -------------------------------
PI_AGENT_ADDRESS = "agent1qdakxxf9saqnmft032m4zfs8mj2cdnmehljv6jkw7yy6t92hq6cjj4mh2tn"
LAPTOP_IP = "10.64.173.208"  # Your laptop IP
SEND_INTERVAL = 0.5  # seconds
HUMAN_DELAY = 1.5    # 500 milliseconds

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
root.title("Spiderbot Simulation & Chat")
root.geometry("900x500")

# Spiderbot Canvas
canvas = tk.Canvas(root, width=400, height=400, bg="white")
canvas.grid(row=0, column=0, padx=10, pady=10)

GRID_SIZE = 10
BOT_SIZE = 40
bot_pos = [5,5]  # starting position

def draw_spiderbot():
    canvas.delete("all")
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x0, y0 = i*BOT_SIZE, j*BOT_SIZE
            x1, y1 = x0+BOT_SIZE, y0+BOT_SIZE
            canvas.create_rectangle(x0, y0, x1, y1, outline="gray")
    # Draw spiderbot
    x0, y0 = bot_pos[0]*BOT_SIZE, bot_pos[1]*BOT_SIZE
    x1, y1 = x0+BOT_SIZE, y0+BOT_SIZE
    canvas.create_oval(x0, y0, x1, y1, fill="blue")

# WhatsApp-style Chat Frame
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

def add_message(text, sender):
    time_str = time.strftime("%H:%M:%S")
    bubble_frame = tk.Frame(scrollable_frame, bg="#efe7dd")
    bubble_frame.pack(pady=4, anchor="e" if sender=="sent" else "w", padx=10)

    if sender == "sent":
        bubble = tk.Label(bubble_frame, text=f"{text}  ", bg="#dcf8c6", fg="black",
                          justify="left", wraplength=220, font=("Arial", 11),
                          relief="flat", padx=12, pady=8)
        bubble.pack(side="right")
        tk.Label(bubble, text=f"{time_str} ✓✓", fg="#34b7f1", bg="#dcf8c6",
                 font=("Arial",8)).place(relx=1.0, rely=1.0, anchor="se")
    else:
        bubble = tk.Label(bubble_frame, text=f"{text}  ", bg="white", fg="black",
                          justify="left", wraplength=220, font=("Arial", 11),
                          relief="flat", padx=12, pady=8)
        bubble.pack(side="left")
        tk.Label(bubble, text=time_str, fg="#999999", bg="white", font=("Arial",8)).place(relx=1.0, rely=1.0, anchor="se")

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

# -------------------------------
# Obstacle Detection
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
        return "FRONT", "No obstacle detected", "NONE"

    x, y, w, h = cv2.boundingRect(largest_contour)
    cx = x + w//2
    frame_center = frame.shape[1]//2

    if cx < frame_center/2:
        return "RIGHT", f"{detected_color} obstacle LEFT", detected_color
    elif cx > frame_center*1.5:
        return "LEFT", f"{detected_color} obstacle RIGHT", detected_color
    else:
        return "BACK", f"{detected_color} obstacle CENTER", detected_color

# -------------------------------
# Async Camera Loop with Delay
# -------------------------------
async def camera_loop(ctx: Context):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        add_message("Camera not found. Using manual moves.", "sent")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            await asyncio.sleep(SEND_INTERVAL)
            continue

        direction, reason, obstacle_type = analyze_frame(frame)
        try:
            await ctx.send(PI_AGENT_ADDRESS, Command(direction=direction, reason=reason, obstacle_type=obstacle_type))
            add_message(f"I suggested to move {direction} because {reason}.", "sent")
            await asyncio.sleep(HUMAN_DELAY)  # 500ms delay
        except Exception as e:
            add_message(f"Failed to send: {e}", "sent")
            await asyncio.sleep(HUMAN_DELAY)

        await asyncio.sleep(SEND_INTERVAL)

# -------------------------------
# Handle Pi Status Messages (Humanized) with Delay
# -------------------------------
@agent.on_message(model=Status)
async def handle_status(ctx: Context, sender: str, msg: Status):
    global bot_pos
    bot_pos = list(msg.new_pos)
    human_text = f"Hey, I moved the spiderbot from {msg.old_pos} to {msg.new_pos} because of the {msg.obstacle_type.lower()} obstacle."
    add_message(human_text, "received")
    draw_spiderbot()
    await asyncio.sleep(HUMAN_DELAY)  # 500ms delay

# -------------------------------
# Agent Startup
# -------------------------------
@agent.on_event("startup")
async def startup(ctx: Context):
    asyncio.create_task(camera_loop(ctx))

# -------------------------------
# Tkinter GUI Update
# -------------------------------
def gui_update():
    draw_spiderbot()
    root.after(100, gui_update)

# -------------------------------
# Run Application
# -------------------------------
if __name__ == "__main__":
    threading.Thread(target=lambda: agent.run(), daemon=True).start()
    gui_update()
    root.mainloop()