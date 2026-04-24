"""
PostgreSQL Schema Initialization
Run this script to create all tables needed for StratoTwin
"""
import subprocess

INIT_SQL = """

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Cross-layer dependency graph
CREATE TABLE IF NOT EXISTS cross_layer_dependencies (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_node_id  VARCHAR(50) NOT NULL,
  source_layer    VARCHAR(5)  NOT NULL,
  target_node_id  VARCHAR(50) NOT NULL,
  target_layer    VARCHAR(5)  NOT NULL,
  relationship    VARCHAR(50) NOT NULL,
  weight          FLOAT       DEFAULT 1.0,
  topology_version INT        DEFAULT 1,
  created_at      TIMESTAMP   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_source ON cross_layer_dependencies(source_node_id);
CREATE INDEX IF NOT EXISTS idx_target ON cross_layer_dependencies(target_node_id);
CREATE INDEX IF NOT EXISTS idx_composite ON cross_layer_dependencies(source_node_id, target_node_id);

-- Thresholds
CREATE TABLE IF NOT EXISTS thresholds (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_type       VARCHAR(50)  NOT NULL,
  metric_name     VARCHAR(100) NOT NULL,
  warn_value      FLOAT,
  crit_value      FLOAT,
  operator        VARCHAR(10)  NOT NULL,
  time_window_sec INT          DEFAULT 300,
  topology_version INT         DEFAULT 1,
  updated_at      TIMESTAMP    DEFAULT NOW()
);

-- ML model registry
CREATE TABLE IF NOT EXISTS ml_models (
  model_id        VARCHAR(50) PRIMARY KEY,
  model_name      VARCHAR(100),
  layer           VARCHAR(5),
  process_ids     TEXT[],
  algorithm       VARCHAR(50),
  feature_names   TEXT[],
  input_window_sec INT,
  threshold_score FLOAT,
  version         INT DEFAULT 1,
  artifact_path   VARCHAR(200),
  deployed_at     TIMESTAMP,
  retrain_cron    VARCHAR(50)
);

-- Skill graph (L5)
CREATE TABLE IF NOT EXISTS skill_graph (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  employee_id VARCHAR(50) NOT NULL,
  skill_id    VARCHAR(50) NOT NULL,
  level       INT DEFAULT 1,
  certified   BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMP DEFAULT NOW()
);

-- Lineage DAG (L4)
CREATE TABLE IF NOT EXISTS lineage_dag (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_dataset  VARCHAR(100) NOT NULL,
  target_dataset  VARCHAR(100) NOT NULL,
  transform_type  VARCHAR(50),
  created_at      TIMESTAMP DEFAULT NOW()
);

-- Rack to compute map (L6 -> L2)
CREATE TABLE IF NOT EXISTS rack_to_compute_map (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rack_id    VARCHAR(50) NOT NULL,
  server_id  VARCHAR(50) NOT NULL,
  vm_id      VARCHAR(50),
  pod_id     VARCHAR(50),
  site       VARCHAR(10) NOT NULL
);

-- Seed thresholds
DELETE FROM thresholds;
INSERT INTO thresholds (node_type, metric_name, warn_value, crit_value, operator, time_window_sec) VALUES
('core-router',   'cpu_util',         70.0,   90.0,   '>',  300),
('core-router',   'bw_util',          75.0,   90.0,   '>',  300),
('firewall',      'cpu_util',         75.0,   92.0,   '>',  300),
('firewall',      'session_count',    700000, 950000, '>',  300),
('load-balancer', 'active_conn',      70000,  95000,  '>',  300),
('k8s-node',      'cpu_util',         80.0,   95.0,   '>',  300),
('k8s-node',      'memory_util',      80.0,   95.0,   '>',  300),
('kafka-topic',   'consumer_lag',     1000,   100000, '>',  60),
('data-lake',     'disk_util',        75.0,   85.0,   '>',  300),
('ups-unit',      'battery_pct',      50.0,   30.0,   '<',  300),
('server-rack',   'temp_celsius',     30.0,   35.0,   '>',  60),
('wan-link',      'latency_ms',       15.0,   20.0,   '>',  60),
('wan-link',      'packet_loss_pct',  0.5,    1.0,    '>',  60)
ON CONFLICT DO NOTHING;

-- Seed cross-layer dependencies
DELETE FROM cross_layer_dependencies;
INSERT INTO cross_layer_dependencies (source_node_id, source_layer, target_node_id, target_layer, relationship) VALUES
-- CHN
('L6-CHN-RACK-01', 'L6', 'L2-CHN-SRV-01', 'L2', 'powers'),
('L2-CHN-SRV-01', 'L2', 'L2-CHN-VM-01', 'L2', 'hosts'),
('L2-CHN-VM-01', 'L2', 'L2-CHN-POD-01', 'L2', 'runs'),
('L2-CHN-POD-01', 'L2', 'L3-CHN-SVC-AUTH', 'L3', 'serves'),
('L2-CHN-POD-01', 'L2', 'L3-CHN-SVC-ORDER', 'L3', 'serves'),
('L3-CHN-GW-01', 'L3', 'L3-CHN-SVC-AUTH', 'L3', 'routes_to'),
('L3-CHN-GW-01', 'L3', 'L3-CHN-SVC-ORDER', 'L3', 'routes_to'),
('L3-CHN-SVC-ORDER', 'L3', 'L3-CHN-SVC-NOTIFY', 'L3', 'calls'),
('L3-CHN-SVC-ORDER', 'L3', 'L4-CHN-KFK-01', 'L4', 'consumes'),
('L1-CHN-FW-01', 'L1', 'L3-CHN-GW-01', 'L3', 'protects'),
('L1-CHN-LB-01', 'L1', 'L3-CHN-GW-01', 'L3', 'fronts'),
('L5-CHN-EMP-1042', 'L5', 'L4-CHN-VAULT-01', 'L4', 'accesses'),
-- PUN
('L6-PUN-RACK-01', 'L6', 'L2-PUN-SRV-01', 'L2', 'powers'),
('L2-PUN-SRV-01', 'L2', 'L2-PUN-VM-01', 'L2', 'hosts'),
('L2-PUN-VM-01', 'L2', 'L2-PUN-POD-01', 'L2', 'runs'),
('L2-PUN-POD-01', 'L2', 'L3-PUN-SVC-AUTH', 'L3', 'serves'),
('L2-PUN-POD-01', 'L2', 'L3-PUN-SVC-ORDER', 'L3', 'serves'),
('L3-PUN-GW-01', 'L3', 'L3-PUN-SVC-AUTH', 'L3', 'routes_to'),
('L3-PUN-GW-01', 'L3', 'L3-PUN-SVC-ORDER', 'L3', 'routes_to'),
('L3-PUN-SVC-ORDER', 'L3', 'L3-PUN-SVC-NOTIFY', 'L3', 'calls'),
('L3-PUN-SVC-ORDER', 'L3', 'L4-PUN-KFK-01', 'L4', 'consumes'),
('L1-PUN-FW-01', 'L1', 'L3-PUN-GW-01', 'L3', 'protects'),
('L1-PUN-LB-01', 'L1', 'L3-PUN-GW-01', 'L3', 'fronts'),
('L5-PUN-EMP-1042', 'L5', 'L4-PUN-VAULT-01', 'L4', 'accesses'),
-- MUM
('L6-MUM-RACK-01', 'L6', 'L2-MUM-SRV-01', 'L2', 'powers'),
('L2-MUM-SRV-01', 'L2', 'L2-MUM-VM-01', 'L2', 'hosts'),
('L2-MUM-VM-01', 'L2', 'L2-MUM-POD-01', 'L2', 'runs'),
('L2-MUM-POD-01', 'L2', 'L3-MUM-SVC-AUTH', 'L3', 'serves'),
('L2-MUM-POD-01', 'L2', 'L3-MUM-SVC-ORDER', 'L3', 'serves'),
('L3-MUM-GW-01', 'L3', 'L3-MUM-SVC-AUTH', 'L3', 'routes_to'),
('L3-MUM-GW-01', 'L3', 'L3-MUM-SVC-ORDER', 'L3', 'routes_to'),
('L3-MUM-SVC-ORDER', 'L3', 'L3-MUM-SVC-NOTIFY', 'L3', 'calls'),
('L3-MUM-SVC-ORDER', 'L3', 'L4-MUM-KFK-01', 'L4', 'consumes'),
('L1-MUM-FW-01', 'L1', 'L3-MUM-GW-01', 'L3', 'protects'),
('L1-MUM-LB-01', 'L1', 'L3-MUM-GW-01', 'L3', 'fronts'),
('L5-MUM-EMP-1042', 'L5', 'L4-MUM-VAULT-01', 'L4', 'accesses'),
-- BLR
('L6-BLR-RACK-01', 'L6', 'L2-BLR-SRV-01', 'L2', 'powers'),
('L2-BLR-SRV-01', 'L2', 'L2-BLR-VM-01', 'L2', 'hosts'),
('L2-BLR-VM-01', 'L2', 'L2-BLR-POD-01', 'L2', 'runs'),
('L2-BLR-POD-01', 'L2', 'L3-BLR-SVC-AUTH', 'L3', 'serves'),
('L2-BLR-POD-01', 'L2', 'L3-BLR-SVC-ORDER', 'L3', 'serves'),
('L3-BLR-GW-01', 'L3', 'L3-BLR-SVC-AUTH', 'L3', 'routes_to'),
('L3-BLR-GW-01', 'L3', 'L3-BLR-SVC-ORDER', 'L3', 'routes_to'),
('L3-BLR-SVC-ORDER', 'L3', 'L3-BLR-SVC-NOTIFY', 'L3', 'calls'),
('L3-BLR-SVC-ORDER', 'L3', 'L4-BLR-KFK-01', 'L4', 'consumes'),
('L1-BLR-FW-01', 'L1', 'L3-BLR-GW-01', 'L3', 'protects'),
('L1-BLR-LB-01', 'L1', 'L3-BLR-GW-01', 'L3', 'fronts'),
('L5-BLR-EMP-1042', 'L5', 'L4-BLR-VAULT-01', 'L4', 'accesses'),
-- NJ
('L6-NJ-RACK-01', 'L6', 'L2-NJ-SRV-01', 'L2', 'powers'),
('L2-NJ-SRV-01', 'L2', 'L2-NJ-VM-01', 'L2', 'hosts'),
('L2-NJ-VM-01', 'L2', 'L2-NJ-POD-01', 'L2', 'runs'),
('L2-NJ-POD-01', 'L2', 'L3-NJ-SVC-AUTH', 'L3', 'serves'),
('L2-NJ-POD-01', 'L2', 'L3-NJ-SVC-ORDER', 'L3', 'serves'),
('L3-NJ-GW-01', 'L3', 'L3-NJ-SVC-AUTH', 'L3', 'routes_to'),
('L3-NJ-GW-01', 'L3', 'L3-NJ-SVC-ORDER', 'L3', 'routes_to'),
('L3-NJ-SVC-ORDER', 'L3', 'L3-NJ-SVC-NOTIFY', 'L3', 'calls'),
('L3-NJ-SVC-ORDER', 'L3', 'L4-NJ-KFK-01', 'L4', 'consumes'),
('L1-NJ-FW-01', 'L1', 'L3-NJ-GW-01', 'L3', 'protects'),
('L1-NJ-LB-01', 'L1', 'L3-NJ-GW-01', 'L3', 'fronts'),
('L5-NJ-EMP-1042', 'L5', 'L4-NJ-VAULT-01', 'L4', 'accesses')
ON CONFLICT DO NOTHING;

-- Seed rack to compute map
DELETE FROM rack_to_compute_map;
INSERT INTO rack_to_compute_map (rack_id, server_id, vm_id, pod_id, site) VALUES
('L6-CHN-RACK-01', 'L2-CHN-SRV-01', 'L2-CHN-VM-01', 'L2-CHN-POD-01', 'CHN'),
('L6-PUN-RACK-01', 'L2-PUN-SRV-01', 'L2-PUN-VM-01', 'L2-PUN-POD-01', 'PUN'),
('L6-MUM-RACK-01', 'L2-MUM-SRV-01', 'L2-MUM-VM-01', 'L2-MUM-POD-01', 'MUM'),
('L6-BLR-RACK-01', 'L2-BLR-SRV-01', 'L2-BLR-VM-01', 'L2-BLR-POD-01', 'BLR'),
('L6-NJ-RACK-01', 'L2-NJ-SRV-01', 'L2-NJ-VM-01', 'L2-NJ-POD-01', 'NJ');

-- Seed ML model registry
DELETE FROM ml_models;
INSERT INTO ml_models (model_id, model_name, layer, process_ids, algorithm, feature_names, input_window_sec, threshold_score, artifact_path, retrain_cron) VALUES
('NET-ISO-V1', 'Network Anomaly Detector', 'L1', ARRAY['PROC-L1L2L3-001','PROC-L1L3-002'], 'IsolationForest', ARRAY['packet_rate','syn_rate','conn_rate','bw_util','port_scan_score'], 5, 0.85, '/models/NET-ISO-V1.joblib', '0 2 * * 0'),
('NET-LSTM-V1', 'WAN Traffic LSTM', 'L1', ARRAY['PROC-L1L3-002'], 'LSTM', ARRAY['outbound_bytes_per_sec'], 300, 10.0, '/models/NET-LSTM-V1.pt', '0 2 * * 0'),
('COMPUTE-SYSCALL-AE-V1', 'Container Syscall Autoencoder', 'L2', ARRAY['PROC-L2L3-006'], 'Autoencoder', ARRAY['syscall_vector_128dim'], 60, 0.85, '/models/COMPUTE-SYSCALL-AE-V1.pt', '0 3 * * 0'),
('APP-ABUSE-ISO-V1', 'API Abuse Detector', 'L3', ARRAY['PROC-L2L3-007'], 'IsolationForest', ARRAY['rps','unique_endpoints','error_rate','source_ip_count'], 60, 0.85, '/models/APP-ABUSE-ISO-V1.joblib', '0 2 * * 0'),
('DATA-ACCESS-VOL-V1', 'Data Exfiltration Z-score', 'L4', ARRAY['PROC-L4L5-010'], 'ZScore', ARRAY['records_accessed_per_session'], 2592000, 3.0, NULL, NULL),
('WRK-ATTRITION-RF-V1', 'Attrition Risk Random Forest', 'L5', ARRAY['PROC-L5-011','PROC-L4L5-010'], 'RandomForest', ARRAY['tenure_days','bench_duration_days','perf_flag_count_90d','cert_count','project_count_12m','manager_change_flag','salary_band_vs_market','last_promotion_days'], 0, 0.8, '/models/WRK-ATTRITION-RF-V1.joblib', '0 3 1 * *')
ON CONFLICT DO NOTHING;

"""

