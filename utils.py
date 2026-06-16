import json
from typing import List, Dict, Any
from pydantic import BaseModel
from schemas import KnowledgeGraphExtraction

# Assuming the Pydantic models from earlier (KnowledgeGraphExtraction, etc.) are imported here.
# from schema import KnowledgeGraphExtraction

def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 400) -> List[str]:
    """
    Splits text into fixed-size chunks with a sliding window overlap.
    Using character-based splitting as a safe proxy for token budget.
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Move start forward by chunk_size minus overlap
        start += (chunk_size - overlap)
        
    return chunks

def merge_knowledge_graphs(graphs: List[KnowledgeGraphExtraction]) -> Dict[str, Any]:
    """Merges multiple extracted graph chunks into a single unique graph payload."""
    master_companies = {}
    master_competitors = {}
    master_risks = {}
    master_relationships = set() # Use a set of tuples to naturally deduplicate edges

    for graph in graphs:
        # Merge Company nodes
        for co in graph.companies:
            master_companies[co.id] = co.model_dump()
            
        # Merge Competitor nodes
        for comp in graph.competitors:
            master_competitors[comp.id] = comp.model_dump()
            
        # Merge Risk Factor nodes
        for risk in graph.risk_factors:
            # If a risk appears in multiple chunks, we keep the longest description
            if risk.id in master_risks:
                if len(risk.description) > len(master_risks[risk.id]['description']):
                    master_risks[risk.id] = risk.model_dump()
            else:
                master_risks[risk.id] = risk.model_dump()
                
        # Merge Relationships
        for rel in graph.relationships:
            # Create a unique edge tuple to prevent duplicate lines
            edge_tuple = (rel.source, rel.target, rel.type)
            master_relationships.add(edge_tuple)

    # Reconstruct into a clean final JSON dictionary structure
    final_relationships = [
        {"source": src, "target": tgt, "type": ttype} 
        for src, tgt, ttype in master_relationships
    ]

    return {
        "companies": list(master_companies.values()),
        "competitors": list(master_competitors.values()),
        "risk_factors": list(master_risks.values()),
        "relationships": final_relationships
    }

