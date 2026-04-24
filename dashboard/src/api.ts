import type { AlertDoc, BlastRadius, GraphEdge, GraphNode, TopologySummary } from "./types";

const API_BASE = "http://127.0.0.1:8080";

export async function fetchTopologySummary(): Promise<TopologySummary> {
  const res = await fetch(`${API_BASE}/topology`);
  if (!res.ok) throw new Error("topology request failed");
  return res.json();
}

export async function fetchTopologyGraph(): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
  const res = await fetch(`${API_BASE}/topology/graph?limit_nodes=400`);
  if (!res.ok) throw new Error("topology graph request failed");
  return res.json();
}

export async function fetchRecentAlerts(limit = 20): Promise<AlertDoc[]> {
  const res = await fetch(`${API_BASE}/alerts/recent?limit=${limit}`);
  if (!res.ok) throw new Error("alerts request failed");
  const data = await res.json();
  return data.alerts ?? [];
}

export async function fetchBlastRadius(nodeId: string): Promise<BlastRadius> {
  const res = await fetch(`${API_BASE}/blast-radius/${encodeURIComponent(nodeId)}`);
  if (!res.ok) throw new Error("blast radius request failed");
  return res.json();
}

export function openAlertsWebSocket(onAlert: (alert: AlertDoc) => void): WebSocket {
  const ws = new WebSocket("ws://127.0.0.1:8080/ws/alerts");
  ws.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data) as { type: string; payload?: AlertDoc };
      if (msg.type === "alert" && msg.payload) {
        onAlert(msg.payload);
      }
    } catch {
      // ignore malformed messages
    }
  };
  return ws;
}

