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
        self.material_id = None
        self.document_id = None
        self.category_id = None
        self.user_type = None  # 'client' or 'admin'

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

    def test_login(self, email="demo@take2studio.com", password="demo123", user_type="client"):
        """Test login and get token"""
        print(f"\n🔐 Testing {user_type.capitalize()} Login")
        endpoint = "admin/auth/login" if user_type == "admin" else "auth/login"
        success, response = self.run_test(
            f"{user_type.capitalize()} Login",
            "POST",
            endpoint,
            200,
            data={"email": email, "password": password},
            auth=False
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_type = user_type
            print(f"Token received: {self.token[:10]}...")
            return True
        return False

    def test_get_profile(self):
        """Test getting user profile"""
        print(f"\n👤 Testing Get {self.user_type.capitalize()} Profile")
        endpoint = "admin/auth/me" if self.user_type == "admin" else "auth/me"
        success, response = self.run_test(
            f"Get {self.user_type.capitalize()} Profile",
            "GET",
            endpoint,
            200
        )
        if success:
            self.client_id = response.get('id')
            print(f"User ID: {self.client_id}")
            print(f"User Name: {response.get('name')}")
            print(f"User Email: {response.get('email')}")
            if self.user_type == "admin":
                print(f"User Role: {response.get('role')}")
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
                self.material_id = sample.get('id')
                print(f"  ID: {self.material_id}")
                print(f"  Title: {sample.get('title')}")
                print(f"  Type: {sample.get('type')}")
                print(f"  Status: {sample.get('status')}")
        return success

    def test_get_material_by_id(self):
        """Test getting a specific material by ID"""
        if not self.material_id:
            print("❌ No material ID available for testing")
            return False
            
        print("\n📦 Testing Get Material by ID")
        success, response = self.run_test(
            f"Get Material {self.material_id}",
            "GET",
            f"materials/{self.material_id}",
            200
        )
        if success:
            print(f"Retrieved material: {response.get('title')}")
        return success

    def test_get_material_comments(self):
        """Test getting comments for a material"""
        if not self.material_id:
            print("❌ No material ID available for testing")
            return False
            
        print("\n💬 Testing Get Material Comments")
        success, response = self.run_test(
            f"Get Comments for Material {self.material_id}",
            "GET",
            f"materials/{self.material_id}/comments",
            200
        )
        if success:
            print(f"Retrieved {len(response)} comments")
        return success

    def test_add_material_comment(self):
        """Test adding a comment to a material"""
        if not self.material_id:
            print("❌ No material ID available for testing")
            return False
            
        print("\n💬 Testing Add Material Comment")
        success, response = self.run_test(
            f"Add Comment to Material {self.material_id}",
            "POST",
            f"materials/{self.material_id}/comments",
            200,
            data={"text": f"Test comment added at {datetime.now().isoformat()}"}
        )
        if success:
            print(f"Comment added: {response.get('text')}")
        return success

    def test_approve_material(self):
        """Test approving a material"""
        if not self.material_id:
            print("❌ No material ID available for testing")
            return False
            
        print("\n✅ Testing Approve Material")
        success, response = self.run_test(
            f"Approve Material {self.material_id}",
            "POST",
            f"materials/{self.material_id}/approve",
            200
        )
        if success:
            print(f"Material approved: {response.get('message')}")
        return success

    def test_request_revision(self):
        """Test requesting revision for a material"""
        if not self.material_id:
            print("❌ No material ID available for testing")
            return False
            
        print("\n🔄 Testing Request Revision")
        success, response = self.run_test(
            f"Request Revision for Material {self.material_id}",
            "POST",
            f"materials/{self.material_id}/request-revision",
            200,
            data={"text": f"Please revise this material - test at {datetime.now().isoformat()}"}
        )
        if success:
            print(f"Revision requested: {response.get('message')}")
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

    def test_get_document_categories(self):
        """Test getting document categories"""
        print("\n📁 Testing Get Document Categories")
        success, response = self.run_test(
            "Get Document Categories",
            "GET",
            "documents/categories",
            200
        )
        if success:
            print(f"Retrieved {len(response)} document categories")
            if len(response) > 0:
                print("Sample category:")
                sample = response[0]
                self.category_id = sample.get('id')
                print(f"  ID: {self.category_id}")
                print(f"  Name: {sample.get('name')}")
                print(f"  Description: {sample.get('description')}")
        return success

    def test_get_documents_by_category(self):
        """Test getting documents by category"""
        if not self.category_id:
            print("❌ No category ID available for testing")
            return False
            
        print("\n📄 Testing Get Documents by Category")
        success, response = self.run_test(
            f"Get Documents for Category {self.category_id}",
            "GET",
            f"documents/{self.category_id}",
            200
        )
        if success:
            print(f"Retrieved {len(response)} documents")
            if len(response) > 0:
                print("Sample document:")
                sample = response[0]
                self.document_id = sample.get('id')
                print(f"  ID: {self.document_id}")
                print(f"  Name: {sample.get('name')}")
                print(f"  Type: {sample.get('type')}")
                print(f"  Size: {sample.get('size')}")
        return success

    def test_download_document(self):
        """Test document download endpoint"""
        if not self.document_id:
            print("❌ No document ID available for testing")
            return False
            
        print("\n📥 Testing Document Download")
        success, response = self.run_test(
            f"Download Document {self.document_id}",
            "GET",
            f"documents/{self.document_id}/download",
            200
        )
        if success:
            print(f"Document download URL: {response.get('download_url')}")
        return success
        
    # =================== ADMIN API TESTS ===================
    
    def test_admin_dashboard_stats(self):
        """Test getting admin dashboard stats"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n📊 Testing Admin Dashboard Stats")
        success, response = self.run_test(
            "Get Admin Dashboard Stats",
            "GET",
            "admin/dashboard/stats",
            200
        )
        if success:
            print(f"Total Clients: {response.get('total_clients')}")
            print(f"Active Clients: {response.get('active_clients')}")
            print(f"Total Materials: {response.get('total_materials')}")
            print(f"Pending Approvals: {response.get('pending_approvals')}")
            print(f"Active Campaigns: {response.get('active_campaigns')}")
        return success
        
    def test_admin_get_clients(self):
        """Test getting all clients as admin"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n👥 Testing Admin Get All Clients")
        success, response = self.run_test(
            "Get All Clients",
            "GET",
            "admin/clients",
            200
        )
        if success:
            print(f"Retrieved {len(response)} clients")
            if len(response) > 0:
                print("Sample client:")
                sample = response[0]
                print(f"  ID: {sample.get('id')}")
                print(f"  Name: {sample.get('name')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  Materials Count: {sample.get('materials_count')}")
                print(f"  Pending Approvals: {sample.get('pending_approvals')}")
        return success
        
    def test_admin_get_materials(self):
        """Test getting all materials as admin"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n📦 Testing Admin Get All Materials")
        success, response = self.run_test(
            "Get All Materials",
            "GET",
            "admin/materials",
            200
        )
        if success:
            print(f"Retrieved {len(response)} materials")
            if len(response) > 0:
                print("Sample material:")
                sample = response[0]
                self.material_id = sample.get('id')
                print(f"  ID: {self.material_id}")
                print(f"  Title: {sample.get('title')}")
                print(f"  Client Name: {sample.get('client_name')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  Type: {sample.get('type')}")
                if sample.get('tags'):
                    print(f"  Tags: {', '.join(sample.get('tags'))}")
        return success
        
    def test_admin_get_campaigns(self):
        """Test getting all campaigns as admin"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n📊 Testing Admin Get All Campaigns")
        success, response = self.run_test(
            "Get All Campaigns",
            "GET",
            "admin/campaigns",
            200
        )
        if success:
            print(f"Retrieved {len(response)} campaigns")
            if len(response) > 0:
                print("Sample campaign:")
                sample = response[0]
                print(f"  Name: {sample.get('name')}")
                print(f"  Client Name: {sample.get('client_name')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  CTR: {sample.get('ctr')}%")
                print(f"  Spend: {sample.get('spend')}")
        return success
        
    def test_admin_get_documents(self):
        """Test getting all documents as admin"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n📄 Testing Admin Get All Documents")
        success, response = self.run_test(
            "Get All Documents",
            "GET",
            "admin/documents",
            200
        )
        if success:
            print(f"Retrieved {len(response)} documents")
            if len(response) > 0:
                print("Sample document:")
                sample = response[0]
                print(f"  ID: {sample.get('id')}")
                print(f"  Name: {sample.get('name')}")
                print(f"  Client Name: {sample.get('client_name')}")
                print(f"  Category: {sample.get('category')}")
        return success
        
    def test_admin_create_client(self):
        """Test creating a new client as admin"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n➕ Testing Admin Create Client")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        client_data = {
            "name": f"Test Client {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "test123",
            "contact_person": "Test Contact",
            "project_type": "marketing_digital"
        }
        
        success, response = self.run_test(
            "Create Client",
            "POST",
            "admin/clients",
            200,
            data=client_data
        )
        if success:
            print(f"Created client: {response.get('name')}")
            print(f"Client ID: {response.get('id')}")
            self.client_id = response.get('id')
        return success
        
    def test_admin_create_material(self):
        """Test creating a new material as admin"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        if not self.client_id:
            print("❌ No client ID available for testing")
            return False
            
        print("\n➕ Testing Admin Create Material")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        scheduled_date = (datetime.now()).isoformat()
        
        material_data = {
            "client_id": self.client_id,
            "title": f"Test Material {timestamp}",
            "description": "This is a test material created via API",
            "type": "photo",
            "scheduled_date": scheduled_date,
            "tags": ["test", "api", "automation"]
        }
        
        success, response = self.run_test(
            "Create Material",
            "POST",
            "admin/materials",
            200,
            data=material_data
        )
        if success:
            print(f"Created material: {response.get('title')}")
            print(f"Material ID: {response.get('id')}")
            self.material_id = response.get('id')
        return success
        
    def test_admin_update_material(self):
        """Test updating a material as admin"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        if not self.material_id:
            print("❌ No material ID available for testing")
            return False
            
        print("\n✏️ Testing Admin Update Material")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        update_data = {
            "title": f"Updated Material {timestamp}",
            "status": "in_production",
            "tags": ["updated", "test", "api"]
        }
        
        success, response = self.run_test(
            "Update Material",
            "PUT",
            f"admin/materials/{self.material_id}",
            200,
            data=update_data
        )
        if success:
            print(f"Updated material: {response.get('title')}")
            print(f"New status: {response.get('status')}")
            print(f"Tags: {', '.join(response.get('tags', []))}")
        return success
        
    def test_admin_material_filters(self):
        """Test getting material filters"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n🔍 Testing Admin Material Filters")
        success, response = self.run_test(
            "Get Material Filters",
            "GET",
            "admin/materials/filters",
            200
        )
        if success:
            print(f"Retrieved filter options:")
            if 'clients' in response:
                print(f"  Clients: {len(response['clients'])}")
            if 'statuses' in response:
                print(f"  Statuses: {[status['_id'] for status in response['statuses']]}")
            if 'types' in response:
                print(f"  Types: {[type['_id'] for type in response['types']]}")
        return success
        
    def test_admin_material_search(self):
        """Test searching materials"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n🔎 Testing Admin Material Search")
        success, response = self.run_test(
            "Search Materials",
            "GET",
            "admin/materials/search",
            200
        )
        if success:
            print(f"Search results: {response.get('total')} materials found")
            print(f"Page: {response.get('page')} of {response.get('total_pages')}")
            if response.get('materials') and len(response.get('materials')) > 0:
                print(f"First result: {response['materials'][0].get('title')}")
        return success
        
    def test_admin_material_tags_autocomplete(self):
        """Test material tags autocomplete"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        print("\n🏷️ Testing Admin Material Tags Autocomplete")
        success, response = self.run_test(
            "Tags Autocomplete",
            "GET",
            "admin/materials/tags/autocomplete?q=te",
            200
        )
        if success:
            print(f"Retrieved {len(response)} tag suggestions")
            if len(response) > 0:
                for tag in response:
                    print(f"  Tag: {tag.get('tag')} (Count: {tag.get('count')})")
        return success
        
    def test_admin_bulk_actions(self):
        """Test bulk actions on materials"""
        if self.user_type != "admin":
            print("❌ Not logged in as admin")
            return False
            
        if not self.material_id:
            print("❌ No material ID available for testing")
            return False
            
        print("\n📦 Testing Admin Bulk Actions")
        success, response = self.run_test(
            "Bulk Update Status",
            "POST",
            "admin/materials/bulk-actions",
            200,
            data={
                "action": "update_status",
                "material_ids": [self.material_id],
                "new_status": "awaiting_approval"
            }
        )
        if success:
            print(f"Bulk action result: {response.get('message')}")
        return success

def main():
    print("=" * 50)
    print("Take 2 Studio Client Portal API Test")
    print("=" * 50)
    
    # Setup
    tester = Take2StudioAPITester()
    
    # Run tests
    tester.test_seed_data()
    
    # =================== CLIENT TESTS ===================
    print("\n" + "=" * 50)
    print("CLIENT PORTAL TESTS")
    print("=" * 50)
    
    if not tester.test_login(email="demo@take2studio.com", password="demo123", user_type="client"):
        print("❌ Client login failed, stopping client tests")
    else:
        if not tester.test_get_profile():
            print("❌ Client profile retrieval failed")
        
        # Materials tests
        if not tester.test_get_materials():
            print("❌ Materials retrieval failed")
        else:
            tester.test_get_material_by_id()
            tester.test_get_material_comments()
            tester.test_add_material_comment()
            tester.test_approve_material()
            tester.test_request_revision()
        
        # Campaigns tests
        if not tester.test_get_campaigns():
            print("❌ Campaigns retrieval failed")
        
        # Documents tests
        if not tester.test_get_document_categories():
            print("❌ Document categories retrieval failed")
        else:
            tester.test_get_documents_by_category()
            tester.test_download_document()
    
    # =================== ADMIN TESTS ===================
    print("\n" + "=" * 50)
    print("ADMIN DASHBOARD TESTS")
    print("=" * 50)
    
    if not tester.test_login(email="admin@take2studio.com", password="admin123", user_type="admin"):
        print("❌ Admin login failed, stopping admin tests")
    else:
        if not tester.test_get_profile():
            print("❌ Admin profile retrieval failed")
        
        # Admin dashboard tests
        tester.test_admin_dashboard_stats()
        tester.test_admin_get_clients()
        tester.test_admin_get_materials()
        tester.test_admin_get_campaigns()
        tester.test_admin_get_documents()
        tester.test_admin_create_client()
        
        # Material management tests
        tester.test_admin_create_material()
        tester.test_admin_update_material()
        tester.test_admin_material_filters()
        tester.test_admin_material_search()
        tester.test_admin_material_tags_autocomplete()
        tester.test_admin_bulk_actions()

    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())