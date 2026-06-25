# Requirements Document

## Introduction

This document defines the requirements for an American Airlines workshop demo agent built with Strands SDK and deployed to Amazon Bedrock AgentCore. The workshop is a 2–4 hour hands-on session where participants learn to build, test, and deploy AI agents using the Strands SDK, AgentCore Runtime, and AgentCore Gateway. The demo is intentionally simplified — one primary agent (Flight Operations) with an optional second agent (Rebooking) — to keep the learning curve manageable while demonstrating the full local-to-cloud lifecycle. All data is backed by in-memory stores or local JSON files for local development; a local graph database (NetworkX) models flight route relationships for the core session, demonstrating how knowledge graphs enable multi-hop reasoning for scenarios like connection disruption rebooking. No Docker is required for local runs. Participants interact with the agent via a CLI terminal interface. A CDK deployment script enables the final "push to cloud" step demonstrating the dual-mode pattern (local dev → AgentCore Runtime). Participants also explore AgentCore Observability to trace and monitor their deployed agent via CloudWatch. An optional extension module demonstrates how the local graph transitions to Amazon Neptune for production-scale knowledge graph queries. The workshop leverages Kiro Powers (aws-agentcore, strands, cloud-architect) to provide in-IDE guidance throughout.

## Glossary

- **Flight_Ops_Agent**: A Strands Agent handling flight status lookup, flight search, and seat availability queries, deployed locally via uvicorn and remotely on AgentCore Runtime
- **Rebooking_Agent**: An optional second Strands Agent that extends the demo by performing passenger rebooking using Flight_Ops_Agent tools plus passenger management tools
- **Workshop_CLI**: A terminal-based Python script providing an interactive loop for participants to send queries to a locally running agent and observe tool invocations
- **Strands_SDK**: The AWS Strands Agent SDK (Python) providing Agent, Tool, and Model abstractions with native AgentCore Runtime integration
- **AgentCore_Runtime**: Amazon Bedrock AgentCore's serverless hosting environment for agents, providing microVM session isolation, HTTP invocation, and health checks
- **AgentCore_Gateway**: Amazon Bedrock AgentCore's centralized MCP-based tool governance layer providing tool discovery, invocation routing, and access policy enforcement
- **Dual_Mode_Pattern**: The architectural approach where agent source code runs unchanged in both local development (uvicorn/FastAPI) and cloud deployment (AgentCore Runtime) by switching only the entrypoint wrapper
- **Tool_Registry**: A local Python module that registers custom tool functions with the Strands Agent, replaced by AgentCore Gateway MCP connection in cloud mode
- **In_Memory_Data_Store**: A Python module providing flight, passenger, and seat data as dictionaries loaded from a JSON file at startup, requiring no database for local development
- **Workshop_Participant**: A developer attending the American Airlines workshop who builds and deploys the agent following guided steps
- **CDK_Deploy_Script**: An AWS CDK Python application that provisions AgentCore Runtime, Gateway, and supporting resources for cloud deployment of the workshop agent
- **AgentCore_Observability**: Amazon Bedrock AgentCore's built-in observability layer providing session metrics, distributed traces, and spans viewable through the CloudWatch GenAI Observability dashboard
- **ADOT**: AWS Distro for OpenTelemetry — the instrumentation library used to emit traces and spans from AgentCore-hosted agents (automatically injected by the Runtime for deployed agents)
- **Kiro_Power**: A Kiro IDE extension that provides domain-specific AI assistance, documentation access, and guided workflows for a particular AWS service or SDK
- **Local_Graph**: A NetworkX-based in-memory graph representing flight routes, connections, and relationships, used for local development and multi-hop queries without requiring a database server
- **Neptune_Graph**: Amazon Neptune graph database used in the production extension to replace the Local_Graph, enabling scalable graph queries with openCypher or Gremlin
- **Connection_Disruption_Scenario**: A workshop test scenario where a passenger's connecting flight through DFW is delayed or cancelled, requiring the agent to traverse the route graph to identify affected itinerary segments and find alternative connections
- **Knowledge_Graph**: A structured representation of entities (flights, airports, passengers, routes) and their relationships, enabling multi-hop reasoning such as "find all rebooking options given a disrupted connection"

