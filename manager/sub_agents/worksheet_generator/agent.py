from google.adk.agents import LlmAgent

class OcrAgent(LlmAgent):
    """
    An agent specialized in extracting text from an image (OCR).
    It takes an image as input and returns the extracted text.
    """
    name: str = "ocr_agent"
    description: str = "Extracts text from an image."
    # Use a model with strong vision capabilities
    model: str = "gemini-1.5-pro"
    instruction: str = """
You are an expert Optical Character Recognition (OCR) service.
Your sole purpose is to accurately extract all written text from the provided image.
Do not summarize, interpret, or add any extra commentary. Output only the raw text.
"""

class ExtractConceptAgent(LlmAgent):
    """
    Takes raw text and distills the core educational concept.
    """
    name: str = "concept_extractor"
    description: str = "Extracts the main science concept from textbook content."
    model: str = "gemini-2.0-flash"
    instruction: str = """
You are a curriculum design expert. Analyze the provided text from a textbook.
Identify and extract the single core scientific concept it explains.

Your output must be concise: just the name of the concept and a one-sentence definition.
Example: Soil - The top layer of the Earth's surface, consisting of rock and mineral particles mixed with organic matter.
"""

class GenerateWorksheetsAgent(LlmAgent):
    """
    Takes a science concept and generates grade-specific worksheets.
    """
    name: str = "worksheet_generator_llm"
    description: str = "Generates multiple grade-specific worksheets for a science concept."
    model: str = "gemini-2.0-flash"
    instruction: str = """
You are a creative and experienced elementary and middle school teacher.
Given a science concept, generate three distinct worksheets for Grades 3, 5, and 7.

Use clear Markdown formatting. For each grade, provide:
- A title (e.g., "Grade 3: Exploring Soil")
- A short, age-appropriate explanation of the concept.
- 2 fill-in-the-blank questions.
- 2 true/false questions.
- 1 open-ended or critical thinking question (especially for Grade 7).

Ensure the language, complexity, and tasks are perfectly suited for each grade level.
"""

from google.adk.agents import SequentialAgent, Agent
from google.adk.events import Event
from google.adk.tools.tool_context import ToolContext
from google.genai.types import Content, Part
import logging

class WorksheetCreationSequence(SequentialAgent):
    """
    Orchestrates the worksheet creation process from an image.
    Flow: Image -> [OcrAgent] -> Text -> [ExtractConceptAgent] -> Concept -> [GenerateWorksheetsAgent] -> Worksheets
    """
    name: str = "worksheet_creation_sequence"
    description: str = "A sequence that creates worksheets from a textbook image."

    # The sub_agents are executed in the order they appear in this list.
    sub_agents: list[Agent] = [
        OcrAgent(),
        ExtractConceptAgent(),
        GenerateWorksheetsAgent(),
    ]

    # By overriding _run_async_impl, we gain fine-grained control and can
    # provide real-time feedback to the user between steps.
    async def _run_async_impl(self, ctx: ToolContext):
        # Step 0: Get the initial input (the image) from the session state.
        image_bytes = ctx.session.state.get("uploaded_image_bytes")
        if not image_bytes:
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="❌ **Error:** No image found. Please upload a photo first.")])
            )
            return

        # Prepare the input for the *first* agent in the sequence (OcrAgent).
        initial_input = Content(parts=[Part.from_data(data=image_bytes, mime_type="image/jpeg")])

        # Step 1: Manually call the first agent (OcrAgent) and yield feedback.
        yield Event(author=self.name, content=Content(parts=[Part(text="🧠 Analyzing image...")]))
        ocr_response = await ctx.call_agent(agent_name="ocr_agent", input=initial_input)
        textbook_text = ocr_response.output
        
        if not textbook_text or not textbook_text.strip():
            yield Event(author=self.name, content=Content(parts=[Part(text="⚠️ Could not find any text in the image. Please try a clearer picture.")]))
            return
            
        yield Event(author=self.name, content=Content(parts=[Part(text=f"**Text Found:**\n> {textbook_text[:200]}...")]))

        # Step 2: Call the second agent (ExtractConceptAgent) with the output of the first.
        yield Event(author=self.name, content=Content(parts=[Part(text="🔬 Identifying the core concept...")]))
        concept_response = await ctx.call_agent(agent_name="concept_extractor", input=textbook_text)
        concept = concept_response.output
        yield Event(author=self.name, content=Content(parts=[Part(text=f"**Concept:** {concept}")]))
        
        # Step 3: Call the final agent (GenerateWorksheetsAgent) with the output of the second.
        yield Event(author=self.name, content=Content(parts=[Part(text="📝 Creating worksheets...")]))
        worksheet_response = await ctx.call_agent(agent_name="worksheet_generator_llm", input=concept)
        final_worksheets = worksheet_response.output

        # Step 4: Yield the final result to the user.
        yield Event(
            author=self.name,
            content=Content(parts=[Part(text=f"✨ **Worksheets Ready!**\n\n{final_worksheets}")])
        )
