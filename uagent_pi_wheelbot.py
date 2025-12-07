# uagent_pi_wheelbot.py
from uagents import Agent, Context, Model
import asyncio
import RPi.GPIO as GPIO
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
# GPIO Setup
# -------------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Motor pins (safe, avoid LCD pins)
LEFT_IN1 = 5
LEFT_IN2 = 6
RIGHT_IN1 = 12
RIGHT_IN2 = 13
MOTOR_PINS = [LEFT_IN1, LEFT_IN2, RIGHT_IN1, RIGHT_IN2]

for pin in MOTOR_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# -------------------------------
# Motor control functions
# -------------------------------
def stop():
    for pin in MOTOR_PINS:
        GPIO.output(pin, GPIO.LOW)

def move_forward(duration=0.5):
    GPIO.output(LEFT_IN1, GPIO.HIGH)
    GPIO.output(LEFT_IN2, GPIO.LOW)
    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)
    time.sleep(duration)
    stop()

def move_backward(duration=0.5):
    GPIO.output(LEFT_IN1, GPIO.LOW)
    GPIO.output(LEFT_IN2, GPIO.HIGH)
    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop()

def turn_left(duration=0.5):
    GPIO.output(LEFT_IN1, GPIO.LOW)
    GPIO.output(LEFT_IN2, GPIO.HIGH)
    GPIO.output(RIGHT_IN1, GPIO.HIGH)
    GPIO.output(RIGHT_IN2, GPIO.LOW)
    time.sleep(duration)
    stop()

def turn_right(duration=0.5):
    GPIO.output(LEFT_IN1, GPIO.HIGH)
    GPIO.output(LEFT_IN2, GPIO.LOW)
    GPIO.output(RIGHT_IN1, GPIO.LOW)
    GPIO.output(RIGHT_IN2, GPIO.HIGH)
    time.sleep(duration)
    stop()

# -------------------------------
# Agent Setup
# -------------------------------
PI_IP = "10.64.173.142"  # Pi IP
agent = Agent(
    name="pi_agent",
    seed="pi_agent_seed",
    port=8001,
    endpoint=[f"http://{PI_IP}:8001/submit"]
)

# Spiderbot state
position = [5, 5]  # starting at center of 10x10 grid

# -------------------------------
# Handle Commands from Laptop
# -------------------------------
@agent.on_message(model=Command)
async def handle_command(ctx: Context, sender: str, msg: Command):
    global position
    old_pos = position.copy()

    # Print received command
    print(f"\n[Pi] Received Command from {sender}: {msg.direction}, reason: {msg.reason}, obstacle: {msg.obstacle_type}")

    # Motor control
    if msg.direction == "LEFT":
        turn_left()
    elif msg.direction == "RIGHT":
        turn_right()
    elif msg.direction == "FRONT":
        move_forward()
    elif msg.direction == "BACK":
        move_backward()
    else:
        stop()

    # Update simulated position
    if msg.direction == "LEFT":
        position[0] = max(0, position[0] - 1)
    elif msg.direction == "RIGHT":
        position[0] = min(9, position[0] + 1)
    elif msg.direction == "FRONT":
        position[1] = max(0, position[1] - 1)
    elif msg.direction == "BACK":
        position[1] = min(9, position[1] + 1)

    # Print new position
    print(f"[Pi] Spiderbot moved from {old_pos} to {position}")

    # Send status back to laptop
    status = Status(old_pos=tuple(old_pos), new_pos=tuple(position), obstacle_type=msg.obstacle_type)
    try:
        await ctx.send(sender, status)
        print(f"[Pi] Status sent back to {sender}")
    except Exception as e:
        print(f"[Pi] Failed to send status: {e}")

# -------------------------------
# Optional Heartbeat
# -------------------------------
async def heartbeat(ctx: Context):
    while True:
        print(f"[Pi] Current Spiderbot position: {position}")
        await asyncio.sleep(5)

# -------------------------------
# Startup
# -------------------------------
@agent.on_event("startup")
async def startup(ctx: Context):
    print("[Pi] Agent started and ready to receive commands.")
    asyncio.create_task(heartbeat(ctx))

# -------------------------------
# Run Agent
# -------------------------------
if __name__ == "__main__":
    try:
        agent.run()
    except KeyboardInterrupt:
        stop()
        GPIO.cleanup()
        print("[Pi] GPIO cleaned up. Exiting.")