## Requirements

### Requirement 1: Flight Operations Agent — Local Execution

**User Story:** As a Workshop_Participant, I want to build and run a Flight Operations agent locally using Python and uvicorn without Docker, so that I can iterate quickly during the workshop and understand agent behavior before deploying to the cloud.

#### Acceptance Criteria

1. THE Flight_Ops_Agent SHALL run locally as a Python process using uvicorn (or equivalent ASGI server) on the participant's machine without requiring Docker, containers, or external databases
2. WHEN the Flight_Ops_Agent starts locally, THE Flight_Ops_Agent SHALL expose an HTTP endpoint at /invocations for query processing and /ping for health checks, matching the AgentCore Runtime contract
3. WHEN a participant sends a natural language query to the local Flight_Ops_Agent, THE Flight_Ops_Agent SHALL use Amazon Bedrock (Amazon Nova Pro) for inference and invoke registered custom tools to produce a response
4. THE Flight_Ops_Agent SHALL load all flight and seat data from an In_Memory_Data_Store backed by a local JSON file at startup, requiring no network connection beyond Bedrock model access
5. WHEN the Flight_Ops_Agent is started with `RUNTIME_MODE=local`, THE entrypoint SHALL wrap the agent handler in a FastAPI application; WHEN started with `RUNTIME_MODE=aws`, THE entrypoint SHALL wrap the handler in BedrockAgentCoreApp
6. THE Flight_Ops_Agent source code (agent logic, system prompt, tool definitions) SHALL contain zero conditional branches based on RUNTIME_MODE — only the entrypoint wrapper differs between modes

### Requirement 2: Custom Tool Definitions

**User Story:** As a Workshop_Participant, I want to define and register custom tools that the agent can call, so that I understand how agents interact with external capabilities and how tools are governed in production via AgentCore Gateway.

#### Acceptance Criteria

1. THE Flight_Ops_Agent SHALL have a minimum of three custom tools registered: get_flight_status (lookup by flight number and date), search_flights (search by origin, destination, and date), and check_seat_availability (lookup available seats by flight number)
2. WHEN the get_flight_status tool is invoked with a valid flight number and date, THE tool SHALL return flight status including departure time, arrival time, origin, destination, gate, and status (on_time, delayed, cancelled, or boarding)
3. WHEN the search_flights tool is invoked with origin, destination, and date, THE tool SHALL return all matching flights from the In_Memory_Data_Store with their status and available seat count
4. WHEN the check_seat_availability tool is invoked with a valid flight number, THE tool SHALL return a list of available seats with seat class (first, business, economy) and seat identifier
5. WHEN any tool is invoked with invalid or missing parameters, THE tool SHALL return a structured error response with the parameter name and expected format
6. THE custom tools SHALL be defined as Python functions decorated with Strands SDK's @tool decorator, each including a docstring that serves as the tool's description for the LLM
7. WHEN running locally, THE Tool_Registry SHALL provide tools directly to the Strands Agent; WHEN deployed to AWS, THE tools SHALL be accessible through AgentCore_Gateway as registered MCP tools

### Requirement 3: In-Memory Data Store and Local Knowledge Graph

**User Story:** As a Workshop_Participant, I want flight data available from a simple local data layer including a graph of route relationships without setting up a database server, so that I can focus on learning agent and tool patterns while understanding how knowledge graphs enable multi-hop reasoning for connection disruption scenarios.

#### Acceptance Criteria

