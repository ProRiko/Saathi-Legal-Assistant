import requests
import json

# Test the rights calculator API endpoints
base_url = 'http://127.0.0.1:5000'

print("Testing Rights Calculator API Endpoints")
print("=" * 50)

# Test 1: Get all calculators
print("\n1. Testing GET /api/rights-calculators")
try:
    response = requests.get(f'{base_url}/api/rights-calculators')
    if response.status_code == 200:
        data = response.json()
        print("✅ Successfully retrieved calculators")
        print(f"Categories available: {list(data.keys())}")
        for category in data:
            print(f"  {category}: {len(data[category])} calculators")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Calculate gratuity
print("\n2. Testing POST /api/calculate-rights (Gratuity)")
try:
    payload = {
        "calculator": "gratuity",
        "category": "employment", 
        "data": {
            "last_drawn_salary": "50000",
            "years_of_service": "10",
            "months_of_service": "6"
        }
    }
    response = requests.post(f'{base_url}/api/calculate-rights', json=payload)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            calc = data['calculation']
            print("✅ Gratuity calculation successful")
            print(f"  Amount: Rs.{calc['amount']:,.2f}")
            print(f"  Formula: {calc['calculation']}")
        else:
            print(f"❌ Calculation failed: {data['error']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Calculate PF
print("\n3. Testing POST /api/calculate-rights (Provident Fund)")
try:
    payload = {
        "calculator": "provident_fund",
        "category": "employment",
        "data": {
            "basic_salary": "30000",
            "years_of_service": "5",
            "interest_rate": "8.5"
        }
    }
    response = requests.post(f'{base_url}/api/calculate-rights', json=payload)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            calc = data['calculation']
            print("✅ PF calculation successful")
            print(f"  Balance: Rs.{calc['amount']:,.2f}")
            print(f"  Monthly Contribution: Rs.{calc['total_monthly_contribution']:,.2f}")
        else:
            print(f"❌ Calculation failed: {data['error']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Calculate stamp duty
print("\n4. Testing POST /api/calculate-rights (Stamp Duty)")
try:
    payload = {
        "calculator": "stamp_duty",
        "category": "property",
        "data": {
            "property_value": "5000000",
            "state": "maharashtra",
            "buyer_type": "male"
        }
    }
    response = requests.post(f'{base_url}/api/calculate-rights', json=payload)
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            calc = data['calculation']
            print("✅ Stamp duty calculation successful")
            print(f"  Amount: Rs.{calc['amount']:,.2f}")
            print(f"  Rate: {calc['effective_rate']:.1f}%")
        else:
            print(f"❌ Calculation failed: {data['error']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("API Testing Complete!")
