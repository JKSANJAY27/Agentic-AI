# from fastapi import FastAPI, Request
# import httpx
# import uvicorn

# # Import your ADK agent here
# from manager.agent import root_agent  # adjust if named differently

# TELEGRAM_TOKEN = "8359970440:AAFaZqpL9V6ZBDupzcIoHjBU_PK8uEWSmA0"
# TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# app = FastAPI()

# @app.post("/webhook")
# async def telegram_webhook(request: Request):
#     data = await request.json()
#     chat_id = data["message"]["chat"]["id"]
#     user_input = data["message"]["text"]

#     # Run user input through your ADK agent
#     response = await root_agent.call(user_input)
#     reply = response.output if response.output else "Sorry, I didn't understand."

#     # Send response back to Telegram
#     async with httpx.AsyncClient() as client:
#         await client.post(f"{TELEGRAM_API}/sendMessage", json={
#             "chat_id": chat_id,
#             "text": reply
#         })

#     return {"ok": True}
#-----gemini's code-----
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# import httpx
# import uvicorn
# import logging

# # Configure basic logging to see messages in your terminal
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Import your ADK agent here
# # This should correctly import the `root_agent` instance you defined in manager/agent.py
# from manager.agent import root_agent


# app = FastAPI()

# @app.post("/webhook")
# async def telegram_webhook(request: Request):
#     chat_id = None # Initialize chat_id to None for error handling outside the try block
#     try:
#         data = await request.json()
#         logger.info(f"Received Telegram webhook data: {data}")

#         message = data.get("message")
#         if not message:
#             logger.warning("Received Telegram update without a 'message' object. Ignoring non-message update.")
#             return {"ok": True} # Acknowledge success to Telegram for non-message updates

#         chat_id = message.get("chat", {}).get("id")
#         user_input = message.get("text")
        
#         # --- Handle potential image input for worksheet_creator_tool ---
#         # This part requires more advanced parsing of Telegram's update object
#         # Telegram sends images in `message.photo` which is a list of photo sizes.
#         # You'd need to pick one (e.g., the largest) and fetch its file_id, then
#         # use Telegram Bot API's getFile method to get the file_path, and then download it.
#         # This is beyond the current scope but important if you want image inputs to work.
#         # For now, if no text and no specific image handling, we just acknowledge.

#         if not chat_id:
#             logger.warning("Could not extract chat_id from Telegram message.")
#             return {"ok": True} # Acknowledge success if no chat ID

#         if not user_input:
#             logger.info(f"No text found in message from chat_id {chat_id}. Ignoring non-text message for now.")
#             # If you want to process images for worksheet_creator_tool, this is where you'd add that logic.
#             return {"ok": True} # Acknowledge success for non-text messages

#         logger.info(f"Processing text message from chat {chat_id}: '{user_input}'")

#         # Call the root_agent.
#         # It returns an AgentOutput object, which contains the final state of the session.
#         agent_output = await root_agent.call(user_input)
#         logger.info(f"Raw AgentOutput from root_agent.call(): {agent_output}")

#         # --- IMPORTANT: Extract the reply from the session state as per manager/agent.py instructions ---
#         reply = "Sorry, I couldn't generate a clear response for that request." # Default fallback
        
#         # The agent_output.state contains the ToolContext.session.state for the turn.
#         if agent_output and hasattr(agent_output, 'state') and agent_output.state:
#             session_state = agent_output.state # Directly use agent_output.state as the session state for this turn
            