1. THE In_Memory_Data_Store SHALL load flight data from a JSON file (data/flights.json) at application startup containing a minimum of 20 flights across 8 routes using American Airlines flight number format (AA followed by 1–4 digits)
2. THE In_Memory_Data_Store SHALL include realistic American Airlines hub airports (DFW, CLT, MIA, ORD, PHX, LAX, JFK, PHL) as origins and destinations in the flight data
3. THE In_Memory_Data_Store SHALL include seat availability data for each flight with a minimum of 3 seat classes (first, business, economy) and realistic seat counts per class
4. THE In_Memory_Data_Store SHALL include passenger booking data with PNR codes, passenger names, assigned flights, seat assignments, and multi-leg itineraries (connecting flights) for use by the Rebooking_Agent
5. WHEN the application starts, THE In_Memory_Data_Store SHALL load and parse all JSON data files into Python dictionaries accessible by the tool functions without file I/O on each tool call
6. THE JSON data files SHALL be human-readable and editable, enabling workshop participants to modify test scenarios by hand
7. THE Local_Graph SHALL be implemented using NetworkX, modeling airports as nodes and flight routes as edges with attributes (flight_number, departure_time, arrival_time, status, available_seats)
8. THE Local_Graph SHALL include at least 3 multi-leg itineraries that route through DFW as a connecting hub, enabling the Connection_Disruption_Scenario where a Dallas connection is delayed or cancelled
9. THE Flight_Ops_Agent SHALL include a find_connections tool that traverses the Local_Graph to identify alternative routing options when a connecting flight is disrupted, demonstrating multi-hop graph reasoning
10. THE data files SHALL include at least one pre-configured Connection_Disruption_Scenario: a flight into DFW that is delayed causing a missed connection, with alternative flights available on different routes

### Requirement 4: Workshop CLI Interface

**User Story:** As a Workshop_Participant, I want a simple terminal interface to interact with my locally running agent, so that I can test queries, observe tool calls, and understand the agent's reasoning process during development.

#### Acceptance Criteria

1. THE Workshop_CLI SHALL provide an interactive terminal loop where participants type natural language queries and receive agent responses with visible tool invocation details
2. WHEN the agent invokes a tool during processing, THE Workshop_CLI SHALL display the tool name and input parameters before showing the final response, making the agent's reasoning transparent
3. WHEN a participant types "exit" or "quit", THE Workshop_CLI SHALL terminate the session gracefully
4. THE Workshop_CLI SHALL connect to the locally running Flight_Ops_Agent via HTTP POST to localhost, using the same /invocations endpoint contract as AgentCore Runtime
5. IF the local agent is not running when the Workshop_CLI starts, THEN THE Workshop_CLI SHALL display a clear error message with instructions to start the agent first
6. THE Workshop_CLI SHALL be executable with a single command (e.g., `python cli.py`) with no additional configuration beyond AWS credentials for Bedrock access

### Requirement 5: AgentCore Gateway Integration

**User Story:** As a Workshop_Participant, I want to understand how AgentCore Gateway governs tool access in production, so that I can see the difference between local tool registration and centralized, policy-controlled tool management.

#### Acceptance Criteria

1. WHEN deployed to AWS, THE Flight_Ops_Agent SHALL discover and invoke tools exclusively through AgentCore_Gateway using MCP protocol, replacing the local Tool_Registry
2. THE CDK_Deploy_Script SHALL register all Flight_Ops_Agent tools in the AgentCore_Gateway under a "flight-operations" target with MCP-compliant tool schemas (name, description, inputSchema)
3. WHERE the optional Rebooking_Agent is deployed, THE CDK_Deploy_Script SHALL register rebooking tools under a "passenger-services" target and enforce an Access_Policy granting the Rebooking_Agent access to both flight-operations and passenger-services targets
4. WHERE the optional Rebooking_Agent is deployed, THE CDK_Deploy_Script SHALL enforce an Access_Policy restricting the Flight_Ops_Agent to the flight-operations target only
5. WHEN an agent attempts to invoke a tool it is not authorized to access, THE AgentCore_Gateway SHALL return an authorization error with error code AUTHORIZATION_ERROR and the denied tool name
6. THE workshop materials SHALL include a guided explanation of how Gateway tool governance differs from local tool registration, highlighting access policy enforcement as a production concern

### Requirement 6: AgentCore Runtime Deployment

**User Story:** As a Workshop_Participant, I want to deploy my locally tested agent to AgentCore Runtime using a CDK script, so that I can experience the full local-to-cloud lifecycle and understand the dual-mode deployment pattern.

#### Acceptance Criteria

