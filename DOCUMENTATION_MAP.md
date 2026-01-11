# UCP Documentation Map

This map helps you navigate the extensive documentation in the Universal Context Protocol repository.

## Quick Start Guides

### For New Users
- [README.md](README.md) - Project overview and quick start (includes dual-track structure)
- [shared/README.md](shared/README.md) - Shared components documentation
- [local/README.md](local/README.md) - Local MVP documentation
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup

### For Developers
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development guidelines for both versions
- [CLAUDE.md](CLAUDE.md) - AI agent developer guide
- [docs/roadmap.md](docs/roadmap.md) - Consolidated roadmap with executive summary, phases, critical path, and prioritization framework

### For Researchers
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) - Original vision and design philosophy

## Documentation Hierarchy

### Architecture & Design
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) ⭐ Source of truth for architecture
- [docs/sota_tool_selection_prototype.md](docs/sota_tool_selection_prototype.md) - SOTA routing pipeline

### Planning & Roadmap
- [docs/roadmap.md](docs/roadmap.md) ⭐ Consolidated roadmap with executive summary, phases, critical path, and prioritization framework
- [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) ⭐ Repository reorganization plan (COMPLETED)

### Research & Best Practices
- [docs/index.md](docs/index.md) - Research paper catalog
- [docs/synthesis_agent_design.md](docs/synthesis_agent_design.md) - Lessons from LangGraph, Gorilla, MCP
- [docs/synthesis_context_management.md](docs/synthesis_context_management.md) - Context management patterns
- [docs/synthesis_feedback_eval.md](docs/synthesis_feedback_eval.md) - Evaluation strategies
- [docs/synthesis_tool_selection.md](docs/synthesis_tool_selection.md) - Tool selection best practices

### User Guides
- [README.md](README.md) - Main project documentation
- [docs/getting_started.md](docs/getting_started.md) - Installation and setup
- [docs/debugging_playbook.md](docs/debugging_playbook.md) - Troubleshooting guide
- [docs/evaluation_harness.md](docs/evaluation_harness.md) - Testing framework
- [docs/production_deployment.md](docs/production_deployment.md) - Production deployment guide

### Local MVP Documentation
- [local/README.md](local/README.md) - Local MVP overview
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup
- [local/docs/mvp_architecture.md](local/docs/mvp_architecture.md) - Architecture overview
- [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) - User guide
- [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) - Deployment guide

### Cloud Version Documentation
- [cloud/README.md](cloud/README.md) - Cloud version overview
- [cloud/docs/roadmap.md](cloud/docs/roadmap.md) - Cloud implementation roadmap
- [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) - Architecture overview
- [cloud/docs/cloud_deployment.md](cloud/docs/cloud_deployment.md) - Deployment guide
- [cloud/docs/cloud_api_reference.md](cloud/docs/cloud_api_reference.md) - API reference

### Shared Components Documentation
- [shared/README.md](shared/README.md) - Shared components overview
- [shared/docs/api_reference.md](shared/docs/api_reference.md) - Shared API documentation

### Client Documentation
- [clients/README.md](clients/README.md) - Client applications overview
- [local/clients/](local/clients/) - Local MVP clients (CLI, desktop)
- [cloud/clients/](cloud/clients/) - Cloud clients (VS Code, web)

### Reports
- [reports/codebase_audit_report.md](reports/codebase_audit_report.md) - Technical audit
- [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md) - Research paper validation
- [reports/roadmap_edge.md](reports/roadmap_edge.md) - Client-focused roadmap
- [reports/validation_report.json](reports/validation_report.json) - Evaluation results

## Document Status Legend

- ⭐ Source of truth / Primary reference
- ✅ Current and maintained
- 📝 Archived (consolidated into other documents)
- ⚠️ Redundant / Consider consolidating
- 📝 Draft / Work in progress

## Redundancy Notes

### Architecture Documentation
- `docs/ucp_design_plan.md` overlaps ~60% with `ucp_source_of_truth_whitepaper.md`
- Recommendation: Keep whitepaper as source of truth, deprecate design plan
- **Status:** Archived to `docs/archive/ucp_design_plan.md` (2026-01-10)

### Planning Documentation
- `DEV_PLAN_TO_COMPLETION.md`, `START_HERE.md`, `ROADMAP_VISUAL.md`, and `PRIORITIZATION_MATRIX.md` have ~40% overlap
- Recommendation: Consolidated into single document with sections
- **Status:** Archived to `docs/archive/` (2026-01-10)
  - `docs/archive/DEV_PLAN_TO_COMPLETION.md`
  - `docs/archive/START_HERE.md`
  - `docs/archive/ROADMAP_VISUAL.md`
  - `docs/archive/PRIORITIZATION_MATRIX.md`
  - **New location:** `docs/roadmap.md` (consolidated roadmap)

### Agent Documentation
- `.agent/AGENT_A_BACKEND_PLAN.md` and `.agent/BACKEND_EXECUTIVE_SUMMARY.md` overlap ~50%
- Recommendation: Keep executive summary, consolidate detailed plans
- **Status:** Archived to `.agent/archive/AGENT_A_BACKEND_PLAN.md` (2026-01-10)
- **Primary reference:** `.agent/BACKEND_EXECUTIVE_SUMMARY.md`

## Finding What You Need

### "I want to understand what UCP is"
1. Read [README.md](README.md) sections 1-3 (includes dual-track structure)
2. Read [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) sections 1-2
3. Read [shared/README.md](shared/README.md) for shared components overview
4. Read [local/README.md](local/README.md) for local MVP overview
5. Read [cloud/README.md](cloud/README.md) for cloud version overview (planned)

### "I want to start developing"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for development guidelines
2. Read [CLAUDE.md](CLAUDE.md) for architecture overview
3. Read [docs/roadmap.md](docs/roadmap.md) for immediate action items
4. Follow [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) for reorganization details

### "I want to understand research foundation"
1. Read [docs/index.md](docs/index.md) for paper catalog
2. Read synthesis documents in [docs/](docs/) for distilled lessons
3. Review OCR'd papers in [docs/pdfs/](docs/pdfs/)

### "I need to debug an issue"
1. Check [docs/debugging_playbook.md](docs/debugging_playbook.md)
2. Review [CLAUDE.md](CLAUDE.md) known issues section
3. Check trace IDs in debug dashboard

