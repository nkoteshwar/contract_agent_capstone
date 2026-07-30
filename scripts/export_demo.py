from langchain_neo4j import Neo4jGraph
import json

print("Connecting to demo database...")

# Connect to demo database
demo_graph = Neo4jGraph(
    url="neo4j+s://demo.neo4jlabs.com:7687",
    username="legalcontracts",
    password="legalcontracts",
    database="legalcontracts"
)

print("Exporting contracts...")

# Export contracts with all related data
contracts = demo_graph.query("""
MATCH (c:Contract)
OPTIONAL MATCH (c)<-[r:PARTY_TO]-(p:Party)
OPTIONAL MATCH (p)-[:LOCATED_IN]->(country:Country)
OPTIONAL MATCH (c)-[:HAS_GOVERNING_LAW]->(gov:Country)
RETURN c as contract, 
       collect(DISTINCT {name: p.name, role: r.role, country: country.name}) as parties,
       gov.name as governing_country
""")

print(f"Found {len(contracts)} contracts")

# Save to JSON file
with open('data/demo_contracts.json', 'w') as f:
    json.dump(contracts, f, indent=2, default=str)

print(f"✅ Exported {len(contracts)} contracts to data/demo_contracts.json")

# Show sample data
if contracts:
    print("\nSample contract:")
    print(f"- ID: {contracts[0]['contract']['file_id']}")
    print(f"- Type: {contracts[0]['contract']['contract_type']}")
    print(f"- Parties: {len(contracts[0]['parties'])}")