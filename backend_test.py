import requests
import sys
import json
from datetime import datetime

class Take2StudioAPITester:
    def __init__(self, base_url="https://66185665-d1f9-4677-b8b5-9e9ea57ab2cb.preview.emergentagent.com"):
        self.base_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.client_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, auth=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except json.JSONDecodeError:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_seed_data(self):
        """Test seeding demo data"""
        print("\n📋 Testing Seed Data Endpoint")
        success, response = self.run_test(
            "Seed Demo Data",
            "POST",
            "seed",
            200,
            auth=False
        )
        return success

    def test_login(self, email="demo@take2studio.com", password="demo123"):
        """Test login and get token"""
        print("\n🔐 Testing Login")
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password},
            auth=False
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"Token received: {self.token[:10]}...")
            return True
        return False

    def test_get_profile(self):
        """Test getting user profile"""
        print("\n👤 Testing Get Profile")
        success, response = self.run_test(
            "Get Profile",
            "GET",
            "auth/me",
            200
        )
        if success:
            self.client_id = response.get('id')
            print(f"Client ID: {self.client_id}")
            print(f"Client Name: {response.get('name')}")
            print(f"Client Email: {response.get('email')}")
        return success

    def test_get_materials(self):
        """Test getting materials"""
        print("\n📦 Testing Get Materials")
        success, response = self.run_test(
            "Get Materials",
            "GET",
            "materials",
            200
        )
        if success:
            print(f"Retrieved {len(response)} materials")
            if len(response) > 0:
                print("Sample material:")
                sample = response[0]
                print(f"  Title: {sample.get('title')}")
                print(f"  Type: {sample.get('type')}")
                print(f"  Status: {sample.get('status')}")
        return success

    def test_get_campaigns(self):
        """Test getting campaigns"""
        print("\n📊 Testing Get Campaigns")
        success, response = self.run_test(
            "Get Campaigns",
            "GET",
            "campaigns",
            200
        )
        if success:
            print(f"Retrieved {len(response)} campaigns")
            if len(response) > 0:
                print("Sample campaign:")
                sample = response[0]
                print(f"  Name: {sample.get('name')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  Impressions: {sample.get('impressions')}")
                print(f"  Clicks: {sample.get('clicks')}")
                print(f"  CTR: {sample.get('ctr')}%")
        return success

def main():
    print("=" * 50)
    print("Take 2 Studio Client Portal API Test")
    print("=" * 50)
    
    # Setup
    tester = Take2StudioAPITester()
    
    # Run tests
    tester.test_seed_data()
    
    if not tester.test_login():
        print("❌ Login failed, stopping tests")
        return 1

    if not tester.test_get_profile():
        print("❌ Profile retrieval failed")
    
    if not tester.test_get_materials():
        print("❌ Materials retrieval failed")
    
    if not tester.test_get_campaigns():
        print("❌ Campaigns retrieval failed")

    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())