### "I want to contribute"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for contribution guidelines
2. Read [docs/roadmap.md](docs/roadmap.md) for current priorities
3. Review [docs/roadmap.md](docs/roadmap.md) for roadmap phases
4. Check [docs/roadmap.md](docs/roadmap.md) for prioritization framework

### "I want to use the Local MVP"
1. Read [local/README.md](local/README.md) for overview
2. Follow [local/docs/getting_started.md](local/docs/getting_started.md) for installation
3. Read [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) for usage guide
4. Check [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) for deployment

### "I want to deploy UCP in production"
1. Read [docs/production_deployment.md](docs/production_deployment.md) for production setup
2. Follow [local/docs/getting_started.md](local/docs/getting_started.md) for installation
3. Check [docs/debugging_playbook.md](docs/debugging_playbook.md) for troubleshooting

### "I want to understand the Cloud version"
1. Read [cloud/README.md](cloud/README.md) for overview
2. Check [cloud/docs/roadmap.md](cloud/docs/roadmap.md) for implementation timeline
3. Review [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) for architecture

## Project Status

**Overall Completion:** ~65% (Alpha Stage)

**Repository Structure:** ✅ Reorganized (2026-01-10) - New dual-track structure implemented

### What's Working (Local MVP):
- Core MCP protocol implementation (stdio transport)
- Semantic router with hybrid search (keyword + embeddings)
- Vector database (ChromaDB + sentence-transformers)
- Session persistence (SQLite)
- SOTA routing pipeline with bandit learning
- Comprehensive test suite
- Evaluation harness framework
- CLI interface (serve, index, search, status)
- Streamlit debug dashboard

### What's Incomplete (Local MVP):
- SSE/HTTP transports for downstream servers
- Client applications not wired to UCP server
- Confidence thresholds and fallback logic
- Tool affordance generation
- Observability contracts
- Error standardization
- Request tracing infrastructure
- PyPI/Docker distribution

### Cloud Version Status:
- **Status:** Planned, not yet implemented
- **Timeline:** See [cloud/docs/roadmap.md](cloud/docs/roadmap.md)
- **Architecture:** See [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md)

**Estimated Time to Local MVP v1.0:** 8-12 weeks

---

*Last updated: 2026-01-11*

This map helps you navigate the extensive documentation in the Universal Context Protocol repository.

## Quick Start Guides

### For New Users
- [README.md](README.md) - Project overview and quick start (includes dual-track structure)
- [shared/README.md](shared/README.md) - Shared components documentation
- [local/README.md](local/README.md) - Local MVP documentation
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup

### For Developers
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development guidelines for both versions
- [CLAUDE.md](CLAUDE.md) - AI agent developer guide
- [docs/roadmap.md](docs/roadmap.md) - Consolidated roadmap with executive summary, phases, critical path, and prioritization framework

### For Researchers
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) - Original vision and design philosophy

## Documentation Hierarchy

### Architecture & Design
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) ⭐ Source of truth for architecture
- [docs/sota_tool_selection_prototype.md](docs/sota_tool_selection_prototype.md) - SOTA routing pipeline

### Planning & Roadmap
- [docs/roadmap.md](docs/roadmap.md) ⭐ Consolidated roadmap with executive summary, phases, critical path, and prioritization framework
- [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) ⭐ Repository reorganization plan (COMPLETED)

### Research & Best Practices
- [docs/index.md](docs/index.md) - Research paper catalog
- [docs/synthesis_agent_design.md](docs/synthesis_agent_design.md) - Lessons from LangGraph, Gorilla, MCP
- [docs/synthesis_context_management.md](docs/synthesis_context_management.md) - Context management patterns
- [docs/synthesis_feedback_eval.md](docs/synthesis_feedback_eval.md) - Evaluation strategies
- [docs/synthesis_tool_selection.md](docs/synthesis_tool_selection.md) - Tool selection best practices

### User Guides
- [README.md](README.md) - Main project documentation
- [docs/getting_started.md](docs/getting_started.md) - Installation and setup
- [docs/debugging_playbook.md](docs/debugging_playbook.md) - Troubleshooting guide
- [docs/evaluation_harness.md](docs/evaluation_harness.md) - Testing framework
- [docs/production_deployment.md](docs/production_deployment.md) - Production deployment guide

### Local MVP Documentation
- [local/README.md](local/README.md) - Local MVP overview
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup
- [local/docs/mvp_architecture.md](local/docs/mvp_architecture.md) - Architecture overview
- [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) - User guide
- [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) - Deployment guide

### Cloud Version Documentation
- [cloud/README.md](cloud/README.md) - Cloud version overview
- [cloud/docs/roadmap.md](cloud/docs/roadmap.md) - Cloud implementation roadmap
- [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) - Architecture overview
- [cloud/docs/cloud_deployment.md](cloud/docs/cloud_deployment.md) - Deployment guide
- [cloud/docs/cloud_api_reference.md](cloud/docs/cloud_api_reference.md) - API reference

### Shared Components Documentation
- [shared/README.md](shared/README.md) - Shared components overview
- [shared/docs/api_reference.md](shared/docs/api_reference.md) - Shared API documentation

### Client Documentation
- [clients/README.md](clients/README.md) - Client applications overview
- [local/clients/](local/clients/) - Local MVP clients (CLI, desktop)
- [cloud/clients/](cloud/clients/) - Cloud clients (VS Code, web)

### Reports
- [reports/codebase_audit_report.md](reports/codebase_audit_report.md) - Technical audit
- [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md) - Research paper validation
- [reports/roadmap_edge.md](reports/roadmap_edge.md) - Client-focused roadmap
- [reports/validation_report.json](reports/validation_report.json) - Evaluation results

## Document Status Legend

- ⭐ Source of truth / Primary reference
- ✅ Current and maintained
- 📝 Archived (consolidated into other documents)
- ⚠️ Redundant / Consider consolidating
- 📝 Draft / Work in progress

## Redundancy Notes

### Architecture Documentation
- `docs/ucp_design_plan.md` overlaps ~60% with `ucp_source_of_truth_whitepaper.md`
- Recommendation: Keep whitepaper as source of truth, deprecate design plan
- **Status:** Archived to `docs/archive/ucp_design_plan.md` (2026-01-10)

