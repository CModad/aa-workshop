# AA Workshop Agent — Steering Guide

This steering file provides guidance for building the American Airlines Workshop Demo Agent. It covers Strands SDK patterns, AgentCore deployment conventions, observability setup, and Kiro Power usage specific to this workshop project.

---

## Kiro Powers

This workshop requires three Kiro Powers installed and active:

| Power | Purpose |
|-------|---------|
| `aws-agentcore` | AgentCore Runtime, Gateway, and observability guidance |
| `strands` | Strands SDK documentation, tool patterns, and agent design |
| `cloud-architect` | AWS service docs, CDK patterns, pricing, and regional availability |

Use powers proactively:
- Before writing agent code, activate `strands` for SDK patterns
- Before writing CDK stacks, activate `cloud-architect` for construct references
- Before configuring Runtime or Gateway, activate `aws-agentcore` for deployment guidance

---

## Strands SDK Conventions

### Agent Definition

Agents are defined with a system prompt, model, and tool list:

```python
from strands import Agent, tool
from strands.models import BedrockModel

model = BedrockModel(model_id="us.amazon.nova-pro-v1:0")

agent = Agent(
    model=model,
    tools=[tool_a, tool_b, tool_c],
    system_prompt="You are a helpful assistant..."
)
```

Guidelines:
- Keep agent definition in a single `agent.py` file — no conditional logic based on deployment mode
- System prompts should be concise and domain-specific
- List tools explicitly; avoid dynamic tool loading in workshop code

### Custom Tool Definitions

Use the `@tool` decorator with typed parameters and Google-style docstrings:

```python
from strands import tool

@tool
def get_flight_status(flight_number: str, date: str) -> dict:
    """Get the current status of a flight.

    Args:
        flight_number: The flight number (e.g., AA1234).
        date: The flight date in YYYY-MM-DD format.

    Returns:
        Flight status including departure, arrival, gate, and status.
    """
    # Implementation here
    ...
```

Rules:
- Every parameter must have a type annotation
- Every tool must have a docstring — this is what the LLM sees as the tool description
- Use `Args:` section in docstring to describe each parameter for the model
- Return structured data (dict or dataclass), not raw strings
- Handle errors gracefully — return error dicts rather than raising exceptions to the agent
- Keep tools focused: one tool = one capability

### Error Handling in Tools

```python
@tool
def get_flight_status(flight_number: str, date: str) -> dict:
    """..."""
    if not flight_number or not flight_number.startswith("AA"):
        return {"error": "invalid_parameter", "parameter": "flight_number", "expected": "AA followed by 1-4 digits"}

    result = data_store.get_flight(flight_number, date)
    if not result:
        return {"error": "not_found", "message": f"No flight {flight_number} found for {date}"}

    return result
```

---

## Dual-Mode Entrypoint Pattern

The agent logic lives in `agent.py`. Two thin entrypoint files handle transport:

### Local Entrypoint (entrypoint_local.py)

```python
from fastapi import FastAPI, Request
from agent import agent
import uvicorn

app = FastAPI()

@app.post("/invocations")
async def invoke(request: Request):
    body = await request.json()
    response = agent(body.get("prompt"))
    return {"response": response.message["content"][0]["text"]}

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### AWS Entrypoint (entrypoint_aws.py)

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent import agent

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    response = agent(payload.get("prompt"))
    return response.message["content"][0]["text"]

@app.ping
def health():
    return "healthy"

if __name__ == "__main__":
    app.run()
```

Rules:
- Entrypoint files should be under 30 lines each
- Zero imports from entrypoint code into agent.py — the dependency flows one direction only
- The `/invocations` and `/ping` contract is non-negotiable — AgentCore Runtime requires both
- `RUNTIME_MODE` environment variable selects which entrypoint to run, never changes agent.py

---

## AgentCore Runtime Deployment

### CDK Conventions

- Use Python CDK (`aws-cdk-lib`)
- One stack for the workshop: Runtime agent + Gateway + IAM roles
- Tag all resources: `project=aa-workshop-agent`, `tier=workshop`
- Output the Runtime endpoint URL on successful deploy
- Include `cdk destroy` cleanup that removes everything

### Runtime Configuration

- 1 vCPU, 2 GB memory for workshop workloads
- Python application deployment (not Docker) via AgentCore CLI or CDK
- Health check at `/ping`, invocation at `/invocations`
- IAM role must include Bedrock model invocation permissions

### Gateway Tool Registration

- Register tools with MCP-compliant schemas (name, description, inputSchema)
- Use descriptive target names: `flight-operations`, `passenger-services`
- Enforce access policies: Flight_Ops_Agent → flight-operations only; Rebooking_Agent → both targets

---

## AgentCore Observability

### Setup

1. Enable CloudWatch Transaction Search (one-time per account)
2. Deploy agent to AgentCore Runtime — automatic OpenTelemetry instrumentation, no code changes needed
3. Invoke agent several times to generate telemetry
4. View data on CloudWatch GenAI Observability dashboard

### Key Concepts

| Level | What It Shows | Generated By |
|-------|---------------|-------------|
| Session | Full conversation lifecycle, high-level metrics | Automatic (Runtime) |
| Trace | Single request-response: input → inference → tools → output | Automatic (Runtime) |
| Span | Individual operations within a trace (LLM call, tool call) | Automatic (Runtime) |

### IAM Permissions for Observability

