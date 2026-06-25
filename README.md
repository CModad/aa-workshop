# AA Agentic AI Workshop

Build and deploy an AI-powered Flight Operations agent using [Strands SDK](https://strandsagents.com) and [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/) — driven by Kiro's spec-driven development workflow.

## The Scenario

A passenger's connecting flight through Dallas is delayed. They ask:

> "My connection in Dallas is delayed. What are my rebooking options to get to Chicago?"

Your agent handles this in a single turn — checking flight status, traversing the route knowledge graph to find alternatives avoiding DFW, and presenting rebooking options with seat availability.

## What You'll Learn

- Build agents with Strands SDK custom `@tool` functions
- Use a knowledge graph (NetworkX) for multi-hop route reasoning
- Run locally with the dual-mode entrypoint pattern (FastAPI ↔ AgentCore Runtime)
- Deploy to AgentCore Runtime via CDK
- Govern tools with AgentCore Gateway access policies
- Monitor with AgentCore Observability (traces, spans, metrics)

## Quick Start

```bash
# Install dependencies
pip install -e .

# Verify AWS access (Nova Pro model required)
aws sts get-caller-identity
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'nova')]"

# Run locally
RUNTIME_MODE=local python -m src.entrypoint_local

# Test with CLI
python cli.py
```

## Workshop Structure

| Module | Duration | Activity |
|--------|----------|----------|
| 1. Kiro Setup | 15 min | Install Powers, dependencies, verify AWS |
| 2. Spec Planning | 30 min | Review requirements → design → tasks, generate scaffolding |
| 3. Build Agent | 45 min | Write tools, graph client, agent definition |
| 4. Test Locally | 20 min | Run agent, test Dallas disruption scenario |
| 5. Run Tests | 15 min | pytest validation |
| 6. Deploy to AWS | 30 min | CDK deploy to AgentCore Runtime |
| 7. Explore Gateway | 20 min | Tool registrations, access policies |
| 8. Observability | 15 min | CloudWatch traces and spans |
| 9. Rebooking Agent | 40 min | *(Optional)* Multi-agent with distinct permissions |
| 10. Neptune Extension | 30 min | *(Optional)* Local graph → Amazon Neptune |

**Total:** ~3 hours core | ~4 hours with extensions

## Project Structure

```
aa-workshop-agent/
├── .kiro/
│   ├── specs/aa-workshop-agent/    # Requirements, design, tasks
│   └── steering/aa-workshop.md     # Project conventions for Kiro
├── src/
│   ├── agent.py                    # Strands Agent (Nova Pro)
│   ├── tools.py                    # @tool functions
│   ├── graph_client.py             # NetworkX / Neptune abstraction
│   ├── data_store.py               # JSON data loader
│   ├── entrypoint_local.py         # FastAPI wrapper
│   └── entrypoint_aws.py           # AgentCore Runtime wrapper
├── data/
│   ├── flights.json                # Flight, seat, passenger data
│   └── routes.json                 # Airport graph (nodes + edges)
├── deployment/
│   └── cdk_app.py                  # CDK stack
├── tests/                          # Unit + property-based tests
├── cli.py                          # Interactive CLI
├── WORKSHOP_GUIDE.md               # Full step-by-step instructions
└── docs/workshop-site/workshop.html # Standalone branded microsite
```

## Prerequisites

- Python 3.11+
- Node.js 20+ (CDK CLI)
- AWS CLI configured with valid credentials
- Amazon Bedrock access for Nova Pro model
- Kiro IDE with Powers: `aws-agentcore`, `strands`, `cloud-architect`

## Resources

- [Workshop Guide](WORKSHOP_GUIDE.md) — Full step-by-step instructions
- [Microsite](docs/workshop-site/workshop.html) — Open in browser (standalone, no server needed)
- [Strands SDK Docs](https://strandsagents.com)
- [AgentCore Docs](https://docs.aws.amazon.com/bedrock-agentcore/)

## Architecture

```
Same agent code → different infrastructure

Local:  agent.py → FastAPI/uvicorn → NetworkX graph → JSON files
Cloud:  agent.py → AgentCore Runtime → Neptune (optional) → Gateway governance
                                                           → CloudWatch traces
```

The dual-mode pattern separates agent logic from transport and data layers. Your code never changes between environments.
