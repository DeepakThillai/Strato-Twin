# StratoTwin Beginner Guide

This document explains StratoTwin from scratch. It assumes you do not already know digital twins, infrastructure monitoring, agents, Kafka, MongoDB, PostgreSQL, or blast-radius analysis.

## 1. What StratoTwin Is

StratoTwin is a prototype digital twin for enterprise IT infrastructure.

A digital twin is a software copy of something real. In this project, the "real thing" is an enterprise IT environment: network devices, servers, applications, data pipelines, employees, and data-center facilities.

StratoTwin stores a live model of that environment and lets an agent answer questions such as:

```text
What is the current topology summary?
If L6-CHN-RACK-01 fails, what is impacted?
Show recent StratoTwin alerts.
Which services depend on the Chennai firewall?
```

In this prototype, the data is simulated. In a real deployment, the same structure would receive metrics from systems such as Prometheus, Kubernetes, firewall logs, Kafka, CI/CD logs, badge systems, HR systems, and database audit logs.

## 2. The Big Idea

StratoTwin has three important jobs:

1. Store the current state of IT components.
2. Store dependency relationships between components.
3. Let an agent answer operational questions using that state and dependency graph.

Example:

```text
L6-CHN-RACK-01 powers L2-CHN-SRV-01
L2-CHN-SRV-01 hosts L2-CHN-VM-01
L2-CHN-VM-01 runs L2-CHN-POD-01
L2-CHN-POD-01 serves L3-CHN-SVC-AUTH
L3-CHN-SVC-ORDER consumes L4-CHN-KFK-01
```

If the rack fails, StratoTwin follows those relationships and reports what is affected. This is called blast-radius analysis.

## 3. The Six Layers

StratoTwin divides the enterprise into six layers.

| Layer | Name | What It Represents |
|---|---|---|
| L1 | Network | Routers, firewalls, load balancers, switches, DNS, WAN links |
| L2 | Compute | Physical servers, VMs, Kubernetes pods, GPU instances, edge nodes |
| L3 | Application | API gateways, auth service, order service, reporting service, message services |
| L4 | Data | Kafka, ETL pipelines, compliance vault, warehouse, feature store |
| L5 | Workforce | Employees, skills, projects, teams, certifications |
| L6 | Facilities | Racks, UPS, cooling, BMS controllers, PDUs |

The seeded prototype currently contains:

| Item | Count |
|---|---:|
| Node registry records | 165 |
| Component twins | 165 |
| Asset twins | 30 |
| System twin | 1 |
| WAN links | 6 |

## 4. Sites and Node IDs

The system models five sites:

| Code | Site |
|---|---|
| CHN | Chennai |
| PUN | Pune |
| MUM | Mumbai |
| BLR | Bangalore |
| NJ | New Jersey |

Every node uses a predictable ID:

```text
<layer>-<site>-<type>-<instance>
```

Examples:

```text
L1-CHN-FW-01       Chennai firewall
L2-CHN-SRV-01      Chennai physical server
L3-CHN-SVC-AUTH    Chennai auth service
L4-CHN-KFK-01      Chennai Kafka node/topic
L5-CHN-EMP-1042    Chennai employee node
L6-CHN-RACK-01     Chennai server rack
```

This naming system matters because the agent can understand the layer, site, and component type from the ID.

## 5. Twin Types

StratoTwin uses three structural twin types.

### Component Twin

A component twin represents one component.

Examples:

```text
L1-CHN-FW-01
L2-CHN-SRV-01
L3-CHN-SVC-AUTH
L6-CHN-RACK-01
```

It stores:

| Field | Meaning |
|---|---|
| `node_id` | Unique node name |
| `layer` | L1 to L6 |
| `site` | CHN, PUN, MUM, BLR, NJ |
| `type` | Firewall, server, service, rack, and so on |
| `config` | Static setup such as vendor and thresholds |
| `state` | Current metrics |
| `health_score` | A 0 to 100 score |
| `last_updated` | Last update time |

