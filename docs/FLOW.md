# Contract Intelligence Agent - Complete Flow

## Overview
This document traces the complete flow from user input to final output in the Contract Intelligence Agent system.

## End-to-End Flow

### 1. User Input (Frontend)
```
User types: "Show me all active Microsoft contracts"
Model selected: "gemini-2.5-flash"
```

**Frontend Components:**
- `ChatInput` component captures user message
- `ChatProvider` manages conversation state
- Model selection dropdown sets LLM choice

### 2. HTTP Request (Frontend → Backend)
```http
POST /run/
Content-Type: application/json

{
  "model": "gemini-2.5-flash",
  "prompt": "Show me all active Microsoft contracts",
  "history": "[]"  // JSON string of previous messages
}
```

### 3. Request Processing (Backend)
**File: `main.py`**
```python
# 1. Parse request payload
payload = RunPayload(model, prompt, history)

# 2. Rebuild conversation history
previous_messages = rebuild_history(history)

# 3. Create new HumanMessage
prompt_message = HumanMessage(content=prompt)
input_messages = [*previous_messages, prompt_message]
```

### 4. Agent Selection (AgentManager)
**File: `agent_manager.py`**
```python
# Get the requested model agent
agent = agent_manager.get_model_by_name("gemini-2.5-flash")
# Returns: LangGraph agent with Gemini 2.0 Flash LLM
```

### 5. Agent Execution (LangGraph)
**File: `agent.py`**

#### Step 5a: System Message Injection
```python
sys_msg = SystemMessage(
    content="You are a helpful assistant tasked with finding and explaining relevant information about internal contracts..."
)
messages = [sys_msg] + input_messages
```

#### Step 5b: LLM Processing
```python
# LLM receives: System message + conversation history + user query
# LLM analyzes: "Show me all active Microsoft contracts"
# LLM decides: Need to use ContractSearchTool
```

#### Step 5c: Tool Call Generation
```json
{
  "tool_calls": [{
    "name": "ContractSearch",
    "args": {
      "parties": ["Microsoft"],
      "active": true
    }
  }]
}
```

### 6. Tool Execution (ContractSearchTool)
**File: `tools/contract_search_tool.py`**

#### Step 6a: Parameter Processing
```python
def _run(self, parties=["Microsoft"], active=True, ...):
    return get_contracts(
        embedding,
        parties=["Microsoft"],
        active=True
    )
```

#### Step 6b: Cypher Query Construction
```python
# Build dynamic Cypher query
cypher_statement = "MATCH (c:Contract) "

# Add party filter
filters.append("""EXISTS {
    MATCH (c)<-[:PARTY_TO]-(party)
    WHERE toLower(party.name) CONTAINS $party_0
}""")
params["party_0"] = "microsoft"

# Add active filter
filters.append("c.end_date >= date()")

# Final query
cypher_statement += f"WHERE {' AND '.join(filters)} "
```

#### Step 6c: Neo4j Database Query
```cypher
MATCH (c:Contract) 
WHERE EXISTS {
    MATCH (c)<-[:PARTY_TO]-(party)
    WHERE toLower(party.name) CONTAINS $party_0
} AND c.end_date >= date()
WITH c ORDER BY c.effective_date DESC 
WITH collect(c) AS nodes
RETURN {
    total_count_of_contracts: size(nodes),
    example_values: [
        el in nodes[..5] |
        {
            summary: el.summary,
            contract_type: el.contract_type,
            file_id: el.file_id,
            effective_date: el.effective_date,
            end_date: el.end_date,
            parties: [(el)<-[r:PARTY_TO]-(party) | {name: party.name, role: r.role}],
            countries: apoc.coll.toSet([(el)<-[:PARTY_TO]-()-[:LOCATED_IN]->(country) | country.name])
        }
    ]
} AS output
```

#### Step 6d: Database Response
```json
[{
  "output": {
    "total_count_of_contracts": 3,
    "example_values": [
      {
        "summary": "Software licensing agreement with Microsoft Corporation...",
        "contract_type": "License Agreement",
        "file_id": "MSFT_001",
        "effective_date": "2023-01-15",
        "end_date": "2025-01-15",
        "parties": [
          {"name": "Microsoft Corporation", "role": "Licensor"},
          {"name": "ABC Corp", "role": "Licensee"}
        ],
        "countries": ["United States"]
      }
    ]
  }
}]
```

### 7. Tool Result Processing
**File: `agent.py`**
```python
# Tool result becomes ToolMessage
tool_message = ToolMessage(
    content=str(database_response),
    tool_call_id="call_123"
)
```

### 8. Final LLM Response Generation
```python
# LLM receives: Original query + Tool result
# LLM generates human-friendly response
ai_response = "I found 3 active contracts with Microsoft Corporation. Here are the details:

1. **Software License Agreement (MSFT_001)**
   - Type: License Agreement
   - Effective: January 15, 2023 - January 15, 2025
   - Parties: Microsoft Corporation (Licensor), ABC Corp (Licensee)
   - Location: United States
   
The contract involves software licensing with Microsoft as the licensor..."
```

### 9. Streaming Response (Backend → Frontend)
**File: `main.py`**

#### Step 9a: Tool Call Stream
```
data: {"content": "{\"name\": \"ContractSearch\", \"args\": {...}}", "type": "tool_call"}
```

#### Step 9b: Tool Message Stream
```
data: {"content": "[{\"output\": {...}}]", "type": "tool_message"}
```

#### Step 9c: AI Response Stream
```
data: {"content": "I found 3 active contracts", "type": "ai_message"}
data: {"content": " with Microsoft Corporation.", "type": "ai_message"}
data: {"content": " Here are the details:", "type": "ai_message"}
```

#### Step 9d: History Update
```
data: {"content": [...updated_conversation_history...], "type": "history"}
```

#### Step 9e: Stream End
```
data: {"content": "", "type": "end"}
```

### 10. Frontend Display (UI Update)
**File: `components/chat/output.tsx`**

#### Step 10a: Message Rendering
- Tool calls displayed as expandable sections
- Tool results shown in structured format
- AI responses rendered as markdown

#### Step 10b: State Updates
- Conversation history updated
- New messages added to chat
- Loading states cleared

## Data Flow Summary

```
User Input
    ↓
Frontend (React)
    ↓ HTTP POST
Backend (FastAPI)
    ↓
AgentManager
    ↓
LangGraph Agent
    ↓
LLM (Gemini/GPT/Claude)
    ↓
ContractSearchTool
    ↓
Neo4j Database
    ↓ Query Results
ContractSearchTool
    ↓ Tool Response
LLM Processing
    ↓ Final Answer
Streaming Response
    ↓ SSE Stream
Frontend Display
    ↓
User sees results
```

## Key Flow Characteristics

1. **Streaming**: Real-time response delivery via Server-Sent Events
2. **Stateless**: Each request includes full conversation history
3. **Tool-Driven**: LLM decides when and how to use contract search
4. **Graph-Powered**: Neo4j provides rich relationship queries
5. **Multi-LLM**: Same flow works with different language models
6. **Contextual**: System message shapes responses for business users

## Error Handling Flow

```
Error occurs
    ↓
Tool/LLM catches exception
    ↓
Error message in stream
    ↓
Frontend displays error
    ↓
User can retry or modify query
```

## Performance Optimizations

- **Lazy Loading**: Agents initialized on first use
- **Connection Pooling**: Neo4j driver reuses connections  
- **Streaming**: Immediate user feedback
- **Caching**: Schema refresh disabled
- **Efficient Queries**: Optimized Cypher with proper indexing