1. THE CDK_Deploy_Script SHALL deploy the Flight_Ops_Agent to AgentCore_Runtime as a Python application (direct code deploy, not Docker) with a /invocations endpoint and /ping health check
2. WHEN `cdk deploy` is executed, THE CDK_Deploy_Script SHALL provision AgentCore Runtime agent, AgentCore Gateway with tool registrations, and required IAM roles in a single deployment command
3. THE CDK_Deploy_Script SHALL complete deployment within 10 minutes for the single-agent configuration
4. WHEN deployment completes, THE CDK_Deploy_Script SHALL output the Runtime endpoint URL for immediate testing
5. WHEN `cdk destroy` is executed, THE CDK_Deploy_Script SHALL remove all provisioned resources cleanly
6. THE CDK_Deploy_Script SHALL tag all resources with "project" (value: "aa-workshop-agent"), "tier" (value: "workshop"), and "created" (value: ISO 8601 timestamp)
7. THE CDK_Deploy_Script SHALL configure the agent with 1 vCPU and 2 GB memory allocation, sufficient for workshop demonstration workloads

### Requirement 7: Optional Rebooking Agent

**User Story:** As a Workshop_Participant who finishes early or wants to explore multi-agent patterns, I want an optional second agent demonstrating agent collaboration and expanded tool access, so that I can see how AgentCore supports multiple agents with distinct tool permissions.

#### Acceptance Criteria

1. WHERE the Rebooking_Agent is implemented, THE Rebooking_Agent SHALL accept passenger rebooking requests and use both flight search tools (from Flight_Ops_Agent) and passenger management tools (get_booking, update_booking) to complete the rebooking workflow
2. WHERE the Rebooking_Agent is implemented, THE Rebooking_Agent SHALL have two additional custom tools: get_booking (lookup passenger booking by PNR) and update_booking (assign passenger to a new flight and seat)
3. WHERE the Rebooking_Agent is implemented, THE Rebooking_Agent SHALL run locally on a separate port (e.g., 8002) alongside the Flight_Ops_Agent (port 8001) without Docker orchestration
4. WHERE the Rebooking_Agent is implemented, THE CDK_Deploy_Script SHALL deploy both agents to AgentCore_Runtime with distinct Gateway access policies demonstrating least-privilege tool access
5. WHERE the Rebooking_Agent is implemented, THE workshop materials SHALL include a guided exercise showing how the two agents have different tool permissions via Gateway policies

### Requirement 8: Workshop Structure and Prerequisites

**User Story:** As a Workshop_Participant, I want clear prerequisites and step-by-step instructions achievable in 2–4 hours, so that I can complete the workshop successfully regardless of my prior experience with AgentCore or Strands SDK.

#### Acceptance Criteria

1. THE workshop materials SHALL define prerequisites limited to: Python 3.11+, an AWS account with Bedrock Amazon Nova model access, AWS CLI configured with valid credentials, pip/uv for package management, and Kiro IDE installed
2. THE workshop materials SHALL be organized into sequential modules: Setup (15 min), Build Agent (45 min), Add Tools & Graph (30 min), Test Locally with Disruption Scenario (20 min), Deploy to Cloud (30 min), Explore Gateway (20 min), Observe Agent (15 min), Optional Rebooking Agent (40 min), Optional Neptune Extension (30 min)
3. THE workshop setup step SHALL install all dependencies with a single command (e.g., `pip install -e .` or `uv sync`) completing in under 2 minutes on a standard connection
4. WHEN a participant completes the core modules (excluding optional extensions), THE total elapsed time SHALL be achievable within 3 hours including setup
5. THE workshop materials SHALL include a "Learning Objectives" section documenting: building agents with Strands SDK, defining custom tools, using knowledge graphs for multi-hop reasoning, running agents locally, deploying to AgentCore Runtime, understanding Gateway tool governance, monitoring agents with AgentCore Observability, transitioning from local graph to Neptune, and using Kiro for spec-driven development
6. IF a participant encounters an error during any workshop step, THEN THE workshop materials SHALL include a troubleshooting section addressing common issues (missing credentials, model access denied, port conflicts, CloudWatch Transaction Search not enabled, NetworkX import errors)
7. THE workshop setup module SHALL instruct participants to install three Kiro Powers — `aws-agentcore`, `strands`, and `cloud-architect` — and verify each power is active before proceeding to the Build Agent module
8. THE workshop materials SHALL explain the purpose of each Kiro Power: `aws-agentcore` for AgentCore Runtime and Gateway guidance, `strands` for Strands SDK documentation and patterns, and `cloud-architect` for AWS service documentation, pricing, and CDK best practices

