# StratoTwin Implementation Walkthrough

This document explains what was implemented step by step. It is written for someone who wants to understand how the project was built and how the parts fit together.

## Current Result

The current project can:

1. Start infrastructure services with Docker Compose.
2. Initialize PostgreSQL tables.
3. Seed MongoDB with six-layer topology data.
4. Store cross-layer dependency relationships.
5. Serve a FastAPI Tool API on `http://127.0.0.1:8080`.
6. Calculate blast radius for a node.
7. Return topology summary and topology graph.
8. Return recent non-positive indicators from process executions.
9. Generate Agent Builder tool payloads.
10. Register a local MCP bridge for MCP-capable agent clients.

The main tested outputs are:

```json
{
  "node_registry": 165,
  "component_twins": 165,
  "asset_twins": 30,
  "system_twin": 1,
  "wan_links": 6
}
```

and:

```json
{
  "start_node_id": "L6-CHN-RACK-01",
  "impacted_count": 7
}
```

## Step 1. Docker Infrastructure

File:

```text
docker-compose.yml
```

Docker Compose defines the local services needed by StratoTwin.

| Service | Purpose |
|---|---|
| MongoDB | Stores twins and live state |
| PostgreSQL | Stores graph dependencies, thresholds, model registry |
| Redis | Caches blast-radius results |
| Kafka | Event streaming layer |
| Zookeeper | Kafka coordination |

PostgreSQL is exposed on host port `55432` in the current implementation.

## Step 2. PostgreSQL Initialization

File:

```text
init_postgres.py
```

This script creates and seeds relational tables.

Tables created:

| Table | Purpose |
|---|---|
| `cross_layer_dependencies` | Graph edges between nodes |
| `thresholds` | Warning and critical metric thresholds |
| `ml_models` | ML model registry |
| `skill_graph` | Workforce skill data |
| `lineage_dag` | Data lineage graph |
| `rack_to_compute_map` | Facilities to compute mapping |

Important seeded dependency chain:

```text
L6-CHN-RACK-01 -> L2-CHN-SRV-01
L2-CHN-SRV-01 -> L2-CHN-VM-01
L2-CHN-VM-01 -> L2-CHN-POD-01
L2-CHN-POD-01 -> L3-CHN-SVC-AUTH
L2-CHN-POD-01 -> L3-CHN-SVC-ORDER
L3-CHN-SVC-ORDER -> L3-CHN-SVC-NOTIFY
L3-CHN-SVC-ORDER -> L4-CHN-KFK-01
```

That chain is why the rack blast-radius test returns seven impacted nodes.

## Step 3. MongoDB Seeding

File:

```text
seed_mongodb.py
```

This script creates the digital twin data.

It seeds five sites:

```text
CHN, PUN, MUM, BLR, NJ
```

It seeds six layers:

```text
L1, L2, L3, L4, L5, L6
```

The component definitions are:

| Layer | Components Per Site |
|---|---|
| L1 | CR, FW, LB, DS, AS, AP, DNS |
| L2 | SRV, VM, POD, K8S, GPU, EDGE |
| L3 | GW, AUTH, ORDER, NOTIFY, REPORT |
| L4 | KFK, ETL, VAULT, WH, FS |
| L5 | EMP, SKILL, PROJ, TEAM, CERT |
| L6 | RACK, UPS, CRAC, BMS, PDU |

Because the project has five sites, this creates:

```text
33 component types across all layers * 5 sites = 165 component twins
6 layers * 5 sites = 30 asset twins
```

The script also seeds:

```text
1 system twin
6 WAN links
```

## Step 4. Simulators

Folder:

```text
simulators/
```

The simulator files represent how live telemetry would enter the system.

Current simulator folders:

| File | Purpose |
|---|---|
| `simulators/network/main.py` | Network metrics |
| `simulators/compute/main.py` | Compute metrics |
| `simulators/application/main.py` | Application metrics |
| `simulators/data/main.py` | Data pipeline metrics |
| `simulators/workforce/main.py` | Workforce metrics |
| `simulators/facilities/main.py` | Facilities metrics |
| `simulators/base_simulator.py` | Shared simulator helpers |

In a production system, these would be replaced or fed by real telemetry sources.

## Step 5. Process Engine

Folder:

```text
process-engine/
```

The process engine is intended to consume event data, evaluate rules, and write process executions.

In the current demo flow, the most important API for indicators is:

```text
GET /alerts/recent
```

That endpoint reads MongoDB `process_executions` where:

```text
indicator in ["negative", "attack"]
```

