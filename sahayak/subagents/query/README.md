# Query Agent System Documentation

## Overview
The Query Agent System is designed to handle teacher queries related to teaching content. It consists of a main routing agent and three specialized sub-agents that handle different types of queries.

## Architecture

### Main Agent: `query_agent`
- **Role**: Main query routing agent that analyzes incoming queries and routes them to appropriate sub-agents
- **Model**: gemini-2.5-flash
- **Tools**: `rag_query`, `ask_vertex_retrieval`, `memorize`
- **Capabilities**:
  - Analyzes query types and determines routing strategy
  - Coordinates between multiple sub-agents for complex queries
  - Synthesizes results from multiple sources
  - Provides comprehensive educational responses

### Sub-Agents

#### 1. `textbook_content_agent`
- **Purpose**: Handles general textbook questions and generates analogies/examples
- **Model**: gemini-2.5-flash
- **Tools**: `rag_query`, `ask_vertex_retrieval`, `memorize`, `memorize_dict`
- **Specializations**:
  - Textbook content retrieval using RAG
  - Generating relatable analogies for complex concepts
  - Creating real-world examples for teaching
  - Providing comprehensive explanations with citations
  - Suggesting follow-up questions and related topics

#### 2. `interactive_image_agent`
- **Purpose**: Fetches textbook images and analyzes marked/highlighted sections
- **Model**: gemini-2.5-flash
- **Tools**: `rag_query`, `ask_vertex_retrieval`, `create_slide_images`, `memorize`, `memorize_dict`
- **Specializations**:
  - Fetching specific images from textbook using RAG
  - Confirming image matches teacher's request
  - Analyzing marked or circled parts of images
  - Providing detailed explanations of highlighted components
  - Creating relatable analogies for complex image parts
  - Generating educational content based on marked sections:
    - Clarifying questions about highlighted areas
    - Sample activities related to image components
    - Quiz questions focusing on marked sections
    - Discussion prompts for classroom use

#### 3. `flow_diagram_agent`
- **Purpose**: Creates flow diagrams, process charts, and visual representations
- **Model**: gemini-2.5-flash
- **Tools**: `rag_query`, `ask_vertex_retrieval`, `create_slide_images`, `memorize`, `memorize_dict`
- **Specializations**:
  - Breaking down complex processes into logical steps
  - Creating comprehensive flow diagrams with:
    - Clear start and end points
    - Logical flow with decision points
    - Descriptive labels and annotations
    - Educational visual elements
  - Generating pedagogically sound visual representations

## Query Flow

1. **Query Reception**: Teacher submits a query to the main `query_agent`
2. **Query Analysis**: Main agent analyzes the query type:
   - Textbook content questions → `textbook_content_agent`
   - Interactive image requests → `interactive_image_agent`
   - Flow diagram requests → `flow_diagram_agent`
3. **Routing**: Query is routed to the appropriate sub-agent(s)
4. **Processing**: Sub-agent processes the query using specialized tools
5. **Response Synthesis**: Main agent coordinates and synthesizes the final response
6. **Memory Storage**: Important information is stored for future reference

## Tools Integration

### RAG Tools
- `rag_query`: Direct corpus querying for textbook content
- `ask_vertex_retrieval`: Advanced retrieval with similarity search

### Image Generation
- `create_slide_images`: Generates visual content from descriptions

### Memory Management
- `memorize`: Stores important information
- `memorize_dict`: Stores structured data

## Usage Examples

### Textbook Content Query
```
Teacher: "Can you explain photosynthesis in simple terms with a good analogy?"
→ Routes to textbook_content_agent
→ Uses RAG to retrieve photosynthesis content
→ Generates relatable analogies (e.g., kitchen/factory analogy)
→ Provides comprehensive explanation with examples
```

### Interactive Image Query
```
Teacher: "Can you show me the diagram of the human heart from chapter 5?"
→ Routes to interactive_image_agent
→ Uses RAG to fetch the specific heart diagram
→ Provides the image and confirms it's correct

Teacher: [Sends same image with aorta circled] "Can you explain this part and create some questions about it?"
→ Routes to interactive_image_agent
→ Analyzes the marked aorta section
→ Provides detailed explanation of aorta function
→ Generates analogies (like highway system)
→ Creates quiz questions about marked area
```

### Flow Diagram Query
```
Teacher: "Can you create a flow diagram showing the steps of cellular respiration?"
→ Routes to flow_diagram_agent
→ Uses RAG to retrieve cellular respiration process
→ Breaks down into logical steps
→ Creates visual flow diagram with clear progression
```

## Configuration

All agents are configured with:
- `disallow_transfer_to_parent=True` (sub-agents)
- `disallow_transfer_to_peers=True` (prevents lateral transfers)
- Detailed instructions for specialized behavior
- Appropriate tool sets for their specific functions

This architecture ensures efficient query handling while maintaining educational quality and teaching effectiveness.
