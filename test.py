import requests
import os
import json
from dotenv import load_dotenv
load_dotenv(override=True)

def test_courtlistener_api():
    """Simple test to verify CourtListener API access and token."""
    
    # Get API token from environment
    token = os.environ.get('COURTLISTENER_API_TOKEN')
    
    print("🧪 Testing CourtListener API...")
    print("-" * 40)
    
    # Test 1: Check if token exists
    if not token:
        print("❌ No API token found!")
        print("   Please set your token: export COURTLISTENER_API_TOKEN='your_token_here'")
        print("   Get a free token at: https://www.courtlistener.com/api/")
        return False
    
    print(f"✅ Token found: {token[:10]}...")
    
    # Test 2: Simple API call - get Supreme Court info
    print("\n📡 Testing API connection...")
    
    url = "https://www.courtlistener.com/api/rest/v4/courts/"
    headers = {
        'Authorization': f'Token {token}',
        'Accept': 'application/json'
    }
    params = {
        'id': 'scotus',  # Supreme Court
        'fields': 'id,full_name,jurisdiction'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                court = data['results'][0]
                print(f"✅ API Working! Found: {court.get('full_name', 'Unknown')}")
                print(f"   Court ID: {court.get('id', 'N/A')}")
                print(f"   Jurisdiction: {court.get('jurisdiction', 'N/A')}")
                return True
            else:
                print("❌ No results returned")
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication failed - check your token")
            return False
            
        elif response.status_code == 429:
            print("❌ Rate limit exceeded - try again later")
            return False
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def test_search():
    """Test a simple search query."""
    
    token = os.environ.get('COURTLISTENER_API_TOKEN')
    if not token:
        return False
    
    print("\n🔍 Testing search functionality...")
    
    url = "https://www.courtlistener.com/api/rest/v4/search/"
    headers = {
        'Authorization': f'Token {token}',
        'Accept': 'application/json'
    }
    params = {
        'type': 'o',  # opinions
        'q': 'constitutional law',
        'court': 'scotus'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            results = len(data.get('results', []))
            
            print(f"✅ Search working! Found {count} total cases ({results} returned)")
            
            if results > 0:
                first_case = data['results'][0]
                print(f"   Example: {first_case.get('caseName', 'Unknown Case')}")
                print(f"   Court: {first_case.get('court', 'Unknown')}")
                print(f"   Date: {first_case.get('dateFiled', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Search error: {e}")
        return False

def main():
    """Run all tests."""
    print("🏛️  CourtListener API Test Script")
    print("=" * 50)
    
    # Test basic API access
    api_works = test_courtlistener_api()
    
    if api_works:
        # Test search if basic API works
        search_works = test_search()
        
        print("\n" + "=" * 50)
        if api_works and search_works:
            print("🎉 All tests passed! Your API setup is working perfectly.")
            print("📚 You can now use the CourtListener MCP tools.")
        else:
            print("⚠️  Basic API works but search has issues.")
    else:
        print("\n" + "=" * 50)
        print("❌ API test failed. Please check your token and connection.")
    
    print("\n💡 Next steps:")
    print("   1. If tests pass: your server.py should work great!")
    print("   2. If tests fail: check your token and internet connection")
    print("   3. Get help at: https://www.courtlistener.com/help/api/")

if __name__ == "__main__":
    main()