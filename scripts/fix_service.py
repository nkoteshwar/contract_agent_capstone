#!/usr/bin/env python3

# Fix the document processing service to handle deterministic workflow
import re

# Read the file
with open('backend/application/services/document_processing_service.py', 'r') as f:
    content = f.read()

# Replace the problematic section
old_text = '''        # Check if storage tool was called
        if "contract_storage" not in tool_calls_made:
            logger.warning("Storage tool was not called during processing")
            result["status"] = "incomplete"
            result["final_result"] = f"Processing incomplete - storage not attempted. Tools called: {tool_calls_made}"'''

new_text = '''        # Check if storage was successful (either via tool calls or deterministic workflow)
        storage_attempted = "contract_storage" in tool_calls_made or "Storage Result:" in (final_result or "")
        if not storage_attempted:
            logger.warning("Storage was not attempted during processing")
            result["status"] = "incomplete"
            result["final_result"] = f"Processing incomplete - storage not attempted. Tools called: {tool_calls_made}"'''

# Make the replacement
content = content.replace(old_text, new_text)

# Write back
with open('backend/application/services/document_processing_service.py', 'w') as f:
    f.write(content)

print("Fixed document processing service")