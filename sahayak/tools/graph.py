async def query_graph(tool_context) -> dict:
    """Debug version that shows exactly what the agent is sending"""
    from neo4j import GraphDatabase, basic_auth
    import os
    
    print("=== QUERY_GRAPH TOOL CALLED ===")
    print(f"Full tool_context.state: {tool_context.state}")
    
    # List all keys in state
    print(f"Available keys in state: {list(tool_context.state.keys())}")
    
    # Try to find our parameters in various possible locations
    possible_locations = [
        tool_context.state,
        tool_context.state.get('parameters', {}),
        tool_context.state.get('args', {}),
    ]
    
    for i, location in enumerate(possible_locations):
        if location and isinstance(location, dict):
            print(f"Location {i} contents: {location}")
            if any(key in location for key in ['user_intent', 'topic_a', 'grade']):
                print(f"Found parameters in location {i}: {location}")
                break
    
    # Original parameter extraction (with fallback debugging)
    params = tool_context.state
    user_intent = params.get("user_intent")
    topic_a = params.get("topic_a") 
    topic_b = params.get("topic_b")
    grade = params.get("grade")
    
    # Debug: check if parameters exist with different names
    if not user_intent:
        # Try alternative names
        for key in ['intent', 'action', 'task']:
            user_intent = params.get(key)
            if user_intent:
                print(f"Found intent with alternative key '{key}': {user_intent}")
                break
    
    print(f"Final extracted params: intent={user_intent}, topic_a={topic_a}, grade={grade}")
    print("=== END DEBUG INFO ===")
    
    # Rest of your original tool code...
    # (Return error if parameters are still missing)
    """
    Query the Neo4j graph database for educational insights.
    Expects parameters in tool_context.state:
    - user_intent: "find_highest" or "form_teams" 
    - topic_a: First topic name
    - topic_b: Second topic name (for team formation)
    - grade: Grade level
    """
    from neo4j import GraphDatabase, basic_auth
    import os

    try:
        # Get parameters from the tool context
        params = tool_context.state
        user_intent = params.get("user_intent")
        topic_a = params.get("topic_a") 
        topic_b = params.get("topic_b")
        grade = params.get("grade")

        print(f"DEBUG: Tool received params: intent={user_intent}, topic_a={topic_a}, topic_b={topic_b}, grade={grade}")

        # Validate required parameters
        if not user_intent:
            return {"status": "error", "message": "Missing user_intent parameter"}

        driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=basic_auth(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )

        if user_intent == "find_highest":
            if not topic_a:
                return {"status": "error", "message": "Missing topic_a for highest scorer query"}

            print(f"DEBUG: Looking for highest scorer in topic: {topic_a}")

            if grade:
                cypher_query = """
                MATCH (s:Student)-[r:SCORED_IN]->(t:Topic)
                WHERE toLower(t.name) = toLower($topic_name) AND t.grade = $grade
                RETURN s.name AS student_name, r.score AS score
                ORDER BY r.score DESC
                LIMIT 5
                """
                query_params = {"topic_name": topic_a, "grade": grade}
                print(f"DEBUG: Running grade-specific query with params: {query_params}")
            else:
                cypher_query = """
                MATCH (s:Student)-[r:SCORED_IN]->(t:Topic)
                WHERE toLower(t.name) = toLower($topic_name)
                RETURN s.name AS student_name, r.score AS score, t.grade AS grade
                ORDER BY r.score DESC
                LIMIT 5
                """
                query_params = {"topic_name": topic_a}
                print(f"DEBUG: Running general query with params: {query_params}")

        elif user_intent == "form_teams":
            if not topic_a or not topic_b or not grade:
                return {"status": "error", "message": f"Missing parameters for team formation: topic_a={topic_a}, topic_b={topic_b}, grade={grade}"}

            cypher_query = """
            MATCH (s:Student)-[r1:SCORED_IN]->(t1:Topic {grade: $grade}),
                  (s)-[r2:SCORED_IN]->(t2:Topic {grade: $grade})
            WHERE toLower(t1.name) = toLower($topic_a) 
              AND toLower(t2.name) = toLower($topic_b)
            RETURN s.name AS student_name, r1.score AS score_a, r2.score AS score_b
            ORDER BY s.name
            LIMIT 20
            """
            query_params = {"topic_a": topic_a, "topic_b": topic_b, "grade": grade}

        else:
            return {"status": "error", "message": f"Unknown intent: {user_intent}. Use 'find_highest' or 'form_teams'"}

        with driver.session() as session:
            records = session.run(cypher_query, query_params)
            data = [r.data() for r in records]

        print(f"DEBUG: Query returned {len(data)} results")
        if data:
            print(f"DEBUG: First few results: {data[:2]}")

        return {
            "status": "success" if data else "warning",
            "message": f"Query completed for intent: {user_intent}. Found {len(data)} results.",
            "results": data,
            "intent": user_intent
        }

    except Exception as e:
        print(f"DEBUG: Tool error: {str(e)}")
        return {"status": "error", "message": f"Database error: {str(e)}"}