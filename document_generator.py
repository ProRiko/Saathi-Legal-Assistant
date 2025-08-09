"""
Document Generator - Creates legal documents from templates and user data
"""
import os
from datetime import datetime
from document_templates import LEGAL_TEMPLATES

class DocumentGenerator:
    def __init__(self):
        self.templates_dir = "templates"
        
    def generate_rent_agreement(self, data):
        """Generate rent agreement from user data"""
        template = f"""
RENTAL AGREEMENT

This Rental Agreement is made on {datetime.now().strftime('%d/%m/%Y')} between:

LANDLORD: {data['landlord_name']}
TENANT: {data['tenant_name']}

PROPERTY ADDRESS:
{data['property_address']}

TERMS AND CONDITIONS:

1. RENT: The monthly rent for the said property is ₹{data['monthly_rent']}/- (Rupees {self._number_to_words(int(data['monthly_rent']))} only).

2. SECURITY DEPOSIT: The tenant has paid a security deposit of ₹{data['security_deposit']}/- which will be refunded at the end of tenancy after deducting any damages.

3. LEASE PERIOD: This agreement is for {data['lease_period']} months starting from the date of possession.

4. RENT DUE DATE: Rent is payable on or before the {data['rent_due_date']} of each month.

5. MAINTENANCE: {"Maintenance charges are included in the rent." if data['maintenance_included'] == 'yes' else "Maintenance charges are to be paid separately by the tenant."}

6. TERMS:
   • The tenant shall use the property only for residential purposes
   • No structural changes without written permission
   • Regular maintenance of the property is tenant's responsibility
   • Subletting is not allowed without landlord's consent
   • Either party can terminate with 1 month notice

IN WITNESS WHEREOF, both parties have signed this agreement.

LANDLORD                                    TENANT
{data['landlord_name']}                     {data['tenant_name']}

Date: {datetime.now().strftime('%d/%m/%Y')}
Place: ________________

Witnesses:
1. Name: _________________ Signature: _________________
2. Name: _________________ Signature: _________________
        """
        return template.strip()

    def generate_employment_offer(self, data):
        """Generate employment offer letter"""
        template = f"""
{data['company_name']}

Date: {datetime.now().strftime('%d %B, %Y')}

Mr./Ms. {data['candidate_name']}

Subject: Offer of Employment - {data['position_title']}

Dear {data['candidate_name']},

We are pleased to offer you the position of {data['position_title']} with {data['company_name']}.

EMPLOYMENT DETAILS:

Position: {data['position_title']}
Annual CTC: ₹{data['salary_amount']}/- (Rupees {self._number_to_words(int(data['salary_amount']))} only)
Joining Date: {data['joining_date']}
Work Location: {data['work_location']}
Probation Period: {data['probation_period']} months

TERMS & CONDITIONS:

1. This offer is subject to successful completion of background verification
2. You will be on probation for {data['probation_period']} months from joining date
3. During probation, either party may terminate employment with 1 month notice
4. Post probation, notice period will be as per company policy
5. You will be eligible for benefits as per company policy
6. This offer supersedes all previous discussions and negotiations

Please confirm your acceptance by signing and returning a copy of this letter by {(datetime.now().replace(day=datetime.now().day + 7)).strftime('%d/%m/%Y')}.

We look forward to welcoming you to our team.

Best regards,

HR Department
{data['company_name']}

ACCEPTANCE:
I, {data['candidate_name']}, accept the above terms and conditions.

Signature: _________________
Date: _________________
        """
        return template.strip()

    def generate_legal_notice(self, data):
        """Generate legal notice"""
        template = f"""
LEGAL NOTICE

To: {data['recipient_name']}
Address: {data['recipient_address']}

From: {data['sender_name']}
Address: {data['sender_address']}

Date: {datetime.now().strftime('%d/%m/%Y')}

Subject: Legal Notice regarding {data['issue_type'].replace('_', ' ').title()}

Sir/Madam,

I, {data['sender_name']}, through this legal notice, bring to your attention the following:

FACTS OF THE CASE:
{data['issue_description']}

{"AMOUNT INVOLVED: ₹" + data['amount_due'] + "/-" if data.get('amount_due') and int(data['amount_due']) > 0 else ""}

NOTICE:
You are hereby called upon to resolve the above matter within {data['notice_period']} days from receipt of this notice, failing which I shall be constrained to initiate appropriate legal proceedings against you for:

1. Recovery of the amount due with interest
2. Damages for mental harassment and agony
3. Cost of legal proceedings
4. Any other relief deemed fit by the Hon'ble Court

Take notice that if you fail to comply with the demands made herein within the stipulated time, legal proceedings will be initiated against you without any further reference or notice.

This notice is served upon you to avoid unnecessary litigation, but if you fail to heed this notice, you will be solely responsible for the consequences.

Yours faithfully,

{data['sender_name']}

Date: {datetime.now().strftime('%d/%m/%Y')}
Place: ________________
        """
        return template.strip()

    def _number_to_words(self, number):
        """Convert number to words (simplified version)"""
        if number < 1000:
            return f"₹{number}"
        elif number < 100000:
            return f"₹{number//1000} thousand {number%1000 if number%1000 else ''}".strip()
        elif number < 10000000:
            return f"₹{number//100000} lakh {(number%100000)//1000 if (number%100000)//1000 else ''}".strip()
        else:
            return f"₹{number//10000000} crore {(number%10000000)//100000 if (number%10000000)//100000 else ''}".strip()

    def get_available_templates(self):
        """Get list of available templates"""
        templates = []
        for key, template in LEGAL_TEMPLATES.items():
            templates.append({
                "id": key,
                "name": template["name"],
                "category": template["category"],
                "description": template["description"],
                "icon": template["icon"],
                "popularity": template["popularity"]
            })
        return sorted(templates, key=lambda x: x["popularity"], reverse=True)

    def get_template_questions(self, template_id):
        """Get questions for a specific template"""
        if template_id in LEGAL_TEMPLATES:
            return LEGAL_TEMPLATES[template_id]["questions"]
        return None

    def generate_document(self, template_id, user_data):
        """Generate document based on template and user data"""
        if template_id == "rent_agreement":
            return self.generate_rent_agreement(user_data)
        elif template_id == "employment_offer":
            return self.generate_employment_offer(user_data)
        elif template_id == "legal_notice":
            return self.generate_legal_notice(user_data)
        else:
            return None