### Requirement 9: Dual-Mode Entrypoint Pattern

**User Story:** As a Workshop_Participant, I want to understand the dual-mode pattern where the same agent code runs locally and in the cloud without modification, so that I can apply this pattern in my own projects for fast local development with production deployment to AgentCore.

#### Acceptance Criteria

1. THE Flight_Ops_Agent SHALL use a single `app.py` file containing agent logic (system prompt, tool list, handler function) that is imported unchanged by both the local entrypoint and the AWS entrypoint
2. WHEN `RUNTIME_MODE=local`, THE local entrypoint SHALL import the handler from app.py and wrap it in a FastAPI application served by uvicorn on a configurable port (default 8001)
3. WHEN `RUNTIME_MODE=aws`, THE AWS entrypoint SHALL import the handler from app.py and register it with BedrockAgentCoreApp using @app.entrypoint and @app.ping decorators
4. THE workshop materials SHALL include a diagram or explanation showing how the dual-mode pattern separates concerns: app.py (agent logic) vs entrypoint (transport layer)
5. THE entrypoint files SHALL each be fewer than 30 lines of code, demonstrating that the mode-switch is minimal boilerplate rather than complex conditional logic

### Requirement 10: Project Structure

**User Story:** As a Workshop_Participant, I want a clean, understandable project structure, so that I can navigate the codebase easily and understand where each component lives.

#### Acceptance Criteria

1. THE workshop project SHALL follow this directory structure: src/ (agent code and tools), data/ (JSON data files and route graph), deployment/ (CDK scripts), tests/ (example tests), cli.py (workshop CLI), and README.md (workshop guide)
2. THE src/ directory SHALL contain: agent.py (Flight_Ops_Agent logic), tools.py (custom tool definitions), graph_client.py (graph abstraction layer), data_store.py (in-memory data loader), entrypoint_local.py (FastAPI wrapper), and entrypoint_aws.py (AgentCore Runtime wrapper)
3. WHERE the optional Rebooking_Agent is included, THE src/ directory SHALL additionally contain: rebooking_agent.py (Rebooking_Agent logic) and rebooking_tools.py (passenger management tools)
4. THE project root SHALL contain a pyproject.toml defining all dependencies with pinned versions for reproducible workshop environments (including networkx for local graph operations)
5. THE README.md SHALL serve as the primary workshop guide with all instructions, learning objectives, and module breakdowns included in a single navigable document
6. THE total project file count SHALL remain under 25 files (excluding __pycache__ and .git) to keep the codebase approachable for a workshop setting
7. THE data/ directory SHALL contain flights.json (flight and passenger data) and routes.json (airport nodes and route edges for the knowledge graph)

### Requirement 11: AgentCore Observability

**User Story:** As a Workshop_Participant, I want to observe my deployed agent's behavior through AgentCore's built-in observability features, so that I can understand how to monitor agent health, trace tool invocations, and debug issues in production.

#### Acceptance Criteria

1. THE workshop Observe Agent module SHALL guide participants through enabling CloudWatch Transaction Search in their AWS account as a prerequisite for viewing traces and spans
2. WHEN the Flight_Ops_Agent is deployed to AgentCore_Runtime, THE Runtime SHALL automatically instrument the agent with OpenTelemetry — requiring no additional OTEL libraries or configuration in the agent code
3. THE workshop materials SHALL guide participants to invoke the deployed agent at least 3 times with different queries, then navigate to the CloudWatch GenAI Observability dashboard to view session-level metrics including invocation count, latency, and error rate
4. THE workshop materials SHALL guide participants to view a trace for a specific agent invocation, showing the full execution path: user input → LLM inference → tool invocation(s) → response generation, with timing for each span
5. THE workshop materials SHALL explain the three-tier observability hierarchy (sessions → traces → spans) and how each level provides progressively deeper insight into agent behavior
6. THE CDK_Deploy_Script SHALL ensure the deployed agent's IAM role has permissions to emit traces and metrics to CloudWatch (xray:PutTraceSegments, xray:PutTelemetryRecords, logs:PutLogEvents, cloudwatch:PutMetricData)
7. THE workshop materials SHALL include a guided exercise where participants identify which tool call in a trace took the longest, demonstrating how span-level data supports performance debugging
8. THE Observe Agent module SHALL be completable within 15 minutes, focusing on viewing pre-generated telemetry from prior invocations rather than requiring participants to configure custom instrumentation

