# ShikshaMitrah

**ShikshaMitrah** is an AI-powered teaching assistant system designed specifically for rural primary school teachers in India. It delivers educational support through instant story generation, knowledge base queries, lesson planning, and worksheet creation—all tailored to the rural context and accessible via an intuitive, multimodal web interface.

---

## Table of Contents

- [ShikshaMitrah Overview](#project-overview)
- [Core Architecture](#high-level-architecture)
- [Specialized Sub-Agents] 
    -[Story Generation Pipeline]
    -[Knowledge Base Pipeline]
    -[Lesson Planner Agent]
    -[Worksheet Generator]
    -[RAG Retrieval System]
- [External Integrations]

    -[Google Calendar Integration]
---
# ShikshaMitrah

## ShikshaMitrah Overview
This document provides a comprehensive overview of ShikshaMitrah, an AI-powered teaching assistant system designed specifically for rural primary school teachers in India. It covers the system's purpose, high-level architecture, core components, and how these components work together to provide educational support through story generation, knowledge base queries, lesson planning, and worksheet creation.

System Purpose and Scope
ShikshaMitrah serves as an intelligent teaching assistant that helps rural Indian teachers create educational content across multiple domains:

Story Generation: Creates culturally relevant stories for primary school children, including comprehension questions.

Knowledge Base Queries: Provides simplified explanations of complex concepts, always contextualized within rural Indian culture.

Lesson Planning: Develops multi-grade lesson plans with Google Calendar integration for efficient scheduling and organization.

Worksheet Creation: Converts textbook images into differentiated worksheets suitable for multiple grade levels.

The system operates through a web-based interface supporting both text and voice interactions, making it accessible to teachers with varying levels of technical expertise.

## Core Architecture

### Purpose and Scope

This document describes the central orchestration system that serves as the backbone of **ShikshaMitrah**. The core architecture handles routing of teacher requests to specialized sub-agents through a centralized `root_agent` that acts as an intelligent dispatcher. This system uses the **AgentTool** pattern to wrap specialized agents and manages session state for complex multi-step workflows.


- For detailed information about the individual specialized agents that the core architecture routes to, see [Specialized Sub-Agents](https://deepwiki.com/JKSANJAY27/Agentic-AI/3-specialized-sub-agents).
- For the communication protocols between the frontend and this core system, see [Communication Layer](https://deepwiki.com/JKSANJAY27/Agentic-AI/4-communication-layer).

### Central Orchestration Overview

The core architecture centers around the `root_agent` defined in [`manager/agent.py` lines 76-123](https://github.com/JKSANJAY27/Agentic-AI/blob/d7607f8f/manager/agent.py#L76-L123), which serves as the central dispatcher for all teacher requests. This agent uses the **Gemini 2.0 Flash** model for fast routing decisions and delegates work to four specialized **AgentTool**-wrapped pipelines.
<img width="1100" height="429" alt="Screenshot 2025-07-27 121404" src="https://github.com/user-attachments/assets/c3b0030a-e373-4d76-a94f-510f48ac6281" />

### AgentTool Architecture Pattern

The system employs a consistent **AgentTool** wrapper pattern that provides a standardized interface for the `root_agent` to interact with diverse specialized agents. Each **AgentTool** acts as an adapter that converts the root agent's tool calls into the appropriate format for the underlying specialized agent.

| AgentTool Instance          | Wrapped Agent                 | Purpose                              |
|----------------------------|------------------------------|------------------------------------|
| `story_generator_tool`      | `story_generation_pipeline`  | Generate culturally relevant stories |
| `knowledge_base_tool`       | `knowledge_base_pipeline`    | Answer knowledge questions with search |
| `lesson_planner_tool`       | `lesson_planner_agent`       | Create lessons and manage calendar |
| `worksheet_creator_tool`    | `WorksheetCreationSequence`  | Generate worksheets from images     |
<img width="607" height="803" alt="image" src="https://github.com/user-attachments/assets/53367f6d-4214-4283-893c-3a96e478216c" />

## Specialized Sub-Agents

This section provides a technical overview of the specialized sub-agent system in **ShikshaMitrah**. Each sub-agent is responsible for a specific educational task, such as story generation, knowledge retrieval, lesson planning, or worksheet creation. These sub-agents are orchestrated by the root agent and implement domain-specific pipelines, ensuring modularity and clarity of function across the system.
### Story Generation Pipeline

This document covers the multi-stage story creation system that generates culturally relevant stories for primary school children, complete with comprehension questions. The pipeline transforms teacher requests into localized educational stories with targeted follow-up questions, specifically designed for rural Indian educational contexts.

The Story Generation Pipeline leverages a sequential processing design, ensuring the creation of safe, age-appropriate, and contextually meaningful stories. It incorporates cultural references, local folklore, and Panchatantra-like motifs, making learning relatable and engaging for students.

For further technical and implementation details, see the [Story Generation Pipeline documentation](https://deepwiki.com/JKSANJAY27/Agentic-AI/3.1-story-generation-pipeline).

<img width="670" height="791" alt="image" src="https://github.com/user-attachments/assets/6e8e54c4-b3e0-4e44-829b-930c2c03055c" />
### Knowledge Base Pipeline

#### Purpose and Scope

The Knowledge Base Pipeline is an educational content generation system that processes teacher questions, retrieves information via Google Search, and delivers simplified answers with culturally relevant analogies for rural Indian primary school children. This pipeline handles knowledge-based queries as a core part of the broader ShikshaMitrah system.

- For information about the central routing system, see: [Core Architecture](https://deepwiki.com/JKSANJAY27/Agentic-AI/2-core-architecture)
- For lesson planning features, see: [Lesson Planner Agent](https://deepwiki.com/JKSANJAY27/Agentic-AI/3.3-lesson-planner-agent)
- For document-based retrieval and deeper content search, see: [RAG Retrieval System](https://deepwiki.com/JKSANJAY27/Agentic-AI/3.5-rag-retrieval-system)
- 
####Pipeline Architecture
The Knowledge Base Pipeline is implemented as a SequentialAgent that orchestrates five specialized sub-agents in a linear workflow. Each agent performs a specific transformation on the teacher's request until a final culturally-adapted answer is produced.

#### Data Flow and State Management

The Knowledge Base Pipeline uses session state variables to manage context and pass information between agents. Each sub-agent in the pipeline reads input from previous agent outputs and writes its results to well-defined session state keys—ensuring reliable, stateful communication and seamless multi-turn interactions for complex knowledge queries.
<img width="1642" height="165" alt="image" src="https://github.com/user-attachments/assets/89aae0e4-9690-422d-ac39-0c58a5354367" />



