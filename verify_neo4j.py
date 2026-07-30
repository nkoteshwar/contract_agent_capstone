import os
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()

try:
    graph = Neo4jGraph()
    print("Neo4j Connected successfully!")
except Exception as e:
    print(f"Neo4j Connection Failed: {e}")
    exit(1)
