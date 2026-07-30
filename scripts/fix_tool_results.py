#!/usr/bin/env python3

# Fix tool results capture
with open('backend/application/services/document_processing_service.py', 'r') as f:
    content = f.read()

# Add tool results capture
old_updates = '''            elif chunk[0] == "updates":
                if "assistant" in chunk[1]:
                    for msg in chunk[1]["assistant"]["messages"]:
                        if hasattr(msg, 'content'):
                            final_result = msg.content
                            logger.info(f"Final result updated: {msg.content[:100]}...")'''

new_updates = '''            elif chunk[0] == "updates":
                if "assistant" in chunk[1]:
                    for msg in chunk[1]["assistant"]["messages"]:
                        if hasattr(msg, 'content'):
                            final_result = msg.content
                            logger.info(f"Final result updated: {msg.content[:100]}...")
                elif "tools" in chunk[1]:
                    for msg in chunk[1]["tools"]["messages"]:
                        if hasattr(msg, 'content'):
                            processing_results.append(msg.content)
                            logger.info(f"Tool result: {msg.content[:100]}...")'''

content = content.replace(old_updates, new_updates)

# Fix contract ID extraction
old_extract = '''        # Try to extract contract ID from results
        logger.info(f"Extracting contract ID from final result: {final_result}")
        
        if final_result:
            if "SUCCESS: Contract stored with ID:" in final_result:
                contract_id = final_result.split("SUCCESS: Contract stored with ID:")[-1].strip()
                result["contract_id"] = contract_id
                result["status"] = "success"
                logger.info(f"Contract stored successfully with ID: {contract_id}")
            elif "REVIEW_REQUIRED" in final_result:
                result["status"] = "review_required"
                logger.info("Contract requires review")
            elif "SKIPPED" in final_result:
                result["status"] = "skipped"
                logger.info("Contract processing skipped")
            elif "ERROR" in final_result:
                result["status"] = "error"
                logger.error(f"Contract processing error: {final_result}")'''

new_extract = '''        # Try to extract contract ID from all results (including tool results)
        all_results = processing_results + ([final_result] if final_result else [])
        logger.info(f"Extracting contract ID from {len(all_results)} result messages")
        
        for result_text in all_results:
            if result_text and "SUCCESS: Contract stored with ID:" in result_text:
                contract_id = result_text.split("SUCCESS: Contract stored with ID:")[-1].strip()
                result["contract_id"] = contract_id
                result["status"] = "success"
                logger.info(f"Contract stored successfully with ID: {contract_id}")
                break
            elif result_text and "REVIEW_REQUIRED" in result_text:
                result["status"] = "review_required"
            elif result_text and "SKIPPED" in result_text:
                result["status"] = "skipped"
            elif result_text and "ERROR" in result_text:
                result["status"] = "error"
                logger.error(f"Contract processing error: {result_text}")'''

content = content.replace(old_extract, new_extract)

with open('backend/application/services/document_processing_service.py', 'w') as f:
    f.write(content)

print("Fixed tool results capture and contract ID extraction")