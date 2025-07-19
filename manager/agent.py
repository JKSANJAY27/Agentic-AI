from google.adk.agents import Agent
from .sub_agents.story_gen.agent import story_gen

root_agent = Agent(
    name="manager_agent",
    model="gemini-1.5-flash",
    description="Temporary root agent; delegates everything to story_gen.",
    instruction="If the request is story‑like, call story_gen.",
    sub_agents=[story_gen],   # later you’ll add visual_aid, knowledge_base…
)