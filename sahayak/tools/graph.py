from google.adk.tools import BaseTool
from google.genai import types
from neo4j import AsyncGraphDatabase
import logging
import os
from typing import Optional, List, Dict, Any
import json
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GraphQueryState(BaseModel):
    user_intent: Optional[str] = None
    topic_a: Optional[str] = None
    topic_b: Optional[str] = None
    grade: Optional[str] = None


class GraphVisualizer(BaseTool):
    def __init__(self):
        super().__init__(
            name="graph_visualizer",
            description="Executes Neo4j graph queries to analyze student performance.",
        )

    def run(
        self,
        user_intent: str,
        topic_a: str,
        grade: Optional[str] = None,
        topic_b: Optional[str] = None,
    ):
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
                "topic_b": topic_b,
            }

            # Validate state
            parsed_state = GraphQueryState(
                **{k: v for k, v in state.items() if v is not None}
            )

        except Exception as e:
            error_msg = f"Invalid parameters: {e}"
            logger.error(error_msg)
            return types.Content(role="tool", parts=[types.Part(text=error_msg)])

        # Since we're in sync context, run the async method in a new event loop
        import asyncio
        import nest_asyncio  # ✅ Handle nested event loops

        try:
            # Allow nested event loops
            nest_asyncio.apply()
            result = asyncio.run(self._run_query(parsed_state))
            if isinstance(result, dict):
                json_string = json.dumps(result, indent=2)
                logger.info(
                    f"🔧 GraphVisualizer.run() returning JSON string: {json_string[:200]}..."
                )
                return types.Content(role="tool", parts=[types.Part(text=json_string)])
            else:
                return types.Content(role="tool", parts=[types.Part(text=result)])
        except Exception as e:
            error_msg = f"Query failed: {e}"
            logger.exception("Neo4j query failed")
            return types.Content(role="tool", parts=[types.Part(text=error_msg)])

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
                    return await self._find_highest_student(session, parsed_state)

                elif parsed_state.user_intent == "find_top_students":
                    return await self._find_top_students(session, parsed_state)

                elif parsed_state.user_intent == "form_teams":
                    return await self._form_teams(session, parsed_state)

                elif parsed_state.user_intent == "get_statistics":
                    return await self._get_topic_statistics(session, parsed_state)

                elif parsed_state.user_intent == "compare_topics":
                    return await self._compare_topics(session, parsed_state)

                else:
                    return "Unsupported or incomplete intent"
        except Exception as e:
            logger.exception("Neo4j query failed")
            return f"Query execution failed: {e}"
        finally:
            await driver.close()

    async def _find_highest_student(
        self, session, parsed_state: GraphQueryState
    ) -> str:
        """Find the highest scoring student."""
        result = await session.run(
            """
            MATCH (s:Student)-[r:SCORED_IN]->(t:Topic {name: $topic_a, grade: $grade})
            RETURN s.name AS student_name, r.score AS score
            ORDER BY r.score DESC
            LIMIT 1
        """,
            {"topic_a": parsed_state.topic_a.title(), "grade": parsed_state.grade},
        )
        record = await result.single()
        if record:
            return f"🏆 Top student in {parsed_state.topic_a} (Grade {parsed_state.grade}): {record['student_name']} (Score: {record['score']})"
        return f"No student found for {parsed_state.topic_a} topic in Grade {parsed_state.grade}"

    async def _find_top_students(self, session, parsed_state: GraphQueryState) -> str:
        """Find top 5 students for a topic."""
        result = await session.run(
            """
            MATCH (s:Student)-[r:SCORED_IN]->(t:Topic {name: $topic_a, grade: $grade})
            RETURN s.name AS student_name, r.score AS score
            ORDER BY r.score DESC
            LIMIT 5
        """,
            {"topic_a": parsed_state.topic_a.title(), "grade": parsed_state.grade},
        )
        students = await result.data()
        if students:
            rankings = []
            for i, student in enumerate(students, 1):
                rankings.append(f"{i}. {student['student_name']}: {student['score']}")
            return (
                f"🏅 Top 5 students in {parsed_state.topic_a} (Grade {parsed_state.grade}):\n"
                + "\n".join(rankings)
            )
        return f"No students found for {parsed_state.topic_a} topic in Grade {parsed_state.grade}"

    async def _form_teams(
        self, session, parsed_state: GraphQueryState
    ) -> Dict[str, Any]:
        """Enhanced team formation returning structured JSON."""
        if parsed_state.topic_b:
            # Dual topic team formation
            logger.info(
                f"Forming teams based on {parsed_state.topic_a} + {parsed_state.topic_b}"
            )

            topic_check = await session.run(
                """
                MATCH (t:Topic {grade: $grade})
                WHERE t.name IN [$topic_a, $topic_b]
                RETURN t.name AS topic_name
            """,
                {
                    "topic_a": parsed_state.topic_a.title(),
                    "topic_b": parsed_state.topic_b.title(),
                    "grade": parsed_state.grade,
                },
            )
            existing_topics = [record["topic_name"] async for record in topic_check]

            if len(existing_topics) < 2:
                missing = set(
                    [parsed_state.topic_a.title(), parsed_state.topic_b.title()]
                ) - set(existing_topics)
                return {
                    "error": f"Cannot form teams: Topics not found: {', '.join(missing)}"
                }

            result = await session.run(
                """
                MATCH (s:Student)-[r1:SCORED_IN]->(t1:Topic {name: $topic_a, grade: $grade}),
                    (s)-[r2:SCORED_IN]->(t2:Topic {name: $topic_b, grade: $grade})
                RETURN s.name AS student_name, r1.score AS score_a, r2.score AS score_b
                ORDER BY (r1.score + r2.score) DESC
                LIMIT 8
            """,
                {
                    "topic_a": parsed_state.topic_a.title(),
                    "topic_b": parsed_state.topic_b.title(),
                    "grade": parsed_state.grade,
                },
            )
            students = await result.data()

            if not students:
                return {
                    "error": f"No students found who have scores for both '{parsed_state.topic_a}' and '{parsed_state.topic_b}'"
                }
        else:
            # Single topic team formation
            logger.info(f"Forming teams based on {parsed_state.topic_a} only")

            topic_check = await session.run(
                """
                MATCH (t:Topic {name: $topic_a, grade: $grade})
                RETURN t.name AS topic_name
            """,
                {"topic_a": parsed_state.topic_a.title(), "grade": parsed_state.grade},
            )
            topic_exists = await topic_check.single()
            if not topic_exists:
                return {
                    "error": f"Cannot form teams: Topic '{parsed_state.topic_a}' not found for grade {parsed_state.grade}"
                }

            result = await session.run(
                """
                MATCH (s:Student)-[r:SCORED_IN]->(t:Topic {name: $topic_a, grade: $grade})
                RETURN s.name AS student_name, r.score AS score
                ORDER BY r.score DESC
                LIMIT 8
            """,
                {"topic_a": parsed_state.topic_a.title(), "grade": parsed_state.grade},
            )
            students = await result.data()

            if not students:
                return {
                    "error": f"No students found with scores for '{parsed_state.topic_a}' topic"
                }

        # ✅ Build structured team JSON
        teams = await self._create_balanced_teams(
            students, parsed_state.topic_b is not None
        )
        return {"type": "study_buddy", "teams": teams}

    async def _create_balanced_teams(
        self, students: List[Dict], is_dual_topic: bool
    ) -> str:
        """Create balanced teams with better distribution."""
        if len(students) == 1:
            student = students[0]
            if is_dual_topic:
                return f"Team 1: {student['student_name']} (Scores: {student['score_a']}, {student['score_b']}) (solo)"
            else:
                score = student.get("score", student.get("score_a", "N/A"))
                return f"Team 1: {student['student_name']} (Score: {score}) (solo)"

        # Create teams of 2-3 students for better collaboration
        teams = []
        team_size = 3 if len(students) >= 6 else 2

        for i in range(0, len(students), team_size):
            team_students = students[i : i + team_size]
            team_members = []

            for student in team_students:
                if is_dual_topic and "score_a" in student:
                    team_members.append(
                        f"{student['student_name']} ({student['score_a']}, {student['score_b']})"
                    )
                else:
                    score = student.get("score", student.get("score_a", "N/A"))
                    team_members.append(f"{student['student_name']} ({score})")

            team_str = f"Team {(i//team_size) + 1}: {', '.join(team_members)}"
            teams.append(team_str)

        return "\n".join(teams)

    async def _get_topic_statistics(
        self, session, parsed_state: GraphQueryState
    ) -> str:
        """Get statistics for a topic."""
        result = await session.run(
            """
            MATCH (s:Student)-[r:SCORED_IN]->(t:Topic {name: $topic_a, grade: $grade})
            RETURN 
                count(r) AS total_scores,
                avg(r.score) AS average_score,
                min(r.score) AS min_score,
                max(r.score) AS max_score
        """,
            {"topic_a": parsed_state.topic_a.title(), "grade": parsed_state.grade},
        )
        record = await result.single()
        if record:
            return (
                f"📊 Statistics for {parsed_state.topic_a} (Grade {parsed_state.grade}):\n"
                f"• Total students: {record['total_scores']}\n"
                f"• Average score: {record['average_score']:.1f}\n"
                f"• Highest score: {record['max_score']}\n"
                f"• Lowest score: {record['min_score']}"
            )
        return f"No data found for {parsed_state.topic_a} topic in Grade {parsed_state.grade}"

    async def _compare_topics(self, session, parsed_state: GraphQueryState) -> str:
        """Compare performance between two topics."""
        if not parsed_state.topic_b:
            return "Please specify two topics to compare"

        # Get average scores for both topics
        result_a = await session.run(
            """
            MATCH (s:Student)-[r:SCORED_IN]->(t:Topic {name: $topic_a, grade: $grade})
            RETURN avg(r.score) AS avg_score, count(r) AS student_count
        """,
            {"topic_a": parsed_state.topic_a.title(), "grade": parsed_state.grade},
        )
        record_a = await result_a.single()

        result_b = await session.run(
            """
            MATCH (s:Student)-[r:SCORED_IN]->(t:Topic {name: $topic_b, grade: $grade})
            RETURN avg(r.score) AS avg_score, count(r) AS student_count
        """,
            {"topic_b": parsed_state.topic_b.title(), "grade": parsed_state.grade},
        )
        record_b = await result_b.single()

        if not record_a or not record_b:
            return "Insufficient data for comparison"

        avg_a = record_a["avg_score"] or 0
        avg_b = record_b["avg_score"] or 0

        comparison = "📈 Topic Comparison:\n"
        comparison += f"• {parsed_state.topic_a}: {avg_a:.1f} avg (from {record_a['student_count']} students)\n"
        comparison += f"• {parsed_state.topic_b}: {avg_b:.1f} avg (from {record_b['student_count']} students)\n"

        if avg_a > avg_b:
            diff = avg_a - avg_b
            comparison += (
                f"• {parsed_state.topic_a} performed better by {diff:.1f} points"
            )
        elif avg_b > avg_a:
            diff = avg_b - avg_a
            comparison += (
                f"• {parsed_state.topic_b} performed better by {diff:.1f} points"
            )
        else:
            comparison += "• Both topics showed similar performance"

        return comparison
