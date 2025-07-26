from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
# import asyncio
# import base64
# import json
# import os
# from fastapi import FastAPI, Query, WebSocket
# from pathlib import Path
# from typing import AsyncIterable
# from google.adk.sessions.in_memory_session_service import InMemorySessionService
# from fastapi.responses import FileResponse
# from fastapi.staticfiles import StaticFiles
# from google.adk.agents import LiveRequestQueue
# from google.adk.agents.run_config import RunConfig
# from google.adk.events.event import Event
# from google.adk.runners import Runner
# from dotenv import load_dotenv
from .sub_agents.story_gen.agent import story_generation_pipeline
# from google.genai import types
from .sub_agents.knowledge_base.agent import knowledge_base_pipeline
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
    agent=knowledge_base_pipeline,
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
    model="gemini-2.0-flash-exp", # Flash is good for routing due to speed
    description="The central orchestration agent for ShikshaMitrah. Routes teacher requests to appropriate specialized agents.",
    instruction="""
    You are ShikshaMitrah, an AI teaching assistant for rural primary school teachers in India.
    Your primary role is to understand the teacher's request and efficiently delegate it to the most suitable specialized tool.
    
    - **{story_generation_pipeline.name}**: Use this tool when the teacher wants to create a story.
      *   **Description**: Generates a short, culturally-relevant story for primary school children.
      *   **Parameters**:
          *   `request` (string, required): The teacher's full request for the story, including topic and desired language (e.g., "Write a story in Marathi about ants and fireflies."). This tool will parse the topic and language internally.
    
     - **{knowledge_base_pipeline.name}**: Use this tool when the teacher or a student asks a "why" question or needs a simple explanation of a science concept.
      *   **Description**: Provides simple, accurate explanations for complex student questions with easy-to-understand, culturally-relevant analogies.
      *   **Parameters**:
          *   `request` (string, required): The teacher's full question (e.g., "Why do we see rainbows?", "Explain photosynthesis in Hindi."). This tool will parse the question and language internally.
      
    - **{lesson_planner_agent.name}**: Use for creating lesson plans OR managing calendar events.
      *   **Description**: Creates weekly lesson plans for multiple grades, and can list, create, edit, or delete events in Google Calendar.
      *   **Parameters**: `request` (string, required): The full user request (e.g., "Plan a math lesson for grade 3", or "List my calendar events for tomorrow", or "Schedule a parent meeting for Friday at 3 PM"). This tool will parse the intent internally.

    - **{worksheet_sequence.name}**: Use this tool when the teacher provides an image of a textbook page and asks to create worksheets from it, especially if differentiated for different grades.
      *   **Description**: Generates differentiated worksheets from a textbook page image, tailored for different grade levels.
      *   **Parameters**:
          *   `grades` (list of integers, required): A list of target grade levels for the worksheets (e.g., `[3, 5]`).
          *   `language` (string, optional): The desired language for the worksheet content. Default to "English" if not specified by the user.
          *   `topic` (string, optional): The topic of the textbook page if known (e.g., "water cycle", "photosynthesis").
      *   **Note**: If an image is provided in the teacher's input, it will be available in the session state for this tool to access via `ctx.input_content` or `ctx.session.state`.

    **Instructions for Tool Use:**
    *   **Always call a tool if the intent is clear.** Do not try to answer questions yourself.
    *   **Extract all required parameters** from the user's prompt for the chosen tool. Be precise.
    *   Always respond in the teacher's requested language.
    *   If any required parameter for a tool is missing or ambiguous, you **MUST** ask a clarifying question to the user. Do not call a tool with missing required parameters.
    *   If the teacher provides an image (even implicitly via context) and asks for worksheets, always use **{worksheet_sequence.name}**.
    *   **AFTER calling a tool, if it successfully returns content, IMMEDIATELY present that content to the user as your response.** Do not add extra commentary unless absolutely necessary for clarity.
    *   Specifically, if you call **{story_generation_pipeline.name}**, the tool's final output will be in `session.state.final_formatted_response`. After the tool call, present that value to the user.
    *   If you called **{knowledge_base_pipeline.name}**, present `session.state.final_knowledge_response`.
    """,

    tools=[
        story_generator_tool,
        knowledge_base_tool,
        lesson_planner_tool,
        worksheet_creator_tool
    ],
)

# load_dotenv()

# APP_NAME = "ADK Streaming example"
# session_service = InMemorySessionService()


# def start_agent_session(session_id, is_audio=False):
#     """Starts an agent session"""

#     # Create a Session
#     session = session_service.create_session(
#         app_name=APP_NAME,
#         user_id=session_id,
#         session_id=session_id,
#     )

#     # Create a Runner
#     runner = Runner(
#         app_name=APP_NAME,
#         agent=root_agent,
#         session_service=session_service,
#     )

#     # Set response modality
#     modality = "AUDIO" if is_audio else "TEXT"

