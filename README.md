# StratoTwin  — Complete Digital Twin Agent Architecture

An enterprise-scale digital twin platform monitoring 6 IT layers across 5 sites with 13 intelligent processes, 6 ML models, and autonomous agent orchestration.

## 🏗️ Project Status: PHASE 1 COMPLETE — SKELETON READY

**Current Phase:** 1 of 6
- ✅ Docker infrastructure defined (5 services)
- ✅ Database schemas created
- ✅ Topology data seeded (35 nodes, 5 assets)
- ⏳ Simulators ready for Phase 2

## 🚀 Quick Start (Phase 1 — 10 minutes)

```bash
# Navigate to project root
cd d:\technoverse

# Step 1: Start Docker containers (2 min)
docker compose up -d

# Step 2: Initialize PostgreSQL schema (1 min)
python init_postgres.py

# Step 3: Seed MongoDB topology (2 min)
python seed_mongodb.py

# Step 4: Verify all systems healthy (1 min)
python verify_phase1.py
```

**Expected Result:** 
```
✅ ALL SYSTEMS READY FOR PHASE 1
- 5 Docker containers healthy
- 35 network nodes seeded
- Kafka 9 topics created
- PostgreSQL thresholds loaded
```

## 📊 System Architecture Overview

### Six Layers (35+ Components)
```
L1 Network       — 35 nodes: routers, firewalls, switches, WAN links across 5 sites
L2 Compute       — VMs, Kubernetes nodes, pods (compute capacity)
L3 Application   — Microservices, API gateway, queues, CI/CD
L4 Data          — Kafka, ETL, data lake, warehouse, ML feature store
L5 Workforce     — Employees, skills, projects, attrition risk scoring
L6 Facilities    — UPS, cooling, racks, BMS, physical access
```

### Twin Hierarchy
```
Component Twin (L1-CHN-FW-01)              ← Live state of one device
    ↓
Asset Twin (ASSET-L1-CHN)                 ← Aggregated state per layer-site
    ↓
System Twin (STRATOTWIN-ENTERPRISE-V1)    ← Enterprise-wide health
    ↓
Process Twin (PROC-L1L3-002)              ← Behavioral execution trace
    ↓
Indicator (positive / negative / attack)   ← Automated decision
```

### 13 Processes with Indicators
Each process has a trigger → steps → execution trace → indicator:

| Process ID | Name | Layers | Decision Logic |
|---|---|---|---|
| PROC-L1L2L3-001 | Internal app access | L1, L2, L3 | Threshold + ML |
| PROC-L1L3-002 | Internet-bound traffic | L1, L3 | Threshold + ML + threat intel |
| PROC-L1-003 | WAN site-to-site | L1 | Threshold + BGP whitelist |
| PROC-L1-004 | BGP flap & convergence | L1 | Threshold + flap frequency ML |
| PROC-L1L5-005 | 802.1X device auth | L1, L5 | Threshold + MAC uniqueness |
| PROC-L2L3-006 | Container scheduling | L2, L3 | Threshold + syscall anomaly ML |
| PROC-L2L3-007 | Microservice API chain | L2, L3 | Threshold + API abuse ML |
| PROC-L2L3-008 | CI/CD pipeline | L2, L3 | Threshold + supply chain rules |
| PROC-L3L4-009 | Data pipeline ingestion | L3, L4 | Threshold + record anomaly ML |
| PROC-L4L5-010 | Data lineage & compliance | L4, L5 | Rule-based authorization + ML |
| PROC-L5-011 | Workforce skill matching | L5 | Threshold + attrition risk ML |
| PROC-L6L2-012 | Facilities power/cooling | L6, L2 | Threshold + physical access rules |
| PROC-ALL-013 | Cross-layer propagation | All 6 | LLM + temporal correlation ML |

