# manager/sub_agents/knowledge_base/agent.py

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from pydantic import BaseModel, Field


# Define the expected parameters for the tool
class KnowledgeBaseToolInput(BaseModel):
    question: str = Field(..., description="The complex question to answer.")
    language: str = Field(default="English", description="Target language for the explanation.")
# --- Pydantic Model for structured search results (Optional, but good practice if needed) ---
# For simplicity, we'll let the search agent directly output text,
# but if you wanted structured results from search, you'd define a schema here.

# --- Sub-Agent 1: Google Search Agent ---
# This agent will perform the actual Google Search.
# ADK provides a built-in GoogleSearch tool.
google_search_agent = LlmAgent(
    name="GoogleSearchAgent",
    model="gemini-1.5-flash", # Flash is good for quickly generating search queries
    description="Performs a Google Search to find information on a given query.",
    instruction="""
    You are an expert search query generator.
    Given a user's question, formulate the most effective and concise Google Search query.
    Your goal is to find accurate and simple explanations suitable for primary school teachers or for simplifying for children.
    
    The question is: '{session.state.question}'
    Desired language for the answer: '{session.state.language}'

    Output only the search query string. Do not add any extra text or formatting.
    """,
    # The GoogleSearch tool expects a single string input, which is the query.
    # The output of this agent will be the search query string.
    output_key="search_query",
    # Importantly, this agent needs the GoogleSearch tool to execute its search.
    # Note: The GoogleSearch tool is provided by ADK and needs to be enabled in your ADK project.
    tools=[google_search],
    input_schema=KnowledgeBaseToolInput,  # ✅ Now accepts 'question' and 'language'
)

# --- Sub-Agent 2: Answer Extraction & Simplification Agent ---
# This agent takes the search results and simplifies them for children.
answer_simplifier_agent = LlmAgent(
    name="AnswerSimplifierAgent",
    model="gemini-1.5-flash", # Use Pro for better understanding and simplification
    description="Extracts the core answer from search results and simplifies it for primary school children.",
    instruction="""
    You are an expert at simplifying complex information for primary school children.
    
    **Original Question:** '{session.state.question}'
    **Desired Language:** '{session.state.language}'
    **Google Search Results:**
    ```
    {search_query.tool_response} # Accessing the result of the GoogleSearch tool
    ```
    
    Your task is to:
    1.  Read through the search results carefully.
    2.  Extract the most accurate and relevant information to answer the original question.
    3.  Simplify this information drastically for primary school children, using short sentences and basic vocabulary.
    4.  Ensure the answer is in '{session.state.language}'.
    5.  Do NOT include analogies yet.
    
    Output *only* the simplified answer text.
    """,
    # The output of this agent will be the simplified core answer.
    output_key="simplified_answer"
)

# --- Sub-Agent 3: Cultural Analogy & Localization Agent ---
# This agent adds the cultural touch.
cultural_analogy_agent = LlmAgent(
    name="CulturalAnalogyAgent",
    model="gemini-1.5-flash", # Use Pro for creative and context-aware analogy generation
    description="Adds culturally relevant analogies and a local touch to a simplified explanation.",
    instruction="""
    You are a creative educator specializing in making science concepts relatable to rural Indian children.
    
    **Original Question:** '{session.state.question}'
    **Simplified Answer:**
    ```
    {simplified_answer}
    ```
    **Target Language:** '{session.state.language}'
    
    Your task is to enhance the simplified answer by:
    1.  Adding **one or two simple analogies** that resonate with children in rural India (e.g., related to farming, village life, cooking, local festivals, animals).
    2.  Ensuring the entire explanation, including analogies, is in the '{session.state.language}' language.
    3.  The final output should be a single, friendly explanation suitable for a teacher to use.

    Example of good analogy: "Why is the sky blue? Think of the sky like a huge filter. When sunlight enters, it bumps into air particles. Blue light is scattered in all directions, just like the smoke from a cooking stove spreads out in the air!"

    Output *only* the final, enhanced explanation. Do not add any introductory or concluding remarks.
    """,
    # The output of this agent will be the final answer for the teacher.
    output_key="final_knowledge_response"
)


# --- Define the SequentialAgent for the Knowledge Base Pipeline ---
knowledge_base_pipeline = SequentialAgent(
    name="KnowledgeBasePipeline",
    description="A pipeline for fetching, simplifying, and localizing answers to science questions.",
    sub_agents=[
        google_search_agent,
        answer_simplifier_agent,
        cultural_analogy_agent,
    ],
    # No output_key here; the output will be the 'final_knowledge_response' from the last sub-agent.
)

# This will be imported by manager/agent.py
knowledge_base_agent = knowledge_base_pipeline