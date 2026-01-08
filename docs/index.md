# Universal Context Protocol (UCP) Documentation Index

Welcome to the central catalog for the Universal Context Protocol (UCP) initialization documents. This index provides a structured overview of all research papers and repository documentation converted for this project.

## 📄 Research Papers (PDF Conversions)

| Filename | Description | Tags |
| :--- | :--- | :--- |
| [2210.03629v3.md](pdfs/2210.03629v3.md) | **ReAct:** Synergizing reasoning and acting in language models. Proposes a paradigm where LLMs generate reasoning traces and task-specific actions in an interleaved manner. | reasoning, action, agents, context |
| [2302.04761v1.md](pdfs/2302.04761v1.md) | **Toolformer:** Language models that can teach themselves to use tools. Introduces a model trained to decide which APIs to call, when, and how to incorporate results. | tool selection, self-supervised, ML |
| [2305.15334v1.md](pdfs/2305.15334v1.md) | **Gorilla:** Large Language Model connected with massive APIs. Focuses on accurate API invocation and reducing hallucinations via retriever-aware finetuning. | API, tool use, finetuning, retrieval |
| [2307.16789v2.md](pdfs/2307.16789v2.md) | **Retooling LLMs:** Explores integrated document retrieval and tool-use. Equips LLMs with the ability to retrieve context and use tools in a synergistic loop. | RAG, tool use, orchestration |
| [2310.11511v1.md](pdfs/2310.11511v1.md) | **Self-Route:** Routing queries to specialized models based on LLM assessment. Improves efficiency and performance by selecting the most appropriate model for a task. | model routing, efficiency, orchestration |
| [2402.01159v2.md](pdfs/2402.01159v2.md) | **UFO:** A UI-focused agent for Windows OS interaction. Uses LLMs to perceive UI elements and plan actions at the control level rather than pixels. | UI agents, OS interaction, planning |
| [2403.03572v1.md](pdfs/2403.03572v1.md) | **Hyperuniform Point Sets:** Mathematical exploration of density fluctuations in many-particle systems. Extends hyperuniformity to projective spaces. | math, point sets, distribution |
| [2405.12166v1.md](pdfs/2405.12166v1.md) | **Stokes-Transport Equation:** Study of asymptotic stability in two-dimensional Couette flow. Focuses on mathematical stability in fluid dynamics models. | fluid dynamics, stability, math |

## 💻 Repository Documentation (Extracted)

### Gorilla
| Document | Description | Tags |
| :--- | :--- | :--- |
| [README.md](repos/gorilla/docs_extracted/README.md) | Main overview of Gorilla, its mission to enable LLMs to invoke 1,600+ APIs, and its key sub-projects. | API, tool use, leaderboard |
| [RAFT.md](repos/gorilla/docs_extracted/RAFT.md) | Details on Retrieval-Augmented Fine-tuning (RAFT) for adapting LLMs to domain-specific RAG and tool use. | RAG, finetuning, dataset |

### LangGraph
| Document | Description | Tags |
| :--- | :--- | :--- |
| [README.md](repos/langgraph/docs_extracted/README.md) | Introduction to LangGraph as a low-level orchestration framework for building stateful, multi-agent workflows. | orchestration, agents, state management |
| [STRUCTURE.md](repos/langgraph/docs_extracted/STRUCTURE.md) | Overview of how LangGraph documentation is structured, including concepts, tutorials, and API references. | docs, structure, mkdocs |

### LlamaIndex
| Document | Description | Tags |
| :--- | :--- | :--- |
| [README.md](repos/llama_index/docs_extracted/README.md) | Core documentation for LlamaIndex, a data framework for augmenting LLMs with private data sources. | RAG, data connectors, indices |
| [CONTRIBUTING.md](repos/llama_index/docs_extracted/CONTRIBUTING.md) | Guide for contributing to LlamaIndex, detailing the framework's monorepo structure and core modules. | framework, community, dev |
