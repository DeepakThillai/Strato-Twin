"""
StratoTwin Phase 1 Verification Script
Checks if Docker containers are healthy and databases are initialized
"""

import subprocess
import time
import sys

def run_cmd(cmd, description=""):
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None

def check_docker():
    """Check if Docker is running."""
    result = run_cmd("docker ps")
    if result is None:
        print(" Docker is not running. Please start Docker Desktop or Docker daemon.")
        sys.exit(1)
    print(" Docker is running")

def check_containers():
    """Check if all required containers are running."""
    required = ["zookeeper", "kafka", "mongodb", "postgresql", "redis"]
    print("\n[Checking containers...]")

    table = run_cmd("docker compose ps --format \"{{.Service}}|{{.State}}|{{.Health}}\"")
    if table is None:
        for service in required:
            print(f"   {service} (unknown)")
        return False

    states = {}
    for line in table.splitlines():
        parts = line.split("|")
        if len(parts) >= 2:
            service = parts[0].strip().lower()
            state = parts[1].strip().lower()
            health = parts[2].strip().lower() if len(parts) >= 3 else ""
            states[service] = (state, health)

    for service in required:
        state, health = states.get(service, ("missing", ""))
        if state == "running":
            if health:
                print(f"   {service} (running, health={health})")
            else:
                print(f"   {service} (running)")
        else:
            if state == "missing":
                print(f"   {service} (missing)")
            else:
                print(f"   {service} (state={state})")
            return False
    return True

def check_mongodb():
    """Check MongoDB connectivity and data."""
    print("\n[Checking MongoDB...]")
    try:
        # Try to connect and run a simple query
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
        db = client["stratotwin"]
        db.command("ping")
        
        count = db.node_registry.count_documents({})
        if count > 0:
            print(f"   MongoDB is healthy ({count} nodes in node_registry)")
            return True
        else:
            print(f"    MongoDB is healthy but node_registry is empty (run seed_mongodb.py)")
            return False
    except Exception as e:
        print(f"   MongoDB not ready yet: {str(e)[:50]}")
        return False

def check_postgresql():
    """Check PostgreSQL connectivity and schema."""
    print("\n[Checking PostgreSQL...]")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="127.0.0.1", port=55432,
            database="stratotwin", user="stratotwin", password="stratotwin_pass"
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM thresholds;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if count > 0:
            print(f"   PostgreSQL is healthy ({count} thresholds seeded)")
            return True
        else:
            print(f"   PostgreSQL schema exists but thresholds not seeded (run init_postgres.py)")
            return False
    except Exception as e:
        print(f"   PostgreSQL not ready yet: {str(e)[:50]}")
        return False

def check_kafka():
    """Check Kafka topics."""
    print("\n[Checking Kafka...]")
    expected_topics = {
        "network.node.state",
        "compute.node.state",
        "application.service.state",
        "data.pipeline.state",
        "workforce.state",
        "facilities.sensor.state",
        "stratotwin.alerts",
        "stratotwin.alerts.retry",
        "stratotwin.alerts.dlq",
    }

    # Primary check: host connectivity via kafka-python
    try:
        from kafka import KafkaAdminClient
        admin = KafkaAdminClient(bootstrap_servers="127.0.0.1:9092", request_timeout_ms=4000)
        topics = set(admin.list_topics())
        admin.close()
        if topics:
            missing = expected_topics - topics
            if missing:
                print(f"   Kafka is reachable ({len(topics)} topics, {len(missing)} expected missing)")
            else:
                print(f"   Kafka is healthy ({len(topics)} topics)")
            return True
        print("   Kafka is reachable (0 topics currently visible)")
        return True
    except Exception:
        pass

    # Fallback: in-container topic list
    result = run_cmd("docker compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list 2>nul")
    if result is not None:
        topics = [t for t in result.split("\n") if t.strip()]
        print(f"   Kafka is reachable ({len(topics)} topics)")
        return True

    print("   Kafka not ready yet")
    return False

def main():
    print("=" * 60)
    print("StratoTwin Phase 1 — Infrastructure Verification")
    print("=" * 60)
    
    check_docker()
    
    all_healthy = True
    max_retries = 30  # 2.5 minutes
    retry = 0
    
    while retry < max_retries:
        print(f"\n[Attempt {retry+1}/{max_retries}]")
        
        containers_ok = check_containers()
        mongodb_ok = check_mongodb()
        postgresql_ok = check_postgresql()
        kafka_ok = check_kafka()
        
        if containers_ok and mongodb_ok and postgresql_ok and kafka_ok:
            print("\n" + "=" * 60)
            print(" ALL SYSTEMS READY FOR PHASE 1")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Run: python seed_mongodb.py")
            print("2. Verify data: docker compose exec -T mongodb mongosh stratotwin --eval \"db.node_registry.countDocuments()\"")
            print("3. Proceed to Phase 2")
            return
        
        if retry < max_retries - 1:
            print("\n Waiting 5 seconds before retry...")
            time.sleep(5)
        
        retry += 1
    
    print("\n" + "=" * 60)
    print(" STARTUP TIMEOUT — Infrastructure not ready")
    print("=" * 60)
    print("\nTroubleshooting:")
    print("- Check Docker daemon is running")
    print("- Run: docker compose down && docker compose up -d")
    print("- Check logs: docker compose logs kafka")
    sys.exit(1)

if __name__ == "__main__":
    main()
