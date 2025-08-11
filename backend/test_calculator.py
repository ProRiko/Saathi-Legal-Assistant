"""
Test script for Legal Rights Calculator
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rights_calculator import LegalRightsCalculator

def test_calculator():
    print("🧮 Testing Legal Rights Calculator")
    print("=" * 50)
    
    # Initialize calculator
    calc = LegalRightsCalculator()
    print("✅ Rights Calculator initialized successfully!")
    print()

    # Test 1: Gratuity calculation
    print("📊 Test 1: Gratuity Calculation")
    print("-" * 30)
    try:
        result = calc.calculate('employment', 'gratuity', {
            'last_drawn_salary': 50000,
            'years_of_service': 10,
            'months_of_service': 6
        })
        print(f"✅ Gratuity amount: ₹{result['amount']:,.2f}")
        print(f"   Calculation: {result['calculation']}")
        print(f"   Years considered: {result['years_considered']}")
        print()
    except Exception as e:
        print(f"❌ Error in gratuity calculation: {e}")
        print()

    # Test 2: PF calculation
    print("📊 Test 2: Provident Fund Calculation")
    print("-" * 35)
    try:
        result = calc.calculate('employment', 'provident_fund', {
            'basic_salary': 30000,
            'years_of_service': 5,
            'interest_rate': 8.5
        })
        print(f"✅ PF balance: ₹{result['amount']:,.2f}")
        print(f"   Monthly contribution: ₹{result['total_monthly_contribution']:,.2f}")
        print(f"   Interest earned: ₹{result['interest_earned']:,.2f}")
        print()
    except Exception as e:
        print(f"❌ Error in PF calculation: {e}")
        print()

    # Test 3: Notice Pay calculation
    print("📊 Test 3: Notice Pay Calculation")
    print("-" * 30)
    try:
        result = calc.calculate('employment', 'notice_pay', {
            'monthly_salary': 60000,
            'notice_period': 60,
            'days_served': 15
        })
        print(f"✅ Notice pay amount: ₹{result['amount']:,.2f}")
        print(f"   Daily salary: ₹{result['daily_salary']:,.2f}")
        print(f"   Remaining days: {result['remaining_days']}")
        print()
    except Exception as e:
        print(f"❌ Error in notice pay calculation: {e}")
        print()

    # Test 4: Stamp Duty calculation
    print("📊 Test 4: Stamp Duty Calculation")
    print("-" * 30)
    try:
        result = calc.calculate('property', 'stamp_duty', {
            'property_value': 5000000,
            'state': 'maharashtra',
            'buyer_type': 'female'
        })
        print(f"✅ Stamp duty amount: ₹{result['amount']:,.2f}")
        print(f"   Base rate: {result['base_rate']}%")
        print(f"   Effective rate: {result['effective_rate']}%")
        print()
    except Exception as e:
        print(f"❌ Error in stamp duty calculation: {e}")
        print()

    # Test 5: Consumer Refund calculation
    print("📊 Test 5: Consumer Refund Calculation")
    print("-" * 35)
    try:
        result = calc.calculate('consumer', 'refund_calculator', {
            'purchase_amount': 25000,
            'dispute_type': 'service_deficiency',
            'days_elapsed': 45
        })
        print(f"✅ Total refund amount: ₹{result['amount']:,.2f}")
        print(f"   Refund: ₹{result['refund_amount']:,.2f}")
        print(f"   Compensation: ₹{result['compensation']:,.2f}")
        print(f"   Interest: ₹{result['interest']:,.2f}")
        print()
    except Exception as e:
        print(f"❌ Error in refund calculation: {e}")
        print()

    # Test 6: Get all calculators
    print("📊 Test 6: Available Calculators")
    print("-" * 30)
    try:
        calculators = calc.get_calculators()
        for category, calcs in calculators.items():
            print(f"✅ {category.title()}: {list(calcs.keys())}")
        print()
    except Exception as e:
        print(f"❌ Error getting calculators: {e}")
        print()

    print("🎉 All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_calculator()
