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

