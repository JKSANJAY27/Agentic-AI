# manager/sub_agents/knowledge_base/agent.py

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from pydantic import BaseModel, Field

# --- Pydantic Model for the parsed request output ---
class ParsedRequestOutput(BaseModel):
    extracted_question: str = Field(description="The question extracted from the request.")
    extracted_language: str = Field(description="The language extracted from the request, defaults to English.")

# --- NEW Sub-Agent 1: Request Parser Agent ---
request_parser_agent = LlmAgent(
    name="RequestParserAgent",
    model="gemini-1.5-flash", # Flash for quick parsing
    description="Parses the user's request and extracts the core question and desired language.",
    instruction="""
    You are an intelligent assistant. The teacher's full request is: '{session.state.request}'.
    
    Your task is to:
    1.  **Extract the core 'question'** the teacher or student is asking from the request.
    2.  **Identify the desired 'language'** for the answer from the request. If no language is explicitly mentioned, assume 'English'.

    Output only in JSON, with keys 'extracted_question' and 'extracted_language'.
    """,
    output_schema=ParsedRequestOutput,
    output_key="parsed_request_details", # Store parsed details here
)

# --- NEW Sub-Agent 2: Search Query Generator Agent ---
search_query_generator_agent = LlmAgent(
    name="SearchQueryGeneratorAgent",
    model="gemini-1.5-flash", # Flash for quick query generation
    description="Generates a Google Search query based on the extracted question and language.",
    instruction="""
    You are an expert search query generator.
    
    **Extracted Question:** '{parsed_request_details.extracted_question}'
    **Desired Language:** '{parsed_request_details.extracted_language}'
    
    Formulate the most effective and concise Google Search query to find accurate and simple explanations suitable for primary school teachers or for simplifying for children.
    
    Output only the search query string. Do not add any extra text or formatting.
    """,
    output_key="search_query_string_for_tool", # This will be the actual query string
    tools=[google_search], # <--- This agent now calls the tool!
)


# --- Sub-Agent 3: Answer Extraction & Simplification Agent ---
answer_simplifier_agent = LlmAgent(
    name="AnswerSimplifierAgent",
    model="gemini-1.5-pro", # Use Pro for better understanding and simplification
    description="Extracts the core answer from search results and simplifies it for primary school children.",
    instruction="""
    You are an expert at simplifying complex information for primary school children.
    
    **Original Question:** '{parsed_request_details.extracted_question}'
    **Desired Language:** '{parsed_request_details.extracted_language}'
    **Google Search Results:**
    ```
    {search_query_string_for_tool.tool_response} # Accessing the result of the GoogleSearch tool
    ```
    
    Your task is to:
    1.  Read through the search results carefully.
    2.  Extract the most accurate and relevant information to answer the original question.
    3.  Simplify this information drastically for primary school children, using short sentences and basic vocabulary.
    4.  Ensure the answer is in '{parsed_request_details.extracted_language}'.
    5.  Do NOT include analogies yet.
    
    Output *only* the simplified answer text.
    """,
    output_key="simplified_answer"
)

# --- Sub-Agent 4: Cultural Analogy & Localization Agent ---
cultural_analogy_agent = LlmAgent(
    name="CulturalAnalogyAgent",
    model="gemini-1.5-pro", # Use Pro for creative and context-aware analogy generation
    description="Adds culturally relevant analogies and a local touch to a simplified explanation.",
    instruction="""
    You are a creative educator specializing in making science concepts relatable to rural Indian children.
    
    **Original Question:** '{parsed_request_details.extracted_question}'
    **Simplified Answer:**
    ```
    {simplified_answer}
    ```
    **Target Language:** '{parsed_request_details.extracted_language}'
    
    Your task is to enhance the simplified answer by:
    1.  Adding **one or two simple analogies** that resonate with children in rural India (e.g., related to farming, village life, cooking, local festivals, animals).
    2.  Ensuring the entire explanation, including analogies, is in the '{parsed_request_details.extracted_language}' language.
    3.  The final output should be a single, friendly explanation suitable for a teacher to use.

    Example of good analogy: "Why is the sky blue? Think of the sky like a huge filter. When sunlight enters, it bumps into air particles. Blue light is scattered in all directions, just like the smoke from a cooking stove spreads out in the air!"

    Output *only* the final, enhanced explanation. Do not add any introductory or concluding remarks.
    """,
    output_key="final_knowledge_response"
)


# --- Define the SequentialAgent for the Knowledge Base Pipeline ---
knowledge_base_pipeline = SequentialAgent(
    name="KnowledgeBasePipeline",
    description="A pipeline for fetching, simplifying, and localizing answers to science questions.",
    sub_agents=[
        request_parser_agent,         # First: parse the request
        search_query_generator_agent, # Second: generate query and call search tool
        answer_simplifier_agent,      # Third: simplify the search results
        cultural_analogy_agent,       # Fourth: add cultural analogies
    ],
)

knowledge_base_agent = knowledge_base_pipeline