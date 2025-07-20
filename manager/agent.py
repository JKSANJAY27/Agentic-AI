from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.story_gen.agent import story_gen
from .sub_agents.knowledge_base.agent import knowledge_base_agent
from google.adk.tools.tool_context import ToolContext
from google.genai.types import Content, Part
import logging
from .sub_agents.worksheet_generator.agent import WorksheetCreationSequence

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
    model="gemini-1.5-flash",
    description="Routes teacher requests to appropriate agents/tools.",
    instruction="""
You are a teaching assistant for rural school teachers.
You can call the following agents:

- story_gen → to generate local-language stories about concepts.
- knowledge_base → to answer science questions with analogies.

If the request is about explaining a science concept or answering a student’s "why" question, use knowledge_base.
If the request involves creating a story, use story_gen.
""",
    sub_agents=[
        story_gen,
        knowledge_base_agent,
    ],
    tools=[worksheet_creator_tool],
    process_attachments=True,
    pre_execution_hook=save_uploaded_image_hook
)