The agent's execution role needs:
- `xray:PutTraceSegments`
- `xray:PutTelemetryRecords`
- `logs:PutLogEvents`
- `cloudwatch:PutMetricData`

Include these in the CDK stack's agent role.

### What Participants Should See

- Invocation count, average latency, error rate on the dashboard
- A full trace showing: user prompt → Bedrock inference → tool call(s) → response
- Span-level timing to identify which tool call is slowest

---

## In-Memory Data Store

### Data File Structure

`data/flights.json` should contain:
- 20+ flights using AA format (AA1234)
- 8 AA hub airports: DFW, CLT, MIA, ORD, PHX, LAX, JFK, PHL
- Status variety: on_time, delayed, cancelled, boarding
- Seat data with 3 classes (first, business, economy)
- Passenger bookings with PNR codes (6 alphanumeric characters)
- Multi-leg itineraries routing through DFW for the connection disruption scenario

`data/routes.json` should contain:
- Airport nodes with code and name
- Route edges with flight_number, departure_time, arrival_time, status, date
- At least 3 multi-leg itineraries through DFW
- A pre-configured disruption: AA456 (MIA→DFW) delayed, causing missed connection to AA789 (DFW→ORD)

### Loading Pattern

```python
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"

def _load_json(filename: str) -> dict:
    with open(_DATA_DIR / filename) as f:
        return json.load(f)

# Load once at module import time
FLIGHTS = _load_json("flights.json")
```

Rules:
- Load at startup, serve from memory — no file I/O per tool call
- Keep data files human-editable so participants can modify scenarios
- Use realistic but obviously fake data (no real PNRs or passenger info)

---

## Knowledge Graph (Local → Neptune)

### Local Graph (NetworkX)

The local graph uses NetworkX with no server process required:
- Airports are nodes, routes are directed edges
- `find_connections` traverses the graph using `nx.all_simple_paths`
- `find_alternatives` excludes a disrupted hub from the traversal
- Loaded from `data/routes.json` at startup

### Graph Client Abstraction

`src/graph_client.py` provides a common interface:
- `find_connections(origin, destination, max_stops)` — multi-hop path finding
- `find_alternatives(origin, destination, exclude_hub, max_stops)` — path finding avoiding a hub
- `GRAPH_BACKEND` environment variable selects NetworkX (default) or Neptune

This mirrors the dual-mode entrypoint pattern:
- Same tool interface (`find_connections` tool)
- Same query semantics
- Different backing store (NetworkX locally, Neptune in production)

### Neptune Extension

When deploying to Neptune:
- Use Neptune Serverless (2-8 NCUs for workshop scale)
- Connect via `gremlinpython` using Gremlin or openCypher queries
- Load the same route data from `routes.json` using bulk loader or insert statements
- Agent code and tools remain unchanged — only `graph_client` initialization changes

---

## Project Structure

```
aa-workshop-agent/
├── src/
│   ├── agent.py              # Agent logic, system prompt, tool list
│   ├── tools.py              # @tool decorated functions
│   ├── graph_client.py       # Graph abstraction (NetworkX / Neptune)
│   ├── data_store.py         # JSON data loader
│   ├── entrypoint_local.py   # FastAPI wrapper
│   └── entrypoint_aws.py     # AgentCore Runtime wrapper
├── data/
│   ├── flights.json          # Flight, seat, and passenger data
│   └── routes.json           # Airport nodes and route edges (knowledge graph)
├── deployment/
│   └── cdk_app.py            # CDK deployment stack
├── tests/
│   └── test_tools.py         # Tool unit tests
├── cli.py                    # Workshop CLI interface
├── pyproject.toml            # Dependencies (pinned versions)
└── README.md                 # Workshop guide
```

Keep total file count under 25 (excluding __pycache__, .git, .kiro).

---

## Workshop Flow

| Module | Duration | Key Activity |
|--------|----------|--------------|
| Setup | 15 min | Install deps, configure AWS creds, install Kiro Powers |
| Build Agent | 45 min | Create agent.py with system prompt and model |
| Add Tools & Graph | 30 min | Define @tool functions, build graph client, wire to data store |
| Test Locally | 20 min | Run local entrypoint, test connection disruption scenario |
| Deploy to Cloud | 30 min | Run CDK deploy, test remote endpoint |
| Explore Gateway | 20 min | Review tool registrations, access policies |
| Observe Agent | 15 min | View traces, spans, and metrics in CloudWatch |
| Optional: Rebooking | 40 min | Second agent with distinct tool permissions |
| Optional: Neptune | 30 min | Swap local graph for Neptune, run same queries |

---

## Code Style

- Python 3.11+ with type annotations on all function signatures
- Google-style docstrings for all tools and public functions
- No classes unless genuinely needed — prefer functions and modules
- Pin all dependencies in pyproject.toml
- Keep imports minimal — standard library + strands + fastapi + aws-cdk-lib
- No Docker, no docker-compose, no containers for local development

---

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Bedrock model access denied | Verify model access is enabled in the Bedrock console for the target region |
| Port already in use | Kill existing process on 8001 or change port in entrypoint_local.py |
| Tools not appearing to agent | Ensure @tool decorator is applied and tool is in the agent's tools list |
| CloudWatch traces not showing | Wait 2-3 minutes after invocation; verify Transaction Search is enabled |
| CDK deploy fails on permissions | Ensure CDK bootstrap has been run in the target account/region |
| Agent returns empty response | Check system prompt and verify Bedrock credentials are valid |
