# Implementation Plan: AA Workshop Agent

## Overview

This plan implements the American Airlines Workshop Demo Agent — a Strands SDK-based Flight Operations agent with dual-mode deployment (local FastAPI / AgentCore Runtime), in-memory flight data, NetworkX knowledge graph, CLI interface, and CDK deployment stack. Tasks are ordered so each builds on the previous, with no orphaned code.

## Tasks

- [ ] 1. Project scaffolding and dependencies
  - [ ] 1.1 Create pyproject.toml with pinned dependencies
    - Define project metadata (name: aa-workshop-agent, python >=3.11)
    - Pin dependencies: strands-agents, strands-agents-bedrock, fastapi, uvicorn, networkx, httpx, boto3
    - Pin dev dependencies: pytest, hypothesis, pytest-asyncio
    - Configure `[project.scripts]` entry for cli (e.g., `cli = "cli:main"`)
    - Include `[tool.pytest.ini_options]` with markers for integration tests
    - _Requirements: 8.3, 10.4_

  - [ ] 1.2 Create directory structure and __init__.py files
    - Create directories: src/, data/, deployment/, tests/property/, tests/unit/, tests/integration/
    - Add empty __init__.py in src/, tests/, tests/property/, tests/unit/, tests/integration/
    - _Requirements: 10.1, 10.2_

- [ ] 2. Data layer — flight data and route graph files
  - [ ] 2.1 Create data/flights.json with flight, seat, and passenger data
    - Include 20+ flights across 8 AA hubs (DFW, CLT, MIA, ORD, PHX, LAX, JFK, PHL) using AA#### format
    - Include status variety: on_time, delayed, cancelled, boarding
    - Include seat data for each flight (first, business, economy classes with realistic counts)
    - Include passenger bookings with PNR codes (6 alphanumeric) and multi-leg itineraries
    - Include Connection_Disruption_Scenario: Alex Johnson (AXJN42) on AA456 MIA→DFW (delayed 2h) connecting to AA789 DFW→ORD
    - Include at least 3 multi-leg itineraries routing through DFW
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.8, 3.10, 13.1_

  - [ ] 2.2 Create data/routes.json with airport nodes and route edges
    - Define 8 airport nodes (code, name) for all AA hubs
    - Define route edges with flight_number, departure_time, arrival_time, status, date attributes
    - Include routes enabling MIA→CLT→ORD, MIA→DFW→ORD, MIA→ORD direct paths
    - Ensure AA456 (MIA→DFW) is marked delayed for disruption scenario
    - Include enough edges for multi-hop alternatives avoiding DFW
    - _Requirements: 3.7, 3.8, 3.9, 3.10, 10.7, 12.3, 13.1_

- [ ] 3. Data store module
  - [ ] 3.1 Implement src/data_store.py — JSON loader and in-memory access
    - Load data/flights.json at module import time (fail fast on missing/malformed file)
    - Expose FLIGHTS, SEATS, PASSENGERS dictionaries for tool access
    - Provide helper functions: get_flight(flight_number, date), search_flights(origin, dest, date), get_seats(flight_number), get_passenger(pnr)
    - No file I/O on individual tool calls — data served from memory
    - _Requirements: 1.4, 3.1, 3.5, 3.6_

  - [ ]* 3.2 Write property tests for data store (Property 5: Data store structural invariants)
    - **Property 5: Data store structural invariants**
    - **Validates: Requirements 3.1, 3.3, 3.4**
    - Verify all flight_numbers match AA\d{1,4} pattern
    - Verify all seat records have first/business/economy with positive totals
    - Verify all passenger records have pnr, name, non-empty itinerary

- [ ] 4. Graph client module
  - [ ] 4.1 Implement src/graph_client.py — NetworkX graph abstraction
    - Load data/routes.json at startup, build NetworkX DiGraph (airports as nodes, routes as edges)
    - Implement find_connections(origin, destination, max_stops=1) using nx.all_simple_paths
    - Implement find_alternatives(origin, destination, exclude_hub, max_stops=1) filtering paths through excluded hub
    - Return list of dicts: {stops, segments: [{from, to, flight_number, departure_time, arrival_time, status}]}
    - Use GRAPH_BACKEND env var to select NetworkX (default) — Neptune extension later
    - _Requirements: 3.7, 3.9, 12.1, 12.2, 12.4_

  - [ ]* 4.2 Write property tests for graph client (Properties 6 & 7)
    - **Property 6: Graph traversal returns valid routes**
    - **Validates: Requirements 3.9, 12.4**
    - For connected origin/destination pairs, verify returned routes contain valid graph edges
    - **Property 7: Hub exclusion prevents routing through excluded airport**
    - **Validates: Requirements 13.4**
    - For origin/dest with alternatives, verify no intermediate stop passes through excluded hub

