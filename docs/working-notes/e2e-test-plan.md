# End-to-End Test Plan

**Date:** June 27, 2026  
**Purpose:** Validate the full workshop flow with logical checkpoints before the June 30 session.

---

## Checkpoint 1: Environment & Dependencies

| # | Test | Command | Expected |
|---|------|---------|----------|
| 1.1 | Python version | `python3 --version` | 3.11+ |
| 1.2 | Install deps | `pip install -e .` | Installs without error |
| 1.3 | Import data_store | `python3 -c "from src.data_store import FLIGHTS; print(len(FLIGHTS))"` | 21 (or more) |
| 1.4 | Import graph_client | `python3 -c "from src.graph_client import graph_client; print(type(graph_client).__name__)"` | `NetworkXGraphClient` |
| 1.5 | Import tools | `python3 -c "from src.tools import get_flight_status, find_connections; print('OK')"` | `OK` |
| 1.6 | Import agent | `python3 -c "from src.agent import agent; print(agent.tools)"` | Lists 4 tools |

**Pass criteria:** All imports succeed. Data loads from JSON without errors.

---

## Checkpoint 2: Data Integrity

| # | Test | Command | Expected |
|---|------|---------|----------|
| 2.1 | Disruption scenario exists | `python3 -c "from src.data_store import get_flight; f=get_flight('AA456','2025-07-15'); print(f['status'], f['delay_minutes'])"` | `delayed 120` |
| 2.2 | Connection target exists | `python3 -c "from src.data_store import get_flight; f=get_flight('AA789','2025-07-15'); print(f['departure_time'])"` | `15:45` |
| 2.3 | Alex Johnson PNR | `python3 -c "from src.data_store import get_passenger; p=get_passenger('AXJN42'); print(p['name'], len(p['itinerary']))"` | `Alex Johnson 2` |
| 2.4 | Graph finds MIA→ORD direct | `python3 -c "from src.graph_client import graph_client; r=graph_client.find_connections('MIA','ORD',0); print(len(r), r[0]['segments'][0]['flight_number'])"` | `1 AA912` |
| 2.5 | Graph finds alternatives excluding DFW | `python3 -c "from src.graph_client import graph_client; r=graph_client.find_alternatives('MIA','ORD','DFW'); print(len(r))"` | 2+ (direct + via CLT) |
| 2.6 | Seats available on AA912 | `python3 -c "from src.data_store import get_seats; s=get_seats('AA912'); print(s['economy']['available'])"` | `12` |

**Pass criteria:** Dallas disruption scenario data is complete. Graph traversal returns correct alternatives.

---

## Checkpoint 3: Tool Behavior

| # | Test | Command | Expected |
|---|------|---------|----------|
| 3.1 | Valid flight status | `python3 -c "from src.tools import get_flight_status; print(get_flight_status(flight_number='AA456', date='2025-07-15'))"` | Dict with status=delayed |
| 3.2 | Invalid flight number | `python3 -c "from src.tools import get_flight_status; print(get_flight_status(flight_number='ZZ999', date='2025-07-15'))"` | `{"error": "invalid_parameter", ...}` |
| 3.3 | Not-found flight | `python3 -c "from src.tools import get_flight_status; print(get_flight_status(flight_number='AA9999', date='2020-01-01'))"` | `{"error": "not_found", ...}` |
| 3.4 | Search flights | `python3 -c "from src.tools import search_flights; r=search_flights(origin='MIA',destination='DFW',date='2025-07-15'); print(r['count'])"` | `1` |
| 3.5 | Seat availability | `python3 -c "from src.tools import check_seat_availability; r=check_seat_availability(flight_number='AA912'); print(r['seats']['economy']['available'])"` | `12` |
| 3.6 | Find connections excluding DFW | `python3 -c "from src.tools import find_connections; r=find_connections(origin='MIA',destination='ORD',date='2025-07-15',exclude_hub='DFW'); print(r.get('routes') and len(r['routes']))"` | 2+ |

**Pass criteria:** All tools return correct structured data. Validation rejects bad input. Graph traversal finds alternatives.

---

## Checkpoint 4: Local Server

