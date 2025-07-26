from google.adk.agents import LlmAgent, SequentialAgent
from pydantic import BaseModel, Field
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from typing import Optional
from google.genai import types


# Define harmful or sensitive keywords (you can expand this list)
BLOCKED_KEYWORDS = [
    # Violence/Harm
    "violence", "abuse", "war", "death", "blood", "gun", "suicide", "kill", "murder", "torture",
    "bomb", "weapon", "fight", "attack", "harm", "destroy", "injure", "brutal", "massacre",
    "conflict", "explosion", "terrorism", "crime", "robbery", "kidnap", "assault",

    # Sexual/Explicit Content
    "sex", "sexual", "porn", "erotic", "nude", "naked", "explicit", "orgasm", "masturbate",
    "prostitute", "rape", "lust", "fetish", "intimate", "private parts",

    # Drugs/Substance Abuse
    "drugs", "drug use", "alcohol", "intoxicate", "addiction", "cocaine", "heroin", "marijuana",
    "smoke", "pill", "overdose", "drunk", "high",

    # Hate Speech/Discrimination
    "racism", "racist", "bigot", "bigotry", "prejudice", "hate speech", "discrimination",
    "sexism", "sexist", "homophobia", "homophobic", "transphobia", "transphobic",
    "xenophobia", "xenophobic", "slur", "curse word", "swear word", "insult", "derogatory",

    # Self-Harm/Mental Distress (beyond "suicide")
    "self-harm", "cut", "depress", "anxiety attack", "panic attack", "mental breakdown",
    "hopeless", "despair", "worthless",

    # Other potentially inappropriate/sensitive themes for young children
    "cursed", "demonic", "devil", "ghost", "monster" # Be careful with fantasy context here
    # "cult", "sect", "gang" # May be context-dependent
]

def block_harmful_prompts(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    agent_name = callback_context.agent_name
    print(f"[Callback] Intercepting request for: {agent_name}")

    prompt = ""
    if llm_request.contents:
        for content in llm_request.contents:
            if content.parts:
                for part in content.parts:
                    if part.text:
                        prompt += part.text + " "
    prompt = prompt.strip().lower()

    # Check for any blocked keyword
    if any(keyword in prompt for keyword in BLOCKED_KEYWORDS):
        print(f"[Callback] Blocked content detected in user prompt: {prompt}")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="❌ The provided prompt contains content that is not appropriate for student stories. Please provide a different topic.")]
            )
        )

    print("[Callback] Prompt is safe. Proceeding with LLM call.")
    return None

class StoryDraftOutput(BaseModel):
    story_draft: str = Field(description="The generated story draft")
    extracted_topic: str = Field(description="The topic identified from the request")
    extracted_language: str = Field(description="The target language for the story")
    
# --- Sub-Agent 1: Story Draft Generator ---
# This agent will now directly consume the 'request' parameter from the orchestrator.
story_draft_generator = LlmAgent(
    name="StoryDraftGenerator",
    model="gemini-2.0-flash", # Use a faster model for the initial draft
    description="Generates a preliminary story draft and extracts key parameters from the request.",
    instruction=""" You are a creative storyteller for primary school children.
The teacher's request is: '{session.state.request}'.

Your task is two-fold:
1.  *Identify the core 'topic'* for the story from the request.
2.  *Identify the desired 'language'* for the story from the request. If no language is explicitly mentioned, assume 'English'.
3.  *Generate a story draft* based on the identified topic and language. The story should be a simple narrative, focusing on the core concept and suitable for young children.

Output only in JSON. The JSON must strictly adhere to the following format:
```json
{{
    "story_draft": "The generated story text goes here. Keep it concise for a draft.",
    "extracted_topic": "The identified topic (e.g., 'friendship', 'space exploration')",
    "extracted_language": "The identified language (e.g., 'English', 'Hindi')"
}}
    """,
    # output_schema=StoryDraftOutput,
    # The output of this agent will be stored as JSON in 'story_details' in the shared state.
    output_key="story_details",
    include_contents="default",
    before_model_callback=block_harmful_prompts
)

