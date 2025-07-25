from neo4j import GraphDatabase
import pandas as pd
import os
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

# Configuration
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
CSV_PATH = r"C:\Users\prajw\Downloads\student_scores_sample.csv"  # Update this path
SIMILARITY_THRESHOLD = 0.85  # Adjust this based on your needs

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def normalize_scores(df):
    """
    Normalize all scores to a 0-1 range based on their 'out of' value
    """
    normalized = df.copy()
    for col in df.columns:
        if 'out of' in str(col):
            try:
                # Extract the maximum score from column name
                max_score = int(col.split('(out of ')[1].strip(')'))
                # Normalize to 0-1 range
                normalized[col] = df[col].astype(float) / max_score
            except (ValueError, IndexError, KeyError) as e:
                print(f"Error processing column '{col}': {e}")
                normalized[col] = 0  # Default to 0 if error occurs
    return normalized

def import_graph(tx, df, grade="10"):
    """
    Import student data and their scores into Neo4j
    """
    df['Roll No'] = df['Roll No'].astype(int)
    
    for _, row in df.iterrows():
        # Create Student node
        tx.run("""
            MERGE (s:Student {roll_no: $roll_no})
            SET s.name = $name,
                s.gender = $gender,
                s.photo = $photo,
                s.grade = $grade
        """, {
            'roll_no': row['Roll No'],
            'name': row['Name'],
            'gender': row['Gender'],
            'photo': row.get('Photo', ''),
            'grade': grade
        })

        # Process all assessment columns
        for col in df.columns:
            if 'out of' in str(col):
                try:
                    # Parse column name to extract components
                    parts = col.split(" - ")
                    test_type = parts[0].strip()
                    topic_part = parts[-1].split(" (out of")
                    topic = topic_part[0].strip()
                    out_of = int(topic_part[-1].strip(") ").strip())
                    score = float(row[col])
                    
                    # Create AssessmentType node if it doesn't exist
                    tx.run("""
                        MERGE (at:AssessmentType {name: $test_type})
                    """, {'test_type': test_type})
                    
                    # Create Topic node with grade property
                    tx.run("""
                        MERGE (t:Topic {name: $topic, grade: $grade})
                        MERGE (at:AssessmentType {name: $test_type})
                        MERGE (s:Student {roll_no: $roll_no})
                        MERGE (s)-[r:SCORED_IN {type: $test_type}]->(t)
                        SET r.score = $score, 
                            r.out_of = $out_of,
                            r.normalized_score = $normalized_score
                    """, {
                        'roll_no': row['Roll No'],
                        'topic': topic,
                        'test_type': test_type,
                        'score': score,
                        'out_of': out_of,
                        'normalized_score': score / out_of,  # Store normalized score
                        'grade': grade
                    })
                    
                except (IndexError, ValueError, KeyError) as e:
                    print(f"Error processing column '{col}': {e}")
                    continue

def add_similarity_edges(tx, df):
    """
    Calculate similarity between students and create SIMILAR_TO relationships
    """
    df['Roll No'] = df['Roll No'].astype(int)
    
    # Normalize all scores first
    normalized_df = normalize_scores(df)
    
    # Get all score columns
    score_cols = [col for col in df.columns if 'out of' in str(col)]
    
    if not score_cols:
        print("⚠️ No score columns found for similarity calculation")
        return
    
    # Calculate similarity on normalized scores
    similarity_matrix = cosine_similarity(normalized_df[score_cols].values)
    
    # Create similarity relationships between students
    for i in range(len(df)):
        for j in range(i+1, len(df)):
            sim = similarity_matrix[i][j]
            if sim > SIMILARITY_THRESHOLD:
                tx.run("""
                    MATCH (a:Student {roll_no: $r1}), (b:Student {roll_no: $r2})
                    MERGE (a)-[s:SIMILAR_TO]->(b)
                    SET s.similarity_score = $sim,
                        s.type = "overall_performance"
                """, {
                    'r1': df.loc[i, 'Roll No'],
                    'r2': df.loc[j, 'Roll No'],
                    'sim': float(sim)
                })

def main():
    try:
        # Load and validate data
        df = pd.read_csv(CSV_PATH)
        
        if df.empty:
            raise ValueError("CSV file is empty")
        if 'Roll No' not in df.columns:
            raise ValueError("CSV must contain 'Roll No' column")
        
        # Specify grade (could be extracted from data if available)
        grade = "10"  
        
        with driver.session() as session:
            # Optional: Clear existing data
            # session.write_transaction(clear_database)
            
            # Import data
            session.write_transaction(import_graph, df, grade)
            session.write_transaction(add_similarity_edges, df)
            
        print("✅ Graph import complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()