### Planning Documentation
- `DEV_PLAN_TO_COMPLETION.md`, `START_HERE.md`, `ROADMAP_VISUAL.md`, and `PRIORITIZATION_MATRIX.md` have ~40% overlap
- Recommendation: Consolidated into single document with sections
- **Status:** Archived to `docs/archive/` (2026-01-10)
  - `docs/archive/DEV_PLAN_TO_COMPLETION.md`
  - `docs/archive/START_HERE.md`
  - `docs/archive/ROADMAP_VISUAL.md`
  - `docs/archive/PRIORITIZATION_MATRIX.md`
  - **New location:** `docs/roadmap.md` (consolidated roadmap)

### Agent Documentation
- `.agent/AGENT_A_BACKEND_PLAN.md` and `.agent/BACKEND_EXECUTIVE_SUMMARY.md` overlap ~50%
- Recommendation: Keep executive summary, consolidate detailed plans
- **Status:** Archived to `.agent/archive/AGENT_A_BACKEND_PLAN.md` (2026-01-10)
- **Primary reference:** `.agent/BACKEND_EXECUTIVE_SUMMARY.md`

## Finding What You Need

### "I want to understand what UCP is"
1. Read [README.md](README.md) sections 1-3 (includes dual-track structure)
2. Read [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) sections 1-2
3. Read [shared/README.md](shared/README.md) for shared components overview
4. Read [local/README.md](local/README.md) for local MVP overview
5. Read [cloud/README.md](cloud/README.md) for cloud version overview (planned)

### "I want to start developing"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for development guidelines
2. Read [CLAUDE.md](CLAUDE.md) for architecture overview
3. Read [docs/roadmap.md](docs/roadmap.md) for immediate action items
4. Follow [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) for reorganization details

### "I want to understand research foundation"
1. Read [docs/index.md](docs/index.md) for paper catalog
2. Read synthesis documents in [docs/](docs/) for distilled lessons
3. Review OCR'd papers in [docs/pdfs/](docs/pdfs/)

### "I need to debug an issue"
1. Check [docs/debugging_playbook.md](docs/debugging_playbook.md)
2. Review [CLAUDE.md](CLAUDE.md) known issues section
3. Check trace IDs in debug dashboard

### "I want to contribute"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for contribution guidelines
2. Read [docs/roadmap.md](docs/roadmap.md) for current priorities
3. Review [docs/roadmap.md](docs/roadmap.md) for roadmap phases
4. Check [docs/roadmap.md](docs/roadmap.md) for prioritization framework

### "I want to use the Local MVP"
1. Read [local/README.md](local/README.md) for overview
2. Follow [local/docs/getting_started.md](local/docs/getting_started.md) for installation
3. Read [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) for usage guide
4. Check [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) for deployment

### "I want to deploy UCP in production"
1. Read [docs/production_deployment.md](docs/production_deployment.md) for production setup
2. Follow [local/docs/getting_started.md](local/docs/getting_started.md) for installation
3. Check [docs/debugging_playbook.md](docs/debugging_playbook.md) for troubleshooting

### "I want to understand the Cloud version"
1. Read [cloud/README.md](cloud/README.md) for overview
2. Check [cloud/docs/roadmap.md](cloud/docs/roadmap.md) for implementation timeline
3. Review [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) for architecture

## Project Status

**Overall Completion:** ~65% (Alpha Stage)

**Repository Structure:** ✅ Reorganized (2026-01-10) - New dual-track structure implemented

### What's Working (Local MVP):
- Core MCP protocol implementation (stdio transport)
- Semantic router with hybrid search (keyword + embeddings)
- Vector database (ChromaDB + sentence-transformers)
- Session persistence (SQLite)
- SOTA routing pipeline with bandit learning
- Comprehensive test suite
- Evaluation harness framework
- CLI interface (serve, index, search, status)
- Streamlit debug dashboard

### What's Incomplete (Local MVP):
- SSE/HTTP transports for downstream servers
- Client applications not wired to UCP server
- Confidence thresholds and fallback logic
- Tool affordance generation
- Observability contracts
- Error standardization
- Request tracing infrastructure
- PyPI/Docker distribution

### Cloud Version Status:
- **Status:** Planned, not yet implemented
- **Timeline:** See [cloud/docs/roadmap.md](cloud/docs/roadmap.md)
- **Architecture:** See [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md)

**Estimated Time to Local MVP v1.0:** 8-12 weeks

---

*Last updated: 2026-01-11*

- [README.md](README.md) - Project overview and quick start (includes dual-track structure)
- [shared/README.md](shared/README.md) - Shared components documentation
- [local/README.md](local/README.md) - Local MVP documentation
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup

### For Developers
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development guidelines for both versions
- [CLAUDE.md](CLAUDE.md) - AI agent developer guide
- [docs/roadmap.md](docs/roadmap.md) - Consolidated roadmap with executive summary, phases, critical path, and prioritization framework

### For Researchers
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) - Original vision and design philosophy

## Documentation Hierarchy

### Architecture & Design
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) ⭐ Source of truth for architecture
- [docs/sota_tool_selection_prototype.md](docs/sota_tool_selection_prototype.md) - SOTA routing pipeline

### Planning & Roadmap
- [docs/roadmap.md](docs/roadmap.md) ⭐ Consolidated roadmap with executive summary, phases, critical path, and prioritization framework
- [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) ⭐ Repository reorganization plan (COMPLETED)

### Research & Best Practices
- [docs/index.md](docs/index.md) - Research paper catalog
- [docs/synthesis_agent_design.md](docs/synthesis_agent_design.md) - Lessons from LangGraph, Gorilla, MCP
- [docs/synthesis_context_management.md](docs/synthesis_context_management.md) - Context management patterns
- [docs/synthesis_feedback_eval.md](docs/synthesis_feedback_eval.md) - Evaluation strategies
- [docs/synthesis_tool_selection.md](docs/synthesis_tool_selection.md) - Tool selection best practices

### User Guides
- [README.md](README.md) - Main project documentation
- [docs/getting_started.md](docs/getting_started.md) - Installation and setup
- [docs/debugging_playbook.md](docs/debugging_playbook.md) - Troubleshooting guide
- [docs/evaluation_harness.md](docs/evaluation_harness.md) - Testing framework

### Local MVP Documentation
- [local/README.md](local/README.md) - Local MVP overview
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup
- [local/docs/mvp_architecture.md](local/docs/mvp_architecture.md) - Architecture overview
- [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) - User guide
- [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) - Deployment guide

