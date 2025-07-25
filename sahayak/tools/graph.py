async def query_graph(tool_context) -> dict:
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
        # Get parameters from the tool context (this is how Google ADK passes them)
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

            if grade:
                cypher_query = """
                MATCH (s:Student)-[r:SCORED_IN]->(t:Topic)
                WHERE toLower(t.name) = toLower($topic_name) AND t.grade = $grade
                RETURN s.name AS student_name, r.score AS score
                ORDER BY r.score DESC
                LIMIT 1
                """
                query_params = {"topic_name": topic_a, "grade": grade}
            else:
                cypher_query = """
                MATCH (s:Student)-[r:SCORED_IN]->(t:Topic)
                WHERE toLower(t.name) = toLower($topic_name)
                RETURN s.name AS student_name, r.score AS score, t.grade AS grade
                ORDER BY r.score DESC
                LIMIT 1
                """
                query_params = {"topic_name": topic_a}

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

        return {
            "status": "success" if data else "warning",
            "message": f"Query completed for intent: {user_intent}",
            "results": data,
            "intent": user_intent
        }

    except Exception as e:
        print(f"DEBUG: Tool error: {str(e)}")
        return {"status": "error", "message": f"Database error: {str(e)}"}