### 6 ML Models
```
NET-ISO-V1              — Isolation Forest (network anomaly detection)
NET-LSTM-V1             — LSTM (WAN traffic exfiltration)
COMPUTE-SYSCALL-AE-V1   — Autoencoder (container escape detection)
APP-ABUSE-ISO-V1        — Isolation Forest (API abuse)
DATA-ACCESS-VOL-V1      — Z-score (data exfiltration spike)
WRK-ATTRITION-RF-V1     — Random Forest (employee risk scoring)
```

## 📁 Project Structure

```
d:\technoverse\
├── docker-compose.yml          ← 5 services: Kafka, MongoDB, PostgreSQL, Redis, Zookeeper
├── requirements.txt            ← Python dependencies
├── init_postgres.py            ← PostgreSQL schema initialization
├── seed_mongodb.py             ← MongoDB topology seed (35 nodes)
├── verify_phase1.py            ← Health verification script
│
├── README.md                   ← This file
├── README_PHASE1.md            ← Phase 1 detailed guide
├── PHASE1_CHECKLIST.md         ← Step-by-step execution
├── PHASE1_SUMMARY.txt          ← Quick reference
│
├── simulators/                 [PHASE 2]
│   ├── network/main.py
│   ├── compute/main.py
│   ├── application/main.py
│   ├── data/main.py
│   ├── workforce/main.py
│   └── facilities/main.py
│
├── process-engine/             [PHASE 2]
│   └── main.py
│
├── ml-sidecar/                 [PHASE 3]
│   ├── main.py
│   ├── train_models.py
│   └── models/
│
├── api/                        [PHASE 3]
│   └── main.py
│
├── agents/                     [PHASE 4]
│   ├── network_agent.py
│   ├── compute_agent.py
│   ├── application_agent.py
│   ├── data_agent.py
│   ├── workforce_agent.py
│   ├── facilities_agent.py
│   ├── router_agent.py
│   └── synthesis_agent.py
│
└── dashboard/                  [PHASE 5]
    └── React + TypeScript app
```

## 📋 Phase Breakdown

### PHASE 1: Infrastructure & Seeding ✅ COMPLETE
- **Goal:** Get Docker up, seed topology
- **Output:** 5 healthy containers, 35 nodes in MongoDB, schema in PostgreSQL
- **Time:** 10 min
- **Status:** Ready to run

### PHASE 2: Data Pipeline (Coming Next)
- **Goal:** Simulators → Kafka → Process Engine → Alerts
- **Output:** Realistic metrics flowing, process executions executing, indicators firing
- **Time:** 30 min
- **Services:** 7 Python processes (6 simulators + 1 process engine)

Run commands:
```bash
python run_phase2.py
```

Verify (in a separate terminal):
```bash
python verify_phase2.py
```

### PHASE 3: ML + API Layer
- **Goal:** Train models, deploy sidecar, stand up agent tools
- **Output:** ML sidecar on :8090, FastAPI tools on :8080
- **Time:** 20 min
- **Services:** 2 FastAPI apps

Run commands:
```bash
python run_phase3.py
```

Verify (in a separate terminal):
```bash
python verify_phase3.py
```

### PHASE 4: LangGraph Agents
- **Goal:** Build all agents, test orchestration
- **Output:** Agents dispatching in parallel, findings collected, reports synthesized
- **Time:** 40 min
- **Services:** 8 LangGraph agents

Run commands:
```bash
python run_phase4.py
```

Verify (in a separate terminal):
```bash
python verify_phase4.py
```

### PHASE 5: React Dashboard
- **Goal:** Interactive topology visualization
- **Output:** Dashboard at http://localhost:3000
- **Time:** 30 min
- **Services:** 1 React app

Run commands:
```bash
python run_phase5.py
```

Verify:
```bash
python verify_phase5.py
```

### PHASE 6: Superset Agent Builder Integration
- **Goal:** Natural language interface
- **Output:** Agent builder connected to FastAPI tools
- **Time:** 15 min
- **Services:** Superset Agent Builder tooling
- **Note:** This is the "Agent Builder wiring" step from the full architecture plan
  (often counted as Phase 7 in the extended sequence).