### Cloud Version Documentation
- [cloud/README.md](cloud/README.md) - Cloud version overview
- [cloud/docs/roadmap.md](cloud/docs/roadmap.md) - Cloud implementation roadmap
- [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) - Architecture overview
- [cloud/docs/cloud_deployment.md](cloud/docs/cloud_deployment.md) - Deployment guide
- [cloud/docs/cloud_api_reference.md](cloud/docs/cloud_api_reference.md) - API reference

### Shared Components Documentation
- [shared/README.md](shared/README.md) - Shared components overview
- [shared/docs/api_reference.md](shared/docs/api_reference.md) - Shared API documentation

### Client Documentation
- [clients/README.md](clients/README.md) - Client applications overview
- [local/clients/](local/clients/) - Local MVP clients (CLI, desktop)
- [cloud/clients/](cloud/clients/) - Cloud clients (VS Code, web)

### Reports
- [reports/codebase_audit_report.md](reports/codebase_audit_report.md) - Technical audit
- [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md) - Research paper validation
- [reports/roadmap_edge.md](reports/roadmap_edge.md) - Client-focused roadmap
- [reports/validation_report.json](reports/validation_report.json) - Evaluation results

## Document Status Legend

- ⭐ Source of truth / Primary reference
- ✅ Current and maintained
- 📝 Archived (consolidated into other documents)
- ⚠️ Redundant / Consider consolidating
- 📝 Draft / Work in progress

## Redundancy Notes

### Architecture Documentation
- `docs/ucp_design_plan.md` overlaps ~60% with `ucp_source_of_truth_whitepaper.md`
- Recommendation: Keep whitepaper as source of truth, deprecate design plan
- **Status:** Archived to `docs/archive/ucp_design_plan.md` (2026-01-10)

### Planning Documentation
- `DEV_PLAN_TO_COMPLETION.md`, `START_HERE.md`, `ROADMAP_VISUAL.md`, and `PRIORITIZATION_MATRIX.md` have ~40% overlap
- Recommendation: Consolidated into single document with sections
- **Status:** Archived to `docs/archive/` (2026-01-10)
  - `docs/archive/DEV_PLAN_TO_COMPLETION.md`
  - `docs/archive/START_HERE.md`
  - `docs/archive/ROADMAP_VISUAL.md`
  - `docs/archive/PRIORITIZATION_MATRIX.md`
  - **New location:** `docs/roadmap.md` (consolidated roadmap)

### Agent Documentation
- `.agent/AGENT_A_BACKEND_PLAN.md` and `.agent/BACKEND_EXECUTIVE_SUMMARY.md` overlap ~50%
- Recommendation: Keep executive summary, consolidate detailed plans
- **Status:** Archived to `.agent/archive/AGENT_A_BACKEND_PLAN.md` (2026-01-10)
- **Primary reference:** `.agent/BACKEND_EXECUTIVE_SUMMARY.md`

## Finding What You Need

### "I want to understand what UCP is"
1. Read [README.md](README.md) sections 1-3 (includes dual-track structure)
2. Read [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) sections 1-2
3. Read [shared/README.md](shared/README.md) for shared components overview
4. Read [local/README.md](local/README.md) for local MVP overview
5. Read [cloud/README.md](cloud/README.md) for cloud version overview (planned)

### "I want to start developing"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for development guidelines
2. Read [CLAUDE.md](CLAUDE.md) for architecture overview
3. Read [docs/roadmap.md](docs/roadmap.md) for immediate action items
4. Follow [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) for reorganization details

### "I want to understand research foundation"
1. Read [docs/index.md](docs/index.md) for paper catalog
2. Read synthesis documents in [docs/](docs/) for distilled lessons
3. Review OCR'd papers in [docs/pdfs/](docs/pdfs/)

### "I need to debug an issue"
1. Check [docs/debugging_playbook.md](docs/debugging_playbook.md)
2. Review [CLAUDE.md](CLAUDE.md) known issues section
3. Check trace IDs in debug dashboard

### "I want to contribute"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for contribution guidelines
2. Read [docs/roadmap.md](docs/roadmap.md) for current priorities
3. Review [docs/roadmap.md](docs/roadmap.md) for roadmap phases
4. Check [docs/roadmap.md](docs/roadmap.md) for prioritization framework

### "I want to use the Local MVP"
1. Read [local/README.md](local/README.md) for overview
2. Follow [local/docs/getting_started.md](local/docs/getting_started.md) for installation
3. Read [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) for usage guide
4. Check [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) for deployment

### "I want to understand the Cloud version"
1. Read [cloud/README.md](cloud/README.md) for overview
2. Check [cloud/docs/roadmap.md](cloud/docs/roadmap.md) for implementation timeline
3. Review [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) for architecture

## Project Status

**Overall Completion:** ~65% (Alpha Stage)

**Repository Structure:** ✅ Reorganized (2026-01-10) - New dual-track structure implemented

### What's Working (Local MVP):
- Core MCP protocol implementation (stdio transport)
- Semantic router with hybrid search (keyword + embeddings)
- Vector database (ChromaDB + sentence-transformers)
- Session persistence (SQLite)
- SOTA routing pipeline with bandit learning
- Comprehensive test suite
- Evaluation harness framework
- CLI interface (serve, index, search, status)
- Streamlit debug dashboard

### What's Incomplete (Local MVP):
- SSE/HTTP transports for downstream servers
- Client applications not wired to UCP server
- Confidence thresholds and fallback logic
- Tool affordance generation
- Observability contracts
- Error standardization
- Request tracing infrastructure
- PyPI/Docker distribution

### Cloud Version Status:
- **Status:** Planned, not yet implemented
- **Timeline:** See [cloud/docs/roadmap.md](cloud/docs/roadmap.md)
- **Architecture:** See [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md)

**Estimated Time to Local MVP v1.0:** 8-12 weeks

---

*Last updated: 2026-01-10*

- [docs/debugging_playbook.md](docs/debugging_playbook.md) - Troubleshooting guide
- [docs/evaluation_harness.md](docs/evaluation_harness.md) - Testing framework

### Client Documentation
- [clients/README.md](clients/README.md) - Client applications overview
- [local/clients/](local/clients/) - Local MVP clients (CLI, desktop)
- [cloud/clients/](cloud/clients/) - Cloud clients (VS Code, web)

