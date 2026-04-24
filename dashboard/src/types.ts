export type TopologySummary = {
  node_registry: number;
  component_twins: number;
  asset_twins: number;
  system_twin: number;
  wan_links: number;
};

export type GraphNode = {
  node_id: string;
  layer: string;
  site: string;
  type: string;
  display_name: string;
  health_score: number;
  state?: {
    status?: string;
  };
};

export type GraphEdge = {
  link_id: string;
  source_node: string;
  target_node: string;
  type: string;
  state?: {
    status?: string;
    latency_ms?: number;
  };
};

export type AlertDoc = {
  execution_id?: string;
  node_id: string;
  layer: string;
  site?: string;
  indicator: "positive" | "negative" | "attack";
  process_id?: string;
  created_at?: string;
};

export type BlastRadius = {
  start_node_id: string;
  impacted_count: number;
  impacted_nodes: Array<{
    node_id: string;
    layer: string;
    relationship: string;
  }>;
};