Run commands:
```bash
python run_phase6.py
```

Verify:
```bash
python verify_phase6.py
```

Alternative aliases (extended phase numbering):
```bash
python run_phase7.py
python verify_phase7.py
```

## 🔧 Technology Stack

### Infrastructure
- **Orchestration:** Docker Compose
- **Message Queue:** Apache Kafka (9 topics)
- **Databases:**
  - MongoDB (document store for state)
  - PostgreSQL (relational for dependencies, thresholds)
  - Redis (cache for blast-radius queries)
- **Coordination:** Zookeeper (Kafka)

### Backend Services
- **Simulators:** Python (Kafka producers)
- **Process Engine:** Python (Kafka consumer → MongoDB writer)
- **ML Sidecar:** FastAPI + scikit-learn + PyTorch
- **Tool API:** FastAPI
- **Agents:** Python LangGraph + LLaMA 3 (via Ollama)

### Frontend
- **Dashboard:** React 18 + TypeScript
- **Visualization:** React Flow (topology graph), Recharts (metrics)
- **State:** Zustand
- **Real-time:** WebSocket (alert streaming)

### Data Models
**MongoDB Collections:**
- `node_registry` (static config for all nodes)
- `component_twins` (live state + health score)
- `asset_twins` (aggregated L1-per-site)
- `system_twin` (enterprise-wide health)
- `wan_links` (WAN link state)
- `process_definitions` (13 process templates)
- `process_executions` (execution traces)
- `incidents` (cross-layer impact reports)

**PostgreSQL Tables:**
- `cross_layer_dependencies` (complete dependency graph)
- `thresholds` (warn/crit values per node type)
- `ml_models` (model registry)
- `skill_graph` (employee skills)
- `lineage_dag` (data lineage)
- `rack_to_compute_map` (L6→L2 mapping)

## ⚙️ Core Concepts

### Component Twin
Mirrors a single device. Stores:
- Static config (vendor, interfaces, thresholds)
- Live state (CPU, memory, latency, status)
- Health score (0-100, computed from metrics vs thresholds)

### Process Twin
Behavioral model of any multi-step activity:
1. **Trigger:** Event that starts the process
2. **Steps:** Ordered sequence of component interactions
3. **Execution Trace:** Timestamped record of what happened
4. **Indicator:** positive | negative | attack (based on metrics + ML)

### Indicator Classes
- **Positive:** All steps completed within SLA, no anomalies
- **Negative:** SLA breach, metric threshold exceeded, degraded performance
- **Attack:** ML model detected anomaly, security rule triggered, unauthorized action

### Cross-Layer Dependency Graph
Stored in PostgreSQL, enables BFS to compute blast radius:
```
L6-CHN-RACK-01 --powers--> L2-CHN-SRV-01 --hosts--> L2-CHN-VM-01 
  --runs--> L2-CHN-POD-01 --serves--> L3-CHN-SVC-AUTH
```

Query: "If rack L6-CHN-RACK-01 overheats, what services are at risk?"
Answer: L3-CHN-SVC-AUTH, L3-CHN-SVC-ORDER (both depend on VM-01 which is in RACK-01)

## 🎯 Use Cases

### 1. DDoS Attack Detection & Impact Analysis
**Trigger:** SYN flood on L1-CHN-FW-01
**Process:** PROC-L1L3-002 (Internet-bound traffic)
**Decision:** ML (NET-ISO-V1) detects syn_rate spike → **ATTACK indicator**
**Impact:** Router Agent → dispatch NetworkAgent + ApplicationAgent → Synthesis → report all affected services

### 2. Rack Overheating with Automatic Correlation
**Trigger:** L6-CHN-RACK-07 temp > 35°C
**Process:** PROC-L6L2-012 (Facilities power/cooling)
**Decision:** Threshold breach → **NEGATIVE indicator**
**Cross-Layer:** Facilities Agent queries compute nodes in rack, finds 3 VMs with 12 pods
→ Synthesis correlates: "12 microservices at risk due to rack temperature"