### Reports
- [reports/codebase_audit_report.md](reports/codebase_audit_report.md) - Technical audit
- [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md) - Research paper validation
- [reports/roadmap_edge.md](reports/roadmap_edge.md) - Client-focused roadmap
- [reports/validation_report.json](reports/validation_report.json) - Evaluation results

## Document Status Legend

- ⭐ Source of truth / Primary reference
- ✅ Current and maintained
- 📝 Archived (consolidated into other documents)
- ⚠️ Redundant / Consider consolidating
- 📝 Draft / Work in progress

## Redundancy Notes

### Architecture Documentation
- `docs/ucp_design_plan.md` overlaps ~60% with `ucp_source_of_truth_whitepaper.md`
- Recommendation: Keep whitepaper as source of truth, deprecate design plan
- **Status:** Archived to `docs/archive/ucp_design_plan.md` (2026-01-10)

### Planning Documentation
- `DEV_PLAN_TO_COMPLETION.md`, `START_HERE.md`, `ROADMAP_VISUAL.md`, and `PRIORITIZATION_MATRIX.md` have ~40% overlap
- Recommendation: Consolidated into single document with sections
- **Status:** Archived to `docs/archive/` (2026-01-10)
  - `docs/archive/DEV_PLAN_TO_COMPLETION.md`
  - `docs/archive/START_HERE.md`
  - `docs/archive/ROADMAP_VISUAL.md`
  - `docs/archive/PRIORITIZATION_MATRIX.md`
  - **New location:** `docs/roadmap.md` (consolidated roadmap)

### Agent Documentation
- `.agent/AGENT_A_BACKEND_PLAN.md` and `.agent/BACKEND_EXECUTIVE_SUMMARY.md` overlap ~50%
- Recommendation: Keep executive summary, consolidate detailed plans
- **Status:** Archived to `.agent/archive/AGENT_A_BACKEND_PLAN.md` (2026-01-10)
- **Primary reference:** `.agent/BACKEND_EXECUTIVE_SUMMARY.md`

## Finding What You Need

### "I want to understand what UCP is"
1. Read [README.md](README.md) sections 1-3 (includes new dual-track structure)
2. Read [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) sections 1-2
3. Read [shared/README.md](shared/README.md) for shared components overview
4. Read [local/README.md](local/README.md) for local MVP overview
5. Read [cloud/README.md](cloud/README.md) for cloud version overview (planned)

### "I want to start developing"
1. Read [CLAUDE.md](CLAUDE.md) for architecture overview
2. Read [docs/roadmap.md](docs/roadmap.md) for immediate action items
3. Follow [.agent/workflows/start-phase1.md](.agent/workflows/start-phase1.md) for step-by-step guide
4. Read [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) for reorganization details

### "I want to understand research foundation"
1. Read [docs/index.md](docs/index.md) for paper catalog
2. Read synthesis documents in [docs/](docs/) for distilled lessons
3. Review OCR'd papers in [docs/pdfs/](docs/pdfs/)

### "I need to debug an issue"
1. Check [docs/debugging_playbook.md](docs/debugging_playbook.md)
2. Review [CLAUDE.md](CLAUDE.md) known issues section
3. Check trace IDs in debug dashboard

### "I want to contribute"
1. Read [docs/roadmap.md](docs/roadmap.md) for current priorities
2. Review [docs/roadmap.md](docs/roadmap.md) for roadmap phases
3. Check [docs/roadmap.md](docs/roadmap.md) for prioritization framework

## Project Status

**Overall Completion:** ~65% (Alpha Stage)

**What's Working:**
- Core MCP protocol implementation (stdio transport)
- Semantic router with hybrid search (keyword + embeddings)
- Vector database (ChromaDB + sentence-transformers)
- Session persistence (SQLite)
- SOTA routing pipeline with bandit learning
- Comprehensive test suite
- Evaluation harness framework
- **Repository reorganized** (2026-01-10) - New dual-track structure implemented

**What's Incomplete:**
- SSE/HTTP transports for downstream servers
- Client applications not wired to UCP server
- Confidence thresholds and fallback logic
- Tool affordance generation
- Observability contracts
- Error standardization
- Request tracing infrastructure
- PyPI/Docker distribution

**Estimated Time to v1.0:** 8-12 weeks

---

*Last updated: 2026-01-10*

This map helps you navigate the extensive documentation in the Universal Context Protocol repository.

## Quick Start Guides

### For New Users
- [README.md](README.md) - Project overview and quick start (includes dual-track structure)
- [shared/README.md](shared/README.md) - Shared components documentation
- [local/README.md](local/README.md) - Local MVP documentation
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup

### For Developers
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development guidelines for both versions
- [CLAUDE.md](CLAUDE.md) - AI agent developer guide
- [docs/roadmap.md](docs/roadmap.md) - Consolidated roadmap with executive summary, phases, critical path, and prioritization framework

### For Researchers
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) - Original vision and design philosophy

## Documentation Hierarchy

### Architecture & Design
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) ⭐ Source of truth for architecture
- [docs/sota_tool_selection_prototype.md](docs/sota_tool_selection_prototype.md) - SOTA routing pipeline

### Planning & Roadmap
- [docs/roadmap.md](docs/roadmap.md) ⭐ Consolidated roadmap with executive summary, phases, critical path, and prioritization framework
- [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) ⭐ Repository reorganization plan (COMPLETED)

### Research & Best Practices
- [docs/index.md](docs/index.md) - Research paper catalog
- [docs/synthesis_agent_design.md](docs/synthesis_agent_design.md) - Lessons from LangGraph, Gorilla, MCP
- [docs/synthesis_context_management.md](docs/synthesis_context_management.md) - Context management patterns
- [docs/synthesis_feedback_eval.md](docs/synthesis_feedback_eval.md) - Evaluation strategies
- [docs/synthesis_tool_selection.md](docs/synthesis_tool_selection.md) - Tool selection best practices

### User Guides
- [README.md](README.md) - Main project documentation
- [docs/getting_started.md](docs/getting_started.md) - Installation and setup
- [docs/debugging_playbook.md](docs/debugging_playbook.md) - Troubleshooting guide
- [docs/evaluation_harness.md](docs/evaluation_harness.md) - Testing framework
- [docs/production_deployment.md](docs/production_deployment.md) - Production deployment guide

### Local MVP Documentation
- [local/README.md](local/README.md) - Local MVP overview
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup
- [local/docs/mvp_architecture.md](local/docs/mvp_architecture.md) - Architecture overview
- [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) - User guide
- [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) - Deployment guide