#             if "final_formatted_response" in session_state:
#                 reply = session_state["final_formatted_response"]
#                 logger.info(f"Found reply in final_formatted_response: {reply}")
#             elif "final_knowledge_response" in session_state:
#                 reply = session_state["final_knowledge_response"]
#                 logger.info(f"Found reply in final_knowledge_response: {reply}")
#             # Add conditions for other agent outputs if they also store their final results in specific state keys
#             # E.g., for lesson_planner_agent or worksheet_creator_tool if they have specific output keys
#             # Otherwise, the root_agent's own direct text response might be the fallback
#             elif hasattr(agent_output, 'text_response') and agent_output.text_response:
#                 # This could be the direct text response from the root agent itself
#                 # if it decided not to call a tool or had a final summary.
#                 reply = agent_output.text_response
#                 logger.info(f"Found reply in agent_output.text_response: {reply}")
#             else:
#                 logger.warning(f"AgentOutput state did not contain expected keys. Keys present: {session_state.keys()}")
#         elif hasattr(agent_output, 'text_response') and agent_output.text_response:
#              # Fallback if agent_output.state is empty but direct text_response is present
#              reply = agent_output.text_response
#              logger.info(f"Direct text_response from agent_output: {reply}")
#         else:
#             logger.warning(f"AgentOutput was empty or did not contain state/text_response. Full output: {agent_output}")


#         if not reply:
#             reply = "Sorry, I couldn't process your request or generate a response at this time."
#             logger.warning(f"Final reply is empty after processing for input: {user_input}")

#         # Ensure the reply is a string
#         reply_text = str(reply)

#         # Send response back to Telegram
#         telegram_send_message_url = f"{TELEGRAM_API}/sendMessage"
#         payload = {
#             "chat_id": chat_id,
#             "text": reply_text
#         }
#         logger.info(f"Sending to Telegram: {payload}")

#         async with httpx.AsyncClient() as client:
#             tg_response = await client.post(telegram_send_message_url, json=payload)
#             tg_response.raise_for_status() # Raise an exception for bad HTTP responses
#             logger.info(f"Telegram API response: {tg_response.json()}")

#         return {"ok": True}

#     except Exception as e:
#         logger.exception(f"Error processing Telegram webhook for data: {data if 'data' in locals() else 'N/A'}")
#         # Attempt to send an error message back to the user if chat_id is available
#         if chat_id: # Check if chat_id was successfully extracted
#             try:
#                 async with httpx.AsyncClient() as client:
#                     await client.post(f"{TELEGRAM_API}/sendMessage", json={
#                         "chat_id": chat_id,
#                         "text": "An internal error occurred while processing your request. Please try again later."
#                     })
#             except Exception as send_e:
#                 logger.error(f"Failed to send error message to user: {send_e}")

#         # It's better to return a 500 status code to Telegram if an unhandled error occurred
#         # So Telegram knows there was a problem and might retry.
#         return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
#sanjay's debugging
# import logging
# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters


# # Import the root_agent instance from your manager folder
# from manager.agent import root_agent

# # Your Telegram bot token
# TELEGRAM_TOKEN = '8359970440:AAFaZqpL9V6ZBDupzcIoHjBU_PK8uEWSmA0'

# # Initialize logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Function to handle incoming messages
# def handle_message(update: Update, context):
#     chat_id = update.message.chat_id
#     user_message = update.message.text

#     try:
#         # Send the user's message to the root agent for processing
#         response = root_agent.process_message(user_message)  # Assuming process_message exists on root_agent

#         # Send the response back to the user on Telegram
#         context.bot.send_message(chat_id=chat_id, text=response)

#     except Exception as e:
#         logger.error(f"Error processing message: {str(e)}")
#         context.bot.send_message(chat_id=chat_id, text="Sorry, I couldn't process your request. Please try again.")

# # Set up the Updater and Dispatcher
# async def main():
#     # Create the Application with the bot token
#     application = Application.builder().token(TELEGRAM_TOKEN).build()

#     # Add a handler for messages (to handle text input)
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

#     # Start polling for updates
#     await application.run_polling()

# if __name__ == "_main_":
#     main()

# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse # Ensure this is imported
# from google.adk.agents import ToolCallingAgent
# import httpx
# import uvicorn
# import logging

# # Configure basic logging to see messages in your terminal
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # # Import your ADK agent here
# # from manager.agent import root_agent
# from manager.agent import root_agent as base_agent
# from google.adk.agents import ToolCallingAgent