# --- Sub-Agent 2: Story Refinement and Localization Agent ---
# This agent now pulls its inputs from the structured output of the previous agent.
story_refinement_localizer = LlmAgent(
    name="StoryRefinementLocalizer",
    model="gemini-2.0-flash", # Use a more capable model for nuanced refinement
    description="Refines the initial story draft for cultural relevance, rural-India friendliness, and length.",
    instruction="""
    You are an expert editor for children's educational content in rural India.
    Your task is to refine the provided story draft to meet specific criteria.

    *Initial Story Draft:*
    
    {story_details.story_draft}
    

    *Story Context (from previous step):*
    Original Topic: '{story_details.extracted_topic}'
    Target Language: '{story_details.extracted_language}'

    *Refinement Criteria:*
    1.  *Length:* The final story must be between 100-150 words. Adjust as necessary.
    2.  *Cultural Relevance:* Ensure the story is deeply culturally relevant and uses analogies/characters suitable for rural India. Incorporate elements inspired by local folklore or Panchatantra themes if appropriate.
    3.  *Language & Simplicity:* Ensure the language is simple, clear, and perfectly suited for primary school children in rural India, in the '{story_details.extracted_language}' language.
    4.  *Concept Clarity:* The story must clearly and simply explain the concept '{story_details.extracted_topic}'.

    *Output:*
    Respond only with the final, refined story text. Do not add any introductory or concluding remarks, or formatting beyond the story itself.
    """,
    # The output of this agent will be the final story.
    output_key="final_story_output"
)

# --- NEW Sub-Agent 3: Follow-Up Questions Agent ---
class FollowUpQuestionsOutput(BaseModel):
    questions: list[str] = Field(description="A list of follow-up questions based on the story")

follow_up_question_agent = LlmAgent(
    name="FollowUpQuestionAgent",
    model="gemini-2.0-flash", # Use Pro for better question generation, especially for reasoning
    description="Generates follow-up questions based on a story to test comprehension and reasoning.",
    instruction="""
    You are an educational assistant specialized in creating engaging questions for primary school children.
    
    *Story:*
    
    {final_story_output}
    
    
    *Context:*
    Original Topic: '{story_details.extracted_topic}'
    Target Language: '{story_details.extracted_language}'
    
    Your task is to generate 3-5 follow-up questions for students based only on the provided story.
    These questions should encourage:
    1.  *Comprehension:* Simple understanding of the plot and characters.
    2.  *Reasoning:* Asking "why" or "how" questions that require a bit more thought than just recalling facts (e.g., "Why did the character make that choice?").
    3.  *Application/Reflection (optional):* Questions that relate the story to real-world concepts or personal experience.
    
    Ensure questions are clear, concise, and in the '{story_details.extracted_language}' language.
    Output only in JSON, with a single key 'questions' containing a list of strings.
    """,
    output_schema=FollowUpQuestionsOutput,
    output_key="follow_up_questions"
)

# --- NEW Sub-Agent 4: Story and Questions Formatter Agent ---
story_and_questions_formatter = LlmAgent(
    name="StoryAndQuestionsFormatter",
    model="gemini-2.0-flash", # Flash is fine for formatting text
    description="Formats the generated story and follow-up questions into a single, user-friendly response.",
    instruction="""
    You are a friendly teaching assistant. Your task is to combine the provided story and follow-up questions into a single, clear message for the teacher.
    
    *Story:*
    {final_story_output}
    
    *Follow-up Questions:*
    List 3 to 5 questions based on the story:

    {follow_up_questions.questions}

    Format them as:
    1. ...
    2. ...
    3. ... 
    
    *Context:*
    Target Language: '{story_details.extracted_language}'
    
    Format the response nicely. Start with the story, then introduce the questions clearly, perhaps numbering them.
    Ensure the entire response is in the '{story_details.extracted_language}' language.
    Output only the formatted text response. Do not add any extra JSON or special characters.
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