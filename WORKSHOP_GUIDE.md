# American Airlines Agent Workshop

Build, test, and deploy an AI-powered Flight Operations agent using the Strands SDK and Amazon Bedrock AgentCore — all driven by Kiro's spec-driven development workflow.

**Duration**: 2.5–3 hours (core modules) | Up to 4 hours with optional extensions

**What you'll build**: A Flight Operations agent that looks up flight status, searches routes, and checks seat availability — running locally first, then deployed to AgentCore Runtime with full observability.

---

## The Scenario: Dallas Connection Disruption

Before we dive into building, here's the business problem we're solving and the customer interaction you'll have working by the end of this workshop:

> **Alex Johnson** is booked MIA → DFW → ORD (Miami to Chicago, connecting through Dallas). Flight AA456 (MIA→DFW) is delayed 2 hours. Alex will miss the connection to AA789 (DFW→ORD departing 15:45). Alex asks: *"My connection in Dallas is delayed. What are my rebooking options to get to Chicago?"*

By the end of this workshop, your agent will handle this in a single conversational turn:

1. **Check status** — confirms AA456 is delayed, arrival now 16:30
2. **Detect the missed connection** — AA789 departs 15:45, connection impossible
3. **Search alternative routes** — traverses the flight network *excluding DFW* to find paths through other hubs
4. **Present options** — "You can take AA912 direct MIA→ORD at 17:00, or route through Charlotte: AA234 MIA→CLT + AA567 CLT→ORD"
5. **Check availability** — confirms open seats on each alternative

**Why this matters**: A simple database lookup can only find direct flights. The **knowledge graph** enables the agent to discover multi-hop alternatives through other hubs — the kind of intelligent routing that differentiates a GenAI agent from a basic search API.

### What Makes This Possible

| Capability | How we build it |
|---|---|
| Natural language understanding | Amazon Nova Pro via Bedrock |
| Real-time flight data | Custom tools with `@tool` decorator |
| Multi-hop route reasoning | Knowledge graph (NetworkX locally → Neptune in production) |
| Connection-aware rebooking | Graph traversal with hub exclusion |
| Production deployment | AgentCore Runtime with Gateway tool governance |
| Operational visibility | AgentCore Observability (traces showing each tool call) |

Each module builds one piece of this picture. By the end, you'll run the full scenario and see every tool call in a CloudWatch trace.

---

## Learning Objectives

By the end of this workshop, you will be able to:

- Set up Kiro with Powers for AI agent development
- Use spec-driven development (requirements → design → tasks) to plan before coding
- Build agents with the Strands SDK using `@tool` decorated functions
- Use a local knowledge graph (NetworkX) for multi-hop reasoning in flight disruption scenarios
- Run agents locally with the dual-mode entrypoint pattern
- Deploy agents to Amazon Bedrock AgentCore Runtime via CDK
- Understand AgentCore Gateway tool governance and access policies
- Monitor deployed agents using AgentCore Observability (sessions, traces, spans)
- (Optional) Transition from a local graph to Amazon Neptune for production-scale knowledge graph queries

---

## Prerequisites

Before the workshop, ensure you have:

- [ ] **Python 3.11+** installed (`python --version`)
- [ ] **Node.js 20+** installed (for CDK CLI: `node --version`)
- [ ] **AWS CLI** configured with valid credentials (`aws sts get-caller-identity`)
- [ ] **Amazon Bedrock model access** enabled for Amazon Nova Pro in your target region
- [ ] **Kiro IDE** installed and signed in
- [ ] **uv** or **pip** available for Python package management
- [ ] **AWS CDK CLI** installed (`npm install -g aws-cdk`)

---

## Module 1: Kiro Environment Setup (15 min)

### 1.1 Install Kiro Powers

Open the Kiro command palette and install these three Powers:

| Power | What it provides |
|-------|-----------------|
| `aws-agentcore` | AgentCore Runtime, Gateway, and observability guidance |
| `strands` | Strands SDK documentation, tool patterns, and agent design |
| `cloud-architect` | AWS service docs, CDK patterns, pricing, and regional availability |

To install each power:
1. Open the Powers panel in the Kiro sidebar
2. Search for the power name
3. Click Install
4. Verify it appears as "Active" before proceeding

### 1.2 Open the Workshop Project

```bash
cd aa-workshop-agent
code .  # or open in Kiro directly
```

### 1.3 Install Python Dependencies

```bash
uv sync
# or
pip install -e .
```