### Cloud Version Documentation
- [cloud/README.md](cloud/README.md) - Cloud version overview
- [cloud/docs/roadmap.md](cloud/docs/roadmap.md) - Cloud implementation roadmap
- [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) - Architecture overview
- [cloud/docs/cloud_deployment.md](cloud/docs/cloud_deployment.md) - Deployment guide
- [cloud/docs/cloud_api_reference.md](cloud/docs/cloud_api_reference.md) - API reference

### Shared Components Documentation
- [shared/README.md](shared/README.md) - Shared components overview
- [shared/docs/api_reference.md](shared/docs/api_reference.md) - Shared API documentation

### Client Documentation
- [clients/README.md](clients/README.md) - Client applications overview
- [local/clients/](local/clients/) - Local MVP clients (CLI, desktop)
- [cloud/clients/](cloud/clients/) - Cloud clients (VS Code, web)

### Reports
- [reports/codebase_audit_report.md](reports/codebase_audit_report.md) - Technical audit
- [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md) - Research paper validation
- [reports/roadmap_edge.md](reports/roadmap_edge.md) - Client-focused roadmap
- [reports/validation_report.json](reports/validation_report.json) - Evaluation results

## Document Status Legend

- ⭐ Source of truth / Primary reference
- ✅ Current and maintained
- 📝 Archived (consolidated into other documents)
- ⚠️ Redundant / Consider consolidating
- 📝 Draft / Work in progress

## Redundancy Notes

### Architecture Documentation
- `docs/ucp_design_plan.md` overlaps ~60% with `ucp_source_of_truth_whitepaper.md`
- Recommendation: Keep whitepaper as source of truth, deprecate design plan
- **Status:** Archived to `docs/archive/ucp_design_plan.md` (2026-01-10)

### Planning Documentation
- `DEV_PLAN_TO_COMPLETION.md`, `START_HERE.md`, `ROADMAP_VISUAL.md`, and `PRIORITIZATION_MATRIX.md` have ~40% overlap
- Recommendation: Consolidated into single document with sections
- **Status:** Archived to `docs/archive/` (2026-01-10)
  - `docs/archive/DEV_PLAN_TO_COMPLETION.md`
  - `docs/archive/START_HERE.md`
  - `docs/archive/ROADMAP_VISUAL.md`
  - `docs/archive/PRIORITIZATION_MATRIX.md`
  - **New location:** `docs/roadmap.md` (consolidated roadmap)

### Agent Documentation
- `.agent/AGENT_A_BACKEND_PLAN.md` and `.agent/BACKEND_EXECUTIVE_SUMMARY.md` overlap ~50%
- Recommendation: Keep executive summary, consolidate detailed plans
- **Status:** Archived to `.agent/archive/AGENT_A_BACKEND_PLAN.md` (2026-01-10)
- **Primary reference:** `.agent/BACKEND_EXECUTIVE_SUMMARY.md`

## Finding What You Need

### "I want to understand what UCP is"
1. Read [README.md](README.md) sections 1-3 (includes dual-track structure)
2. Read [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) sections 1-2
3. Read [shared/README.md](shared/README.md) for shared components overview
4. Read [local/README.md](local/README.md) for local MVP overview
5. Read [cloud/README.md](cloud/README.md) for cloud version overview (planned)

### "I want to start developing"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for development guidelines
2. Read [CLAUDE.md](CLAUDE.md) for architecture overview
3. Read [docs/roadmap.md](docs/roadmap.md) for immediate action items
4. Follow [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) for reorganization details

### "I want to understand research foundation"
1. Read [docs/index.md](docs/index.md) for paper catalog
2. Read synthesis documents in [docs/](docs/) for distilled lessons
3. Review OCR'd papers in [docs/pdfs/](docs/pdfs/)

### "I need to debug an issue"
1. Check [docs/debugging_playbook.md](docs/debugging_playbook.md)
2. Review [CLAUDE.md](CLAUDE.md) known issues section
3. Check trace IDs in debug dashboard

### "I want to contribute"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for contribution guidelines
2. Read [docs/roadmap.md](docs/roadmap.md) for current priorities
3. Review [docs/roadmap.md](docs/roadmap.md) for roadmap phases
4. Check [docs/roadmap.md](docs/roadmap.md) for prioritization framework

### "I want to use the Local MVP"
1. Read [local/README.md](local/README.md) for overview
2. Follow [local/docs/getting_started.md](local/docs/getting_started.md) for installation
3. Read [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) for usage guide
4. Check [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) for deployment

### "I want to understand the Cloud version"
1. Read [cloud/README.md](cloud/README.md) for overview
2. Check [cloud/docs/roadmap.md](cloud/docs/roadmap.md) for implementation timeline
3. Review [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) for architecture

## Project Status

**Overall Completion:** ~65% (Alpha Stage)

**Repository Structure:** ✅ Reorganized (2026-01-10) - New dual-track structure implemented

### What's Working (Local MVP):
- Core MCP protocol implementation (stdio transport)
- Semantic router with hybrid search (keyword + embeddings)
- Vector database (ChromaDB + sentence-transformers)
- Session persistence (SQLite)
- SOTA routing pipeline with bandit learning
- Comprehensive test suite
- Evaluation harness framework
- CLI interface (serve, index, search, status)
- Streamlit debug dashboard

### What's Incomplete (Local MVP):
- SSE/HTTP transports for downstream servers
- Client applications not wired to UCP server
- Confidence thresholds and fallback logic
- Tool affordance generation
- Observability contracts
- Error standardization
- Request tracing infrastructure
- PyPI/Docker distribution

### Cloud Version Status:
- **Status:** Planned, not yet implemented
- **Timeline:** See [cloud/docs/roadmap.md](cloud/docs/roadmap.md)
- **Architecture:** See [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md)

**Estimated Time to Local MVP v1.0:** 8-12 weeks

---

*Last updated: 2026-01-10*

This map helps you navigate the extensive documentation in the Universal Context Protocol repository.

## Quick Start Guides

### For New Users
- [README.md](README.md) - Project overview and quick start (includes dual-track structure)
- [shared/README.md](shared/README.md) - Shared components documentation
- [local/README.md](local/README.md) - Local MVP documentation
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup

### For Developers
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development guidelines for both versions
- [CLAUDE.md](CLAUDE.md) - AI agent developer guide
- [docs/roadmap.md](docs/roadmap.md) - Consolidated roadmap with executive summary, phases, critical path, and prioritization framework

