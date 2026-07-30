#!/usr/bin/env python3

# Read the current file
with open('backend/shared/utils/contract_search_tool.py', 'r') as f:
    content = f.read()

# Replace the CONTRACT_TYPES list
old_contract_types = '''CONTRACT_TYPES = [
    "Affiliate Agreement" "Development",
    "Distributor",
    "Endorsement",
    "Franchise",
    "Hosting",
    "IP",
    "Joint Venture",
    "License Agreement",
    "Maintenance",
    "Manufacturing",
    "Marketing",
    "Non Compete/Solicit" "Outsourcing",
    "Promotion",
    "Reseller",
    "Service",
    "Sponsorship",
    "Strategic Alliance",
    "Supply",
    "Transportation",
]'''

new_contract_types = '''CONTRACT_TYPES = [
    "Affiliate Agreement",
    "Development",
    "Distributor",
    "Endorsement",
    "Franchise",
    "Hosting",
    "IP",
    "Joint Venture",
    "License Agreement",
    "Maintenance",
    "Manufacturing",
    "Marketing",
    "Non Compete/Solicit",
    "Outsourcing",
    "Promotion",
    "Reseller",
    "Service",
    "Sponsorship",
    "Strategic Alliance",
    "Supply",
    "Transportation",
    # New contract types
    "MSA",
    "Master Services Agreement",
    "SOW",
    "Statement of Work",
    "NDA",
    "MNDA",
    "Non-Disclosure Agreement",
    "DPA",
    "Data Processing Agreement",
    "SaaS Agreement",
    "Subscription Agreement",
    "IP Addendum",
    "Licensing Addendum",
]'''

# Replace the content
updated_content = content.replace(old_contract_types, new_contract_types)

# Write back to file
with open('backend/shared/utils/contract_search_tool.py', 'w') as f:
    f.write(updated_content)

print("✅ Contract types updated successfully!")
print("Added new contract types:")
print("- MSA (Master Services Agreement)")
print("- SOW (Statement of Work)")
print("- NDA/MNDA (Non-Disclosure Agreement)")
print("- DPA (Data Processing Agreement)")
print("- SaaS/Subscription Agreements")
print("- IP & Licensing Addendums")
