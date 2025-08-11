def generate_letter(letter_type, details):
    if letter_type == "landlord_complaint":
        return f"""To: {details.get("landlord_name", "The Landlord")}

Subject: Request for Security Deposit Refund

Dear {details.get("landlord_name", "Sir/Madam")},

I am {details.get("tenant_name", "your tenant")}. I have vacated the rented premises and fulfilled all obligations. I kindly request the return of my security deposit at the earliest.

Sincerely,
{details.get("tenant_name", "Your Tenant")}
"""

    elif letter_type == "rti_request":
        return f"""To: The Public Information Officer

Subject: Application under Right to Information Act, 2005

Dear Sir/Madam,

I am {details.get("name", "a citizen of India")}, seeking the following information under the RTI Act: {details.get("query", "please specify")}

Sincerely,
{details.get("name", "Your Name")}
"""

    else:
        return "Sorry, I cannot generate this type of letter yet."
