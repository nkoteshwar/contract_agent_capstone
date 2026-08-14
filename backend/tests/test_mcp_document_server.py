import unittest
import json
import asyncio
from unittest.mock import patch, MagicMock

# Import the tool wrapper directly from our new server
from backend.mcp_document_server import extract_contract_sections

class TestMCPDocumentServer(unittest.IsolatedAsyncioTestCase):
    
    @patch('backend.mcp_document_server.get_text_extractor')
    @patch('backend.mcp_document_server.get_section_agent')
    async def test_extract_contract_sections_all(self, mock_get_agent, mock_get_extractor):
        # Setup mocks
        mock_extractor = MagicMock()
        mock_extractor.extract_with_fallback.return_value = "Mock contract text"
        mock_get_extractor.return_value = mock_extractor
        
        mock_agent = MagicMock()
        mock_agent.extract_sections.return_value = [
            {"title": "Termination", "content": "Termination text..."},
            {"title": "Indemnification", "content": "Indemnity text..."},
            {"title": "General terms", "content": "General terms..."}
        ]
        mock_get_agent.return_value = mock_agent
        
        # Call tool without target_sections
        result_json = await extract_contract_sections("dummy_path.pdf")
        result = json.loads(result_json)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["total_sections_found"], 3)
        self.assertEqual(result["sections_returned"], 3)
        
    @patch('backend.mcp_document_server.get_text_extractor')
    @patch('backend.mcp_document_server.get_section_agent')
    async def test_extract_contract_sections_filtered(self, mock_get_agent, mock_get_extractor):
        # Setup mocks
        mock_extractor = MagicMock()
        mock_extractor.extract_with_fallback.return_value = "Mock contract text"
        mock_get_extractor.return_value = mock_extractor
        
        mock_agent = MagicMock()
        mock_agent.extract_sections.return_value = [
            {"title": "Termination", "content": "Termination text..."},
            {"title": "Indemnification", "content": "Indemnity text..."},
            {"title": "General", "content": "General terms..."}
        ]
        mock_get_agent.return_value = mock_agent
        
        # Call tool with specific target_sections (using case-insensitive substring)
        result_json = await extract_contract_sections("dummy_path.pdf", ["termin", "general"])
        result = json.loads(result_json)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["total_sections_found"], 3)
        self.assertEqual(result["sections_returned"], 2)
        
        returned_titles = [s["title"] for s in result["sections"]]
        self.assertIn("Termination", returned_titles)
        self.assertIn("General", returned_titles)
        self.assertNotIn("Indemnification", returned_titles)
        
    @patch('backend.mcp_document_server.get_text_extractor')
    async def test_extract_contract_sections_failure(self, mock_get_extractor):
        # Mock a failure in the extraction process
        mock_extractor = MagicMock()
        mock_extractor.extract_with_fallback.side_effect = Exception("File read error")
        mock_get_extractor.return_value = mock_extractor
        
        result_json = await extract_contract_sections("bad_path.pdf")
        result = json.loads(result_json)
        
        self.assertFalse(result["success"])
        self.assertIn("File read error", result["error"])

if __name__ == "__main__":
    unittest.main()