### Asset Twin

An asset twin groups related component twins by layer and site.

Examples:

```text
ASSET-L1-CHN
ASSET-L2-PUN
ASSET-L6-NJ
```

It stores:

| Field | Meaning |
|---|---|
| `asset_id` | Asset name |
| `component_node_ids` | Nodes inside the asset |
| `aggregated_health_score` | Combined health of the components |
| `health_weights` | Importance of each component |

### System Twin

The system twin represents the whole enterprise.

It stores:

| Field | Meaning |
|---|---|
| `system_id` | Enterprise twin ID |
| `asset_ids` | All asset twins |
| `system_health_score` | Overall health |
| `layer_health_scores` | Health per layer |
| `layer_weights` | Importance of each layer |

## 6. Metrics Used

Metrics are values that describe the current condition of a component.

### Network Metrics

Used for routers, firewalls, load balancers, switches, DNS, and WAN links.

| Metric | Meaning |
|---|---|
| `cpu_util` | CPU usage percentage |
| `bw_util` | Bandwidth usage percentage |
| `latency_ms` | Network delay in milliseconds |
| `session_count` | Firewall active sessions |
| `active_conn` | Load balancer active connections |
| `queries_per_sec` | DNS query rate |
| `packet_loss_pct` | Packet loss percentage |
| `status` | `ok`, `warning`, `critical`, or `down` |

### Compute Metrics

Used for servers, VMs, pods, Kubernetes nodes, GPUs, and edge nodes.

| Metric | Meaning |
|---|---|
| `cpu_util` | CPU usage |
| `memory_util` | Memory usage |
| `disk_util` | Disk usage |
| `status` | Component state |

### Application Metrics

Used for API gateways and services.

| Metric | Meaning |
|---|---|
| `rps` | Requests per second |
| `error_rate` | Percentage of failed requests |
| `p95_latency_ms` | 95th percentile latency |
| `status` | Service state |

### Data Metrics

Used for Kafka, ETL, warehouse, vault, and feature store.

| Metric | Meaning |
|---|---|
| `consumer_lag` | Messages waiting to be processed |
| `etl_duration_sec` | ETL job duration |
| `throughput_rpm` | Records per minute |
| `status` | Data component state |

### Workforce Metrics

Used for employees, skills, teams, projects, and certifications.

| Metric | Meaning |
|---|---|
| `active_staff` | Number of active staff |
| `bench_duration_days` | Time unallocated |
| `attrition_risk_score` | Risk score from 0 to 1 |
| `status` | Workforce component state |

### Facilities Metrics

Used for racks, UPS, cooling, BMS, and PDU.

| Metric | Meaning |
|---|---|
| `rack_temp_celsius` | Rack temperature |
| `ups_battery_pct` | UPS battery percentage |
| `cooling_status` | Cooling condition |
| `status` | Facilities component state |

## 7. Indicators

An indicator is the result of evaluating metrics or a process.

StratoTwin uses three indicator classes:

| Indicator | Meaning |
|---|---|
| `positive` | Everything is healthy or within threshold |
| `negative` | Something is degraded or failing |
| `attack` | A security rule or anomaly model detected suspicious behavior |

Examples:

```text
positive: API latency is normal and response code is 200
negative: Rack temperature is above 35 C
attack: Firewall traffic pattern looks like a DDoS
```

## 8. Processes

A process is an IT activity that happens across components.

Examples:

| Process | Real-World Meaning |
|---|---|
| Internal application access | A user accesses an internal app |
| Internet-bound traffic | A service connects to an external IP |
| WAN site-to-site communication | Traffic moves between sites |
| Container scheduling | Kubernetes schedules a pod |
| Microservice API chain | API Gateway calls Auth, Order, and downstream services |
| Data pipeline ingestion | Application publishes to Kafka, ETL writes to warehouse |
| Facilities power/cooling | BMS checks rack temperature and UPS state |

In this prototype, the process engine and alerts are simplified, but the project keeps the same structure a production system would use.

