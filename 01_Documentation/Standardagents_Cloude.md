# Comprehensive Agent List - Claude Flow & Hive Mind System

## Executive Summary

This document contains a comprehensive list of all available agents in the Claude Flow and Hive Mind orchestration system. The data has been compiled from multiple sources including configuration files and system documentation.

### Key Statistics
- **Total Agents**: 57
- **Categories**: 10 distinct categories
- **Detailed Configurations**: 8 agents with full specifications
- **Additional Agents**: 49 agents with basic specifications

### Category Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| Core Development | 11 | 19.3% |
| GitHub & Repository | 9 | 15.8% |
| Specialized Development | 8 | 14.0% |
| Consensus & Distributed | 7 | 12.3% |
| SPARC Methodology | 6 | 10.5% |
| Swarm Coordination | 5 | 8.8% |
| Performance & Optimization | 5 | 8.8% |
| Testing & Validation | 2 | 3.5% |
| Migration & Planning | 2 | 3.5% |
| Core Systems | 2 | 3.5% |

## Complete Agent Database

| Agent ID | Agent Name | Category | Role | Description | Model | Temperature | Max Tokens | Capabilities | Tools |
|----------|------------|----------|------|-------------|-------|-------------|------------|--------------|-------|
| queen-orchestrator | Hive Queen | Core Systems | orchestrator | Zentrale Orchestrierung und Koordination aller Agenten | claude-3-opus-20240229 | 0.1 | 8192 | task_planning, agent_coordination, quality_control, progress_monitoring, decision_making | mcp_filesystem, task_manager, agent_monitor |
| architect-1 | System Architect | Core Systems | architect | Systemarchitektur und Design-Entscheidungen | claude-3-sonnet-20240229 | 0.2 | 8192 | system_design, architecture_patterns, technology_selection, scalability_planning | mcp_filesystem, diagramming |
| coder-backend | Backend Developer | Core Development | coder | Backend-Entwicklung und API-Implementation | claude-3-sonnet-20240229 | 0.1 | 8192 | api_development, database_design, backend_logic, performance_optimization | mcp_filesystem, code_executor, database |
| coder-frontend | Frontend Developer | Core Development | coder | Frontend-Entwicklung und UI/UX Implementation | claude-3-sonnet-20240229 | 0.1 | 8192 | ui_development, responsive_design, state_management, component_architecture | mcp_filesystem, code_executor |
| reviewer-1 | Code Reviewer | Core Development | reviewer | Code-Review und Qualitätssicherung | claude-3-sonnet-20240229 | 0.0 | 4096 | code_review, security_audit, performance_analysis, best_practices_validation | mcp_filesystem, static_analyzer |
| tester-1 | Test Engineer | Core Development | tester | Test-Entwicklung und Qualitätssicherung | claude-3-sonnet-20240229 | 0.0 | 4096 | unit_testing, integration_testing, test_automation, coverage_analysis | mcp_filesystem, code_executor, test_runner |
| documenter-1 | Technical Writer | Core Development | documenter | Technische Dokumentation und Anleitungen | claude-3-sonnet-20240229 | 0.2 | 8192 | api_documentation, user_guides, technical_specs, readme_creation | mcp_filesystem, markdown_editor |
| devops-1 | DevOps Engineer | Core Development | devops | Deployment und Infrastructure | claude-3-sonnet-20240229 | 0.1 | 4096 | ci_cd_setup, containerization, infrastructure_as_code, monitoring_setup | mcp_filesystem, terminal, docker |
| coder | Coder | Core Development | coder | General purpose coding and development tasks | Not specified | Default | Default | software_development | Not specified |
| reviewer | Reviewer | Core Development | reviewer | Code review and quality assurance | Not specified | Default | Default | code_review | Not specified |
| tester | Tester | Core Development | tester | Testing and validation tasks | Not specified | Default | Default | testing | Not specified |
| planner | Planner | Core Development | planner | Project planning and task organization | Not specified | Default | Default | planning | Not specified |
| researcher | Researcher | Core Development | researcher | Research and analysis tasks | Not specified | Default | Default | research | Not specified |
| hierarchical-coordinator | Hierarchical Coordinator | Swarm Coordination | coordinator | Manages hierarchical swarm topology coordination | Not specified | Default | Default | hierarchical_coordination | Not specified |
| mesh-coordinator | Mesh Coordinator | Swarm Coordination | coordinator | Manages mesh topology coordination | Not specified | Default | Default | mesh_coordination | Not specified |
| adaptive-coordinator | Adaptive Coordinator | Swarm Coordination | coordinator | Adaptive coordination strategies | Not specified | Default | Default | adaptive_coordination | Not specified |
| collective-intelligence-coordinator | Collective Intelligence Coordinator | Swarm Coordination | coordinator | Collective intelligence coordination | Not specified | Default | Default | collective_intelligence | Not specified |
| swarm-memory-manager | Swarm Memory Manager | Swarm Coordination | manager | Manages shared memory across swarm agents | Not specified | Default | Default | memory_management | Not specified |
| byzantine-coordinator | Byzantine Coordinator | Consensus & Distributed | coordinator | Byzantine fault tolerance coordination | Not specified | Default | Default | byzantine_tolerance | Not specified |
| raft-manager | Raft Manager | Consensus & Distributed | manager | Raft consensus algorithm management | Not specified | Default | Default | raft_consensus | Not specified |
| gossip-coordinator | Gossip Coordinator | Consensus & Distributed | coordinator | Gossip protocol coordination | Not specified | Default | Default | gossip_protocol | Not specified |
| consensus-builder | Consensus Builder | Consensus & Distributed | builder | Builds consensus across distributed systems | Not specified | Default | Default | consensus_building | Not specified |
| crdt-synchronizer | CRDT Synchronizer | Consensus & Distributed | synchronizer | Conflict-free replicated data types synchronization | Not specified | Default | Default | crdt_sync | Not specified |
| quorum-manager | Quorum Manager | Consensus & Distributed | manager | Manages quorum-based decisions | Not specified | Default | Default | quorum_management | Not specified |
| security-manager | Security Manager | Consensus & Distributed | manager | Security and access control management | Not specified | Default | Default | security_management | Not specified |
| perf-analyzer | Performance Analyzer | Performance & Optimization | analyzer | Analyzes system performance and bottlenecks | Not specified | Default | Default | performance_analysis | Not specified |
| performance-benchmarker | Performance Benchmarker | Performance & Optimization | benchmarker | Runs performance benchmarks and tests | Not specified | Default | Default | benchmarking | Not specified |
| task-orchestrator | Task Orchestrator | Performance & Optimization | orchestrator | Orchestrates task execution and optimization | Not specified | Default | Default | task_orchestration | Not specified |
| memory-coordinator | Memory Coordinator | Performance & Optimization | coordinator | Coordinates memory usage and optimization | Not specified | Default | Default | memory_coordination | Not specified |
| smart-agent | Smart Agent | Performance & Optimization | agent | Intelligent agent with adaptive capabilities | Not specified | Default | Default | adaptive_intelligence | Not specified |
| github-modes | GitHub Modes | GitHub & Repository | manager | Manages different GitHub operation modes | Not specified | Default | Default | github_integration | Not specified |
| pr-manager | PR Manager | GitHub & Repository | manager | Manages pull requests and code reviews | Not specified | Default | Default | pr_management | Not specified |
| code-review-swarm | Code Review Swarm | GitHub & Repository | reviewer | Swarm-based code review coordination | Not specified | Default | Default | swarm_code_review | Not specified |
| issue-tracker | Issue Tracker | GitHub & Repository | tracker | Tracks and manages GitHub issues | Not specified | Default | Default | issue_management | Not specified |
| release-manager | Release Manager | GitHub & Repository | manager | Manages software releases and versioning | Not specified | Default | Default | release_management | Not specified |
| workflow-automation | Workflow Automation | GitHub & Repository | automation | Automates GitHub workflows and processes | Not specified | Default | Default | workflow_automation | Not specified |
| project-board-sync | Project Board Sync | GitHub & Repository | synchronizer | Synchronizes project boards and tasks | Not specified | Default | Default | project_sync | Not specified |
| repo-architect | Repository Architect | GitHub & Repository | architect | Designs repository structure and organization | Not specified | Default | Default | repo_architecture | Not specified |
| multi-repo-swarm | Multi-Repository Swarm | GitHub & Repository | coordinator | Coordinates operations across multiple repositories | Not specified | Default | Default | multi_repo_coordination | Not specified |
| sparc-coord | SPARC Coordinator | SPARC Methodology | coordinator | Coordinates SPARC methodology implementation | Not specified | Default | Default | sparc_coordination | Not specified |
| sparc-coder | SPARC Coder | SPARC Methodology | coder | Implements code following SPARC methodology | Not specified | Default | Default | sparc_development | Not specified |
| specification | Specification | SPARC Methodology | analyst | Handles specification phase of SPARC | Not specified | Default | Default | specification_analysis | Not specified |
| pseudocode | Pseudocode | SPARC Methodology | designer | Handles pseudocode phase of SPARC | Not specified | Default | Default | pseudocode_design | Not specified |
| architecture | Architecture | SPARC Methodology | architect | Handles architecture phase of SPARC | Not specified | Default | Default | architecture_design | Not specified |
| refinement | Refinement | SPARC Methodology | refiner | Handles refinement phase of SPARC | Not specified | Default | Default | code_refinement | Not specified |
| backend-dev | Backend Developer | Specialized Development | developer | Specialized backend development | Not specified | Default | Default | backend_development | Not specified |
| mobile-dev | Mobile Developer | Specialized Development | developer | Mobile application development | Not specified | Default | Default | mobile_development | Not specified |
| ml-developer | ML Developer | Specialized Development | developer | Machine learning and AI development | Not specified | Default | Default | ml_development | Not specified |
| cicd-engineer | CI/CD Engineer | Specialized Development | engineer | Continuous integration and deployment | Not specified | Default | Default | cicd_management | Not specified |
| api-docs | API Documentation | Specialized Development | documenter | API documentation specialist | Not specified | Default | Default | api_documentation | Not specified |
| system-architect | System Architect | Specialized Development | architect | System architecture and design | Not specified | Default | Default | system_architecture | Not specified |
| code-analyzer | Code Analyzer | Specialized Development | analyzer | Code analysis and quality assessment | Not specified | Default | Default | code_analysis | Not specified |
| base-template-generator | Base Template Generator | Specialized Development | generator | Generates base templates and scaffolding | Not specified | Default | Default | template_generation | Not specified |
| tdd-london-swarm | TDD London Swarm | Testing & Validation | tester | Test-driven development London school approach | Not specified | Default | Default | tdd_london | Not specified |
| production-validator | Production Validator | Testing & Validation | validator | Validates production readiness | Not specified | Default | Default | production_validation | Not specified |
| migration-planner | Migration Planner | Migration & Planning | planner | Plans system migrations and upgrades | Not specified | Default | Default | migration_planning | Not specified |
| swarm-init | Swarm Initializer | Migration & Planning | initializer | Initializes swarm configurations | Not specified | Default | Default | swarm_initialization | Not specified |