This installs all pinned dependencies from `pyproject.toml` including `strands-agents`, `fastapi`, `uvicorn`, and `aws-cdk-lib`.

### 1.4 Verify AWS Access

```bash
aws sts get-caller-identity
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'nova')]" --output table
```

You should see your account ID and at least one Nova model listed.

---

## Module 2: Spec-Driven Planning (30 min)

In this module, you'll use Kiro's spec workflow to plan the agent before writing code. This demonstrates how spec-driven development keeps you aligned with requirements throughout implementation.

### 2.1 Review the Requirements

Open `.kiro/specs/aa-workshop-agent/requirements.md` in Kiro.

This document defines:
- The Flight Operations Agent and its tools
- The in-memory data store backed by JSON
- The knowledge graph for multi-hop reasoning
- The dual-mode entrypoint pattern
- The CLI interface for testing
- AgentCore Gateway integration
- Deployment and observability requirements

Take 5 minutes to read through the requirements. Note how each requirement has:
- A user story explaining the "who" and "why"
- Acceptance criteria in EARS format (WHEN/THE/SHALL) that are testable

### 2.2 Review the Technical Design

Open `.kiro/specs/aa-workshop-agent/design.md`.

This was generated from the requirements by Kiro. It includes:
- Architecture diagrams (system overview, dual-mode pattern, data flow sequence)
- Component specifications (agent, tools, graph client, data store, entrypoints)
- Data models (flights.json structure, routes.json graph schema)
- Interface contracts (HTTP /invocations + /ping, tool signatures, graph client protocol)
- 8 correctness properties that our tests will validate

Notice how the design traces directly to requirements — every component exists because a requirement demanded it.

### 2.3 Review the Task List

Open `.kiro/specs/aa-workshop-agent/tasks.md`.

This was generated from the design by Kiro. It breaks the work into 15 ordered tasks with dependencies. Key points:
- Tasks are grouped into parallel execution "waves"
- Each task references specific requirements for traceability
- Property-based tests are interleaved with implementation (test what you build, when you build it)
- Checkpoints ensure we verify before moving on

### 2.4 Execute Scaffolding Tasks with Kiro

Now let's see Kiro generate code. In the tasks panel:

1. Click **Start task** on Task 1.1 (pyproject.toml) — Kiro creates the dependency file
2. Click **Start task** on Task 1.2 (directory structure) — Kiro creates the folders
3. Click **Start task** on Task 2.1 (flights.json) — Kiro generates the test data including the Dallas disruption scenario
4. Click **Start task** on Task 2.2 (routes.json) — Kiro generates the route graph

Review each generated file. These are the **infrastructure** files that support the learning — not the learning itself.

**Key takeaway:** In 5 minutes, Kiro generated a project skeleton with realistic test data, all traced back to the requirements. This is the acceleration that spec-driven development provides.

---

## Module 3: Build the Agent (45 min)

In this module, you'll write the core agent code yourself — the tools, graph client, and agent definition. This is the learning. The data layer (Task 3.1) can be generated by Kiro, but we'll write the interesting parts by hand to understand how they work.

### 3.1 Create the Data Store (Kiro-assisted)

Let Kiro generate this from the task list — click **Start task** on Task 3.1, or write it yourself:

Create `src/data_store.py` — this loads flight data from JSON at startup:

```python
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> dict:
    with open(_DATA_DIR / filename) as f:
        return json.load(f)


# Load once at module import time — no file I/O per tool call
FLIGHTS = _load_json("flights.json")
```

Verify the data file exists:
```bash
cat data/flights.json | python -m json.tool | head -20
```

### 3.2 Define Custom Tools (write this yourself)

This is the core learning — understanding how `@tool` functions work. Create `src/tools.py` with three tools:

```python
from strands import tool
from src.data_store import FLIGHTS


@tool
def get_flight_status(flight_number: str, date: str) -> dict:
    """Get the current status of a flight.

    Args:
        flight_number: The flight number (e.g., AA1234).
        date: The flight date in YYYY-MM-DD format.

    Returns:
        Flight status including departure time, arrival time, origin, destination, gate, and status.
    """
    if not flight_number or not flight_number.upper().startswith("AA"):
        return {"error": "invalid_parameter", "parameter": "flight_number", "expected": "AA followed by 1-4 digits"}

    key = f"{flight_number.upper()}_{date}"
    flight = FLIGHTS.get("flights", {}).get(key)
    if not flight:
        return {"error": "not_found", "message": f"No flight {flight_number} found for {date}"}

    return flight


@tool
def search_flights(origin: str, destination: str, date: str) -> dict:
    """Search for flights between two airports on a specific date.

    Args:
        origin: The origin airport code (e.g., DFW).
        destination: The destination airport code (e.g., JFK).
        date: The flight date in YYYY-MM-DD format.

    Returns:
        List of matching flights with status and available seat count.
    """
    results = []
    for key, flight in FLIGHTS.get("flights", {}).items():
        if (flight.get("origin") == origin.upper()
            and flight.get("destination") == destination.upper()
            and flight.get("date") == date):
            results.append(flight)

    if not results:
        return {"error": "not_found", "message": f"No flights from {origin} to {destination} on {date}"}

    return {"flights": results, "count": len(results)}


@tool
def check_seat_availability(flight_number: str) -> dict:
    """Check available seats on a specific flight.

    Args:
        flight_number: The flight number (e.g., AA1234).

    Returns:
        Available seats grouped by class (first, business, economy).
    """
    if not flight_number or not flight_number.upper().startswith("AA"):
        return {"error": "invalid_parameter", "parameter": "flight_number", "expected": "AA followed by 1-4 digits"}

    seats = FLIGHTS.get("seats", {}).get(flight_number.upper())
    if not seats:
        return {"error": "not_found", "message": f"No seat data for flight {flight_number}"}

    return {"flight_number": flight_number.upper(), "seats": seats}
```

**Key points:**
- Each tool has typed parameters and a Google-style docstring
- The docstring is what the LLM sees as the tool description
- Errors return structured dicts, not exceptions

### 3.3 Build the Knowledge Graph Client (write this yourself)

This is where you learn how a graph enables multi-hop reasoning. Create `src/graph_client.py` — this models the flight network as a graph:

```python
import json
from pathlib import Path
import networkx as nx

_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_routes() -> dict:
    with open(_DATA_DIR / "routes.json") as f:
        return json.load(f)


class LocalGraphClient:
    """NetworkX-based local graph for flight route traversal."""

    def __init__(self):
        data = _load_routes()
        self.graph = nx.DiGraph()

        # Add airport nodes
        for airport in data["airports"]:
            self.graph.add_node(airport["code"], **airport)

        # Add route edges
        for route in data["routes"]:
            self.graph.add_edge(
                route["origin"],
                route["destination"],
                flight_number=route["flight_number"],
                departure_time=route["departure_time"],
                arrival_time=route["arrival_time"],
                status=route["status"],
                date=route["date"],
            )

    def find_connections(self, origin: str, destination: str, max_stops: int = 1) -> list:
        """Find all routes from origin to destination with up to max_stops intermediate airports."""
        paths = []
        for path in nx.all_simple_paths(self.graph, origin, destination, cutoff=max_stops + 1):
            route_details = []
            for i in range(len(path) - 1):
                edge_data = self.graph.edges[path[i], path[i + 1]]
                route_details.append({
                    "from": path[i],
                    "to": path[i + 1],
                    **edge_data,
                })
            paths.append({"stops": len(path) - 2, "segments": route_details})
        return paths

    def find_alternatives(self, origin: str, destination: str, exclude_hub: str, max_stops: int = 1) -> list:
        """Find routes that avoid a specific hub (e.g., avoid DFW when connection is disrupted)."""
        all_paths = self.find_connections(origin, destination, max_stops)
        return [p for p in all_paths if not any(seg["from"] == exclude_hub or seg["to"] == exclude_hub
                                                 for seg in p["segments"][1:])]  # Allow origin/dest to be the hub


# Initialize once at module load
graph_client = LocalGraphClient()
```

This is the **same pattern as the dual-mode entrypoint** — the `find_connections` and `find_alternatives` methods define the interface. In production, you'd swap `LocalGraphClient` for a `NeptuneGraphClient` that runs the same queries via Gremlin/openCypher against Amazon Neptune.

### 3.4 Add the Connection Finder Tool (write this yourself)

This is the tool that ties the graph to the agent. Add this to `src/tools.py`:

```python
from src.graph_client import graph_client


@tool
def find_connections(origin: str, destination: str, date: str, exclude_hub: str = "") -> dict:
    """Find available flight connections between two airports, optionally excluding a hub.

    Use this when a customer's connection is disrupted and needs alternative routing.
    This traverses the flight network graph to find multi-hop alternatives.

    Args:
        origin: The origin airport code (e.g., MIA).
        destination: The final destination airport code (e.g., ORD).
        date: The travel date in YYYY-MM-DD format.
        exclude_hub: Optional airport to exclude from routing (e.g., DFW if connection there is disrupted).

    Returns:
        Available connection options with flight details for each leg.
    """
    if exclude_hub:
        routes = graph_client.find_alternatives(origin.upper(), destination.upper(), exclude_hub.upper())
    else:
        routes = graph_client.find_connections(origin.upper(), destination.upper())

    if not routes:
        return {"error": "not_found", "message": f"No connections found from {origin} to {destination}"}

    return {"connections": routes, "count": len(routes), "excluding": exclude_hub or "none"}
```

**Why a graph?** A simple `search_flights` can only find direct flights. The `find_connections` tool traverses the route network to discover multi-hop alternatives — exactly what's needed when a customer says "my Dallas connection is delayed, what are my options?"

### 3.5 Create the Agent (write this yourself)

Now wire everything together. Create `src/agent.py`:

```python
from strands import Agent
from strands.models import BedrockModel
from src.tools import get_flight_status, search_flights, check_seat_availability, find_connections

model = BedrockModel(model_id="us.amazon.nova-pro-v1:0")

SYSTEM_PROMPT = """You are an American Airlines flight operations assistant. You help customers with:
- Checking flight status (departures, arrivals, delays, cancellations)
- Searching for available flights between airports
- Checking seat availability on specific flights
- Finding alternative connections when a flight is disrupted

Always use the available tools to look up real data. Never make up flight information.
When a customer reports a disrupted connection, use find_connections to search for alternative
routing options, potentially excluding the disrupted hub airport.
When presenting results, format them clearly for the customer.
Use airport codes (DFW, JFK, etc.) in your tool calls even if the customer uses city names.
"""

agent = Agent(
    model=model,
    tools=[get_flight_status, search_flights, check_seat_availability, find_connections],
    system_prompt=SYSTEM_PROMPT,
)
```

**Note:** This file contains zero conditional logic about deployment mode. It's imported unchanged by both entrypoints.

---

## Module 4: Test Locally (20 min)

### 4.1 Create the Local Entrypoint

Create `src/entrypoint_local.py`:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.agent import agent
import uvicorn

app = FastAPI(title="Flight Ops Agent - Local")


