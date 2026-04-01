import requests
import sys
import json
from datetime import datetime

class LuxeDiscoveryAPITester:
    def __init__(self, base_url="https://luxe-discovery.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        if self.admin_token:
            test_headers['Authorization'] = f'Bearer {self.admin_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:300]
                })

            return success, response.json() if response.status_code < 400 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                'name': name,
                'error': str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n" + "="*50)
        print("TESTING HEALTH ENDPOINTS")
        print("="*50)
        
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_profiles_endpoints(self):
        """Test profiles endpoints"""
        print("\n" + "="*50)
        print("TESTING PROFILES ENDPOINTS")
        print("="*50)
        
        # Test get all profiles
        success, profiles_data = self.run_test("Get All Profiles", "GET", "profiles", 200)
        
        # Test with filters
        self.run_test("Get Profiles with City Filter", "GET", "profiles?city=Москва", 200)
        self.run_test("Get Profiles with Age Filter", "GET", "profiles?min_age=21&max_age=30", 200)
        self.run_test("Get Featured Profiles", "GET", "profiles?featured_only=true", 200)
        self.run_test("Get Profiles Sorted by Newest", "GET", "profiles?sort_by=newest", 200)
        
        # Test get single profile if we have profiles
        if success and profiles_data and len(profiles_data) > 0:
            profile_id = profiles_data[0].get('id')
            if profile_id:
                self.run_test("Get Single Profile", "GET", f"profiles/{profile_id}", 200)
                self.run_test("Get Single Profile with City", "GET", f"profiles/{profile_id}?city=Москва", 200)
        
        # Test non-existent profile
        self.run_test("Get Non-existent Profile", "GET", "profiles/non-existent-id", 404)

    def test_admin_auth(self):
        """Test admin authentication"""
        print("\n" + "="*50)
        print("TESTING ADMIN AUTHENTICATION")
        print("="*50)
        
        # Test login with correct credentials
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        success, response = self.run_test("Admin Login", "POST", "admin/login", 200, data=login_data)
        
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   ✅ Admin token obtained: {self.admin_token[:20]}...")
            
            # Test protected endpoints
            self.run_test("Get Admin Profile", "GET", "admin/me", 200)
            self.run_test("Get Admin Stats", "GET", "admin/stats", 200)
        else:
            print("   ❌ Failed to get admin token")
        
        # Test login with wrong credentials
        wrong_login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        self.run_test("Admin Login Wrong Password", "POST", "admin/login", 401, data=wrong_login_data)

    def test_admin_profile_management(self):
        """Test admin profile management (requires admin token)"""
        if not self.admin_token:
            print("\n❌ Skipping admin profile management tests - no admin token")
            return
            
        print("\n" + "="*50)
        print("TESTING ADMIN PROFILE MANAGEMENT")
        print("="*50)
        
        # Test create profile
        new_profile_data = {
            "name": "Test Profile",
            "age": 25,
            "city": "Москва",
            "country": "Россия",
            "descriptionShort": "Test short description",
            "descriptionFull": "Test full description for testing purposes",
            "images": ["https://example.com/test.jpg"],
            "height": 170,
            "weight": 55,
            "languages": ["Русский", "English"],
            "tags": ["test", "profile"],
            "lat": 55.7558,
            "lng": 37.6176,
            "isActive": True,
            "isFeatured": False
        }
        
        success, created_profile = self.run_test("Create Profile", "POST", "profiles", 201, data=new_profile_data)
        
        if success and 'id' in created_profile:
            profile_id = created_profile['id']
            print(f"   ✅ Created profile with ID: {profile_id}")
            
            # Test update profile
            update_data = {
                "age": 26,
                "descriptionShort": "Updated short description"
            }
            self.run_test("Update Profile", "PUT", f"profiles/{profile_id}", 200, data=update_data)
            
            # Test delete profile
            self.run_test("Delete Profile", "DELETE", f"profiles/{profile_id}", 200)
            
            # Verify profile is deleted
            self.run_test("Get Deleted Profile", "GET", f"profiles/{profile_id}", 404)
        
        # Test operations without admin token
        temp_token = self.admin_token
        self.admin_token = None
        self.run_test("Create Profile Without Auth", "POST", "profiles", 401, data=new_profile_data)
        self.admin_token = temp_token

    def test_contact_form(self):
        """Test contact form submission"""
        print("\n" + "="*50)
        print("TESTING CONTACT FORM")
        print("="*50)
        
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+7 (999) 123-45-67",
            "message": "This is a test message from automated testing"
        }
        
        self.run_test("Submit Contact Form", "POST", "contact", 200, data=contact_data)

    def test_cloudinary_endpoints(self):
        """Test Cloudinary endpoints (requires admin token)"""
        if not self.admin_token:
            print("\n❌ Skipping Cloudinary tests - no admin token")
            return
            
        print("\n" + "="*50)
        print("TESTING CLOUDINARY ENDPOINTS")
        print("="*50)
        
        self.run_test("Get Cloudinary Signature", "GET", "cloudinary/signature?folder=profiles", 200)
        self.run_test("Get Cloudinary Signature Invalid Folder", "GET", "cloudinary/signature?folder=invalid", 400)

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"📊 Tests run: {self.tests_run}")
        print(f"✅ Tests passed: {self.tests_passed}")
        print(f"❌ Tests failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['name']}")
                if 'error' in test:
                    print(f"   Error: {test['error']}")
                else:
                    print(f"   Expected: {test['expected']}, Got: {test['actual']}")
                    if test.get('response'):
                        print(f"   Response: {test['response']}")
        
        return self.tests_passed == self.tests_run

def main():
    print("🚀 Starting L'Aura API Testing...")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = LuxeDiscoveryAPITester()
    
    # Run all tests
    tester.test_health_check()
    tester.test_profiles_endpoints()
    tester.test_admin_auth()
    tester.test_admin_profile_management()
    tester.test_contact_form()
    tester.test_cloudinary_endpoints()
    
    # Print summary
    all_passed = tester.print_summary()
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())