# root_agent = ToolCallingAgent(agent=base_agent)





# app = FastAPI()

# @app.post("/webhook")
# async def telegram_webhook(request: Request):
#     chat_id = None
#     try:
#         data = await request.json()
#         logger.info(f"Received Telegram webhook data: {data}")

#         message = data.get("message")
#         if not message:
#             logger.warning("Received Telegram update without a 'message' object. Ignoring non-message update.")
#             return {"ok": True}

#         chat_id = message.get("chat", {}).get("id")
#         user_input = message.get("text")
        
#         if not chat_id:
#             logger.warning("Could not extract chat_id from Telegram message.")
#             return {"ok": True}

#         if not user_input:
#             logger.info(f"No text found in message from chat_id {chat_id}. Ignoring non-text message for now.")
#             return {"ok": True}

#         logger.info(f"Processing text message from chat {chat_id}: '{user_input}'")

#         # --- DIAGNOSTIC LINES TO ADD ---
#         logger.info(f"Type of root_agent BEFORE call: {type(root_agent)}")
#         # logger.info(f"Does root_agent have .call() method? {'call' in dir(root_agent)}")
#         logger.info(f"root_agent has .run()? {'run' in dir(root_agent)}")
#         # --- END DIAGNOSTIC LINES ---

#         # agent_output = await root_agent.call(user_input) # This is where it fails
#         agent_output = await root_agent.run(user_input)


#         logger.info(f"Raw AgentOutput from root_agent.call(): {agent_output}")

#         # ... (rest of your existing main.py code for handling agent_output) ...
#         reply = "Sorry, I couldn't generate a clear response for that request."
        
#         if agent_output and hasattr(agent_output, 'state') and agent_output.state:
#             session_state = agent_output.state
            
#             if "final_formatted_response" in session_state:
#                 reply = session_state["final_formatted_response"]
#                 logger.info(f"Found reply in final_formatted_response: {reply}")
#             elif "final_knowledge_response" in session_state:
#                 reply = session_state["final_knowledge_response"]
#                 logger.info(f"Found reply in final_knowledge_response: {reply}")
#             elif hasattr(agent_output, 'text_response') and agent_output.text_response:
#                 reply = agent_output.text_response
#                 logger.info(f"Found reply in agent_output.text_response: {reply}")
#             else:
#                 logger.warning(f"AgentOutput state did not contain expected keys. Keys present: {session_state.keys()}")
#         elif hasattr(agent_output, 'text_response') and agent_output.text_response:
#              reply = agent_output.text_response
#              logger.info(f"Direct text_response from agent_output: {reply}")
#         else:
#             logger.warning(f"AgentOutput was empty or did not contain state/text_response. Full output: {agent_output}")

#         if not reply:
#             reply = "Sorry, I couldn't process your request or generate a response at this time."
#             logger.warning(f"Final reply is empty after processing for input: {user_input}")

#         reply_text = str(reply)

#         telegram_send_message_url = f"{TELEGRAM_API}/sendMessage"
#         payload = {
#             "chat_id": chat_id,
#             "text": reply_text
#         }
#         logger.info(f"Sending to Telegram: {payload}")

#         async with httpx.AsyncClient() as client:
#             tg_response = await client.post(telegram_send_message_url, json=payload)
#             tg_response.raise_for_status()
#             logger.info(f"Telegram API response: {tg_response.json()}")

#         return {"ok": True}

#     except Exception as e:
#         logger.exception(f"Error processing Telegram webhook for data: {data if 'data' in locals() else 'N/A'}")
#         if chat_id:
#             try:
#                 async with httpx.AsyncClient() as client:
#                     await client.post(f"{TELEGRAM_API}/sendMessage", json={
#                         "chat_id": chat_id,
#                         "text": "An internal error occurred while processing your request. Please try again later."
#                     })
#             except Exception as send_e:
#                 logger.error(f"Failed to send error message to user: {send_e}")

#         return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})