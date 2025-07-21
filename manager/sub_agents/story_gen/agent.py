from google.adk.agents import LlmAgent, SequentialAgent
from pydantic import BaseModel, Field

class StoryDraftOutput(BaseModel):
    story_draft: str = Field(description="The generated story draft")
    extracted_topic: str = Field(description="The topic identified from the request")
    extracted_language: str = Field(description="The target language for the story")
    
# --- Sub-Agent 1: Story Draft Generator ---
# This agent will now directly consume the 'request' parameter from the orchestrator.
story_draft_generator = LlmAgent(
    name="StoryDraftGenerator",
    model="gemini-1.5-flash", # Use a faster model for the initial draft
    description="Generates a preliminary story draft and extracts key parameters from the request.",
    instruction="""
    You are a creative storyteller for primary school children.
    The teacher's request is: '{session.state.request}'.
    
    Your task is two-fold:
    1.  **Identify the core 'topic'** for the story from the request.
    2.  **Identify the desired 'language'** for the story from the request. If no language is explicitly mentioned, assume 'English'.
    3.  **Generate a story draft** based on the identified topic and language.
    Focus purely on conveying the core concept in a narrative form, ignoring specific word counts or hyper-localization details for now.
    
    Output only in JSON.
    """,
    output_schema=StoryDraftOutput,
    # The output of this agent will be stored as JSON in 'story_details' in the shared state.
    output_key="story_details",
    include_contents="default",
)

# --- Sub-Agent 2: Story Refinement and Localization Agent ---
# This agent now pulls its inputs from the structured output of the previous agent.
story_refinement_localizer = LlmAgent(
    name="StoryRefinementLocalizer",
    model="gemini-1.5-flash", # Use a more capable model for nuanced refinement
    description="Refines the initial story draft for cultural relevance, rural-India friendliness, and length.",
    instruction="""
    You are an expert editor for children's educational content in rural India.
    Your task is to refine the provided story draft to meet specific criteria.

    **Initial Story Draft:**
    ```
    {story_details.story_draft}
    ```

    **Story Context (from previous step):**
    Original Topic: '{story_details.extracted_topic}'
    Target Language: '{story_details.extracted_language}'

    **Refinement Criteria:**
    1.  **Length:** The final story must be between 100-150 words. Adjust as necessary.
    2.  **Cultural Relevance:** Ensure the story is deeply culturally relevant and uses analogies/characters suitable for rural India. Incorporate elements inspired by local folklore or Panchatantra themes if appropriate.
    3.  **Language & Simplicity:** Ensure the language is simple, clear, and perfectly suited for primary school children in rural India, in the '{story_details.extracted_language}' language.
    4.  **Concept Clarity:** The story must clearly and simply explain the concept '{story_details.extracted_topic}'.

    **Output:**
    Respond *only* with the final, refined story text. Do not add any introductory or concluding remarks, or formatting beyond the story itself.
    """,
    # The output of this agent will be the final story.
    output_key="final_story_output"
)

# --- NEW Sub-Agent 3: Follow-Up Questions Agent ---
class FollowUpQuestionsOutput(BaseModel):
    questions: list[str] = Field(description="A list of follow-up questions based on the story")

follow_up_question_agent = LlmAgent(
    name="FollowUpQuestionAgent",
    model="gemini-1.5-flash", # Use Pro for better question generation, especially for reasoning
    description="Generates follow-up questions based on a story to test comprehension and reasoning.",
    instruction="""
    You are an educational assistant specialized in creating engaging questions for primary school children.
    
    **Story:**
    ```
    {final_story_output}
    ```
    
    **Context:**
    Original Topic: '{story_details.extracted_topic}'
    Target Language: '{story_details.extracted_language}'
    
    Your task is to generate 3-5 follow-up questions for students based *only* on the provided story.
    These questions should encourage:
    1.  **Comprehension:** Simple understanding of the plot and characters.
    2.  **Reasoning:** Asking "why" or "how" questions that require a bit more thought than just recalling facts (e.g., "Why did the character make that choice?").
    3.  **Application/Reflection (optional):** Questions that relate the story to real-world concepts or personal experience.
    
    Ensure questions are clear, concise, and in the '{story_details.extracted_language}' language.
    Output only in JSON, with a single key 'questions' containing a list of strings.
    """,
    output_schema=FollowUpQuestionsOutput,
    output_key="follow_up_questions"
)

# --- NEW Sub-Agent 4: Story and Questions Formatter Agent ---
story_and_questions_formatter = LlmAgent(
    name="StoryAndQuestionsFormatter",
    model="gemini-1.5-flash", # Flash is fine for formatting text
    description="Formats the generated story and follow-up questions into a single, user-friendly response.",
    instruction="""
    You are a friendly teaching assistant. Your task is to combine the provided story and follow-up questions into a single, clear message for the teacher.
    
    **Story:**
    {final_story_output}
    
    **Follow-up Questions:**
    List 3 to 5 questions based on the story:

    {follow_up_questions.questions}

    Format them as:
    1. ...
    2. ...
    3. ... 
    
    **Context:**
    Target Language: '{story_details.extracted_language}'
    
    Format the response nicely. Start with the story, then introduce the questions clearly, perhaps numbering them.
    Ensure the entire response is in the '{story_details.extracted_language}' language.
    Output *only* the formatted text response. Do not add any extra JSON or special characters.
    """,
    # This agent's output will be the final text presented to the user.
    # No output_schema needed as it's meant to produce plain text.
    output_key="final_formatted_response", # Explicitly name the final output key
)

# --- 4. Create the SequentialAgent for the Story Generation Pipeline ---
story_generation_pipeline = SequentialAgent(
    name="StoryGenerationPipeline",
    description="Orchestrates the generation, refinement, follow-up questioning, and formatting of culturally relevant, localized stories for teachers.",
    sub_agents=[
        story_draft_generator,
        story_refinement_localizer,
        follow_up_question_agent,
        story_and_questions_formatter
    ],
)