This is how the agent can answer questions such as:

```text
Show recent StratoTwin alerts.
What is the latest non-positive indicator?
```

## Step 6. ML Sidecar

Folder:

```text
ml-sidecar/
```

The ML sidecar contains model serving code and serialized model artifacts.

Important files:

| File | Purpose |
|---|---|
| `ml-sidecar/main.py` | FastAPI model service |
| `ml-sidecar/train_models.py` | Training script |
| `ml-sidecar/models/manifest.json` | Model registry manifest |
| `ml-sidecar/models/*.joblib` | Serialized models |

Models in the manifest:

| Model | Purpose |
|---|---|
| `NET-ISO-V1` | Network anomaly detection |
| `NET-LSTM-V1` | WAN traffic anomaly/exfiltration pattern |
| `COMPUTE-SYSCALL-AE-V1` | Container syscall anomaly |
| `APP-ABUSE-ISO-V1` | API abuse detection |
| `DATA-ACCESS-VOL-V1` | Data access volume z-score |
| `WRK-ATTRITION-RF-V1` | Workforce attrition risk |

## Step 7. Tool API

File:

```text
api/main.py
```

This FastAPI app is the main interface used by Agent Builder and Codex.

It runs on:

```text
http://127.0.0.1:8080
```

Implemented endpoints:

| Endpoint | What It Does |
|---|---|
| `GET /health` | Checks MongoDB, PostgreSQL, and Redis |
| `GET /topology` | Returns counts for topology collections |
| `GET /topology/graph` | Returns graph nodes and edges |
| `GET /blast-radius/{node_id}` | Calculates impacted nodes |
| `GET /alerts/recent` | Returns recent negative or attack indicators |
| `POST /query` | Simple natural-language wrapper |
| `WS /ws/alerts` | Alert heartbeat and streaming endpoint |

## Step 8. Blast-Radius Logic

Function:

```text
compute_blast_radius(start_node_id)
```

Location:

```text
api/main.py
```

How it works:

1. Check Redis cache for `blast_radius:{node_id}`.
2. If cached, return the cached result.
3. If not cached, read all edges from PostgreSQL `cross_layer_dependencies`.
4. Build an in-memory graph.
5. Start from the requested node.
6. Traverse outgoing dependencies using breadth-first search.
7. Return impacted nodes and relationships.
8. Cache the result in Redis for 30 seconds.

