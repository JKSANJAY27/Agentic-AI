from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.story_gen.agent import story_generation_pipeline
from .sub_agents.knowledge_base.agent import knowledge_base_agent
from google.adk.tools.tool_context import ToolContext
from google.genai.types import Content, Part
import logging
from .sub_agents.worksheet_generator.agent import WorksheetCreationSequence
from .sub_agents.lesson_planner.agent import lesson_planner_agent

# Story Generation Tool
story_generator_tool = AgentTool(
    agent=story_generation_pipeline,
)

# Knowledge Base Tool
knowledge_base_tool = AgentTool(
    agent=knowledge_base_agent,
)

# Lesson Planner Tool
lesson_planner_tool = AgentTool(
    agent=lesson_planner_agent,
)

worksheet_sequence = WorksheetCreationSequence()

# Then, wrap it in an AgentTool. This makes it a callable tool.
worksheet_creator_tool = AgentTool(
    agent=worksheet_sequence,
)

async def save_uploaded_image_hook(
    ctx: ToolContext,
    input_content: Content | str | None,
) -> None:
    """
    A pre-execution hook that checks for image attachments in the input
    and saves the first one found to the session state.
    """
    logging.info("Running save_uploaded_image_hook...")
    if not isinstance(input_content, Content) or not input_content.parts:
        logging.info("No content or parts in input. Skipping image save.")
        return

    # Find the first part that is an image and save its data
    for part in input_content.parts:
        # Uploaded files are accessible via the `file_data` attribute
        if part.file_data:
            # Check the mime type to ensure it's an image
            if "image" in part.file_data.mime_type:
                logging.info(f"Image found! Mime type: {part.file_data.mime_type}. Saving to session state.")
                # Save the raw bytes to the session state
                ctx.session.state["uploaded_image_bytes"] = part.file_data.data
                # We only need the first image, so we can stop here.
                return

    logging.info("No image attachment found in the input.")

root_agent = Agent(
    name="manager_agent",
    model="gemini-1.5-flash", # Flash is good for routing due to speed
    description="The central orchestration agent for ShikshaMitrah. Routes teacher requests to appropriate specialized agents.",
    instruction="""
    You are ShikshaMitrah, an AI teaching assistant for rural primary school teachers in India.
    Your primary role is to understand the teacher's request and efficiently delegate it to the most suitable specialized tool.
    
    You can use the following tools:
    
    - **story_generator_tool**: Use this tool when the teacher wants to create a story (e.g., "Create a story about...", "Tell me a story about...").
      *   **Parameters**: `request` — the full teacher prompt.
    
    - **knowledge_base_tool**: Use this tool when the teacher or a student asks a "why" question or needs a simple explanation of a science concept (e.g., "Why is the sky blue?", "Explain photosynthesis simply.").
      *   **Parameters**: `question` (the question to answer), `language` (the desired language for the explanation).
      
    - **lesson_planner_tool**: Use this tool when the teacher asks for a weekly lesson plan (e.g., "Plan a lesson for next week on math for grade 3.", "Help me prepare a weekly schedule.").
      *   **Parameters**: `topic` (the subject of the lesson), `grade` (the target grade level), `duration` (e.g., "weekly", "daily"), `language` (the desired language for the plan).

    - **worksheet_creator_tool**: Use this tool when the teacher provides an image of a textbook page and asks to create worksheets from it, especially if differentiated for different grades (e.g., "Generate worksheets from this picture for grades 3 and 5.", "Make questions from this page.").
      *   **Parameters**: `grades` (a list of target grade levels, e.g., `[3, 5]`), `language` (the desired language for the worksheet content), `topic` (optional: the topic of the textbook page if known).
      *   **Note**: The image content from the teacher's input is automatically made available to this tool via a pre-execution hook.

    **Instructions for Tool Use:**
    *   Carefully analyze the teacher's request.
    *   Choose the single best tool for the request.
    *   Extract all necessary parameters from the request to pass to the chosen tool.
    *   Always respond in the teacher's requested language.
    *   If the teacher provides an image and asks for worksheets, always use `worksheet_creator_tool`.
    *   If the request is unclear or missing information, ask clarifying questions.
    """,

    tools=[
        story_generator_tool,
        knowledge_base_tool,
        lesson_planner_tool,
        worksheet_creator_tool
    ],
)