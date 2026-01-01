import requests
import sys
import json
from datetime import datetime

class PayrollAPITester:
    def __init__(self, base_url="https://payhub-76.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

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

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            details = ""
            
            if not success:
                details = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'No error details')}"
                except:
                    details += f" - Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"   Error: {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}

    def test_login(self):
        """Test login functionality"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        if success:
            print(f"   Active Employees: {response.get('total_active_employees', 0)}")
            print(f"   Total Payroll: ₹{response.get('total_monthly_payroll', 0)}")
            print(f"   Payslips Generated: {response.get('total_payslips_generated', 0)}")
        return success

    def test_create_employee(self):
        """Test employee creation"""
        employee_data = {
            "employee_no": f"EMP{datetime.now().strftime('%H%M%S')}",
            "name": "Test Employee",
            "designation": "Software Engineer",
            "date_of_joining": "2024-01-15",
            "work_location": "Mumbai",
            "department": "IT",
            "bank_account_no": "1234567890",
            "salary_components": {
                "basic": 50000,
                "house_rent_allowance": 20000,
                "transport_allowance": 5000,
                "fixed_allowance": 10000,
                "home_collection_visit": 0,
                "professional_tax": 2000
            }
        }
        
        success, response = self.run_test(
            "Create Employee",
            "POST",
            "employees",
            200,
            data=employee_data
        )
        
        if success:
            self.test_employee_id = response.get('id')
            print(f"   Employee created with ID: {self.test_employee_id}")
            return response
        return None

    def test_get_employees(self):
        """Test get all employees"""
        success, response = self.run_test(
            "Get All Employees",
            "GET",
            "employees",
            200
        )
        if success:
            print(f"   Found {len(response)} employees")
        return success, response

    def test_get_employee_by_id(self, employee_id):
        """Test get employee by ID"""
        success, response = self.run_test(
            "Get Employee by ID",
            "GET",
            f"employees/{employee_id}",
            200
        )
        return success, response

    def test_update_employee(self, employee_id):
        """Test employee update"""
        update_data = {
            "designation": "Senior Software Engineer",
            "salary_components": {
                "basic": 60000,
                "house_rent_allowance": 25000,
                "transport_allowance": 6000,
                "fixed_allowance": 12000,
                "home_collection_visit": 0,
                "professional_tax": 2000
            }
        }
        
        success, response = self.run_test(
            "Update Employee",
            "PUT",
            f"employees/{employee_id}",
            200,
            data=update_data
        )
        return success, response

    def test_create_promotion(self, employee_id):
        """Test promotion creation"""
        promotion_data = {
            "employee_id": employee_id,
            "new_designation": "Team Lead",
            "promotion_date": "2024-08-01",
            "new_salary_components": {
                "basic": 70000,
                "house_rent_allowance": 30000,
                "transport_allowance": 7000,
                "fixed_allowance": 15000,
                "home_collection_visit": 0,
                "professional_tax": 2000
            }
        }
        
        success, response = self.run_test(
            "Create Promotion",
            "POST",
            "promotions",
            200,
            data=promotion_data
        )
        
        if success:
            self.test_promotion_id = response.get('id')
            print(f"   Promotion created with ID: {self.test_promotion_id}")
        return success, response

    def test_get_promotions(self):
        """Test get all promotions"""
        success, response = self.run_test(
            "Get All Promotions",
            "GET",
            "promotions",
            200
        )
        if success:
            print(f"   Found {len(response)} promotions")
        return success, response

    def test_generate_payslip(self, employee_id):
        """Test payslip generation"""
        payslip_data = {
            "employee_id": employee_id,
            "month": 8,
            "year": 2024,
            "paid_days": 30,
            "lop_days": 0
        }
        
        success, response = self.run_test(
            "Generate Payslip",
            "POST",
            "payslips/generate",
            200,
            data=payslip_data
        )
        
        if success:
            self.test_payslip_id = response.get('id')
            print(f"   Payslip generated with ID: {self.test_payslip_id}")
            print(f"   Net Payable: ₹{response.get('net_payable', 0)}")
        return success, response

    def test_get_payslips(self):
        """Test get all payslips"""
        success, response = self.run_test(
            "Get All Payslips",
            "GET",
            "payslips",
            200
        )
        if success:
            print(f"   Found {len(response)} payslips")
        return success, response

    def test_download_payslip(self, payslip_id):
        """Test payslip PDF download"""
        url = f"{self.api_url}/payslips/download/{payslip_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        print(f"\n🔍 Testing Download Payslip PDF...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            success = response.status_code == 200
            if success:
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type:
                    print(f"   PDF downloaded successfully, size: {len(response.content)} bytes")
                    self.log_test("Download Payslip PDF", True)
                else:
                    self.log_test("Download Payslip PDF", False, f"Wrong content type: {content_type}")
                    success = False
            else:
                self.log_test("Download Payslip PDF", False, f"Status {response.status_code}")
            
            return success
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"   Error: {error_msg}")
            self.log_test("Download Payslip PDF", False, error_msg)
            return False

    def test_delete_employee(self, employee_id):
        """Test employee soft delete"""
        success, response = self.run_test(
            "Soft Delete Employee",
            "DELETE",
            f"employees/{employee_id}",
            200
        )
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Payroll API Tests...")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)

        # Test login first
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return False

        # Test dashboard
        self.test_dashboard_stats()

        # Test employee CRUD
        employee = self.test_create_employee()
        if employee:
            employee_id = employee.get('id')
            
            # Test get employees
            self.test_get_employees()
            
            # Test get employee by ID
            self.test_get_employee_by_id(employee_id)
            
            # Test update employee
            self.test_update_employee(employee_id)
            
            # Test promotion
            self.test_create_promotion(employee_id)
            self.test_get_promotions()
            
            # Test payslip generation
            payslip = self.test_generate_payslip(employee_id)
            if payslip:
                payslip_id = payslip.get('id')
                
                # Test get payslips
                self.test_get_payslips()
                
                # Test PDF download
                self.test_download_payslip(payslip_id)
            
            # Test soft delete (at the end)
            self.test_delete_employee(employee_id)

        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = PayrollAPITester()
    success = tester.run_all_tests()
    
    # Save test results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
            'test_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())