Example request:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/blast-radius/L6-CHN-RACK-01
```

Example result:

```json
{
  "start_node_id": "L6-CHN-RACK-01",
  "impacted_count": 7,
  "impacted_nodes": [
    {"node_id": "L2-CHN-SRV-01", "layer": "L2", "relationship": "powers"},
    {"node_id": "L2-CHN-VM-01", "layer": "L2", "relationship": "hosts"},
    {"node_id": "L2-CHN-POD-01", "layer": "L2", "relationship": "runs"}
  ]
}
```

## Step 9. Agents

Folder:

```text
agents/
```

The agents represent layer-specific reasoning modules.

Current agent files:

| File | Purpose |
|---|---|
| `network_agent.py` | Network layer reasoning |
| `compute_agent.py` | Compute layer reasoning |
| `application_agent.py` | Application layer reasoning |
| `data_agent.py` | Data layer reasoning |
| `workforce_agent.py` | Workforce layer reasoning |
| `facilities_agent.py` | Facilities layer reasoning |
| `router_agent.py` | Routes questions or alerts to the right agents |
| `synthesis_agent.py` | Summarizes findings |
| `orchestrator.py` | Higher-level orchestration entry point |
| `common.py` | Shared logic |

For the current demo path, the local API is the reliable tool surface. Agent Builder and Codex use the API to answer questions.

## Step 10. Agent Builder Payload

Folder:

```text
superset/
```

Important files:

| File | Purpose |
|---|---|
| `agent_builder_tools.json` | Local tool manifest |
| `agent_builder_import_payload.json` | Generated import payload |

The payload exposes:

| Tool | API Path |
|---|---|
| `stratotwin_query` | `POST /query` |
| `stratotwin_blast_radius` | `GET /blast-radius/{node_id}` |
| `stratotwin_topology_graph` | `GET /topology/graph` |
| `stratotwin_alerts_recent` | `GET /alerts/recent?limit=20` |

`run_phase6.py` validates the API and writes the payload.

`run_phase7.py` is an alias for teams using the extended phase numbering.

## Step 11. MCP Bridge

Folder:

```text
mcp/
```

Files:

| File | Purpose |
|---|---|
| `stratotwin_mcp_server.py` | Local MCP server exposing StratoTwin tools |
| `stratotwin_mcp_server.cmd` | Windows launcher for MCP clients |

The MCP bridge exposes the same four tools:

```text
stratotwin_query
stratotwin_blast_radius
stratotwin_topology_graph
stratotwin_alerts_recent
```

The MCP server was registered in Copilot's MCP configuration. In testing, Copilot discovered it but timed out during tool loading. Codex successfully used the local API fallback, which is the reliable demo path.

## Step 12. Verification Scripts

Verification files:

| File | Purpose |
|---|---|
| `verify_phase1.py` | Checks infrastructure and initial seeds |
| `verify_phase2.py` | Checks data pipeline phase |
| `verify_phase3.py` | Checks API and ML/service layer |
| `verify_phase4.py` | Checks agents |
| `verify_phase5.py` | Checks dashboard |
| `verify_phase6.py` | Checks Agent Builder assets |
| `verify_phase7.py` | Alias for Phase 6 verification |

The latest important verification is:

```powershell
python verify_phase7.py
```

Expected successful output includes:

```text
[API] /health status=200
[API] /query blast status=200
[API] blast impacted_count=7
[API] /query topology status=200
[SUCCESS] PHASE 6 AGENT BUILDER ASSETS READY (FULL MODE)
```

## Step 13. Demo Flow

Use these prompts in Codex or Agent Builder:

```text
Use the local StratoTwin API to show the topology summary.
```

Expected result:

```json
{
  "node_registry": 165,
  "component_twins": 165,
  "asset_twins": 30,
  "system_twin": 1,
  "wan_links": 6
}
```

Second prompt:

```text
Use the local StratoTwin API to calculate blast radius for L6-CHN-RACK-01.
```

Expected result:

```json
{
  "start_node_id": "L6-CHN-RACK-01",
  "impacted_count": 7,
  "impacted_nodes": [
    "L2-CHN-SRV-01",
    "L2-CHN-VM-01",
    "L2-CHN-POD-01",
    "L3-CHN-SVC-AUTH",
    "L3-CHN-SVC-ORDER",
    "L3-CHN-SVC-NOTIFY",
    "L4-CHN-KFK-01"
  ]
}
```

Third prompt:

```text
Use the local StratoTwin API to show recent StratoTwin alerts.
```

Expected result depends on whether process executions with `negative` or `attack` indicators exist.

## Step 14. How To Run The Current Demo

From the project root:

```powershell
cd D:\technoverse
```

Start infrastructure:

```powershell
docker compose up -d
```

Initialize PostgreSQL:

```powershell
python init_postgres.py
```

Seed MongoDB:

```powershell
python seed_mongodb.py
```

Start the API:

```powershell
python run_phase3.py
```

Verify Agent Builder assets:

```powershell
python verify_phase7.py
```

Generate Agent Builder payload:

```powershell
python run_phase7.py
```

## Step 15. What Is Complete

Completed for the current demo scope:

| Area | Status |
|---|---|
| Docker infrastructure | Implemented |
| PostgreSQL schema | Implemented |
| MongoDB six-layer seed | Implemented |
| Cross-layer dependencies | Implemented |
| Blast-radius API | Implemented |
| Topology summary API | Implemented |
| Topology graph API | Implemented |
| Recent alerts API | Implemented |
| Agent Builder payload | Implemented |
| MCP bridge | Implemented and registered |
| Codex/API demo | Verified |

## Step 16. Known Limitations

The current project is a prototype.

Known limitations:

1. Data is simulated, not connected to real enterprise telemetry.
2. The `/query` endpoint supports only a few simple intents: blast radius, topology summary, and alerts.
3. Copilot's MCP client discovered `stratotwin` but timed out during tool loading in one tested session.
4. Codex did not receive the MCP tools in its own session, but successfully used the local API fallback.
5. Full autonomous remediation is not implemented.
6. The dashboard and agents exist as project components, but the most reliable demo path is the FastAPI Tool API.

## Step 17. What To Say In A Project Presentation

StratoTwin is a six-layer enterprise IT digital twin. It models network, compute, application, data, workforce, and facilities components across five sites. MongoDB stores live twin state, PostgreSQL stores cross-layer dependencies, and Redis caches blast-radius queries. A FastAPI Tool API exposes topology, alerts, and impact analysis to Agent Builder or Codex. The demo proves that a facilities failure at `L6-CHN-RACK-01` impacts seven nodes across compute, application, and data layers.
