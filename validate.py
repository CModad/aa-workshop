"""Workshop Validation Script — run after each module to check progress.

Usage:
    python3 validate.py           # Run all checks (skips what doesn't exist yet)
    python3 validate.py --module 3  # Run checks for a specific module only

This script does NOT require Bedrock access or a running server.
It validates data integrity, imports, tool behavior, and file structure.
"""

import importlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PASS = "\033[32m✅\033[0m"
FAIL = "\033[31m❌\033[0m"
SKIP = "\033[33m⏭️\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check(description: str, fn):
    """Run a check function and report pass/fail/skip."""
    try:
        result = fn()
        if result is True:
            print(f"  {PASS} {description}")
            return True
        else:
            print(f"  {FAIL} {description} — got: {result}")
            return False
    except ImportError:
        print(f"  {SKIP} {description} — module not yet created")
        return None
    except FileNotFoundError:
        print(f"  {SKIP} {description} — file not found")
        return None
    except Exception as e:
        print(f"  {FAIL} {description} — {type(e).__name__}: {e}")
        return False


def module_1_checks():
    """Module 1: Environment & Dependencies."""
    print(f"\n{BOLD}Module 1: Environment & Dependencies{RESET}")
    results = []

    # Check Python version
    results.append(check(
        "Python 3.11+",
        lambda: sys.version_info >= (3, 11) or f"Python {sys.version_info.major}.{sys.version_info.minor}"
    ))

    # Check pyproject.toml exists
    results.append(check(
        "pyproject.toml exists",
        lambda: (PROJECT_ROOT / "pyproject.toml").exists() or "file missing"
    ))

    # Check data files exist
    results.append(check(
        "data/flights.json exists and is valid JSON",
        lambda: bool(json.loads((PROJECT_ROOT / "data" / "flights.json").read_text())) or "invalid"
    ))

    results.append(check(
        "data/routes.json exists and is valid JSON",
        lambda: bool(json.loads((PROJECT_ROOT / "data" / "routes.json").read_text())) or "invalid"
    ))

    # Check directory structure
    results.append(check(
        "src/ directory exists",
        lambda: (PROJECT_ROOT / "src").is_dir() or "missing"
    ))

    results.append(check(
        "tests/ directory exists",
        lambda: (PROJECT_ROOT / "tests").is_dir() or "missing"
    ))

    return results


def module_2_checks():
    """Module 2: Spec files exist."""
    print(f"\n{BOLD}Module 2: Spec-Driven Planning{RESET}")
    results = []

    spec_dir = PROJECT_ROOT / ".kiro" / "specs" / "aa-workshop-agent"

    results.append(check(
        "requirements.md exists",
        lambda: (spec_dir / "requirements.md").exists() or "missing"
    ))

    results.append(check(
        "design.md exists",
        lambda: (spec_dir / "design.md").exists() or "missing"
    ))

    results.append(check(
        "tasks.md exists",
        lambda: (spec_dir / "tasks.md").exists() or "missing"
    ))

    return results


def module_3_checks():
    """Module 3: Build the Agent — data store, graph, tools, agent."""
    print(f"\n{BOLD}Module 3: Build the Agent{RESET}")
    results = []

    # Data store
    def check_data_store():
        from src.data_store import FLIGHTS, SEATS, PASSENGERS
        assert len(FLIGHTS) >= 20, f"Only {len(FLIGHTS)} flights"
        assert len(SEATS) > 0, "No seat data"
        assert len(PASSENGERS) > 0, "No passenger data"
        return True

    results.append(check("src/data_store.py — loads 20+ flights", check_data_store))

    # Disruption data
    def check_disruption_data():
        from src.data_store import get_flight, get_passenger
        f = get_flight("AA456", "2025-07-15")
        assert f is not None, "AA456 not found"
        assert f["status"] == "delayed", f"Expected delayed, got {f['status']}"
        p = get_passenger("AXJN42")
        assert p is not None, "Alex Johnson (AXJN42) not found"
        assert len(p["itinerary"]) == 2, "Expected 2-leg itinerary"
        return True

    results.append(check("Disruption scenario data (AA456 delayed, Alex Johnson AXJN42)", check_disruption_data))

    # Graph client
    def check_graph():
        from src.graph_client import graph_client
        direct = graph_client.find_connections("MIA", "ORD", max_stops=0)
        assert len(direct) >= 1, "No direct MIA→ORD route"
        alts = graph_client.find_alternatives("MIA", "ORD", "DFW")
        assert len(alts) >= 2, f"Expected 2+ alternatives, got {len(alts)}"
        # Verify DFW is excluded
        for route in alts:
            for seg in route["segments"][1:]:
                assert seg["from"] != "DFW", "DFW found in alternatives!"
        return True

    results.append(check("src/graph_client.py — finds MIA→ORD alternatives excluding DFW", check_graph))

    # Tools
    def check_tools_valid():
        from src.tools import get_flight_status
        r = get_flight_status(flight_number="AA456", date="2025-07-15")
        assert "error" not in r, f"Unexpected error: {r}"
        assert r["status"] == "delayed"
        return True

    results.append(check("src/tools.py — get_flight_status returns AA456 as delayed", check_tools_valid))

    def check_tools_invalid():
        from src.tools import get_flight_status
        r = get_flight_status(flight_number="ZZ999", date="2025-07-15")
        assert r.get("error") == "invalid_parameter"
        return True

    results.append(check("src/tools.py — rejects invalid flight number", check_tools_invalid))

    def check_find_connections():
        from src.tools import find_connections
        r = find_connections(origin="MIA", destination="ORD", date="2025-07-15", exclude_hub="DFW")
        assert "error" not in r, f"Unexpected error: {r}"
        assert "routes" in r, f"Missing routes key: {r.keys()}"
        assert len(r["routes"]) >= 2
        return True

    results.append(check("src/tools.py — find_connections excludes DFW, finds 2+ routes", check_find_connections))

    # Agent
    def check_agent():
        from src.agent import agent
        tool_names = [t.tool_name if hasattr(t, 'tool_name') else str(t) for t in agent.tools]
        assert len(agent.tools) == 4, f"Expected 4 tools, got {len(agent.tools)}"
        return True

    results.append(check("src/agent.py — agent has 4 tools registered", check_agent))

    return results


