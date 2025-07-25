from neo4j import GraphDatabase
import pandas as pd
import os
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv

load_dotenv()

print(os.environ.get('NEO4J_URI'))
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")  # Added default value
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")        # Added default value
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")    # Added default value

CSV_PATH = r"C:\Users\prajw\Downloads\student_scores_sample.csv"
# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def import_graph(tx, df):
    # First clean the data
    df['Roll No'] = df['Roll No'].astype(int)
    
    for _, row in df.iterrows():
        # Create Student node
        tx.run("""
            MERGE (s:Student {roll_no: $roll_no})
            SET s.name = $name,
                s.gender = $gender,
                s.photo = $photo
        """, {
            'roll_no': row['Roll No'],
            'name': row['Name'],
            'gender': row['Gender'],
            'photo': row.get('Photo', '')  # Use get() with default in case column is missing
        })

        for col in df.columns:
            if 'out of' in str(col):  # Added str() in case column is not string
                try:
                    parts = col.split(" - ")
                    test_type = parts[0].strip()
                    topic_part = parts[-1].split(" (out of")
                    topic = topic_part[0].strip()
                    out_of = int(topic_part[-1].strip(") ").strip())
                    score = int(row[col])
                except (IndexError, ValueError) as e:
                    print(f"Error processing column '{col}': {e}")
                    continue

                tx.run("""
                    MERGE (t:Topic {name: $topic})
                    MERGE (s:Student {roll_no: $roll_no})
                    MERGE (s)-[r:SCORED_IN {test: $test_type}]->(t)
                    SET r.score = $score, r.out_of = $out_of
                """, {
                    'roll_no': row['Roll No'],
                    'topic': topic,
                    'test_type': test_type,
                    'score': score,
                    'out_of': out_of
                })

def add_similarity_edges(tx, df):
    # Ensure Roll No is clean
    df['Roll No'] = df['Roll No'].astype(int)
    
    score_cols = [col for col in df.columns if 'out of' in str(col)]
    
    if not score_cols:
        print("⚠️ No score columns found for similarity calculation")
        return
        
    # Handle missing values - fill with 0 or mean as appropriate
    score_data = df[score_cols].fillna(0).astype(float)
    
    scaler = MinMaxScaler()
    try:
        score_vectors = scaler.fit_transform(score_data)
    except ValueError as e:
        print(f"Error in scaling: {e}")
        return
        
    similarity_matrix = cosine_similarity(score_vectors)

    for i in range(len(df)):
        for j in range(i+1, len(df)):
            sim = similarity_matrix[i][j]
            if sim > 0.85:
                tx.run("""
                    MATCH (a:Student {roll_no: $r1}), (b:Student {roll_no: $r2})
                    MERGE (a)-[s:SIMILAR_TO]->(b)
                    SET s.similarity = $sim
                """, {
                    'r1': df.loc[i, 'Roll No'],
                    'r2': df.loc[j, 'Roll No'],
                    'sim': float(sim)
                })

def main():
    try:
        df = pd.read_csv(CSV_PATH)
        
        # Basic data validation
        if df.empty:
            raise ValueError("CSV file is empty")
        if 'Roll No' not in df.columns:
            raise ValueError("CSV must contain 'Roll No' column")
            
        with driver.session() as session:
            session.write_transaction(import_graph, df)
            session.write_transaction(add_similarity_edges, df)
        print("✅ Graph import complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.close()  # Always close the driver

if __name__ == "__main__":
    main()