# Section Order Preservation Strategy

## 🎯 Problem
Preserve the exact order of sections when extracting and storing contract sections in Neo4j.

## ✅ Solution - Multi-Level Order Preservation

### **1. Order Field (Primary)**
```python
Section {
    order: int  # Sequential: 0, 1, 2, 3...
}
```

### **2. Position Tracking (Secondary)**
```python
Section {
    start_position: int  # Character offset in original text
    end_position: int    # End character offset
}
```

### **3. Relationship Order (Tertiary)**
```cypher
(Contract)-[:HAS_SECTION {order: 0, sequence: 0}]->(Section)
```

### **4. Zero-Padded IDs (Quaternary)**
```python
section_id: "CONTRACT_123_section_001"  # Lexicographic sorting
section_id: "CONTRACT_123_section_002"
section_id: "CONTRACT_123_section_010"
```

## 📊 Storage Schema

```cypher
CREATE (s:Section {
    section_id: "CONTRACT_123_section_001",
    title: "Definitions",
    content: "...",
    order: 0,                    // Primary sort key
    start_position: 1250,        // Original text position
    end_position: 3400,          // End position
    section_type: "definitions",
    confidence: 0.95,
    tenant_id: "tenant_1",
    created_at: datetime()
})

CREATE (c:Contract)-[:HAS_SECTION {
    order: 0,        // Duplicate order on relationship
    sequence: 0      // Additional sequence field
}]->(s:Section)
```

## 🔍 Retrieval with Order Guarantee

```cypher
// Method 1: Order by section.order (Primary)
MATCH (c:Contract {file_id: $contract_id})-[:HAS_SECTION]->(s:Section)
RETURN s
ORDER BY s.order ASC

// Method 2: Order by relationship property
MATCH (c:Contract {file_id: $contract_id})-[r:HAS_SECTION]->(s:Section)
RETURN s
ORDER BY r.order ASC

// Method 3: Order by position (fallback)
MATCH (c:Contract {file_id: $contract_id})-[:HAS_SECTION]->(s:Section)
RETURN s
ORDER BY s.start_position ASC

// Method 4: Combined (most robust)
MATCH (c:Contract {file_id: $contract_id})-[r:HAS_SECTION]->(s:Section)
RETURN s
ORDER BY s.order ASC, s.start_position ASC
```

## 🛡️ Order Preservation Guarantees

### **During Extraction:**
1. Sections extracted sequentially from top to bottom
2. Order assigned incrementally: 0, 1, 2, 3...
3. Start/end positions captured from original text
4. Sorted before storage to ensure correctness

### **During Storage:**
1. Sections sorted by order before insertion
2. Transaction ensures atomic insertion
3. Order field indexed for fast retrieval
4. Relationship order property set

### **During Retrieval:**
1. Always ORDER BY s.order ASC
2. Fallback to start_position if order missing
3. Index on order field ensures O(log n) sorting

## 📈 Performance Optimization

### **Indexes:**
```cypher
CREATE INDEX section_order IF NOT EXISTS 
FOR (s:Section) ON (s.order)

CREATE INDEX section_position IF NOT EXISTS 
FOR (s:Section) ON (s.start_position)

CREATE INDEX section_contract IF NOT EXISTS 
FOR (s:Section) ON (s.contract_id)
```

### **Composite Index:**
```cypher
CREATE INDEX section_contract_order IF NOT EXISTS 
FOR (s:Section) ON (s.contract_id, s.order)
```

## 🔄 Order Validation

```python
def validate_section_order(sections: List[Section]) -> bool:
    """Validate section order is sequential"""
    orders = [s.order for s in sections]
    return orders == list(range(len(orders)))

def validate_position_order(sections: List[Section]) -> bool:
    """Validate positions are sequential"""
    positions = [s.start_position for s in sections]
    return positions == sorted(positions)
```

## 🎯 Best Practices

1. **Always sort before storage**: `sorted(sections, key=lambda x: x.order)`
2. **Use zero-padded IDs**: `f"{contract_id}_section_{order:03d}"`
3. **Store order in multiple places**: Node property + relationship property
4. **Index order fields**: For fast sorted retrieval
5. **Validate order**: Check sequential order before storage
6. **Use position as fallback**: If order field corrupted

## 🔧 Implementation

```python
# Extraction with order
sections = extractor.extract_sections(text)
sections = sorted(sections, key=lambda x: x.order)

# Storage with order preservation
for section in sections:
    store_section(
        order=section.order,
        start_position=section.start_position,
        end_position=section.end_position
    )

# Retrieval with order guarantee
sections = get_sections_ordered(contract_id)
# Returns sections in correct order
```

## ✅ Order Preservation Checklist

- [x] Order field on Section node
- [x] Start/end position tracking
- [x] Order property on HAS_SECTION relationship
- [x] Zero-padded section IDs
- [x] Sort before storage
- [x] Index on order field
- [x] ORDER BY in retrieval queries
- [x] Validation functions
- [x] Fallback to position-based ordering

**Result: 4-level redundancy ensures section order is never lost.**
