import os
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval

from vertexai.preview import rag
from google.adk.tools import ToolContext

from typing import Any

def get_rag_resources(tool_context: ToolContext):

    # Access the state from tool_context

    current_grade = tool_context.state.get("current_grade")
    current_grade = current_grade.get("grade", None)

    if current_grade:
        rag_corpus = os.environ.get(f"RAG_CORPUS_GRADE_{current_grade}")

    else:
        rag_corpus = os.environ.get("RAG_CORPUS_GRADE_6")

    return [rag.RagResource(rag_corpus=rag_corpus)]


class DynamicRagRetrieval(VertexAiRagRetrieval):

    async def process_llm_request(self, *, tool_context: ToolContext, llm_request):
        self.vertex_rag_store.rag_resources = get_rag_resources(tool_context)
        print(f"RAG resources updated: {self.vertex_rag_store.rag_resources}")

        await super().process_llm_request(
            tool_context=tool_context, llm_request=llm_request
        )

        print(f"Processed LLM request with updated RAG resources: {self.vertex_rag_store.rag_resources}")


ask_vertex_retrieval = DynamicRagRetrieval(
    name="retrieve_rag_documentation",
    description=(
        "Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,"
    ),
    similarity_top_k=12,
    vector_distance_threshold=0.6,
)


def rag_query(
    corpus_name: str,
    query: str,
    tool_context: ToolContext,
) -> dict:
    """
    Query a Vertex AI RAG corpus with a user question and return relevant information.

    Args:
        corpus_name (str): The name of the corpus to query. If empty, the current corpus will be used.
                          Preferably use the resource_name from list_corpora results.
        query (str): The text query to search for in the corpus
        tool_context (ToolContext): The tool context

    Returns:
        dict: The query results and status
    """
    try:

        # Configure retrieval parameters
        rag_retrieval_config = rag.RagRetrievalConfig(
            top_k=20,
            filter=rag.Filter(vector_distance_threshold=0.6),
        )

        current_grade = tool_context.state.get("current_grade")
        current_grade = current_grade.get("grade", None)

        if current_grade:
            rag_corpus = os.environ.get(f"RAG_CORPUS_GRADE_{current_grade}")
        else:
            rag_corpus = os.environ.get("RAG_CORPUS_GRADE_6")

        # Perform the query
        print("Performing retrieval query...")
        response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=rag_corpus,
                )
            ],
            text=query,
            rag_retrieval_config=rag_retrieval_config,
        )

        # Process the response into a more usable format
        results = []
        if hasattr(response, "contexts") and response.contexts:
            for ctx_group in response.contexts.contexts:
                result = {
                    "source_uri": (
                        ctx_group.source_uri if hasattr(ctx_group, "source_uri") else ""
                    ),
                    "source_name": (
                        ctx_group.source_display_name
                        if hasattr(ctx_group, "source_display_name")
                        else ""
                    ),
                    "text": ctx_group.text if hasattr(ctx_group, "text") else "",
                    "score": ctx_group.score if hasattr(ctx_group, "score") else 0.0,
                }
                results.append(result)

        # If we didn't find any results
        if not results:
            return {
                "status": "warning",
                "message": f"No results found in corpus '{corpus_name}' for query: '{query}'",
                "query": query,
                "corpus_name": corpus_name,
                "results": [],
                "results_count": 0,
            }

        return {
            "status": "success",
            "message": f"Successfully queried corpus '{corpus_name}'",
            "query": query,
            "corpus_name": corpus_name,
            "results": results,
            "results_count": len(results),
        }

    except Exception as e:
        error_msg = f"Error querying corpus: {str(e)}"
        # logging.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "query": query,
            "corpus_name": corpus_name,
        }
