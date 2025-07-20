from google.adk.agents import LlmAgent, SequentialAgent

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
    
    Output in a structured JSON format with three keys:
    {{
      "story_draft": "YOUR_GENERATED_STORY_TEXT",
      "extracted_topic": "IDENTIFIED_TOPIC",
      "extracted_language": "IDENTIFIED_LANGUAGE"
    }}
    """,
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

# --- 3. Create the SequentialAgent for the Story Generation Pipeline ---
story_generation_pipeline = SequentialAgent(
    name="StoryGenerationPipeline",
    description="Orchestrates the generation and refinement of culturally relevant, localized stories for teachers.",
    sub_agents=[
        story_draft_generator,
        story_refinement_localizer
    ],
)