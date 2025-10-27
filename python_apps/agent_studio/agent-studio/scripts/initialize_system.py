#!/usr/bin/env python3
"""
Script to initialize the Agent Studio system via API endpoint.

This script calls the /admin/initialize endpoint to set up:
1. Prompts (required for agents)
2. Tool categories and tools
3. Agents

Usage:
    python scripts/initialize_system.py [--host HOST] [--port PORT]
"""

import argparse
import requests
import json
import sys


def initialize_system(host="localhost", port=8000):
    """Initialize the system via API endpoint."""
    url = f"http://{host}:{port}/admin/initialize"
    
    print(f"Initializing system via {url}...")
    print("=" * 50)
    
    try:
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✅ System initialization completed successfully!")
                print(f"📝 {data.get('message', 'No message')}")
                
                results = data.get("results", {})
                
                # Display prompts results
                if "prompts" in results:
                    prompts = results["prompts"]
                    print(f"\n📋 Prompts: {prompts.get('message', 'No details')}")
                    if prompts.get("details", {}).get("added_prompts"):
                        for prompt in prompts["details"]["added_prompts"]:
                            print(f"   ✓ Added: {prompt}")
                
                # Display tools results
                if "tools" in results:
                    tools = results["tools"]
                    print(f"\n🛠️  Tools: {tools.get('message', 'No details')}")
                    details = tools.get("details", {})
                    if details:
                        print(f"   📁 Categories: {details.get('categories', 0)}")
                        print(f"   🔧 Tools: {details.get('tools', 0)}")
                
                # Display agents results
                if "agents" in results:
                    agents = results["agents"]
                    print(f"\n🤖 Agents: {agents.get('message', 'No details')}")
                    if agents.get("details", {}).get("added_agents"):
                        for agent in agents["details"]["added_agents"]:
                            print(f"   ✓ Added: {agent}")
                
                print("\n" + "=" * 50)
                print("🎉 Initialization complete! The system is ready to use.")
                return True
                
            else:
                print(f"❌ Initialization failed: {data.get('error', 'Unknown error')}")
                return False
                
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed. Is the Agent Studio server running on {host}:{port}?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The initialization might be taking longer than expected.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Initialize Agent Studio system")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    
    args = parser.parse_args()
    
    success = initialize_system(args.host, args.port)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