- [ ] 5. Custom tools
  - [ ] 5.1 Implement src/tools.py — core @tool functions
    - Implement get_flight_status(flight_number, date) with @tool decorator and docstring
    - Implement search_flights(origin, destination, date) with @tool decorator and docstring
    - Implement check_seat_availability(flight_number) with @tool decorator and docstring
    - Implement find_connections(origin, destination, date, exclude_hub="") with @tool decorator and docstring
    - Add input validation: flight numbers must start with "AA" + 1-4 digits, airport codes 3 uppercase letters, dates YYYY-MM-DD
    - Return structured error dicts (never raise to agent): {"error": "invalid_parameter"...} or {"error": "not_found"...}
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.9_

  - [ ]* 5.2 Write property tests for tools (Properties 1–4)
    - **Property 1: Flight status lookup returns complete structure**
    - **Validates: Requirements 2.2**
    - For valid flight keys, verify result contains departure_time, arrival_time, origin, destination, gate, status
    - **Property 2: Flight search returns exactly the matching flights**
    - **Validates: Requirements 2.3**
    - For known origin/dest/date, verify result set matches data store exactly
    - **Property 3: Seat availability returns valid class structure**
    - **Validates: Requirements 2.4**
    - For valid flight numbers, verify result has first/business/economy with non-negative available counts
    - **Property 4: Invalid inputs produce structured error responses**
    - **Validates: Requirements 2.5**
    - For invalid inputs (empty, non-AA prefix, malformed dates), verify "error" key in response

- [ ] 6. Checkpoint — Verify data layer and tools
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Agent definition
  - [ ] 7.1 Implement src/agent.py — Strands Agent with system prompt and tools
    - Import BedrockModel with model_id="us.amazon.nova-pro-v1:0"
    - Define system prompt for Flight Operations agent (concise, domain-specific)
    - Create Agent instance with model, system_prompt, and tools list [get_flight_status, search_flights, check_seat_availability, find_connections]
    - Expose a handler function that accepts a prompt string and returns agent response
    - Zero conditional logic based on RUNTIME_MODE — agent.py is mode-agnostic
    - _Requirements: 1.3, 1.6, 9.1_

  - [ ]* 7.2 Write unit tests for agent definition
    - Verify agent has 4 core tools registered
    - Verify system prompt is non-empty
    - Verify agent.py contains no RUNTIME_MODE conditionals
    - _Requirements: 1.6, 9.1_

- [ ] 8. Local entrypoint
  - [ ] 8.1 Implement src/entrypoint_local.py — FastAPI wrapper
    - Import agent handler from agent.py
    - Define POST /invocations endpoint accepting {"prompt": "..."} and returning {"response": "..."}
    - Define GET /ping endpoint returning {"status": "healthy"}
    - Run uvicorn on configurable port (default 8001)
    - Keep under 30 lines total
    - _Requirements: 1.2, 1.5, 9.2, 9.5_

  - [ ]* 8.2 Write unit test for entrypoint structure
    - Verify entrypoint_local.py is under 30 lines
    - Verify it does not import anything from entrypoint_aws.py
    - _Requirements: 9.5_

- [ ] 9. AWS entrypoint
  - [ ] 9.1 Implement src/entrypoint_aws.py — BedrockAgentCoreApp wrapper
    - Import agent handler from agent.py
    - Create BedrockAgentCoreApp instance
    - Register @app.entrypoint handler accepting payload and returning response text
    - Register @app.ping returning "healthy"
    - Keep under 30 lines total
    - _Requirements: 1.5, 9.3, 9.5_

  - [ ]* 9.2 Write unit test for AWS entrypoint structure
    - Verify entrypoint_aws.py is under 30 lines
    - Verify it does not import anything from entrypoint_local.py
    - _Requirements: 9.5_

- [ ] 10. CLI interface
  - [ ] 10.1 Implement cli.py — interactive terminal loop
    - Provide interactive input loop (prompt → send HTTP POST to localhost:8001/invocations → display response)
    - Display tool invocation details (tool name and parameters) before final response
    - Handle "exit" and "quit" commands to terminate gracefully
    - Display clear error message if agent not running (connection refused)
    - Executable with `python cli.py` — no extra config beyond AWS credentials
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 10.2 Write property test for CLI display formatting (Property 8)
    - **Property 8: CLI tool display includes name and parameters**
    - **Validates: Requirements 4.2**
    - For random tool_name and parameter dicts, verify display function output contains tool_name and all parameter values

  - [ ]* 10.3 Write unit tests for CLI
    - Test "exit" and "quit" commands terminate session
    - Test connection refused error message
    - _Requirements: 4.3, 4.5_