## Detailed Agent Configurations

### Agents with Full Specifications

The following 8 agents have complete configuration details including specific Claude models, temperature settings, and token limits:

1. **Hive Queen (queen-orchestrator)**
   - Model: claude-3-opus-20240229
   - Temperature: 0.1
   - Max Tokens: 8192
   - Primary Role: Central orchestration and coordination

2. **System Architect (architect-1)**
   - Model: claude-3-sonnet-20240229
   - Temperature: 0.2
   - Max Tokens: 8192
   - Primary Role: System design and architecture decisions

3. **Backend Developer (coder-backend)**
   - Model: claude-3-sonnet-20240229
   - Temperature: 0.1
   - Max Tokens: 8192
   - Primary Role: Backend and API implementation

4. **Frontend Developer (coder-frontend)**
   - Model: claude-3-sonnet-20240229
   - Temperature: 0.1
   - Max Tokens: 8192
   - Primary Role: UI/UX implementation

5. **Code Reviewer (reviewer-1)**
   - Model: claude-3-sonnet-20240229
   - Temperature: 0.0
   - Max Tokens: 4096
   - Primary Role: Code quality and security review

6. **Test Engineer (tester-1)**
   - Model: claude-3-sonnet-20240229
   - Temperature: 0.0
   - Max Tokens: 4096
   - Primary Role: Test development and quality assurance

