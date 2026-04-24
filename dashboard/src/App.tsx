import { useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap, type Edge, type Node } from "reactflow";
import "reactflow/dist/style.css";

import {
  fetchBlastRadius,
  fetchRecentAlerts,
  fetchTopologyGraph,
  fetchTopologySummary,
  openAlertsWebSocket,
} from "./api";
import type { AlertDoc, BlastRadius, GraphEdge, GraphNode, TopologySummary } from "./types";
import "./styles.css";

const LAYERS = ["ALL", "L1", "L2", "L3", "L4", "L5", "L6"] as const;
const SITE_ORDER = ["CHN", "PUN", "MUM", "BLR", "NJ"];
const L1_TYPE_ORDER = ["CR", "FW", "LB", "DS", "AS", "AP", "DNS"];

function healthColor(score: number): string {
  if (score >= 85) return "#22c55e";
  if (score >= 70) return "#f59e0b";
  return "#ef4444";
}

function priorityBadge(indicator: string): string {
  if (indicator === "attack") return "badge b-critical";
  if (indicator === "negative") return "badge b-high";
  return "badge b-info";
}

export default function App() {
  const [summary, setSummary] = useState<TopologySummary | null>(null);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [alerts, setAlerts] = useState<AlertDoc[]>([]);
  const [blast, setBlast] = useState<BlastRadius | null>(null);
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [activeLayer, setActiveLayer] = useState<(typeof LAYERS)[number]>("L1");
  const [showDependencies, setShowDependencies] = useState<boolean>(false);

  useEffect(() => {
    fetchTopologySummary().then(setSummary).catch(() => undefined);
    fetchTopologyGraph()
      .then((g) => {
        setGraphNodes(g.nodes ?? []);
        setGraphEdges(g.edges ?? []);
      })
      .catch(() => undefined);
    fetchRecentAlerts(30).then(setAlerts).catch(() => undefined);
  }, []);

  useEffect(() => {
    const ws = openAlertsWebSocket((alert) => {
      setAlerts((prev) => [alert, ...prev].slice(0, 40));
    });
    return () => ws.close();
  }, []);

  const nodes: Node[] = useMemo(() => {
    const filteredNodes = activeLayer === "ALL" ? graphNodes : graphNodes.filter((n) => n.layer === activeLayer);
    const siteX: Record<string, number> = {};
    SITE_ORDER.forEach((s, i) => {
      siteX[s] = 140 + i * 250;
    });

    const groupOrder: Record<string, number> = {};
    const blastSet = new Set((blast?.impacted_nodes ?? []).map((n) => n.node_id));

    return filteredNodes.map((n, idx) => {
      const yByLayer = { L1: 80, L2: 170, L3: 260, L4: 350, L5: 440, L6: 530 } as Record<string, number>;
      const baseX = siteX[n.site] ?? 100 + ((idx % 6) * 180);
      const baseY = yByLayer[n.layer] ?? 80 + ((idx % 8) * 70);
      const shortCode = n.node_id.split("-")[2] ?? "UNK";
      const l1TypeIdx = L1_TYPE_ORDER.indexOf(shortCode);

      let x = baseX;
      let y = baseY;

      if (n.layer === "L1" && l1TypeIdx >= 0) {
        y = 70 + l1TypeIdx * 70;
      } else {
        const k = `${n.layer}:${n.site}`;
        const order = groupOrder[k] ?? 0;
        groupOrder[k] = order + 1;
        x = baseX + ((order % 3) - 1) * 70;
        y = baseY + Math.floor(order / 3) * 56;
      }

      return {
        id: n.node_id,
        data: { label: `${n.node_id} (${Math.round(n.health_score ?? 0)})` },
        position: { x, y },
        style: {
          border:
            n.node_id === selectedNode
              ? "3px solid #38bdf8"
              : blastSet.has(n.node_id)
                ? "3px solid #f59e0b"
                : `2px solid ${healthColor(n.health_score ?? 0)}`,
          borderRadius: 8,
          padding: 6,
          background: "#111827",
          color: "#e5e7eb",
          fontSize: 11,
          width: 145,
        },
      };
    });
  }, [graphNodes, activeLayer, blast, selectedNode]);

  const edges: Edge[] = useMemo(() => {
    const visibleIds = new Set(nodes.map((n) => n.id));
    const slimView = nodes.length > 60;

    return graphEdges
      .filter((e) => visibleIds.has(e.source_node) && visibleIds.has(e.target_node))
      .filter((e) => showDependencies || !e.link_id.startsWith("DEP-"))
      .map((e) => {
        const isWan = e.link_id.startsWith("WAN-");
        return {
          id: e.link_id,
          source: e.source_node,
          target: e.target_node,
          label: slimView ? undefined : isWan && e.state?.latency_ms ? `${Math.round(e.state.latency_ms)}ms` : e.type,
          style: { stroke: isWan ? "#38bdf8" : "#64748b", opacity: isWan ? 0.9 : 0.45 },
          labelStyle: { fill: "#cbd5e1", fontSize: 10 },
          animated: isWan,
        } as Edge;
      });
  }, [graphEdges, nodes, showDependencies]);

  const edgeStats = useMemo(() => {
    let wan = 0;
    let dep = 0;
    for (const e of edges) {
      if (e.id.startsWith("WAN-")) wan += 1;
      else if (e.id.startsWith("DEP-")) dep += 1;
    }
    return { total: edges.length, wan, dep };
  }, [edges]);

  const runBlast = async (nodeId: string) => {
    setSelectedNode(nodeId);
    const layer = nodeId.split("-")[0] as (typeof LAYERS)[number];
    if (LAYERS.includes(layer)) {
      setActiveLayer(layer);
    }
    const data = await fetchBlastRadius(nodeId);
    setBlast(data);
  };

  return (
    <div className="app">
      <section className="panel">
        <h3 className="title">System Summary</h3>
        <div className="metric"><span>node_registry</span><strong>{summary?.node_registry ?? "-"}</strong></div>
        <div className="metric"><span>component_twins</span><strong>{summary?.component_twins ?? "-"}</strong></div>
        <div className="metric"><span>asset_twins</span><strong>{summary?.asset_twins ?? "-"}</strong></div>
        <div className="metric"><span>wan_links</span><strong>{summary?.wan_links ?? "-"}</strong></div>

        <h3 className="title" style={{ marginTop: 18 }}>Scenario Launcher</h3>
        <button className="btn" onClick={() => runBlast("L1-CHN-FW-01")}>DDoS @ CHN Firewall</button>
        <button className="btn" onClick={() => runBlast("L6-CHN-RACK-01")}>Rack Overheat @ CHN</button>
        <button className="btn" onClick={() => runBlast("L5-CHN-EMP-1042")}>Insider Access @ CHN</button>
        <button className="btn" onClick={() => runBlast("L1-PUN-CR-01")}>WAN/Core Failure @ PUN</button>

        <h3 className="title" style={{ marginTop: 18 }}>Topology Filters</h3>
        <div className="chip-grid">
          {LAYERS.map((layer) => (
            <button
              key={layer}
              className={`chip ${activeLayer === layer ? "chip-active" : ""}`}
              onClick={() => setActiveLayer(layer)}
            >
              {layer}
            </button>
          ))}
        </div>
        <button className="btn" onClick={() => setShowDependencies((v) => !v)}>
          {showDependencies ? "Hide Dependency Edges" : "Show Dependency Edges"}
        </button>
        <div style={{ fontSize: 11, opacity: 0.85, marginTop: 6 }}>
          deps: <strong>{showDependencies ? "ON" : "OFF"}</strong> | edges:{" "}
          <strong>{edgeStats.total}</strong> (wan {edgeStats.wan}, dep {edgeStats.dep})
        </div>

        <h3 className="title" style={{ marginTop: 18 }}>Blast Radius</h3>
        <div style={{ fontSize: 12, marginBottom: 8 }}>node: <strong>{selectedNode || "-"}</strong></div>
        <div style={{ fontSize: 12, marginBottom: 8 }}>
          impacted: <strong>{blast?.impacted_count ?? 0}</strong>
        </div>
        <ul className="list">
          {(blast?.impacted_nodes ?? []).slice(0, 12).map((n) => (
            <li key={n.node_id}>
              <div className="row">
                <span>{n.node_id}</span>
                <span>{n.layer}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h3 className="title">Topology View</h3>
        <div style={{ height: "calc(100% - 30px)" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            fitViewOptions={{ padding: 0.2, minZoom: 0.25, maxZoom: 1.2 }}
            onNodeClick={(_, node) => {
              void runBlast(node.id);
            }}
          >
            <MiniMap />
            <Controls />
            <Background />
          </ReactFlow>
        </div>
      </section>

      <section className="panel">
        <h3 className="title">Live Alerts (WebSocket)</h3>
        <ul className="list">
          {alerts.map((a, i) => (
            <li key={`${a.execution_id ?? "evt"}-${i}`}>
              <div className="row" style={{ marginBottom: 5 }}>
                <strong>{a.node_id}</strong>
                <span className={priorityBadge(a.indicator)}>{a.indicator}</span>
              </div>
              <div className="row">
                <span>{a.layer}</span>
                <span>{a.site ?? "-"}</span>
              </div>
              <div style={{ fontSize: 11, opacity: 0.8 }}>{a.process_id ?? "-"}</div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

