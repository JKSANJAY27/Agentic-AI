from google.adk.agents import Agent
# from google.adk.tools.agent_tool import AgentTool

from .sub_agents.story_gen.agent import story_gen
from .sub_agents.knowledge_base.agent import knowledge_base_agent

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
        knowledge_base_agent
    ],
    tools=[]
)