7. **Technical Writer (documenter-1)**
   - Model: claude-3-sonnet-20240229
   - Temperature: 0.2
   - Max Tokens: 8192
   - Primary Role: Technical documentation

8. **DevOps Engineer (devops-1)**
   - Model: claude-3-sonnet-20240229
   - Temperature: 0.1
   - Max Tokens: 4096
   - Primary Role: Deployment and infrastructure

## Usage Guide

### Accessing Agents

Agents can be spawned and coordinated through:

1. **Claude Code Task Tool**: Primary method for spawning agents
   ```javascript
   Task("description", "prompt", "agent-type")
   ```

2. **MCP Tools**: For coordination and orchestration
   - `mcp__claude-flow__agent_spawn`
   - `mcp__claude-flow__task_orchestrate`
   - `mcp__claude-flow__swarm_init`

### Agent Categories Explained

- **Core Systems**: Central control and system-level orchestration
- **Core Development**: General development and coding tasks
- **Swarm Coordination**: Multi-agent coordination patterns
- **Consensus & Distributed**: Distributed system protocols
- **Performance & Optimization**: System optimization and analysis
- **GitHub & Repository**: Source control and collaboration
- **SPARC Methodology**: Structured development methodology
- **Specialized Development**: Domain-specific development
- **Testing & Validation**: Quality assurance and testing
- **Migration & Planning**: System migration and planning

## Notes

- Agents marked with "Not specified" for model/temperature/tokens use system defaults
- All agents support parallel execution when spawned through the Task tool
- Agents can communicate through shared memory and coordination hooks
- The Hive Queen (queen-orchestrator) serves as the primary orchestrator for complex multi-agent tasks

---

*Generated by Hive Mind Collective Intelligence System*
*Date: 2025-08-23*
*Total Processing Agents: 4 (Researcher, Coder, Tester, Validator)*