#     # Create speech config with voice settings
#     speech_config = types.SpeechConfig(
#         voice_config=types.VoiceConfig(
#             # Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, and Zephyr
#             prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
#         )
#     )

#     # Create run config with basic settings
#     config = {"response_modalities": [modality], "speech_config": speech_config}

#     # Add output_audio_transcription when audio is enabled to get both audio and text
#     if is_audio:
#         config["output_audio_transcription"] = {}

#     run_config = RunConfig(**config)

#     # Create a LiveRequestQueue for this session
#     live_request_queue = LiveRequestQueue()

#     # Start agent session
#     live_events = runner.run_live(
#         session=session,
#         live_request_queue=live_request_queue,
#         run_config=run_config,
#     )
#     return live_events, live_request_queue


# async def agent_to_client_messaging(
#     websocket: WebSocket, live_events: AsyncIterable[Event | None]
# ):
#     """Agent to client communication"""
#     while True:
#         async for event in live_events:
#             if event is None:
#                 continue

#             # If the turn complete or interrupted, send it
#             if event.turn_complete or event.interrupted:
#                 message = {
#                     "turn_complete": event.turn_complete,
#                     "interrupted": event.interrupted,
#                 }
#                 await websocket.send_text(json.dumps(message))
#                 print(f"[AGENT TO CLIENT]: {message}")
#                 continue

#             # Read the Content and its first Part
#             part = event.content and event.content.parts and event.content.parts[0]
#             if not part:
#                 continue

#             # Make sure we have a valid Part
#             if not isinstance(part, types.Part):
#                 continue

#             # Only send text if it's a partial response (streaming)
#             # Skip the final complete message to avoid duplication
#             if part.text and event.partial:
#                 message = {
#                     "mime_type": "text/plain",
#                     "data": part.text,
#                     "role": "model",
#                 }
#                 await websocket.send_text(json.dumps(message))
#                 print(f"[AGENT TO CLIENT]: text/plain: {part.text}")

#             # If it's audio, send Base64 encoded audio data
#             is_audio = (
#                 part.inline_data
#                 and part.inline_data.mime_type
#                 and part.inline_data.mime_type.startswith("audio/pcm")
#             )
#             if is_audio:
#                 audio_data = part.inline_data and part.inline_data.data
#                 if audio_data:
#                     message = {
#                         "mime_type": "audio/pcm",
#                         "data": base64.b64encode(audio_data).decode("ascii"),
#                         "role": "model",
#                     }
#                     await websocket.send_text(json.dumps(message))
#                     print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")


# async def client_to_agent_messaging(
#     websocket: WebSocket, live_request_queue: LiveRequestQueue
# ):
#     """Client to agent communication"""
#     while True:
#         # Decode JSON message
#         message_json = await websocket.receive_text()
#         message = json.loads(message_json)
#         mime_type = message["mime_type"]
#         data = message["data"]
#         role = message.get("role", "user")  # Default to 'user' if role is not provided

#         # Send the message to the agent
#         if mime_type == "text/plain":
#             # Send a text message
#             content = types.Content(role=role, parts=[types.Part.from_text(text=data)])
#             live_request_queue.send_content(content=content)
#             print(f"[CLIENT TO AGENT PRINT]: {data}")
#         elif mime_type == "audio/pcm":
#             # Send audio data
#             decoded_data = base64.b64decode(data)

#             # Send the audio data - note that ActivityStart/End and transcription
#             # handling is done automatically by the ADK when input_audio_transcription
#             # is enabled in the config
#             live_request_queue.send_realtime(
#                 types.Blob(data=decoded_data, mime_type=mime_type)
#             )
#             print(f"[CLIENT TO AGENT]: audio/pcm: {len(decoded_data)} bytes")

#         else:
#             raise ValueError(f"Mime type not supported: {mime_type}")


# #
# # FastAPI web app
# #

# app = FastAPI()

# STATIC_DIR = Path("static")
# app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# @app.get("/")
# async def root():
#     """Serves the index.html"""
#     return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# @app.websocket("/ws/{session_id}")
# async def websocket_endpoint(
#     websocket: WebSocket,
#     session_id: str,
#     is_audio: str = Query(...),
# ):
#     """Client websocket endpoint"""

#     # Wait for client connection
#     await websocket.accept()
#     print(f"Client #{session_id} connected, audio mode: {is_audio}")

#     # Start agent session
#     live_events, live_request_queue = start_agent_session(
#         session_id, is_audio == "true"
#     )

#     # Start tasks
#     agent_to_client_task = asyncio.create_task(
#         agent_to_client_messaging(websocket, live_events)
#     )
#     client_to_agent_task = asyncio.create_task(
#         client_to_agent_messaging(websocket, live_request_queue)
#     )
#     await asyncio.gather(agent_to_client_task, client_to_agent_task)

#     # Disconnected
#     print(f"Client #{session_id} disconnected")