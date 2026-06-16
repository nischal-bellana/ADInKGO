import json
from pathlib import Path
from utils import chunk_text, merge_knowledge_graphs
from pipeline import extract_graph_from_chunks
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    # 1. Define the directory where your text files are stored
    input_dir = Path("./Extracted")
    
    # This list will hold the extracted graph objects from ALL companies
    all_extracted_graphs = []
    
    # 2. Find and loop through all .txt files in the data directory
    text_files = list(input_dir.glob("*.txt"))
    
    if not text_files:
        print(f"No .txt files found in {input_dir.absolute()}. Please add files and try again.")
        exit()
        
    print(f"Found {len(text_files)} files to process.\n")

    for file_path in text_files:
        print(f"==================================================")
        print(f"STARTING PROCESSING FOR: {file_path.name}")
        print(f"==================================================")
        
        try:
            # 3. Read the raw text from the current company file
            with open(file_path, "r", encoding="utf-8") as f:
                raw_company_text = f.read()
                
            if not raw_company_text.strip():
                print(f"Skipping empty file: {file_path.name}")
                continue
            
            # 4. Chunk this specific company's text safely
            # Using 4000 character windows with a 400 character overlap
            company_chunks = chunk_text(raw_company_text, chunk_size=4000, overlap=400)
            print(f"Split {file_path.name} into {len(company_chunks)} chunks.")
            
            # 5. Extract the graph structured data for this company's chunks
            company_graphs = extract_graph_from_chunks(company_chunks)
            
            # 6. Append the results to our master staging list
            all_extracted_graphs.extend(company_graphs)
            print(f"Successfully processed {file_path.name}\n")
            
        except Exception as e:
            print(f"Critical error processing file {file_path.name}: {e}")
            # Continue to the next file even if this one failed
            continue

    # 7. Merge and deduplicate across all companies globally
    print("Combining and deduplicating global entities and relationships...")
    final_master_graph = merge_knowledge_graphs(all_extracted_graphs)
    
    # 8. Save the entire unified knowledge graph to a final JSON file
    output_file = "Extracted/global_sec_knowledge_graph.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_master_graph, f, indent=2)
        
    print(f"\n--- Master Pipeline Complete! Output saved to {output_file} ---")