### 3. Insider Threat Detection
**Trigger:** L5-CHN-EMP-1042 (attrition_score=0.95) accesses L4-CHN-VAULT-01 (PII dataset) + 10,000 records bulk export
**Process:** PROC-L5-011 (Skill matching) + PROC-L4L5-010 (Lineage & compliance)
**Decision:** ML (WRK-ATTRITION-RF-V1) + cross-layer rule → **ATTACK indicator**
**Report:** "High-risk employee with elevated data access anomaly — potential data exfiltration"

### 4. Natural Language Query
**User:** "What's the blast radius if the Mumbai firewall goes down during peak hours?"
**Router:** Identifies query involves L1 network + L3 applications + time sensitivity
**Dispatch:** NetworkAgent + ApplicationAgent in parallel
**Response:** "45 API endpoints affected, 2M req/sec at risk, estimated 15-min recovery"

## 🔗 API Surface (FastAPI on :8080)

**All requests** go through REST endpoints that agents call:

```
GET  /api/internal/nodes/{node_id}
GET  /api/internal/nodes/{node_id}/history?minutes=60
GET  /api/internal/topology/{layer}
GET  /api/internal/blast-radius/{node_id}?max_depth=6
GET  /api/internal/thresholds/{node_type}
GET  /api/internal/process/executions?process_id=X&limit=10
GET  /api/internal/cross-layer/dependencies/{node_id}
POST /api/internal/alerts
GET  /api/internal/workflow/match
GET  /api/internal/data/lineage/{dataset_id}?direction=downstream
GET  /api/internal/facilities/pue/{site_id}
POST /api/simulate (DDoS, rack-overheat, insider-threat scenarios)
```

## 🧪 Testing Strategy

**Unit Tests:** ML models, threshold logic, BFS traversal
**Integration Tests:** Kafka → MongoDB, process execution completeness
**Simulation Tests:** Inject events (DDoS, link failure, overtemp) and verify agent response
**E2E Tests:** Dashboard query → Router → Agents → Synthesis → Report

## 📖 Documentation

- **README.md** — Overview (this file)
- **docs/STRATOTWIN_BEGINNER_GUIDE.md** — Explains the project from scratch: components, metrics, twins, storage, APIs, Agent Builder, and demo queries
- **docs/IMPLEMENTATION_WALKTHROUGH.md** — Explains what was implemented step by step and how to run/verify the current demo
- **README_PHASE1.md** — Phase 1 deep dive
- **PHASE1_CHECKLIST.md** — Step-by-step execution
- **PHASE1_SUMMARY.txt** — Quick reference

## ⚠️ Important Notes

1. **Windows Environment:** All paths use backslashes (`d:\technoverse\`). PowerShell may require `pwsh` or fall back to `cmd`.

2. **Docker Network:** Containers communicate via internal network. External connections use localhost:port mapping.

3. **Data Seeding Order:** PostgreSQL must be seeded before MongoDB (PostgreSQL is dependency graph source of truth).

4. **ML Models:** Only trained during Phase 3. Phase 1-2 won't have ML predictions — fallback to thresholds.

5. **Agent Scaling:** All 6 agents run in parallel using ThreadPoolExecutor. Per-agent timeout is 5000ms.

## 🚀 Next Steps

1. **Confirm Phase 1 is ready:**
   ```bash
   python verify_phase1.py
   ```

2. **Proceed to Phase 2** when verification shows ✅ ALL SYSTEMS READY

3. **Phase 2 will deliver:** Realistic metrics flowing through Kafka, process executions executing, indicators firing.

---

**Status:** PHASE 1 SKELETON COMPLETE AND READY FOR EXECUTION

**Current Date/Time:** 2026-04-23T08:56:28Z
**Next Review:** After Phase 1 verification success
