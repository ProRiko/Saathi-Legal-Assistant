# Legal Document Templates Database
# Each template has questions that get filled into the document

LEGAL_TEMPLATES = {
    "rent_agreement": {
        "name": "Rent Agreement",
        "category": "Property",
        "description": "Create a legally valid rental agreement between landlord and tenant",
        "icon": "🏠",
        "popularity": 95,
        "questions": [
            {
                "id": "landlord_name",
                "question": "What is the landlord's full name?",
                "type": "text",
                "placeholder": "Enter full name as per ID proof",
                "required": True
            },
            {
                "id": "tenant_name", 
                "question": "What is the tenant's full name?",
                "type": "text",
                "placeholder": "Enter full name as per ID proof",
                "required": True
            },
            {
                "id": "property_address",
                "question": "What is the complete property address?",
                "type": "textarea",
                "placeholder": "House/Flat No., Street, Area, City, State, PIN",
                "required": True
            },
            {
                "id": "monthly_rent",
                "question": "What is the monthly rent amount (₹)?",
                "type": "number",
                "placeholder": "Enter amount in numbers",
                "required": True
            },
            {
                "id": "security_deposit",
                "question": "What is the security deposit amount (₹)?",
                "type": "number",
                "placeholder": "Usually 1-3 months rent",
                "required": True
            },
            {
                "id": "lease_period",
                "question": "What is the lease period?",
                "type": "select",
                "options": [
                    {"value": "11", "text": "11 months"},
                    {"value": "12", "text": "1 year"},
                    {"value": "24", "text": "2 years"},
                    {"value": "36", "text": "3 years"}
                ],
                "required": True
            },
            {
                "id": "rent_due_date",
                "question": "On which date is rent due each month?",
                "type": "select",
                "options": [
                    {"value": "1", "text": "1st of every month"},
                    {"value": "5", "text": "5th of every month"},
                    {"value": "10", "text": "10th of every month"},
                    {"value": "15", "text": "15th of every month"}
                ],
                "required": True
            },
            {
                "id": "maintenance_included",
                "question": "Is maintenance included in rent?",
                "type": "select",
                "options": [
                    {"value": "yes", "text": "Yes, maintenance included"},
                    {"value": "no", "text": "No, tenant pays separately"}
                ],
                "required": True
            }
        ]
    },
    
    "employment_offer": {
        "name": "Employment Offer Letter",
        "category": "Employment",
        "description": "Professional offer letter for new employees",
        "icon": "💼",
        "popularity": 85,
        "questions": [
            {
                "id": "company_name",
                "question": "What is your company name?",
                "type": "text",
                "required": True
            },
            {
                "id": "candidate_name",
                "question": "What is the candidate's full name?",
                "type": "text",
                "required": True
            },
            {
                "id": "position_title",
                "question": "What is the job position/title?",
                "type": "text",
                "placeholder": "e.g. Software Developer, Marketing Manager",
                "required": True
            },
            {
                "id": "salary_amount",
                "question": "What is the annual salary (₹)?",
                "type": "number",
                "placeholder": "Enter annual CTC",
                "required": True
            },
            {
                "id": "joining_date",
                "question": "What is the joining date?",
                "type": "date",
                "required": True
            },
            {
                "id": "work_location",
                "question": "What is the work location?",
                "type": "text",
                "placeholder": "City or specific office address",
                "required": True
            },
            {
                "id": "probation_period",
                "question": "What is the probation period?",
                "type": "select",
                "options": [
                    {"value": "3", "text": "3 months"},
                    {"value": "6", "text": "6 months"},
                    {"value": "12", "text": "12 months"}
                ],
                "required": True
            }
        ]
    },

    "legal_notice": {
        "name": "Legal Notice",
        "category": "Legal Notice",
        "description": "Send legal notice for various issues like payment recovery, contract breach",
        "icon": "⚖️",
        "popularity": 75,
        "questions": [
            {
                "id": "sender_name",
                "question": "Your full name (notice sender)?",
                "type": "text",
                "required": True
            },
            {
                "id": "sender_address",
                "question": "Your complete address?",
                "type": "textarea",
                "required": True
            },
            {
                "id": "recipient_name",
                "question": "Recipient's full name?",
                "type": "text",
                "required": True
            },
            {
                "id": "recipient_address",
                "question": "Recipient's complete address?",
                "type": "textarea",
                "required": True
            },
            {
                "id": "issue_type",
                "question": "What is the issue type?",
                "type": "select",
                "options": [
                    {"value": "payment", "text": "Payment Recovery"},
                    {"value": "contract", "text": "Contract Breach"},
                    {"value": "property", "text": "Property Dispute"},
                    {"value": "defamation", "text": "Defamation"},
                    {"value": "other", "text": "Other"}
                ],
                "required": True
            },
            {
                "id": "amount_due",
                "question": "Amount involved (₹) - if applicable?",
                "type": "number",
                "placeholder": "Enter 0 if not applicable",
                "required": False
            },
            {
                "id": "issue_description",
                "question": "Briefly describe the issue/dispute?",
                "type": "textarea",
                "placeholder": "Explain what happened and what you want",
                "required": True
            },
            {
                "id": "notice_period",
                "question": "How many days to respond/comply?",
                "type": "select",
                "options": [
                    {"value": "7", "text": "7 days"},
                    {"value": "15", "text": "15 days"},
                    {"value": "30", "text": "30 days"}
                ],
                "required": True
            }
        ]
    }
}