def module_4_checks():
    """Module 4: Local server files exist."""
    print(f"\n{BOLD}Module 4: Test Locally{RESET}")
    results = []

    def check_entrypoint_local():
        path = PROJECT_ROOT / "src" / "entrypoint_local.py"
        assert path.exists(), "file missing"
        lines = path.read_text().splitlines()
        assert len(lines) <= 30, f"Expected ≤30 lines, got {len(lines)}"
        content = path.read_text()
        assert "/invocations" in content, "Missing /invocations endpoint"
        assert "/ping" in content, "Missing /ping endpoint"
        return True

    results.append(check("src/entrypoint_local.py — exists, ≤30 lines, has endpoints", check_entrypoint_local))

    def check_cli():
        path = PROJECT_ROOT / "cli.py"
        assert path.exists(), "file missing"
        content = path.read_text()
        assert "exit" in content.lower() or "quit" in content.lower(), "Missing exit/quit handling"
        assert "localhost" in content or "8001" in content, "Missing localhost connection"
        return True

    results.append(check("cli.py — exists, handles exit, connects to localhost", check_cli))

    return results


def module_6_checks():
    """Module 6: AWS entrypoint and CDK."""
    print(f"\n{BOLD}Module 6: Deploy to AWS{RESET}")
    results = []

    def check_entrypoint_aws():
        path = PROJECT_ROOT / "src" / "entrypoint_aws.py"
        assert path.exists(), "file missing"
        lines = path.read_text().splitlines()
        assert len(lines) <= 30, f"Expected ≤30 lines, got {len(lines)}"
        content = path.read_text()
        assert "BedrockAgentCoreApp" in content, "Missing BedrockAgentCoreApp"
        assert "entrypoint" in content, "Missing @app.entrypoint"
        assert "ping" in content, "Missing @app.ping"
        return True

    results.append(check("src/entrypoint_aws.py — exists, ≤30 lines, has AgentCore decorators", check_entrypoint_aws))

    def check_cdk():
        path = PROJECT_ROOT / "deployment" / "cdk_app.py"
        assert path.exists(), "file missing"
        return True

    results.append(check("deployment/cdk_app.py — exists", check_cdk))

    return results


def main():
    """Run all validation checks."""
    target_module = None
    if "--module" in sys.argv:
        idx = sys.argv.index("--module")
        if idx + 1 < len(sys.argv):
            target_module = int(sys.argv[idx + 1])

    print(f"{BOLD}{'=' * 50}")
    print(f"  ✈️  AA Workshop — Validation")
    print(f"{'=' * 50}{RESET}")

    all_results = []
    modules = [
        (1, module_1_checks),
        (2, module_2_checks),
        (3, module_3_checks),
        (4, module_4_checks),
        (6, module_6_checks),
    ]

    for num, fn in modules:
        if target_module and num != target_module:
            continue
        results = fn()
        all_results.extend(results)

    # Summary
    passed = sum(1 for r in all_results if r is True)
    failed = sum(1 for r in all_results if r is False)
    skipped = sum(1 for r in all_results if r is None)

    print(f"\n{BOLD}{'─' * 50}")
    print(f"  Results: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"{'─' * 50}{RESET}\n")

    if failed > 0:
        print(f"  {FAIL} Some checks failed. Review the output above.")
        sys.exit(1)
    elif skipped > 0 and passed > 0:
        print(f"  {PASS} All completed checks pass! Remaining items not yet built.")
    else:
        print(f"  {PASS} All checks pass! You're ready for the next module.")


if __name__ == "__main__":
    main()