@app.post("/invocations")
async def invoke(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    response = agent(prompt)
    return JSONResponse({"response": response.message["content"][0]["text"]})


@app.get("/ping")
async def ping():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 4.2 Start the Agent Locally

```bash
RUNTIME_MODE=local python -m src.entrypoint_local
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### 4.3 Test with the CLI

In a new terminal:

```bash
python cli.py
```

Try these queries:
```
> What's the status of flight AA456 on 2025-07-15?
> Find me flights from DFW to JFK tomorrow
> What seats are available on AA789?
> My flight AA456 from Miami to Dallas is delayed 2 hours. I'm going to miss my connection to Chicago. What are my options?
> exit
```

Watch the CLI output — you'll see tool invocations (tool name + parameters) before each response. For the connection disruption query, notice how the agent:
1. Checks the status of AA456 (confirms the delay)
2. Uses `find_connections` to search MIA→ORD alternatives excluding DFW
3. Checks seat availability on the recommended alternatives

This multi-step reasoning is powered by the knowledge graph — a simple flight search couldn't find one-stop alternatives through other hubs.

### 4.4 Test with curl

```bash
# Health check
curl http://localhost:8001/ping

# Query the agent
curl -X POST http://localhost:8001/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the status of flight AA1234 on 2025-07-15?"}'
```

---

## Module 5: Run Tests (15 min)

### 5.1 Run Unit Tests

```bash
pytest tests/ -v
```

Tests validate:
- Each tool returns correct data for valid inputs
- Tools return structured errors for invalid inputs
- The data store loads successfully from JSON

### 5.2 Review Test Patterns

Open `tests/test_tools.py` and observe:
- Tools are tested as plain Python functions (no agent needed)
- Edge cases are covered (invalid flight numbers, missing data)
- Return structures are validated

---

## Module 6: Deploy to AWS (30 min)

### 6.1 Create the AWS Entrypoint

Create `src/entrypoint_aws.py`:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.agent import agent

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt", "")
    response = agent(prompt)
    return response.message["content"][0]["text"]


@app.ping
def health():
    return "healthy"


if __name__ == "__main__":
    app.run()
```

**Compare with the local entrypoint** — the agent import and invocation logic is identical. Only the transport wrapper changes.

### 6.2 Bootstrap CDK (if first time)

```bash
cd deployment
cdk bootstrap
```

### 6.3 Deploy

```bash
cdk deploy
```

This provisions:
- AgentCore Runtime agent (1 vCPU, 2 GB memory)
- AgentCore Gateway with tool registrations under "flight-operations" target
- IAM roles with Bedrock invoke and observability permissions
- All resources tagged: `project=aa-workshop-agent`, `tier=workshop`

Deployment takes approximately 5-10 minutes. When complete, you'll see:

```
Outputs:
AaWorkshopStack.AgentEndpointUrl = https://runtime.agentcore.us-east-1.amazonaws.com/agents/...
```

### 6.4 Test the Deployed Agent

```bash
# Using the endpoint URL from the deploy output
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "<YOUR_AGENT_RUNTIME_ARN>" \
  --runtime-session-id "workshop-test-001" \
  --payload '{"prompt": "What flights go from DFW to LAX?"}'
```

You should get the same quality response as your local agent — same code, different transport.

---

## Module 7: Explore Gateway (20 min)

### 7.1 View Tool Registrations

In the AWS Console, navigate to **Bedrock → AgentCore → Gateway** and find the "flight-operations" target. You'll see your three tools registered with MCP-compliant schemas:

- `get_flight_status` — with inputSchema defining flight_number and date
- `search_flights` — with inputSchema defining origin, destination, and date
- `check_seat_availability` — with inputSchema defining flight_number

### 7.2 Understand Access Policies

The Flight_Ops_Agent has access only to the "flight-operations" target. If you later deploy the optional Rebooking Agent, it will have access to both "flight-operations" and "passenger-services" — demonstrating least-privilege tool governance.

### 7.3 Key Takeaway

Locally, tools are registered directly with the agent via the `tools=[...]` parameter. In production, AgentCore Gateway:
- Provides centralized tool discovery via MCP protocol
- Enforces access policies (which agent can call which tools)
- Enables tool sharing across multiple agents
- Adds an audit trail for tool invocations

---

## Module 8: Observe Your Agent (15 min)

### 8.1 Prerequisites

Ensure CloudWatch Transaction Search is enabled (one-time per account):

1. Open the **CloudWatch Console**
2. Navigate to **Settings → Account → X-Ray traces**
3. Under **Transaction Search**, click **View settings**
4. Click **Edit** → **Enable Transaction Search**
5. Select **For X-Ray users** and set sampling to 100% (for workshop purposes)
6. Click **Save** and wait until "Ingest OpenTelemetry spans" shows **Enabled**

### 8.2 Generate Telemetry

Invoke your deployed agent 3-5 times with different queries to generate telemetry data:

```bash
# Query 1: Flight status
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "<YOUR_ARN>" \
  --runtime-session-id "obs-demo-001" \
  --payload '{"prompt": "Status of AA1234 on 2025-07-15?"}'

# Query 2: Flight search
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "<YOUR_ARN>" \
  --runtime-session-id "obs-demo-002" \
  --payload '{"prompt": "Find flights from MIA to ORD on 2025-07-20"}'

# Query 3: Seat check
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "<YOUR_ARN>" \
  --runtime-session-id "obs-demo-003" \
  --payload '{"prompt": "What seats are open on AA5678?"}'
```

Wait 2-3 minutes for telemetry to propagate.

### 8.3 View Session Metrics

1. Open **CloudWatch Console → Generative AI Observability**
2. Find your agent in the dashboard
3. Observe:
   - **Invocation count** — how many times the agent was called
   - **Average latency** — how long responses take
   - **Error rate** — percentage of failed invocations

### 8.4 Drill Into a Trace

1. Click on a specific invocation to view its trace
2. The trace shows the full execution path:
   - User prompt received
   - Bedrock LLM inference (model thinking)
   - Tool invocation(s) with input parameters
   - Tool response processing
   - Final response generation
3. Each step shows timing as a span

### 8.5 Exercise: Find the Slowest Tool Call

Look at a trace that involved multiple tool calls (e.g., the flight search query). Identify:
- Which span represents the LLM inference?
- Which span represents the tool execution?
- Which operation took the longest?

This is exactly how you'd debug a slow agent response in production — traces pinpoint whether latency comes from the model, from tool execution, or from data retrieval.

### 8.6 Key Takeaway: The Observability Hierarchy

| Level | What you see | Use it for |
|-------|-------------|------------|
| **Session** | Full conversation metrics | Usage patterns, high-level health |
| **Trace** | Single request lifecycle | Debugging a specific invocation |
| **Span** | Individual operations | Performance optimization, bottleneck identification |

AgentCore Runtime provides all of this automatically — no custom instrumentation needed for agents deployed on Runtime.

---

## Module 9 (Optional): Rebooking Agent (40 min)

If you finish early, extend the workshop with a second agent demonstrating multi-agent patterns and distinct tool permissions.

### 9.1 Add Passenger Tools

Create `src/rebooking_tools.py` with two additional tools:
- `get_booking` — looks up a passenger booking by PNR code
- `update_booking` — reassigns a passenger to a new flight and seat

### 9.2 Create the Rebooking Agent

Create `src/rebooking_agent.py` — this agent uses all five tools (3 flight tools + 2 passenger tools) to handle rebooking requests like:

> "My flight AA1234 was cancelled. Can you rebook me on another DFW to JFK flight today? My PNR is ABC123."

### 9.3 Run Locally

Start the Rebooking Agent on port 8002 alongside the Flight Ops Agent on 8001. Test rebooking scenarios via the CLI.

### 9.4 Deploy with Distinct Permissions

Update the CDK stack to deploy both agents with separate Gateway access policies:
- Flight_Ops_Agent → access to "flight-operations" target only
- Rebooking_Agent → access to both "flight-operations" and "passenger-services" targets

This demonstrates least-privilege tool governance in a multi-agent system.

---

## Module 10 (Optional): Local Graph → Amazon Neptune (30 min)

This extension demonstrates how the same graph queries that run locally on NetworkX transition to Amazon Neptune for production — mirroring the dual-mode entrypoint pattern but for the data layer.

### 10.1 Understanding the Pattern

In the core workshop, you built `graph_client.py` with a `LocalGraphClient` class using NetworkX. The key insight: **the `find_connections` tool doesn't know or care whether the graph is NetworkX or Neptune.** It calls `graph_client.find_connections()` — and that's it.

```
Local Development          Production
┌─────────────────┐       ┌─────────────────┐
│  find_connections│       │  find_connections│
│      (tool)      │       │      (tool)      │
└────────┬─────────┘       └────────┬─────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐       ┌─────────────────┐
│ LocalGraphClient │       │NeptuneGraphClient│
│   (NetworkX)     │       │  (Gremlin/OC)    │
└─────────────────┘       └─────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐       ┌─────────────────┐
│  routes.json     │       │ Amazon Neptune   │
│  (in-memory)     │       │  (managed DB)    │
└─────────────────┘       └─────────────────┘
```

### 10.2 Create the Neptune Graph Client

Add a `NeptuneGraphClient` to `src/graph_client.py`:

```python
from gremlin_python.driver import client as gremlin_client
from gremlin_python.driver.serializer import GraphSONSerializersV2d0
import os


class NeptuneGraphClient:
    """Amazon Neptune graph client using Gremlin for flight route traversal."""

    def __init__(self):
        endpoint = os.environ["NEPTUNE_ENDPOINT"]
        self.client = gremlin_client.Client(
            f"wss://{endpoint}:8182/gremlin",
            "g",
            message_serializer=GraphSONSerializersV2d0(),
        )

    def find_connections(self, origin: str, destination: str, max_stops: int = 1) -> list:
        """Find routes via Gremlin traversal."""
        query = (
            f"g.V('{origin}')"
            f".repeat(out('flies_to').simplePath())"
            f".until(hasId('{destination}').or().loops().is(gte({max_stops + 1})))"
            f".hasId('{destination}')"
            f".path()"
            f".by(valueMap(true))"
        )
        results = self.client.submit(query).all().result()
        return self._format_paths(results)

    def find_alternatives(self, origin: str, destination: str, exclude_hub: str, max_stops: int = 1) -> list:
        """Find routes avoiding a specific hub via Gremlin traversal."""
        query = (
            f"g.V('{origin}')"
            f".repeat(out('flies_to').not(hasId('{exclude_hub}')).simplePath())"
            f".until(hasId('{destination}').or().loops().is(gte({max_stops + 1})))"
            f".hasId('{destination}')"
            f".path()"
            f".by(valueMap(true))"
        )
        results = self.client.submit(query).all().result()
        return self._format_paths(results)

    def _format_paths(self, raw_paths: list) -> list:
        """Convert Gremlin path results to the same format as LocalGraphClient."""
        paths = []
        for path in raw_paths:
            segments = []
            nodes = path["objects"]
            for i in range(0, len(nodes) - 1, 2):  # nodes alternate vertex/edge
                segments.append({
                    "from": nodes[i].get("code", [""])[0],
                    "to": nodes[i + 2].get("code", [""])[0],
                    "flight_number": nodes[i + 1].get("flight_number", [""])[0],
                })
            paths.append({"stops": len(segments) - 1, "segments": segments})
        return paths


# Select client based on environment
def get_graph_client():
    if os.environ.get("GRAPH_BACKEND") == "neptune":
        return NeptuneGraphClient()
    return LocalGraphClient()


graph_client = get_graph_client()
```

### 10.3 Deploy Neptune via CDK

Add a Neptune Serverless cluster to the CDK stack:

```python
from aws_cdk import aws_neptune as neptune

# Neptune Serverless cluster for the knowledge graph
graph_cluster = neptune.CfnDBCluster(
    self, "WorkshopGraphCluster",
    db_cluster_identifier="aa-workshop-graph",
    engine_version="1.3.2.0",
    serverless_scaling_configuration=neptune.CfnDBCluster.ServerlessScalingConfigurationProperty(
        min_capacity=2,
        max_capacity=8,
    ),
)
```

Deploy:
```bash
cd deployment
cdk deploy --context graph_backend=neptune
```

### 10.4 Load Graph Data into Neptune

Use the bulk loader or Gremlin inserts to populate Neptune with the same data from `routes.json`:

```python
# Load airports as vertices
for airport in routes_data["airports"]:
    client.submit(f"g.addV('airport').property(id, '{airport['code']}').property('name', '{airport['name']}')")

# Load routes as edges
for route in routes_data["routes"]:
    client.submit(
        f"g.V('{route['origin']}').addE('flies_to').to(V('{route['destination']}'))"
        f".property('flight_number', '{route['flight_number']}')"
        f".property('departure_time', '{route['departure_time']}')"
    )
```

### 10.5 Test the Same Scenario on Neptune

Run the connection disruption query against the Neptune-backed agent:

```bash
GRAPH_BACKEND=neptune python cli.py
> My connection in Dallas is delayed. I'm flying from Miami to Chicago. What are my options?
```

You should get the **same results** as the local graph — the agent logic, tool interface, and response format are identical. Only the data layer changed.

### 10.6 Key Takeaway: The Data Layer Pattern

| Layer | Local | Production |
|-------|-------|------------|
| Agent logic | `agent.py` | `agent.py` (unchanged) |
| Transport | FastAPI/uvicorn | AgentCore Runtime |
| Tool interface | `find_connections` tool | `find_connections` tool (unchanged) |
| Graph backend | NetworkX (in-memory) | Amazon Neptune (managed) |
| Data source | `routes.json` | Neptune bulk load / real-time feeds |

This is the **same separation of concerns** applied twice:
1. **Compute**: dual-mode entrypoint (local ↔ AgentCore Runtime)
2. **Data**: graph client abstraction (NetworkX ↔ Neptune)

In production, Neptune provides:
- Scalability to billions of relationships
- ACID transactions for concurrent updates
- Integration with Bedrock Knowledge Bases for GraphRAG
- Managed backups, high availability, and encryption

### 10.7 Production Vision: GraphRAG with Bedrock Knowledge Bases

For production flight operations, the architecture extends further:

```
Customer Query
      │
      ▼
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│ Flight Ops  │────▶│ Bedrock Knowledge│────▶│ Amazon Neptune │
│   Agent     │     │   Base (GraphRAG)│     │ (Knowledge     │
│             │     │                  │     │  Graph)        │
└─────────────┘     └──────────────────┘     └────────────────┘
                                                      │
                                              ┌───────┴───────┐
                                              │ Real-time     │
                                              │ flight feeds, │
                                              │ crew data,    │
                                              │ maintenance   │
                                              └───────────────┘
```

Amazon Bedrock Knowledge Bases with Neptune enables:
- **GraphRAG**: Combining graph traversal with vector similarity for richer context retrieval
- **Entity extraction**: Automatically building the knowledge graph from unstructured data
- **Multi-hop reasoning**: Answering complex queries that span multiple relationship types
- **Real-time updates**: Flight status changes propagate through the graph instantly

The workshop demonstrates the core pattern. Production adds scale, real-time data, and richer graph schemas.

---

## Cleanup

When you're done, remove all deployed resources:

```bash
cd deployment
cdk destroy
```

Confirm the stack deletion. All AgentCore Runtime agents, Gateway registrations, Neptune clusters (if deployed), and IAM roles will be removed.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `AccessDeniedException` on Bedrock calls | Verify model access is enabled in Bedrock console for your region |
| `Address already in use` on port 8001 | `lsof -i :8001` then `kill <PID>`, or change port in entrypoint_local.py |
| Tools not invoked by agent | Verify @tool decorator is present and tool is in the `tools=[...]` list |
| No traces in CloudWatch | Wait 2-3 min after invocation; verify Transaction Search is enabled |
| CDK deploy fails | Run `cdk bootstrap` first; verify AWS credentials have admin permissions |
| Agent returns empty or garbled response | Check system prompt is set; verify Bedrock credentials and model ID |
| `ModuleNotFoundError` on import | Run `pip install -e .` or `uv sync` from the project root |
| CLI can't connect to agent | Ensure the local agent is running before starting cli.py |
| NetworkX `import` error | Run `pip install networkx` or verify it's in pyproject.toml |
| Neptune connection timeout | Ensure VPC security group allows inbound on port 8182; check endpoint URL |

---

## What You Built

### The Business Scenario — Delivered

Remember Alex Johnson from the beginning? Here's what your agent now handles:

```
Customer: "My connection in Dallas is delayed. What are my rebooking options to get to Chicago?"

Agent thinking:
  → get_flight_status("AA456", "2025-07-15") → Delayed, arrives 16:30
  → get_flight_status("AA789", "2025-07-15") → Departs 15:45, connection missed
  → find_connections("MIA", "ORD", exclude_hub="DFW") → 2 alternatives found
  → check_seat_availability("AA912") → 3 economy seats available
  → check_seat_availability("AA234") → 5 economy seats available

Agent: "Your flight AA456 is delayed 2 hours, so you'll miss your AA789 connection
in Dallas. Here are your options to get to Chicago:

  1. AA912 — Direct MIA→ORD, departs 17:00, arrives 20:15 (3 economy seats)
  2. AA234 + AA567 — Via Charlotte: MIA→CLT 16:30, CLT→ORD 19:00 (5 seats available)

Would you like me to rebook you on either option?"
```

That's GenAI reasoning + knowledge graph traversal + real-time data — working together in a single conversational turn.

### The Architecture — Summarized

```
┌─────────────────────────────────────────────────────────────┐
│                    What You Built                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Planning (Kiro Spec Workflow)                               │
│  ┌────────────┐  ┌──────────┐  ┌───────────┐              │
│  │Requirements│→ │  Design  │→ │   Tasks   │              │
│  └────────────┘  └──────────┘  └───────────┘              │
│                                                              │
│  Agent Logic (unchanged across environments)                 │
│  ┌────────┐  ┌───────┐  ┌─────────────┐                   │
│  │agent.py│→ │tools.py│→ │graph_client │                   │
│  └────────┘  └───────┘  └─────────────┘                   │
│                                                              │
│  Local Development          Cloud Deployment                 │
│  ┌──────────────┐          ┌───────────────────┐           │
│  │FastAPI/uvicorn│          │ AgentCore Runtime  │           │
│  │NetworkX graph │          │ Neptune (optional) │           │
│  │CLI testing    │          │ Gateway governance │           │
│  └──────────────┘          │ CloudWatch traces  │           │
│                             └───────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Takeaways

1. **Separation of concerns scales** — The same pattern (abstraction layer + swappable backend) applies to compute *and* data. Agent logic never changes.

2. **Knowledge graphs enable reasoning flat queries can't** — A direct flight search finds MIA→ORD. A graph traversal discovers MIA→CLT→ORD when DFW is disrupted. That's the difference between a lookup tool and an intelligent agent.

3. **Spec-driven development keeps you aligned** — Requirements captured the scenario up front. Design mapped it to tools and graph structure. Tasks broke it into buildable units. No drift.

4. **Observability closes the loop** — You can see exactly which tool calls happened, how long each took, and where to optimize. In production, this is how you debug "why did the agent recommend that route?"

5. **Local → Cloud is a configuration change, not a rewrite** — Same agent, same tools, same graph queries. Different infrastructure underneath.

---

## Next Steps

- Explore the [Strands SDK documentation](https://strandsagents.com) for advanced patterns (multi-agent, agents-as-tools, streaming)
- Review [AgentCore documentation](https://docs.aws.amazon.com/bedrock-agentcore/) for Memory, Identity, and Browser capabilities
- Try adding custom OpenTelemetry spans for fine-grained observability
- Build a production agent with real data sources replacing the JSON store
