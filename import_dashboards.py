import json
import urllib.request
import urllib.error
import base64
import sys

# Configuration
GRAFANA_URL = "http://localhost:3000"
# Use the password set in previous steps (admin / admin or Mrugakshi1225*)
USERNAME = "admin" 
# Try to detect which password to use or default to standard
PASSWORD = "admin" 

DASHBOARDS = [
    {"id": 14574, "name": "NVIDIA GPU Exporter"},
    {"id": 14694, "name": "Windows Exporter Dashboard"},
    {"id": 10619, "name": "Docker Dashboard"}
]

def get_grafana_headers(user, password):
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def download_dashboard(dashboard_id):
    url = f"https://grafana.com/api/dashboards/{dashboard_id}/revisions/latest/download"
    print(f"Downloading dashboard {dashboard_id} from {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Error downloading dashboard {dashboard_id}: {e}")
        return None

def import_dashboard(dashboard_data, name):
    url = f"{GRAFANA_URL}/api/dashboards/import"
    
    # Payload wrapper
    payload = {
        "dashboard": dashboard_data,
        "overwrite": True
    }
    
    # 1. Datasource fix: Replace input variables with actual datasources if needed
    # (Simple approach: Grafana usually prompts, but API import might fail if inputs match nothing. 
    #  We'll try raw import first.)
    
    headers = get_grafana_headers(USERNAME, PASSWORD)
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"SUCCESS: Imported {name}")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
             print("Authentication failed. Trying alternative password...")
             return False
        print(f"Failed to import {name}: HTTP {e.code} - {e.reason}")
        print(e.read().decode())
    except Exception as e:
        print(f"Failed to import {name}: {e}")
    return False

def main():
    print("dLogs Dashboard Importer")
    print("------------------------")
    
    # Try default password first, then the user's custom one
    global PASSWORD
    passwords_to_try = ["admin", "Mrugakshi1225*"]
    
    for pwd in passwords_to_try:
        PASSWORD = pwd
        print(f"Trying authentication with password: {PASSWORD[:3]}***")
        
        # Test auth with a simple call
        try:
             req = urllib.request.Request(f"{GRAFANA_URL}/api/health", headers=get_grafana_headers(USERNAME, PASSWORD))
             # Just checking if we can import, actually /api/admin/settings or similar needs auth. 
             # Let's just try importing the first dashboard.
             dashboard1 = download_dashboard(DASHBOARDS[0]["id"])
             if dashboard1:
                 if import_dashboard(dashboard1, DASHBOARDS[0]["name"]):
                     # If success, proceed with others using this password
                     for db in DASHBOARDS[1:]:
                         data = download_dashboard(db["id"])
                         if data:
                             import_dashboard(data, db["name"])
                     print("\nAll dashboards processing complete.")
                     return
        except Exception as e:
            print(f"Auth check failed: {e}")
            
    print("\nCould not authenticate with Grafana. Please check if it is running and passwords are correct.")

if __name__ == "__main__":
    main()