- [ ] 11. Checkpoint — Full local stack verification
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. CDK deployment stack
  - [ ] 12.1 Implement deployment/cdk_app.py — CDK stack for AgentCore
    - Define CDK app and AaWorkshopStack
    - Provision AgentCore Runtime agent (1 vCPU, 2 GB memory, Python app deploy)
    - Provision AgentCore Gateway with "flight-operations" target and 4 tool registrations (MCP schema)
    - Create IAM execution role with bedrock:InvokeModel, xray:PutTraceSegments, xray:PutTelemetryRecords, logs:PutLogEvents, cloudwatch:PutMetricData
    - Tag all resources: project=aa-workshop-agent, tier=workshop, created=ISO8601
    - Output Runtime endpoint URL on deploy
    - Support `cdk destroy` for clean teardown
    - _Requirements: 5.1, 5.2, 6.1, 6.2, 6.4, 6.5, 6.6, 6.7, 11.6_

  - [ ]* 12.2 Write unit test for CDK synth validation
    - Verify `cdk synth` produces valid CloudFormation template
    - Verify required resource types are present in synthesized template
    - _Requirements: 6.2_

- [ ] 13. Optional — Rebooking agent
  - [ ] 13.1 Implement src/rebooking_agent.py — second Strands Agent
    - Define Rebooking Agent with system prompt for passenger rebooking workflows
    - Register tools: get_flight_status, search_flights, check_seat_availability, find_connections, get_booking, update_booking
    - Expose handler function following same pattern as Flight Ops Agent
    - _Requirements: 7.1, 7.2_

  - [ ] 13.2 Implement src/rebooking_tools.py — passenger management tools
    - Implement get_booking(pnr) — lookup passenger booking by PNR code
    - Implement update_booking(pnr, new_flight, new_seat) — assign passenger to new flight/seat
    - Add validation (PNR must be 6 alphanumeric characters)
    - Return structured error dicts on failure
    - _Requirements: 7.1, 7.2_

  - [ ] 13.3 Add rebooking agent to local entrypoint on port 8002
    - Create src/entrypoint_rebooking.py or extend local runner to support second port
    - Rebooking agent runs alongside Flight Ops on separate port without Docker
    - _Requirements: 7.3_

  - [ ] 13.4 Add rebooking to CDK stack with distinct Gateway access policies
    - Register "passenger-services" target with get_booking and update_booking tools
    - Enforce access policy: Flight_Ops_Agent → flight-operations only; Rebooking_Agent → flight-operations + passenger-services
    - _Requirements: 5.3, 5.4, 7.4_

- [ ] 14. Optional — Neptune extension
  - [ ] 14.1 Add Neptune graph client implementation to src/graph_client.py
    - Implement NeptuneGraphClient class implementing same interface as NetworkX client
    - Connect via gremlinpython using Gremlin/openCypher queries
    - find_connections and find_alternatives semantically equivalent to NetworkX versions
    - Select backend via GRAPH_BACKEND env var ("neptune" vs "networkx" default)
    - _Requirements: 12.1, 12.4, 12.6_

  - [ ] 14.2 Add Neptune Serverless to CDK stack
    - Provision Neptune Serverless cluster (2-8 NCUs)
    - Add neptune-db:* permissions to agent role (conditional on Neptune extension)
    - _Requirements: 12.5_

  - [ ] 14.3 Create Neptune data loading script
    - Script to populate Neptune with same route graph data from data/routes.json
    - Use Gremlin insert statements or Neptune bulk loader
    - _Requirements: 12.7_

- [ ] 15. Final checkpoint — Full test suite
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The design uses Python throughout — all implementations use Python 3.11+
- Tasks 13 and 14 are optional extensions per the workshop structure

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1", "4.1"] },
    { "id": 3, "tasks": ["3.2", "4.2", "5.1"] },
    { "id": 4, "tasks": ["5.2", "7.1"] },
    { "id": 5, "tasks": ["7.2", "8.1", "9.1", "10.1"] },
    { "id": 6, "tasks": ["8.2", "9.2", "10.2", "10.3"] },
    { "id": 7, "tasks": ["12.1"] },
    { "id": 8, "tasks": ["12.2", "13.1", "13.2"] },
    { "id": 9, "tasks": ["13.3", "13.4", "14.1"] },
    { "id": 10, "tasks": ["14.2", "14.3"] }
  ]
}
```
