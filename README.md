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
#### Pipeline Architecture
The Knowledge Base Pipeline is implemented as a SequentialAgent that orchestrates five specialized sub-agents in a linear workflow. Each agent performs a specific transformation on the teacher's request until a final culturally-adapted answer is produced.

#### Data Flow and State Management

The Knowledge Base Pipeline uses session state variables to manage context and pass information between agents. Each sub-agent in the pipeline reads input from previous agent outputs and writes its results to well-defined session state keys—ensuring reliable, stateful communication and seamless multi-turn interactions for complex knowledge queries.
<img width="1642" height="165" alt="image" src="https://github.com/user-attachments/assets/89aae0e4-9690-422d-ac39-0c58a5354367" />

### Lesson Planner Agent

#### Purpose and Scope
The Lesson Planner Agent is a specialized sub-agent within the ShikshaMitrah system that handles two primary functions: creating multi-grade weekly lesson plans and managing Google Calendar integration for scheduling educational activities. This agent serves rural primary school teachers by generating structured lesson plans for grades across Monday-Saturday schedules and providing comprehensive calendar management capabilities.

For information about other specialized sub-agents, see Story Generation Pipeline, Knowledge Base Pipeline, and Worksheet Generator. For details on how this agent integrates with the central routing system, see Root Agent Orchestration.

#### Agent Architecture
The Lesson Planner Agent is implemented as an LlmAgent using the gemini-2.0-flash-exp model, designed specifically for fast, conversational interactions around lesson planning and calendar management.

#### Agent Structure

- **Source Code:** [`manager/sub_agents/lesson_planner/agent.py`](https://github.com/JKSANJAY27/Agentic-AI/blob/d7607f8f/manager/sub_agents/lesson_planner/agent.py)

| Property       | Value                   | Purpose                                    |
|----------------|-------------------------|--------------------------------------------|
| `name`         | `"lesson_planner"`       | Agent identifier used for routing           |
| `model`        | `"gemini-2.0-flash-exp"` | Fast response model optimized for interactive lesson planning |
| `description`  | Creates weekly lesson plans and manages calendar integration |                                                 |

---
#### Calendar Integration Tools
The agent provides comprehensive Google Calendar integration through five specialized tools that handle all aspects of calendar management.

##### Tool Specifications
<img width="626" height="766" alt="image" src="https://github.com/user-attachments/assets/a7911126-785f-4986-ace6-dec4f791f6d6" />

### Worksheet Generator

#### Purpose and Scope
The Worksheet Generator is a specialized sub-agent pipeline that converts textbook images into grade-specific educational worksheets. It processes uploaded textbook pages through optical character recognition (OCR), concept extraction, and multi-grade worksheet generation to create differentiated learning materials for primary school students.

This system handles image-to-worksheet conversion specifically. For story generation from text prompts, see Story Generation Pipeline. For general knowledge retrieval, see Knowledge Base Pipeline.

#### System Architecture
The Worksheet Generator implements a three-stage sequential processing pipeline using the Google Agent Development Kit (ADK) framework:

##### Sequential Processing Flow

<img width="694" height="789" alt="image" src="https://github.com/user-attachments/assets/59b01c7e-4d5e-44bd-90d3-5ed03056e093" />

###### Component Class Hierarchy
<img width="1639" height="776" alt="image" src="https://github.com/user-attachments/assets/2f204b4e-ad18-465e-becb-f17dff52120c" />

#### Data Flow and Session State
The worksheet generation process relies on session state management for image handling and real-time user feedback:
<img width="1673" height="719" alt="image" src="https://github.com/user-attachments/assets/52c11679-f083-4f62-9f6a-d403ca082026" />


### RAG Retrieval System

#### Purpose and Scope
The RAG Retrieval System provides context-based question answering capabilities by retrieving relevant information from a pre-indexed knowledge base of educational content. This system uses vector embeddings and cosine similarity search to find the most relevant document chunks for user queries, then generates simplified answers suitable for primary school children.

This system specifically handles retrieval from indexed study materials stored in Google Cloud Storage. For broader knowledge retrieval that includes Google Search integration, see Knowledge Base Pipeline. For lesson-specific content generation, see Lesson Planner Agent.

#### System Architecture
The RAG system operates as a three-stage sequential pipeline that processes user queries through embedding-based retrieval and answer generation.

##### RAG Pipeline Architecture

<img width="1475" height="651" alt="Screenshot 2025-07-27 121146" src="https://github.com/user-attachments/assets/1703345d-be8e-4040-a74d-3d4711beaa92" />


##### Data Storage and Loading Architecture

<img width="1570" height="556" alt="image" src="https://github.com/user-attachments/assets/93ab1544-3eca-4855-93c3-dcf97ffa9155" />

#### Data Flow and Processing
<img width="1414" height="791" alt="image" src="https://github.com/user-attachments/assets/cf3cd2e2-91b9-46db-879f-bc65eb659de2" />

##### Vector Similarity Search Algorithm

The core retrieval algorithm implements cosine similarity search across pre-computed embeddings:

1. **Query Embedding:**  
   The user query is embedded using `EMBEDDING_MODEL.get_embeddings()`.

2. **Similarity Computation:**  
   Cosine similarity is calculated for each chunk using the formula:  
   `np.dot(a, b) / (norm(a) * norm(b))`

3. **Best Match Selection:**  
   The chunk with the highest similarity score is selected via `np.argmax(similarities)`.

4. **Context Retrieval:**  
   The corresponding text and metadata are retrieved from `GLOBAL_CHUNK_METADATA`.

**Sources:**  
[`manager/sub_agents/rag_retrieval/agent.py` lines 82-105](https://github.com

### External Integrations
#### Purpose and Scope
This document covers the external service integrations that enable ShikshaMitrah to function as a comprehensive AI teaching assistant. The system integrates with multiple Google Cloud Platform services and APIs to provide educational content generation, calendar management, knowledge retrieval, and AI processing capabilities.

For information about the internal agent orchestration that utilizes these external services, see Core Architecture. For specific implementation details of individual sub-agents that consume these services, see Specialized Sub-Agents.

#### Integration Overview
ShikshaMitrah integrates with several external services to deliver its educational capabilities:

##### External Services Integration Architecture
<img width="1644" height="344" alt="image" src="https://github.com/user-attachments/assets/d4f51751-2898-48a3-82c1-14d42c306cb3" />

#### Google Calendar Integration
The Google Calendar integration provides comprehensive event management capabilities for lesson planning and scheduling. This integration is implemented through a dedicated set of tools in the lesson planner sub-agent.

##### Calendar Service Architecture
<img width="1274" height="823" alt="image" src="https://github.com/user-attachments/assets/86a4d9ea-9f46-47df-9bfe-74f49dd1e1c4" />

##### Calendar Operations
<img width="831" height="721" alt="image" src="https://github.com/user-attachments/assets/120a2bca-7e36-4c61-becf-ef3549140397" />




