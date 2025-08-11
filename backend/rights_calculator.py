"""
Legal Rights Calculator
Calculates various legal entitlements for employment, property, and consumer rights
"""

import math
from datetime import datetime, date
from typing import Dict, Any, Optional

class LegalRightsCalculator:
    def __init__(self):
        self.calculators = {
            "employment": {
                "gratuity": {
                    "name": "Gratuity Calculator",
                    "icon": "💰",
                    "description": "Calculate gratuity amount based on years of service and last drawn salary",
                    "applicable_to": "Employees with 5+ years of continuous service",
                    "fields": [
                        {
                            "id": "last_drawn_salary",
                            "label": "Last Drawn Monthly Salary (₹)",
                            "type": "number",
                            "required": True,
                            "help": "Basic salary + Dearness Allowance (if it forms part of salary)"
                        },
                        {
                            "id": "years_of_service",
                            "label": "Years of Continuous Service",
                            "type": "number",
                            "required": True,
                            "min": 0,
                            "help": "Total years of continuous service with the employer"
                        },
                        {
                            "id": "months_of_service",
                            "label": "Additional Months of Service",
                            "type": "number",
                            "default": 0,
                            "min": 0,
                            "max": 11,
                            "help": "Additional months (0-11) beyond complete years"
                        }
                    ]
                },
                "provident_fund": {
                    "name": "Provident Fund Calculator",
                    "icon": "🏦",
                    "description": "Calculate PF balance and monthly contributions",
                    "applicable_to": "Employees in organizations with 20+ employees",
                    "fields": [
                        {
                            "id": "basic_salary",
                            "label": "Monthly Basic Salary (₹)",
                            "type": "number",
                            "required": True,
                            "help": "Basic salary component only (not gross salary)"
                        },
                        {
                            "id": "years_of_service",
                            "label": "Years of Service",
                            "type": "number",
                            "required": True,
                            "min": 0,
                            "help": "Total years of service for PF calculation"
                        },
                        {
                            "id": "interest_rate",
                            "label": "Annual Interest Rate (%)",
                            "type": "number",
                            "default": 8.5,
                            "help": "Current EPF interest rate (8.5% for 2023-24)"
                        }
                    ]
                },
                "notice_pay": {
                    "name": "Notice Pay Calculator",
                    "icon": "📋",
                    "description": "Calculate notice pay when employment is terminated without proper notice",
                    "applicable_to": "All employees as per employment contract terms",
                    "fields": [
                        {
                            "id": "monthly_salary",
                            "label": "Monthly Gross Salary (₹)",
                            "type": "number",
                            "required": True,
                            "help": "Total monthly salary including all allowances"
                        },
                        {
                            "id": "notice_period",
                            "label": "Notice Period",
                            "type": "select",
                            "required": True,
                            "options": [
                                {"value": "30", "text": "30 Days (1 Month)"},
                                {"value": "60", "text": "60 Days (2 Months)"},
                                {"value": "90", "text": "90 Days (3 Months)"}
                            ],
                            "help": "Standard notice period as per employment contract"
                        },
                        {
                            "id": "days_served",
                            "label": "Days of Notice Already Served",
                            "type": "number",
                            "default": 0,
                            "min": 0,
                            "help": "Number of days already served during notice period"
                        }
                    ]
                }
            },
            "property": {
                "stamp_duty": {
                    "name": "Stamp Duty Calculator",
                    "icon": "🏠",
                    "description": "Calculate stamp duty for property transactions",
                    "applicable_to": "Property buyers in various states of India",
                    "fields": [
                        {
                            "id": "property_value",
                            "label": "Property Value (₹)",
                            "type": "number",
                            "required": True,
                            "help": "Market value or circle rate of the property (whichever is higher)"
                        },
                        {
                            "id": "state",
                            "label": "State",
                            "type": "select",
                            "required": True,
                            "options": [
                                {"value": "maharashtra", "text": "Maharashtra", "rate": 0.05},
                                {"value": "delhi", "text": "Delhi", "rate": 0.06},
                                {"value": "karnataka", "text": "Karnataka", "rate": 0.05},
                                {"value": "gujarat", "text": "Gujarat", "rate": 0.04},
                                {"value": "rajasthan", "text": "Rajasthan", "rate": 0.05},
                                {"value": "haryana", "text": "Haryana", "rate": 0.06},
                                {"value": "other", "text": "Other States", "rate": 0.05}
                            ],
                            "help": "Select your state for accurate stamp duty calculation"
                        },
                        {
                            "id": "buyer_type",
                            "label": "Buyer Type",
                            "type": "select",
                            "required": True,
                            "options": [
                                {"value": "male", "text": "Male"},
                                {"value": "female", "text": "Female (may get rebate)"},
                                {"value": "joint", "text": "Joint (Male + Female)"}
                            ],
                            "help": "Some states offer rebates for female buyers"
                        }
                    ]
                },
                "rental_deposit": {
                    "name": "Rental Security Deposit Calculator",
                    "icon": "🔑",
                    "description": "Calculate maximum security deposit that can be charged",
                    "applicable_to": "Tenants and landlords across India",
                    "fields": [
                        {
                            "id": "monthly_rent",
                            "label": "Monthly Rent (₹)",
                            "type": "number",
                            "required": True,
                            "help": "Monthly rent amount as per rental agreement"
                        },
                        {
                            "id": "property_type",
                            "label": "Property Type",
                            "type": "select",
                            "required": True,
                            "options": [
                                {"value": "residential", "text": "Residential", "rate": 2},
                                {"value": "commercial", "text": "Commercial", "rate": 6},
                                {"value": "industrial", "text": "Industrial", "rate": 6}
                            ],
                            "help": "Type of property being rented"
                        }
                    ]
                }
            },
            "consumer": {
                "refund_calculator": {
                    "name": "Consumer Refund Calculator",
                    "icon": "💳",
                    "description": "Calculate refund amount with compensation for consumer disputes",
                    "applicable_to": "Consumers seeking refund with compensation",
                    "fields": [
                        {
                            "id": "purchase_amount",
                            "label": "Purchase Amount (₹)",
                            "type": "number",
                            "required": True,
                            "help": "Original amount paid for goods/services"
                        },
                        {
                            "id": "dispute_type",
                            "label": "Type of Dispute",
                            "type": "select",
                            "required": True,
                            "options": [
                                {"value": "defective_goods", "text": "Defective Goods", "compensation": 0.1},
                                {"value": "service_deficiency", "text": "Service Deficiency", "compensation": 0.15},
                                {"value": "unfair_trade", "text": "Unfair Trade Practice", "compensation": 0.2},
                                {"value": "mental_harassment", "text": "Mental Harassment", "compensation": 0.25}
                            ],
                            "help": "Select the type of consumer dispute"
                        },
                        {
                            "id": "days_elapsed",
                            "label": "Days Since Purchase",
                            "type": "number",
                            "required": True,
                            "min": 0,
                            "help": "Number of days since the purchase was made"
                        }
                    ]
                }
            }
        }

    def get_calculators(self):
        """Return all calculator definitions"""
        return self.calculators

    def calculate(self, category: str, calculator: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform calculation based on category and calculator type
        
        Args:
            category: The category of calculation (employment, property, consumer)
            calculator: The specific calculator to use
            data: Input data for calculation
            
        Returns:
            Dictionary containing calculation results
        """
        if category not in self.calculators:
            raise ValueError(f"Unknown category: {category}")
        
        if calculator not in self.calculators[category]:
            raise ValueError(f"Unknown calculator: {calculator} in category {category}")
        
        # Route to appropriate calculation method
        method_name = f"calculate_{category}_{calculator}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(data)
        else:
            raise ValueError(f"Calculation method not implemented: {method_name}")

    def calculate_employment_gratuity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate gratuity amount"""
        last_salary = float(data.get('last_drawn_salary', 0))
        years = int(data.get('years_of_service', 0))
        months = int(data.get('months_of_service', 0))
        
        # Gratuity eligibility - minimum 5 years of service
        if years < 5:
            return {
                "eligible": False,
                "amount": 0,
                "reason": "Gratuity is applicable only after completing 5 years of continuous service"
            }
        
        # Convert additional months to fraction of year (>6 months counts as 1 year)
        if months >= 6:
            years += 1
        
        # Gratuity formula: (Last drawn salary × 15 × Years of service) / 26
        # Maximum gratuity cap is ₹20 lakhs
        formula_amount = (last_salary * 15 * years) / 26
        max_limit = 2000000  # ₹20 lakhs
        
        final_amount = min(formula_amount, max_limit)
        
        return {
            "eligible": True,
            "amount": final_amount,
            "calculation": f"(₹{last_salary:,.0f} × 15 × {years}) ÷ 26",
            "formula_amount": formula_amount,
            "years_considered": years,
            "max_limit": max_limit,
            "capped": formula_amount > max_limit
        }

    def calculate_employment_provident_fund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate PF balance estimation"""
        basic_salary = float(data.get('basic_salary', 0))
        years = float(data.get('years_of_service', 0))
        interest_rate = float(data.get('interest_rate', 8.5)) / 100
        
        # PF calculation - 12% employee + 12% employer contribution
        monthly_employee_contribution = basic_salary * 0.12
        monthly_employer_contribution = basic_salary * 0.12
        total_monthly_contribution = monthly_employee_contribution + monthly_employer_contribution
        
        # Annual contribution
        annual_contribution = total_monthly_contribution * 12
        
        # Compound interest calculation for PF balance
        if years > 0:
            # Using compound interest formula: A = P * (1 + r)^t
            total_balance = annual_contribution * (((1 + interest_rate) ** years - 1) / interest_rate)
            interest_earned = total_balance - (annual_contribution * years)
        else:
            total_balance = 0
            interest_earned = 0
        
        return {
            "eligible": True,
            "amount": total_balance,
            "monthly_employee_contribution": monthly_employee_contribution,
            "monthly_employer_contribution": monthly_employer_contribution,
            "total_monthly_contribution": total_monthly_contribution,
            "annual_contribution": annual_contribution,
            "interest_earned": interest_earned,
            "calculation": f"₹{annual_contribution:,.0f} annual contribution for {years} years at {interest_rate*100:.1f}% interest"
        }

    def calculate_employment_notice_pay(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate notice pay amount"""
        monthly_salary = float(data.get('monthly_salary', 0))
        notice_period = int(data.get('notice_period', 30))
        days_served = int(data.get('days_served', 0))
        
        # Calculate daily salary (assuming 30 days in a month)
        daily_salary = monthly_salary / 30
        
        # Remaining days to be compensated
        remaining_days = notice_period - days_served
        
        if remaining_days <= 0:
            return {
                "eligible": False,
                "amount": 0,
                "reason": "Full notice period has been served, no payment due"
            }
        
        notice_pay_amount = daily_salary * remaining_days
        
        return {
            "eligible": True,
            "amount": notice_pay_amount,
            "daily_salary": daily_salary,
            "remaining_days": remaining_days,
            "calculation": f"₹{daily_salary:.2f} per day × {remaining_days} days"
        }

    def calculate_property_stamp_duty(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate stamp duty for property transactions"""
        property_value = float(data.get('property_value', 0))
        state = data.get('state', 'other')
        buyer_type = data.get('buyer_type', 'male')
        
        # Get stamp duty rate based on state
        state_rates = {
            'maharashtra': 0.05,
            'delhi': 0.06,
            'karnataka': 0.05,
            'gujarat': 0.04,
            'rajasthan': 0.05,
            'haryana': 0.06,
            'other': 0.05
        }
        
        base_rate = state_rates.get(state, 0.05)
        
        # Apply rebate for female buyers in certain states
        rebate = 0
        if buyer_type == 'female' and state in ['maharashtra', 'delhi', 'haryana']:
            rebate = 0.01  # 1% rebate for female buyers
        elif buyer_type == 'joint' and state in ['maharashtra', 'delhi']:
            rebate = 0.005  # 0.5% rebate for joint registration
        
        effective_rate = max(base_rate - rebate, 0.01)  # Minimum 1%
        stamp_duty = property_value * effective_rate
        
        return {
            "eligible": True,
            "amount": stamp_duty,
            "property_value": property_value,
            "base_rate": base_rate * 100,
            "rebate": rebate * 100,
            "effective_rate": effective_rate * 100,
            "calculation": f"₹{property_value:,.0f} × {effective_rate*100:.1f}%"
        }

    def calculate_property_rental_deposit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate maximum rental security deposit"""
        monthly_rent = float(data.get('monthly_rent', 0))
        property_type = data.get('property_type', 'residential')
        
        # Security deposit limits as per rental laws
        deposit_multipliers = {
            'residential': 2,  # 2 months rent
            'commercial': 6,   # 6 months rent
            'industrial': 6    # 6 months rent
        }
        
        multiplier = deposit_multipliers.get(property_type, 2)
        max_deposit = monthly_rent * multiplier
        
        return {
            "eligible": True,
            "amount": max_deposit,
            "monthly_rent": monthly_rent,
            "multiplier": multiplier,
            "property_type": property_type.title(),
            "calculation": f"₹{monthly_rent:,.0f} × {multiplier} months"
        }

    def calculate_consumer_refund_calculator(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate consumer refund with compensation"""
        purchase_amount = float(data.get('purchase_amount', 0))
        dispute_type = data.get('dispute_type', 'defective_goods')
        days_elapsed = int(data.get('days_elapsed', 0))
        
        # Compensation rates based on dispute type
        compensation_rates = {
            'defective_goods': 0.1,      # 10%
            'service_deficiency': 0.15,   # 15%
            'unfair_trade': 0.2,         # 20%
            'mental_harassment': 0.25     # 25%
        }
        
        compensation_rate = compensation_rates.get(dispute_type, 0.1)
        
        # Base refund amount
        refund_amount = purchase_amount
        
        # Compensation for trouble/harassment
        compensation = purchase_amount * compensation_rate
        
        # Interest calculation (9% per annum for delays > 30 days)
        interest = 0
        if days_elapsed > 30:
            interest_days = days_elapsed - 30
            annual_interest_rate = 0.09
            interest = (purchase_amount * annual_interest_rate * interest_days) / 365
        
        total_amount = refund_amount + compensation + interest
        
        return {
            "eligible": True,
            "amount": total_amount,
            "refund_amount": refund_amount,
            "compensation": compensation,
            "interest": interest,
            "days_elapsed": days_elapsed,
            "compensation_rate": compensation_rate * 100,
            "calculation": f"Refund: ₹{refund_amount:,.0f} + Compensation: ₹{compensation:,.0f} + Interest: ₹{interest:,.0f}"
        }

    def number_to_words(self, num: int) -> str:
        """Convert number to words (Indian numbering system)"""
        if num == 0:
            return "zero"
        
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
                "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
                "seventeen", "eighteen", "nineteen"]
        
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        
        def convert_hundreds(n):
            result = ""
            if n >= 100:
                result += ones[n // 100] + " hundred "
                n %= 100
            if n >= 20:
                result += tens[n // 10]
                if n % 10:
                    result += " " + ones[n % 10]
            elif n > 0:
                result += ones[n]
            return result.strip()
        
        if num < 0:
            return "minus " + self.number_to_words(-num)
        
        crore = num // 10000000
        lakh = (num // 100000) % 100
        thousand = (num // 1000) % 100
        hundred = num % 1000
        
        result = []
        
        if crore:
            result.append(convert_hundreds(crore) + " crore")
        if lakh:
            result.append(convert_hundreds(lakh) + " lakh")
        if thousand:
            result.append(convert_hundreds(thousand) + " thousand")
        if hundred:
            result.append(convert_hundreds(hundred))
        
        return " ".join(result)