## 9. How Components Are Connected

Connections are stored in PostgreSQL in `cross_layer_dependencies`.

Each row says:

```text
source node -> relationship -> target node
```

Examples:

```text
L6-CHN-RACK-01 -> powers -> L2-CHN-SRV-01
L2-CHN-SRV-01 -> hosts -> L2-CHN-VM-01
L2-CHN-VM-01 -> runs -> L2-CHN-POD-01
L2-CHN-POD-01 -> serves -> L3-CHN-SVC-AUTH
L3-CHN-SVC-ORDER -> consumes -> L4-CHN-KFK-01
```

The blast-radius engine reads these relationships and performs a graph traversal.

## 10. Storage

StratoTwin uses three main storage systems.

### MongoDB

MongoDB stores document-style data.

Important collections:

| Collection | Purpose |
|---|---|
| `node_registry` | Static node metadata |
| `component_twins` | Current state of each component |
| `asset_twins` | Grouped assets by layer and site |
| `system_twin` | Enterprise-level twin |
| `wan_links` | WAN link details |
| `process_executions` | Recent process outcomes and indicators |
| `incidents` | Incident reports |

### PostgreSQL

PostgreSQL stores structured relational data.

Important tables:

| Table | Purpose |
|---|---|
| `cross_layer_dependencies` | Graph edges for blast radius |
| `thresholds` | Warning and critical values |
| `ml_models` | Model registry |
| `skill_graph` | Workforce skill relationships |
| `lineage_dag` | Data lineage |
| `rack_to_compute_map` | Rack to server to VM to pod map |

### Redis

Redis stores short-lived cached results.

Example:

```text
blast_radius:L6-CHN-RACK-01
```

This avoids recalculating the same blast radius repeatedly.

## 11. API Layer

The FastAPI service runs locally on:

```text
http://127.0.0.1:8080
```

Important endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Check MongoDB, PostgreSQL, and Redis |
| `GET /topology` | Return topology counts |
| `GET /topology/graph` | Return graph nodes and edges |
| `GET /blast-radius/{node_id}` | Return impacted nodes |
| `GET /alerts/recent` | Return recent negative or attack indicators |
| `POST /query` | Simple natural-language wrapper for supported questions |
| `WS /ws/alerts` | WebSocket stream for alerts |

## 12. Agent Builder

Agent Builder is the natural-language interface.

The project generates:

```text
superset/agent_builder_import_payload.json
```

That payload defines tools such as:

| Tool | Purpose |
|---|---|
| `stratotwin_query` | Ask a general supported question |
| `stratotwin_blast_radius` | Calculate blast radius |
| `stratotwin_topology_graph` | Fetch topology graph |
| `stratotwin_alerts_recent` | Fetch recent alerts |

There is also an MCP bridge:

```text
mcp/stratotwin_mcp_server.py
mcp/stratotwin_mcp_server.cmd
```

The MCP bridge exposes the same StratoTwin API as tools for MCP-capable agent clients.

## 13. Example Query

Question:

```text
If L6-CHN-RACK-01 fails, what is impacted?
```

Answer:

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

This means a rack failure can affect compute, application, and data layers.

## 14. What Is Simulated

The prototype uses simulated infrastructure state. That means:

```text
The servers are not real physical servers.
The rack temperature is not from a real sensor.
The application latency is generated data.
The Kafka and workforce data are modeled for demonstration.
```

The architecture is still meaningful because production telemetry can replace the simulator later.

## 15. How To Explain The Project In One Minute

StratoTwin is an AI-assisted digital twin for enterprise IT. It stores a simulated model of six IT layers: network, compute, application, data, workforce, and facilities. Each component has metrics and health state. Dependencies between components are stored as a graph in PostgreSQL. When a component fails or an indicator appears, the system can calculate blast radius across layers and explain what is affected. Agent Builder or Codex can ask the local API questions such as topology summary, recent alerts, and impact analysis.
