from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv
import json
import os

load_dotenv()

print("Connecting to your Aura database...")

# Connect to your Aura database
aura_graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)

print("Loading exported data...")

# Load exported data
try:
    with open('data/demo_contracts.json', 'r') as f:
        contracts = json.load(f)
    print(f"Loaded {len(contracts)} contracts")
except FileNotFoundError:
    print("❌ data/demo_contracts.json not found. Run scripts/export_demo.py first!")
    exit(1)

print("Creating database constraints...")

# Create constraints for better performance
try:
    aura_graph.query("CREATE CONSTRAINT contract_id IF NOT EXISTS FOR (c:Contract) REQUIRE c.file_id IS UNIQUE")
    aura_graph.query("CREATE CONSTRAINT party_name IF NOT EXISTS FOR (p:Party) REQUIRE p.name IS UNIQUE")
    aura_graph.query("CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE")
    print("✅ Constraints created")
except Exception as e:
    print(f"⚠️  Constraint creation: {e}")

print("Importing contracts...")

# Import each contract
imported_count = 0
for i, item in enumerate(contracts):
    try:
        contract = item['contract']
        parties = item['parties'] or []
        governing_country = item.get('governing_country')
        
        # Create contract node
        aura_graph.query("""
        MERGE (c:Contract {file_id: $file_id})
        SET c.summary = $summary,
            c.contract_type = $contract_type,
            c.contract_scope = $contract_scope,
            c.effective_date = date($effective_date),
            c.end_date = date($end_date),
            c.total_amount = $total_amount,
            c.embedding = $embedding
        """, {
            'file_id': contract.get('file_id', f'contract_{i}'),
            'summary': contract.get('summary', ''),
            'contract_type': contract.get('contract_type', 'Unknown'),
            'contract_scope': contract.get('contract_scope', ''),
            'effective_date': str(contract.get('effective_date', '2023-01-01')),
            'end_date': str(contract.get('end_date', '2025-01-01')),
            'total_amount': contract.get('total_amount', 0),
            'embedding': contract.get('embedding', [])
        })
        
        # Create party relationships
        for party in parties:
            if party.get('name'):
                aura_graph.query("""
                MATCH (c:Contract {file_id: $file_id})
                MERGE (p:Party {name: $party_name})
                MERGE (p)-[:PARTY_TO {role: $role}]->(c)
                """, {
                    'file_id': contract.get('file_id', f'contract_{i}'),
                    'party_name': party['name'],
                    'role': party.get('role', 'Unknown')
                })
                
                # Create country for party if available
                if party.get('country'):
                    aura_graph.query("""
                    MATCH (p:Party {name: $party_name})
                    MERGE (country:Country {name: $country_name})
                    MERGE (p)-[:LOCATED_IN]->(country)
                    """, {
                        'party_name': party['name'],
                        'country_name': party['country']
                    })
        
        # Create governing law relationship
        if governing_country:
            aura_graph.query("""
            MATCH (c:Contract {file_id: $file_id})
            MERGE (gov:Country {name: $country_name})
            MERGE (c)-[:HAS_GOVERNING_LAW]->(gov)
            """, {
                'file_id': contract.get('file_id', f'contract_{i}'),
                'country_name': governing_country
            })
        
        imported_count += 1
        if imported_count % 10 == 0:
            print(f"Imported {imported_count}/{len(contracts)} contracts...")
            
    except Exception as e:
        print(f"❌ Error importing contract {i}: {e}")

print(f"✅ Import completed! {imported_count}/{len(contracts)} contracts imported")

# Verify import
result = aura_graph.query("MATCH (c:Contract) RETURN count(c) as contract_count")
print(f"Total contracts in database: {result[0]['contract_count']}")

result = aura_graph.query("MATCH (p:Party) RETURN count(p) as party_count")
print(f"Total parties in database: {result[0]['party_count']}")

print("\n🎉 Your Neo4j Aura database is ready!")