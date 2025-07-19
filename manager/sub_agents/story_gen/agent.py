from google.adk.agents import Agent

story_gen = Agent(
    name="story_gen",
    model="gemini-1.5-flash",
    description="Generates short, culturally‑relevant stories for kids.",
    instruction="""
Write a 100‑150‑word story that teaches the concept supplied by the teacher. 
Respond in the language used in the prompt. Keep it rural‑India‑friendly.
"""
)