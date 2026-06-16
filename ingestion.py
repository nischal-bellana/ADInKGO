from neo4j import GraphDatabase
import json
from dotenv import load_dotenv
import os
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
load_dotenv()

# Initialize the lightweight embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def resolve_entities(graph_data: dict, similarity_threshold: float = 0.85) -> dict:
    """
    Groups highly similar entity names using embeddings and creates an ID mapping dictionary.
    
    Returns:
        dict: A mapping of { original_id: canonical_id }
    """
    # Collect all unique nodes from the graph payload
    all_nodes = []
    for category in ["companies", "competitors", "risk_factors"]:
        all_nodes.extend(graph_data.get(category, []))
        
    if not all_nodes:
        return {}

    # Extract text/names to embed (using 'name' for companies/competitors, 'id' or 'description' for risks)
    node_ids = [node["id"] for node in all_nodes]
    node_texts = [node.get("name", node["id"]) for node in all_nodes]
    
    # Generate embeddings
    embeddings = embedding_model.encode(node_texts, convert_to_numpy=True)
    
    # Calculate similarity matrix
    sim_matrix = cosine_similarity(embeddings)
    
    # Find clusters/duplicates and map them to a canonical ID
    id_mapping = {}
    visited = set()
    
    for i in range(len(node_ids)):
        if i in visited:
            continue
            
        canonical_id = node_ids[i]
        id_mapping[canonical_id] = canonical_id
        visited.add(i)
        
        # Check all other nodes for similarity
        for j in range(i + 1, len(node_ids)):
            if j not in visited and sim_matrix[i][j] >= similarity_threshold:
                # Resolve to the canonical ID of the first match
                id_mapping[node_ids[j]] = canonical_id
                visited.add(j)
                
    return id_mapping

def apply_resolution(graph_data: dict, id_mapping: dict) -> dict:
    """
    Rebuilds the graph data payload by applying the canonical ID mapping, 
    deduplicating entities, and updating relationships.
    """
    resolved_graph = {
        "companies": {},
        "competitors": {},
        "risk_factors": {},
        "relationships": set() # Use set to avoid duplicate relationships
    }
    
    # 1. Resolve and deduplicate Nodes
    for comp in graph_data.get("companies", []):
        new_id = id_mapping.get(comp["id"], comp["id"])
        comp["id"] = new_id
        resolved_graph["companies"][new_id] = comp  # Overwrites duplicates, keeping latest
        
    for comp in graph_data.get("competitors", []):
        new_id = id_mapping.get(comp["id"], comp["id"])
        comp["id"] = new_id
        resolved_graph["competitors"][new_id] = comp
        
    for risk in graph_data.get("risk_factors", []):
        new_id = id_mapping.get(risk["id"], risk["id"])
        risk["id"] = new_id
        resolved_graph["risk_factors"][new_id] = risk

    # 2. Update and deduplicate Relationships
    for rel in graph_data.get("relationships", []):
        resolved_source = id_mapping.get(rel["source"], rel["source"])
        resolved_target = id_mapping.get(rel["target"], rel["target"])
        
        # Avoid self-referencing loops created by entity resolution
        if resolved_source != resolved_target:
            resolved_graph["relationships"].add((resolved_source, resolved_target, rel["type"]))

    # Reconstruct final payload structural format
    return {
        "companies": list(resolved_graph["companies"].values()),
        "competitors": list(resolved_graph["competitors"].values()),
        "risk_factors": list(resolved_graph["risk_factors"].values()),
        "relationships": [
            {"source": r[0], "target": r[1], "type": r[2]} for r in resolved_graph["relationships"]
        ]
    }

class Neo4jIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def ingest_graph(self, resolved_graph_data: dict):
        """Executes batched transactional upserts to Neo4j."""
        with self.driver.session() as session:
            session.execute_write(self._upsert_nodes, resolved_graph_data)
            session.execute_write(self._upsert_relationships, resolved_graph_data.get("relationships", []))

    @staticmethod
    def _upsert_nodes(tx, graph_data: dict):
        # 1. Upsert Companies
        company_query = """
        UNWIND $companies AS comp
        MERGE (c:Company {id: comp.id})
        SET c.name = comp.name,
            c.ticker = comp.ticker,
            c.sector = comp.sector
        """
        tx.run(company_query, companies=graph_data.get("companies", []))

        # 2. Upsert Competitors
        competitor_query = """
        UNWIND $competitors AS comp
        MERGE (c:Competitor {id: comp.id})
        SET c.name = comp.name
        """
        tx.run(competitor_query, competitors=graph_data.get("competitors", []))

        # 3. Upsert Risk Factors
        risk_query = """
        UNWIND $risk_factors AS risk
        MERGE (r:RiskFactor {id: risk.id})
        SET r.description = risk.description,
            r.severity = risk.severity,
            r.category = risk.category
        """
        tx.run(risk_query, risk_factors=graph_data.get("risk_factors", []))

    @staticmethod
    def _upsert_relationships(tx, relationships: List[dict]):
        # Dynamic type handling in Cypher using APOC or standard string evaluation 
        # (Since relationship types are constrained literals, we map them securely)
        allowed_types = ["COMPETES_WITH", "VULNERABLE_TO", "PARTNERS_WITH", "AFFECTS"]
        
        for rel_type in allowed_types:
            # Filter relationships belonging to this specific type block
            filtered_rels = [r for r in relationships if r["type"] == rel_type]
            if not filtered_rels:
                continue

            # Cypher requires type to be hardcoded or used via APOC. This query safely resolves node labels dynamically.
            rel_query = f"""
            UNWIND $rels AS rel
            MATCH (source {{id: rel.source}})
            MATCH (target {{id: rel.target}})
            MERGE (source)-[r:{rel_type}]->(target)
            """
            tx.run(rel_query, rels=filtered_rels)

if __name__ == "__main__":
    
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    raw_payload = {}
    with open('Extracted/global_sec_knowledge_graph.json', 'r') as file:
        raw_payload = json.load(file)


    # Step 1: Run Entity Resolution
    print("Resolving entities...")
    mapping = resolve_entities(raw_payload, similarity_threshold=0.85)
    clean_payload = apply_resolution(raw_payload, mapping)

    with open('Extracted/clean_graph_data.json', 'w') as file:
        json.dump(clean_payload, file)
    
    # Step 2: Ingest into Neo4j
    db = Neo4jIngestor("bolt://localhost:7687", "neo4j", neo4j_password)
    db.ingest_graph(clean_payload)
    db.close()