### For Researchers
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) - Original vision and design philosophy

## Documentation Hierarchy

### Architecture & Design
- [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) ⭐ Source of truth for architecture
- [docs/sota_tool_selection_prototype.md](docs/sota_tool_selection_prototype.md) - SOTA routing pipeline

### Planning & Roadmap
- [docs/roadmap.md](docs/roadmap.md) ⭐ Consolidated roadmap with executive summary, phases, critical path, and prioritization framework
- [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) ⭐ Repository reorganization plan (COMPLETED)

### Research & Best Practices
- [docs/index.md](docs/index.md) - Research paper catalog
- [docs/synthesis_agent_design.md](docs/synthesis_agent_design.md) - Lessons from LangGraph, Gorilla, MCP
- [docs/synthesis_context_management.md](docs/synthesis_context_management.md) - Context management patterns
- [docs/synthesis_feedback_eval.md](docs/synthesis_feedback_eval.md) - Evaluation strategies
- [docs/synthesis_tool_selection.md](docs/synthesis_tool_selection.md) - Tool selection best practices

### User Guides
- [README.md](README.md) - Main project documentation
- [docs/getting_started.md](docs/getting_started.md) - Installation and setup
- [docs/debugging_playbook.md](docs/debugging_playbook.md) - Troubleshooting guide
- [docs/evaluation_harness.md](docs/evaluation_harness.md) - Testing framework

### Local MVP Documentation
- [local/README.md](local/README.md) - Local MVP overview
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP installation and setup
- [local/docs/mvp_architecture.md](local/docs/mvp_architecture.md) - Architecture overview
- [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) - User guide
- [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) - Deployment guide

### Cloud Version Documentation
- [cloud/README.md](cloud/README.md) - Cloud version overview
- [cloud/docs/roadmap.md](cloud/docs/roadmap.md) - Cloud implementation roadmap
- [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) - Architecture overview
- [cloud/docs/cloud_deployment.md](cloud/docs/cloud_deployment.md) - Deployment guide
- [cloud/docs/cloud_api_reference.md](cloud/docs/cloud_api_reference.md) - API reference

### Shared Components Documentation
- [shared/README.md](shared/README.md) - Shared components overview
- [shared/docs/api_reference.md](shared/docs/api_reference.md) - Shared API documentation

### Client Documentation
- [clients/README.md](clients/README.md) - Client applications overview
- [local/clients/](local/clients/) - Local MVP clients (CLI, desktop)
- [cloud/clients/](cloud/clients/) - Cloud clients (VS Code, web)

### Reports
- [reports/codebase_audit_report.md](reports/codebase_audit_report.md) - Technical audit
- [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md) - Research paper validation
- [reports/roadmap_edge.md](reports/roadmap_edge.md) - Client-focused roadmap
- [reports/validation_report.json](reports/validation_report.json) - Evaluation results

## Document Status Legend

- ⭐ Source of truth / Primary reference
- ✅ Current and maintained
- 📝 Archived (consolidated into other documents)
- ⚠️ Redundant / Consider consolidating
- 📝 Draft / Work in progress

## Redundancy Notes

### Architecture Documentation
- `docs/ucp_design_plan.md` overlaps ~60% with `ucp_source_of_truth_whitepaper.md`
- Recommendation: Keep whitepaper as source of truth, deprecate design plan
- **Status:** Archived to `docs/archive/ucp_design_plan.md` (2026-01-10)

### Planning Documentation
- `DEV_PLAN_TO_COMPLETION.md`, `START_HERE.md`, `ROADMAP_VISUAL.md`, and `PRIORITIZATION_MATRIX.md` have ~40% overlap
- Recommendation: Consolidated into single document with sections
- **Status:** Archived to `docs/archive/` (2026-01-10)
  - `docs/archive/DEV_PLAN_TO_COMPLETION.md`
  - `docs/archive/START_HERE.md`
  - `docs/archive/ROADMAP_VISUAL.md`
  - `docs/archive/PRIORITIZATION_MATRIX.md`
  - **New location:** `docs/roadmap.md` (consolidated roadmap)

### Agent Documentation
- `.agent/AGENT_A_BACKEND_PLAN.md` and `.agent/BACKEND_EXECUTIVE_SUMMARY.md` overlap ~50%
- Recommendation: Keep executive summary, consolidate detailed plans
- **Status:** Archived to `.agent/archive/AGENT_A_BACKEND_PLAN.md` (2026-01-10)
- **Primary reference:** `.agent/BACKEND_EXECUTIVE_SUMMARY.md`

## Finding What You Need

### "I want to understand what UCP is"
1. Read [README.md](README.md) sections 1-3 (includes dual-track structure)
2. Read [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) sections 1-2
3. Read [shared/README.md](shared/README.md) for shared components overview
4. Read [local/README.md](local/README.md) for local MVP overview
5. Read [cloud/README.md](cloud/README.md) for cloud version overview (planned)

### "I want to start developing"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for development guidelines
2. Read [CLAUDE.md](CLAUDE.md) for architecture overview
3. Read [docs/roadmap.md](docs/roadmap.md) for immediate action items
4. Follow [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) for reorganization details

### "I want to understand research foundation"
1. Read [docs/index.md](docs/index.md) for paper catalog
2. Read synthesis documents in [docs/](docs/) for distilled lessons
3. Review OCR'd papers in [docs/pdfs/](docs/pdfs/)

### "I need to debug an issue"
1. Check [docs/debugging_playbook.md](docs/debugging_playbook.md)
2. Review [CLAUDE.md](CLAUDE.md) known issues section
3. Check trace IDs in debug dashboard

