#!/usr/bin/env python3
import requests
import sys
import os

def upload_pdf(file_path, api_url="http://localhost:8000"):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
    
    if not file_path.lower().endswith('.pdf'):
        print("Error: Only PDF files are supported")
        return False
    
    try:
        print(f"Uploading {os.path.basename(file_path)}...")
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(f"{api_url}/documents/upload", files=files, timeout=600)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful: {result.get('message', 'File processed')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Details: {result.get('details', '')[:100]}...")
            
            # Print contract ID and intelligence analysis command
            contract_id = result.get('contract_id')
            if contract_id:
                print(f"\n📋 Contract ID: {contract_id}")
                print(f"\n🧠 Run Intelligence Analysis:")
                print(f"curl -X POST \"http://localhost:8000/intelligence/contracts/{contract_id}/analyze\"")
            else:
                print(f"\n⚠️  Contract ID not available (processing may be incomplete)")
                print(f"\n🧠 Try Intelligence Analysis with existing contracts:")
                print(f"curl -X POST \"http://localhost:8000/intelligence/contracts/NUVEEN%20-%20REMARKETING%20AGREEMENT/analyze\"")
            
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 upload_cli.py <pdf_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = upload_pdf(file_path)
    sys.exit(0 if success else 1)