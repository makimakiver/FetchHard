# FetchHard

A distributed robotics system demonstrating machine-to-machine communication using Fetch.ai's uAgents framework. This project implements a spiderbot/wheelbot that can be controlled remotely through autonomous agents communicating over the Fetch.ai network.

## Overview

FetchHard consists of multiple components working together:
- **Laptop Agent**: Sends movement commands to the Raspberry Pi agent
- **Raspberry Pi Agent**: Receives commands and controls physical hardware (motors)
- **Arduino Controller**: Low-level motor control via serial communication

The system uses Fetch.ai's uAgents framework to enable secure, decentralized communication between agents without requiring direct network connections or centralized servers.

## Architecture

```
┌─────────────┐         Fetch.ai Network         ┌──────────────┐
│             │  ──────────────────────────────>  │              │
│ Laptop      │  Command Messages (HTTP)         │ Raspberry Pi │
│ Agent       │  <──────────────────────────────  │ Agent         │
│             │  Status Messages (HTTP)           │              │
└─────────────┘                                   └──────┬───────┘
                                                          │
                                                          │ Serial (USB)
                                                          │
                                                          ▼
                                                   ┌──────────────┐
                                                   │   Arduino    │
                                                   │   Controller │
                                                   └──────┬───────┘
                                                          │
                                                          │ GPIO
                                                          │
                                                          ▼
                                                   ┌──────────────┐
                                                   │   Motors     │
                                                   │  (Wheelbot)  │
                                                   └──────────────┘
```

## Fetch.ai Machine-to-Machine Communication Protocol

### What is Fetch.ai uAgents?

Fetch.ai uAgents is a framework for building autonomous agents that can communicate with each other over a decentralized network. Agents are identified by unique addresses derived from cryptographic seeds, enabling secure peer-to-peer communication without requiring centralized servers.

### Key Concepts

#### 1. **Agents**
Agents are autonomous entities that can send and receive messages. Each agent has:
- **Name**: Human-readable identifier
- **Seed**: Cryptographic seed used to generate a unique agent address
- **Port**: HTTP port for receiving messages
- **Endpoint**: HTTP endpoint URL where messages are sent

```python
agent = Agent(
    name="pi_agent",
    seed="pi_agent_seed",
    port=8001,
    endpoint=[f"http://{PI_IP}:8001/submit"]
)
```

#### 2. **Models**
Models define the structure of messages using Pydantic. They ensure type safety and validation:

```python
class Command(Model):
    direction: str      # Movement direction: LEFT, RIGHT, FRONT, BACK
    reason: str         # Reason for movement
    obstacle_type: str  # Type of obstacle detected

class Status(Model):
    old_pos: tuple      # Previous position (x, y)
    new_pos: tuple      # New position (x, y)
    obstacle_type: str  # Obstacle information
```

#### 3. **Message Handlers**
Agents register handlers for specific message types using decorators:

```python
@agent.on_message(model=Command)
async def handle_command(ctx: Context, sender: str, msg: Command):
    # Process the message
    # ctx: Agent context for sending replies
    # sender: Address of the agent that sent the message
    # msg: The received message (validated against Command model)
```

#### 4. **Sending Messages**
Agents send messages using the context object:

```python
await ctx.send(sender, status)  # Send Status message back to sender
```

#### 5. **Agent Discovery**
Agents can discover each other through:
- Direct endpoint URLs (as shown in this project)
- Fetch.ai's agent registry/discovery service
- Manual address exchange

### Communication Flow

1. **Agent Initialization**
   - Agent starts and registers its endpoint
   - Agent generates its unique address from the seed
   - Agent begins listening on the specified port

2. **Message Sending**
   - Sender agent creates a message instance (e.g., `Command`)
   - Sender uses `ctx.send(recipient_address, message)` to send
   - Message is serialized and sent via HTTP POST to recipient's endpoint

3. **Message Reception**
   - Recipient agent receives HTTP POST at `/submit` endpoint
   - Message is deserialized and validated against the Model
   - Matching handler function is invoked with the message

4. **Response Pattern**
   - Handler processes the message
   - Handler can send a response using `ctx.send(sender, response)`
   - This creates a bidirectional communication channel

### Protocol Benefits

- **Decentralized**: No central server required
- **Secure**: Cryptographic addressing ensures message authenticity
- **Type-Safe**: Pydantic models validate message structure
- **Asynchronous**: Built on async/await for efficient I/O
- **Network-Agnostic**: Works over any network (LAN, internet, etc.)

### Example Communication Sequence

```
1. Laptop Agent → Pi Agent: Command(direction="FRONT", reason="path_clear", obstacle_type="none")
   HTTP POST to http://10.64.173.142:8001/submit

2. Pi Agent receives Command
   - Validates message structure
   - Executes movement (GPIO control or simulation)
   - Updates position state

3. Pi Agent → Laptop Agent: Status(old_pos=(5,5), new_pos=(5,4), obstacle_type="none")
   HTTP POST to laptop agent's endpoint

4. Laptop Agent receives Status
   - Updates its view of robot state
   - Can send next command based on status
```

## Message Protocol

### Command Message
```python
{
    "direction": "LEFT" | "RIGHT" | "FRONT" | "BACK",
    "reason": "string describing reason for movement",
    "obstacle_type": "string describing obstacle type"
}
```

### Status Message
```python
{
    "old_pos": (x, y),  # Tuple of integers
    "new_pos": (x, y),  # Tuple of integers
    "obstacle_type": "string"
}
```

## Position System

The robot operates on a 10x10 grid:
- Starting position: `[5, 5]` (center)
- X-axis: 0-9 (LEFT decreases, RIGHT increases)
- Y-axis: 0-9 (FRONT decreases, BACK increases)
- Position is bounded to stay within grid limits

## Troubleshooting

1. **Agent not receiving messages**
   - Check IP address and port configuration
   - Verify network connectivity
   - Check firewall settings

2. **GPIO errors on Raspberry Pi**
   - Ensure you have GPIO permissions
   - Run with `sudo` if needed (not recommended)
   - Check pin assignments match your hardware

3. **Serial communication issues**
   - Verify Arduino is connected via USB
   - Check baud rate matches (9600)
   - Ensure Arduino sketch is uploaded correctly

## Future Enhancements

- Add sensor integration (ultrasonic, camera)
- Implement obstacle avoidance algorithms
- Add agent discovery service integration
- Implement multi-agent coordination
- Add logging and monitoring

## License

[Specify your license here]

## Contributing

[Contributing guidelines if applicable]
