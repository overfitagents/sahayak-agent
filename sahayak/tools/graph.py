from google.adk.tools import BaseTool
from google.genai import types
from sahayak.tools.graph_state import GraphQueryState
from neo4j import AsyncGraphDatabase
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class GraphVisualizer(BaseTool):
    def __init__(self):
        super().__init__(
            name="graph_visualizer",
            description="Executes Neo4j graph queries to analyze student performance."
        )

    def run(self, user_intent: str, topic_a: str, grade: Optional[str] = None, topic_b: Optional[str] = None):
        """
        Sync wrapper for async Neo4j query execution.
        """
        logger.info(f"🔧 GraphVisualizer.run() called with:")
        logger.info(f"   user_intent={user_intent}")
        logger.info(f"   topic_a={topic_a}")
        logger.info(f"   grade={grade}")
        logger.info(f"   topic_b={topic_b}")

        try:
            # Build state dict
            state = {
                "user_intent": user_intent,
                "topic_a": topic_a,
                "grade": grade,
                "topic_b": topic_b
            }
            
            # Validate state
            parsed_state = GraphQueryState(**{k: v for k, v in state.items() if v is not None})
            
        except Exception as e:
            error_msg = f"Invalid parameters: {e}"
            logger.error(error_msg)
            return types.Content(
                role="tool",
                parts=[types.Part(text=error_msg)]
            )

        # Since we're in sync context, run the async method in a new event loop
        import asyncio
        import nest_asyncio  # ✅ Handle nested event loops
        
        try:
            # Allow nested event loops
            nest_asyncio.apply()
            result = asyncio.run(self._run_query(parsed_state))
            return types.Content(
                role="tool",
                parts=[types.Part(text=result)]
            )
        except Exception as e:
            error_msg = f"Query failed: {e}"
            logger.exception("Neo4j query failed")
            return types.Content(
                role="tool",
                parts=[types.Part(text=error_msg)]
            )

    async def _run_query(self, parsed_state: GraphQueryState) -> str:
        """Async method to run Neo4j queries."""
        logger.info("🚀 Executing Neo4j query...")
        
        driver = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
        )

        try:
            async with driver.session(database="neo4j") as session:
                if parsed_state.user_intent == "find_highest":
                    # ✅ Fixed: Filter by topic.grade instead of student.grade
                    result = await session.run("""
                        MATCH (s:Student)-[r:SCORED_IN]->(t:Topic {name: $topic_a, grade: $grade})
                        RETURN s.name AS student_name, r.score AS score
                        ORDER BY r.score DESC
                        LIMIT 1
                    """, {
                        "topic_a": parsed_state.topic_a.title(),  # "light" -> "Light"
                        "grade": parsed_state.grade              # "6" (topic grade)
                    })
                    record = await result.single()
                    if record:
                        return f"Top student in {parsed_state.topic_a} (Grade {parsed_state.grade}): {record['student_name']} (Score: {record['score']})"
                    return "No student found for this grade and topic"

                elif parsed_state.user_intent == "form_teams" and parsed_state.topic_b:
                    # ✅ First validate that both topics exist
                    topic_check = await session.run("""
                        MATCH (t:Topic {grade: $grade})
                        WHERE t.name IN [$topic_a, $topic_b]
                        RETURN t.name AS topic_name
                    """, {
                        "topic_a": parsed_state.topic_a.title(),
                        "topic_b": parsed_state.topic_b.title(),
                        "grade": parsed_state.grade
                    })
                    existing_topics = []
                    async for record in topic_check:
                        existing_topics.append(record["topic_name"])
                    
                    logger.info(f"Existing topics: {existing_topics}")
                    
                    if len(existing_topics) < 2:
                        missing = set([parsed_state.topic_a.title(), parsed_state.topic_b.title()]) - set(existing_topics)
                        return f"Cannot form teams: Topics not found: {', '.join(missing)}"
                    
                    # ✅ Check if any students have scores for both topics
                    debug_result = await session.run("""
                        MATCH (s:Student)-[r1:SCORED_IN]->(t1:Topic {name: $topic_a, grade: $grade}),
                              (s)-[r2:SCORED_IN]->(t2:Topic {name: $topic_b, grade: $grade})
                        RETURN s.name AS student_name, r1.score AS score_a, r2.score AS score_b
                        ORDER BY (r1.score + r2.score) DESC
                        LIMIT 4
                    """, {
                        "topic_a": parsed_state.topic_a.title(),
                        "topic_b": parsed_state.topic_b.title(),
                        "grade": parsed_state.grade
                    })
                    students = await debug_result.data()
                    
                    if not students:
                        return f"No students found who have scores for both '{parsed_state.topic_a}' and '{parsed_state.topic_b}' topics"
                    
                    teams = []
                    for i in range(0, len(students), 2):
                        team = f"Team {i//2 + 1}: {students[i]['student_name']}"
                        if i + 1 < len(students):
                            team += f", {students[i+1]['student_name']}"
                        else:
                            team += " (solo)"
                        teams.append(team)
                    
                    return f"Teams formed: {', '.join(teams)}"

                else:
                    return "Unsupported or incomplete intent"
        except Exception as e:
            logger.exception("Neo4j query failed")
            return f"Query execution failed: {e}"
        finally:
            await driver.close()