| # | Test | How | Expected |
|---|------|-----|----------|
| 4.1 | Server starts | `RUNTIME_MODE=local python3 -m src.entrypoint_local` | Uvicorn running on :8001 |
| 4.2 | Ping | `curl http://localhost:8001/ping` | `{"status":"healthy"}` |
| 4.3 | Simple query | `curl -X POST http://localhost:8001/invocations -H "Content-Type: application/json" -d '{"prompt":"Status of AA456 on 2025-07-15?"}'` | JSON response with flight status |
| 4.4 | CLI starts | `python3 cli.py` (in new terminal) | Shows welcome banner |
| 4.5 | CLI status query | Type: `What's the status of AA456 on 2025-07-15?` | Response mentions "delayed" |
| 4.6 | CLI disruption query | Type: `My flight AA456 from Miami to Dallas is delayed 2 hours. I'll miss my connection to Chicago. What are my options?` | Mentions alternative routes (AA912 or via CLT) |
| 4.7 | CLI exit | Type: `exit` | Terminates cleanly |
| 4.8 | CLI error on no server | Stop server, run `python3 cli.py`, type anything | "Could not connect" error message |

**Pass criteria:** Server serves requests. Agent calls tools correctly. Dallas disruption scenario produces rebooking options.

---

## Checkpoint 5: Agent Reasoning Quality

| # | Scenario | Query | Expected Agent Behavior |
|---|----------|-------|------------------------|
| 5.1 | Simple status | "What's the status of flight AA789?" | Calls `get_flight_status`, returns on_time, DFW→ORD |
| 5.2 | Search | "Find flights from MIA to DFW tomorrow" | Calls `search_flights`, lists AA456 |
| 5.3 | Seat check | "Any first class seats on AA912?" | Calls `check_seat_availability`, mentions 1 first class seat |
| 5.4 | **Dallas disruption** (KEY) | "My connection in Dallas is delayed. I'm trying to get from Miami to Chicago. What are my options?" | Calls `find_connections` with exclude_hub=DFW, presents AA912 direct + CLT route |
| 5.5 | Multi-step reasoning | "Is AA456 delayed? If so, will I make my AA789 connection?" | Calls `get_flight_status` for both, reasons about timing |

**Pass criteria:** Agent reliably calls `find_connections` with `exclude_hub="DFW"` for the disruption scenario. If Nova Pro doesn't make this tool call consistently, we have a prompt issue.

---

## Checkpoint 6: CDK Stack (post-implementation)

| # | Test | Command | Expected |
|---|------|---------|----------|
| 6.1 | CDK synth | `cd deployment && cdk synth` | Produces valid CloudFormation YAML |
| 6.2 | Resource types | Inspect synth output | Contains AgentCore Runtime, Gateway, IAM resources |
| 6.3 | CDK deploy | `cdk deploy` | Completes in <10 min, outputs endpoint URL |
| 6.4 | Remote ping | Invoke via AWS CLI | Agent responds |
| 6.5 | Remote disruption scenario | Same query as 5.4 via remote endpoint | Same quality response |

---

## Checkpoint 7: Observability (post-deployment)

| # | Test | How | Expected |
|---|------|-----|----------|
| 7.1 | Transaction Search enabled | CloudWatch Console → Settings | Shows "Enabled" |
| 7.2 | Traces appear | Invoke 3x, wait 3 min, check GenAI Observability | Session metrics visible |
| 7.3 | Trace drill-down | Click a trace | Shows spans: LLM inference → tool calls → response |
| 7.4 | Span timing | Inspect disruption query trace | Multiple tool call spans visible |

---

## Checkpoint 8: Cleanup

| # | Test | Command | Expected |
|---|------|---------|----------|
| 8.1 | CDK destroy | `cdk destroy` | All resources removed |
| 8.2 | Verify cleanup | Check console | No orphaned resources |

---

## Quick Smoke Test Script

Runs checkpoints 1-4 in ~5 minutes:

```bash
# 1. Install
pip install -e .

# 2. Verify data
python3 -c "
from src.data_store import get_flight, get_passenger
from src.graph_client import graph_client
from src.tools import find_connections

# Disruption data
f = get_flight('AA456', '2025-07-15')
assert f['status'] == 'delayed', f'Expected delayed, got {f[\"status\"]}'

# Graph alternatives
alts = graph_client.find_alternatives('MIA', 'ORD', 'DFW')
assert len(alts) >= 2, f'Expected 2+ alternatives, got {len(alts)}'

# Tool layer
r = find_connections(origin='MIA', destination='ORD', date='2025-07-15', exclude_hub='DFW')
assert 'routes' in r, f'Expected routes key, got {r}'
print('✅ All data checks passed')
"

# 3. Start server (background)
RUNTIME_MODE=local python3 -m src.entrypoint_local &
sleep 3

# 4. Test endpoints
curl -s http://localhost:8001/ping | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='healthy'; print('✅ Ping OK')"

curl -s -X POST http://localhost:8001/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Status of AA456 on 2025-07-15?"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ Agent responded:', d.get('response','')[:80])"

# 5. Cleanup
kill %1
```