if __name__ == "__main__":
    import psycopg2
    import sys
    
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=55432,
            database="stratotwin",
            user="stratotwin",
            password="stratotwin_pass"
        )
        cur = conn.cursor()
        
        # Split SQL into individual statements
        for statement in INIT_SQL.split(';'):
            statement = statement.strip()
            if statement:
                cur.execute(statement)
        
        conn.commit()
        cur.close()
        conn.close()
        print("[SUCCESS] PostgreSQL schema initialized successfully")
    except Exception as e:
        error_text = str(e)
        if "password authentication failed" in error_text:
            print("[INFO] Host PostgreSQL auth mismatch detected; using container initialization.")
        else:
            print(f"[WARN] Direct connection failed: {e}")
            print("[INFO] Falling back to in-container initialization via docker compose exec...")
        fallback = subprocess.run(
            [
                "docker", "compose", "exec", "-T", "postgresql",
                "psql", "-U", "stratotwin", "-d", "stratotwin", "-v", "ON_ERROR_STOP=1"
            ],
            input=INIT_SQL,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
        if fallback.returncode == 0:
            print("[SUCCESS] PostgreSQL schema initialized successfully (container fallback)")
            sys.exit(0)
        print("[ERROR] Fallback initialization failed")
        if fallback.stdout:
            print(fallback.stdout)
        if fallback.stderr:
            print(fallback.stderr)
        sys.exit(1)
