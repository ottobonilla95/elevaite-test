import requests

BASE_URL = "http://localhost:8000"


def test_demo_endpoints():
    print("🧪 Testing Demo Endpoints")
    print("=" * 50)

    # Test 1: Get demo info
    print("\n1. Testing /demo/info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/demo/info")
        if response.status_code == 200:
            data = response.json()
            print(
                f"✅ Success! Found {len(data['available_prompts'])} prompts and {len(data['available_agents'])} agents"
            )
            print(f"   Deployment codes: {data['deployment_codes']}")
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Get demo status
    print("\n2. Testing /demo/status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/demo/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(
                f"   Prompts initialized: {data['prompts_initialized']} ({data['total_prompts']} total)"
            )
            print(
                f"   Agents initialized: {data['agents_initialized']} ({data['total_agents']} total)"
            )
            print(
                f"   Available deployment codes: {data['available_deployment_codes']}"
            )
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Initialize demo data
    print("\n3. Testing /demo/initialize endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/demo/initialize")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"   Message: {data['message']}")
            if "details" in data:
                prompts = data["details"].get("prompts", {})
                agents = data["details"].get("agents", {})
                print(
                    f"   Prompts: {prompts.get('added_count', 0)} added, {prompts.get('skipped_count', 0)} skipped"
                )
                print(
                    f"   Agents: {agents.get('added_count', 0)} added, {agents.get('updated_count', 0)} updated, {agents.get('skipped_count', 0)} skipped"
                )
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 4: Check status after initialization
    print("\n4. Testing /demo/status after initialization...")
    try:
        response = requests.get(f"{BASE_URL}/demo/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(
                f"   Prompts initialized: {data['prompts_initialized']} ({data['total_prompts']} total)"
            )
            print(
                f"   Agents initialized: {data['agents_initialized']} ({data['total_agents']} total)"
            )
            print(
                f"   Available deployment codes: {data['available_deployment_codes']}"
            )
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Demo endpoint testing complete!")
    print("\nTo use the new API endpoints:")
    print("  GET  /demo/info     - Get information about available demo data")
    print("  GET  /demo/status   - Check initialization status")
    print("  POST /demo/initialize - Initialize all demo data")
    print("  POST /demo/initialize/prompts - Initialize only prompts")
    print("  POST /demo/initialize/agents  - Initialize only agents")


if __name__ == "__main__":
    test_demo_endpoints()
