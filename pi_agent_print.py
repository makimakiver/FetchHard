# Raspberry pi code


# pi_agent_print.py
from uagents import Agent, Context, Model
import asyncio

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

    # Update spiderbot position
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
    await ctx.send(sender, status)

# -------------------------------
# Heartbeat (optional)
# -------------------------------
async def heartbeat(ctx: Context):
    while True:
        # Optional: print periodic status
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
# Run agent
# -------------------------------
if __name__ == "__main__":
    agent.run()