### "I want to contribute"
1. Read [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for contribution guidelines
2. Read [docs/roadmap.md](docs/roadmap.md) for current priorities
3. Review [docs/roadmap.md](docs/roadmap.md) for roadmap phases
4. Check [docs/roadmap.md](docs/roadmap.md) for prioritization framework

### "I want to use the Local MVP"
1. Read [local/README.md](local/README.md) for overview
2. Follow [local/docs/getting_started.md](local/docs/getting_started.md) for installation
3. Read [local/docs/mvp_user_guide.md](local/docs/mvp_user_guide.md) for usage guide
4. Check [local/docs/mvp_deployment.md](local/docs/mvp_deployment.md) for deployment

### "I want to understand the Cloud version"
1. Read [cloud/README.md](cloud/README.md) for overview
2. Check [cloud/docs/roadmap.md](cloud/docs/roadmap.md) for implementation timeline
3. Review [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md) for architecture

## Project Status

**Overall Completion:** ~65% (Alpha Stage)

**Repository Structure:** ✅ Reorganized (2026-01-10) - New dual-track structure implemented

### What's Working (Local MVP):
- Core MCP protocol implementation (stdio transport)
- Semantic router with hybrid search (keyword + embeddings)
- Vector database (ChromaDB + sentence-transformers)
- Session persistence (SQLite)
- SOTA routing pipeline with bandit learning
- Comprehensive test suite
- Evaluation harness framework
- CLI interface (serve, index, search, status)
- Streamlit debug dashboard

### What's Incomplete (Local MVP):
- SSE/HTTP transports for downstream servers
- Client applications not wired to UCP server
- Confidence thresholds and fallback logic
- Tool affordance generation
- Observability contracts
- Error standardization
- Request tracing infrastructure
- PyPI/Docker distribution

### Cloud Version Status:
- **Status:** Planned, not yet implemented
- **Timeline:** See [cloud/docs/roadmap.md](cloud/docs/roadmap.md)
- **Architecture:** See [cloud/docs/cloud_architecture.md](cloud/docs/cloud_architecture.md)

**Estimated Time to Local MVP v1.0:** 8-12 weeks

---

*Last updated: 2026-01-10*

- [docs/debugging_playbook.md](docs/debugging_playbook.md) - Troubleshooting guide
- [docs/evaluation_harness.md](docs/evaluation_harness.md) - Testing framework

### Client Documentation
- [clients/README.md](clients/README.md) - Client applications overview
- [local/clients/](local/clients/) - Local MVP clients (CLI, desktop)
- [cloud/clients/](cloud/clients/) - Cloud clients (VS Code, web)

### Reports
- [reports/codebase_audit_report.md](reports/codebase_audit_report.md) - Technical audit
- [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md) - Research paper validation
- [reports/roadmap_edge.md](reports/roadmap_edge.md) - Client-focused roadmap
- [reports/validation_report.json](reports/validation_report.json) - Evaluation results

## Document Status Legend

- ⭐ Source of truth / Primary reference
- ✅ Current and maintained
- 📝 Archived (consolidated into other documents)
- ⚠️ Redundant / Consider consolidating
- 📝 Draft / Work in progress

## Redundancy Notes

### Architecture Documentation
- `docs/ucp_design_plan.md` overlaps ~60% with `ucp_source_of_truth_whitepaper.md`
- Recommendation: Keep whitepaper as source of truth, deprecate design plan
- **Status:** Archived to `docs/archive/ucp_design_plan.md` (2026-01-10)

### Planning Documentation
- `DEV_PLAN_TO_COMPLETION.md`, `START_HERE.md`, `ROADMAP_VISUAL.md`, and `PRIORITIZATION_MATRIX.md` have ~40% overlap
- Recommendation: Consolidated into single document with sections
- **Status:** Archived to `docs/archive/` (2026-01-10)
  - `docs/archive/DEV_PLAN_TO_COMPLETION.md`
  - `docs/archive/START_HERE.md`
  - `docs/archive/ROADMAP_VISUAL.md`
  - `docs/archive/PRIORITIZATION_MATRIX.md`
  - **New location:** `docs/roadmap.md` (consolidated roadmap)

### Agent Documentation
- `.agent/AGENT_A_BACKEND_PLAN.md` and `.agent/BACKEND_EXECUTIVE_SUMMARY.md` overlap ~50%
- Recommendation: Keep executive summary, consolidate detailed plans
- **Status:** Archived to `.agent/archive/AGENT_A_BACKEND_PLAN.md` (2026-01-10)
- **Primary reference:** `.agent/BACKEND_EXECUTIVE_SUMMARY.md`

## Finding What You Need

### "I want to understand what UCP is"
1. Read [README.md](README.md) sections 1-3 (includes new dual-track structure)
2. Read [ucp_source_of_truth_whitepaper.md](ucp_source_of_truth_whitepaper.md) sections 1-2
3. Read [shared/README.md](shared/README.md) for shared components overview
4. Read [local/README.md](local/README.md) for local MVP overview
5. Read [cloud/README.md](cloud/README.md) for cloud version overview (planned)

### "I want to start developing"
1. Read [CLAUDE.md](CLAUDE.md) for architecture overview
2. Read [docs/roadmap.md](docs/roadmap.md) for immediate action items
3. Follow [.agent/workflows/start-phase1.md](.agent/workflows/start-phase1.md) for step-by-step guide
4. Read [plans/repository_reorganization_plan.md](plans/repository_reorganization_plan.md) for reorganization details

### "I want to understand research foundation"
1. Read [docs/index.md](docs/index.md) for paper catalog
2. Read synthesis documents in [docs/](docs/) for distilled lessons
3. Review OCR'd papers in [docs/pdfs/](docs/pdfs/)

### "I need to debug an issue"
1. Check [docs/debugging_playbook.md](docs/debugging_playbook.md)
2. Review [CLAUDE.md](CLAUDE.md) known issues section
3. Check trace IDs in debug dashboard

### "I want to contribute"
1. Read [docs/roadmap.md](docs/roadmap.md) for current priorities
2. Review [docs/roadmap.md](docs/roadmap.md) for roadmap phases
3. Check [docs/roadmap.md](docs/roadmap.md) for prioritization framework

## Project Status

**Overall Completion:** ~65% (Alpha Stage)

**What's Working:**
- Core MCP protocol implementation (stdio transport)
- Semantic router with hybrid search (keyword + embeddings)
- Vector database (ChromaDB + sentence-transformers)
- Session persistence (SQLite)
- SOTA routing pipeline with bandit learning
- Comprehensive test suite
- Evaluation harness framework
- **Repository reorganized** (2026-01-10) - New dual-track structure implemented

**What's Incomplete:**
- SSE/HTTP transports for downstream servers
- Client applications not wired to UCP server
- Confidence thresholds and fallback logic
- Tool affordance generation
- Observability contracts
- Error standardization
- Request tracing infrastructure
- PyPI/Docker distribution

**Estimated Time to v1.0:** 8-12 weeks

---

*Last updated: 2026-01-10*