### Requirement 12: Knowledge Graph — Local to Neptune Extension

**User Story:** As a Workshop_Participant, I want to see how the local NetworkX graph transitions to Amazon Neptune for production, so that I can understand how graph-powered reasoning scales from a development prototype to a managed cloud service without changing agent logic.

#### Acceptance Criteria

1. THE workshop SHALL implement a graph_client abstraction layer (src/graph_client.py) with a common interface for querying routes, finding connections, and traversing the flight network — backed by NetworkX locally and Neptune in the cloud extension
2. WHEN running locally, THE graph_client SHALL use NetworkX to load the route graph from data/routes.json at startup, providing sub-second multi-hop traversal for the Connection_Disruption_Scenario without requiring any database server or Docker container
3. THE Local_Graph SHALL model entities as nodes (airports, flights, passengers) and relationships as edges (flies_to, connects_through, booked_on), enabling queries like "find all 1-stop alternatives from MIA to JFK avoiding DFW"
4. THE find_connections tool SHALL use the graph_client interface, making it agnostic to whether the underlying graph is NetworkX (local) or Neptune (cloud) — only the graph_client initialization differs between modes
5. WHERE the Neptune extension is implemented, THE CDK_Deploy_Script SHALL provision a Neptune Serverless cluster with a single instance, configured for workshop-scale workloads (2-8 Neptune Capacity Units)
6. WHERE the Neptune extension is implemented, THE graph_client SHALL connect to Neptune using the `gremlinpython` library with openCypher or Gremlin queries that are semantically equivalent to the local NetworkX traversals
7. WHERE the Neptune extension is implemented, THE workshop materials SHALL include a data loading step that populates Neptune with the same route graph data used locally (airports, routes, connections), using Neptune's bulk loader or Gremlin insert statements
8. WHERE the Neptune extension is implemented, THE workshop materials SHALL guide participants through running the same Connection_Disruption_Scenario query against Neptune and comparing the results to the local graph output, demonstrating functional equivalence
9. THE workshop materials SHALL include a "Production Architecture" discussion explaining how the Local_Graph → Neptune pattern mirrors the dual-mode entrypoint pattern: same agent logic, same tool interface, different backing infrastructure for scale
10. THE workshop materials SHALL explain how Neptune integrates with Amazon Bedrock Knowledge Bases for GraphRAG patterns, connecting the workshop exercise to production use cases where agents reason over enterprise knowledge graphs

### Requirement 13: Connection Disruption Scenario

**User Story:** As a Workshop_Participant, I want to test the agent with a realistic flight disruption scenario where a Dallas connection is delayed and I need rebooking options, so that I can see how graph-powered multi-hop reasoning enables intelligent rebooking recommendations.

#### Acceptance Criteria

1. THE flight data SHALL include a specific Connection_Disruption_Scenario: passenger "Alex Johnson" (PNR: AXJN42) booked on AA456 (MIA→DFW, arriving 14:30) connecting to AA789 (DFW→ORD, departing 15:45), where AA456 is delayed 2 hours making the connection impossible
2. WHEN a participant asks "My connection in Dallas is delayed, what are my rebooking options?", THE agent SHALL use the find_connections tool to traverse the route graph and identify alternative paths from MIA to ORD (direct flights or connections through other hubs)
3. THE agent SHALL present rebooking options with flight numbers, departure times, available seats, and estimated arrival times, demonstrating multi-step tool use (graph traversal → seat availability check)
4. THE Connection_Disruption_Scenario SHALL demonstrate multi-hop graph reasoning: the agent must identify the affected itinerary leg, find the final destination, and search for alternative routes — not just alternative direct flights
5. THE workshop materials SHALL walk participants through the Connection_Disruption_Scenario query step by step, explaining which tools are invoked and how the graph traversal identifies alternatives that a simple flight search would miss (e.g., routing through CLT instead of DFW)

