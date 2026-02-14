import os
from dotenv import load_dotenv

load_dotenv()

from backend.agent.agent import Agent

# ── Initialize the Agent ──
agent = Agent()

# ════════════════════════════════════════════════
#  TEST 1: Multi-turn Conversation (Memory)
# ════════════════════════════════════════════════
THREAD_ID = "user-session-001"

print("=" * 60)
print("TURN 1: Greeting")
print("=" * 60)
result = agent.run_agent(
    query="Hi, I need help booking a flight. What do you need from me?",
    thread_id=THREAD_ID
)
print(f"Response: {result.get('response', 'No response')}")
print(f"Route: {result.get('route_decision', 'N/A')}")

print("\n" + "=" * 60)
print("TURN 2: Flight Details (Agent remembers previous turn)")
print("=" * 60)
result = agent.run_agent(
    query="I want to travel from Kolkata to Mumbai on 10th March 2026 under 6000 rupees",
    thread_id=THREAD_ID  # Same thread = remembers context
)
print(f"Response: {result.get('response', 'No response')}")
print(f"Route: {result.get('route_decision', 'N/A')}")
print(f"Search Params: {result.get('search_params', 'N/A')}")

# ── Check Memory ──
print("\n" + "=" * 60)
print("CONVERSATION MEMORY")
print("=" * 60)
memory = agent.get_memory(THREAD_ID)
for entry in memory:
    print(f"  [{entry['role']}]: {entry['content'][:80]}...")


# ════════════════════════════════════════════════
#  TEST 2: Streaming Response (Token-by-Token)
# ════════════════════════════════════════════════
print("\n\n" + "=" * 60)
print("STREAMING RESPONSE TEST")
print("=" * 60)
print("Response: ", end="", flush=True)
for token in agent.stream_response(
    query="Find flights from Delhi to Goa for next week",
    thread_id="stream-test-001"
):
    print(token, end="", flush=True)
print()  # newline


# ════════════════════════════════════════════════
#  TEST 3: Node-by-Node Streaming
# ════════════════════════════════════════════════
print("\n" + "=" * 60)
print("NODE-BY-NODE STREAM TEST")
print("=" * 60)
for node_name, state_update in agent.stream_agent(
    query="What flights go from Chennai to Bangalore?",
    thread_id="node-stream-001"
):
    print(f"  📡 [{node_name}] → keys: {list(state_update.keys())}")