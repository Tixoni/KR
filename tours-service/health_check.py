#!/usr/bin/env python3
import sys
import requests
import os

def check_tours_service():
    try:
        # В контейнере используем localhost, т.к. скрипт запускается внутри того же контейнера
        host = os.getenv("HEALTH_CHECK_HOST", "localhost")
        response = requests.get(f"http://{host}:8001/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tours Service: {data['status']}, Database: {data.get('database', 'unknown')}")
            return data['status'] == 'healthy'
        else:
            print(f"❌ Tours Service: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Tours Service: Connection failed - {e}")
        return False

if __name__ == "__main__":
    if check_tours_service():
        sys.exit(0)
    else:
        sys.exit(1)
