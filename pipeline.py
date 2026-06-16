from google import genai
from schemas import KnowledgeGraphExtraction
from typing import List, Dict, Any
from google.genai import types


def extract_graph_from_chunks(chunks: List[str]) -> List[KnowledgeGraphExtraction]:
    """Iterates through text chunks and sends them to Gemini for structured extraction."""
    # Initialize the official Gemini client (requires GEMINI_API_KEY env variable)
    client = genai.Client()
    
    extracted_graphs = []
    
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        prompt = f"""
        You are an expert financial analyst and knowledge graph engineer.
        Analyze the following SEC 10-K text chunk and extract Companies, Competitors, Risk Factors, and their Relationships.
        
        Strict Guidelines:
        1. Create deterministic, unique uppercase string IDs for all nodes (e.g., 'APPLE_INC', 'CYBERSECURITY_BREACH').
        2. Ensure that every Relationship 'source' and 'target' matches an 'id' defined in the companies, competitors, or risk_factors arrays.
        3. Do not hallucinate or extrapolate beyond the provided text.
        
        SEC Text Chunk:
        {chunk}
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',  # High-speed structured extraction model
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=KnowledgeGraphExtraction,
                    temperature=0.1,  # Keep it highly deterministic
                ),
            )
            
            # Rehydrate the JSON string back into the Pydantic model for validation
            graph_chunk = KnowledgeGraphExtraction.model_validate_json(response.text)
            extracted_graphs.append(graph_chunk)
            
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            continue
            
    return extracted_graphs
