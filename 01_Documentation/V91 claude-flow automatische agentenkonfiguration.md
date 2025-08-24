# Claude-Flow Alpha 91: Complete feature documentation

## Version clarification and release status

The research reveals that Claude-Flow uses the versioning scheme **v2.0.0-alpha.XX**, where v91 refers to **v2.0.0-alpha.91**, released on August 21, 2025. This is the latest alpha release of Claude-Flow, an enterprise-grade AI orchestration platform for coordinating multiple Claude Code agents. The version progression from alpha.86 to alpha.91 represents incremental improvements within the v2.0.0 alpha series.

## Current CLI syntax for .claude/agents option

The v91 release maintains the `.claude/agents/` directory structure as the primary mechanism for automatic agent composition. The current CLI implementation creates a comprehensive 64-agent system across 16 categories during initialization. The basic syntax follows this pattern:

```bash
# Initialize with full agent structure
npx claude-flow@alpha init --force

# Basic agent usage pattern
claude-flow agent spawn --type <agent-type> --name "<agent-name>"
claude-flow swarm "task description" --agents coder,tester,reviewer

# Direct agent invocation
claude-flow agent use coder "implement user authentication"
```

The `.claude/agents/` directory automatically populates with agent definitions in YAML frontmatter format, enabling Claude Code to detect and utilize available agents without manual configuration. Each agent file includes capabilities, priority levels, tool assignments, and specialized system prompts that define their behavior and expertise areas.

## Dynamic Agent Architecture changes from v86

The Dynamic Agent Architecture underwent significant enhancements between alpha.86 and alpha.91, with the most critical change being the **separation of execution and coordination responsibilities**. In v91, MCP tools are strictly coordination-only, while the Claude Code Task tool handles all agent execution. This architectural shift improves performance by 300% through better resource allocation and clearer responsibility boundaries.

The DAA now features self-organizing agents with fault tolerance, supporting four coordination topologies: hierarchical (tree structure with queen-led coordination), mesh (peer-to-peer with redundancy), ring (sequential pipeline workflows), and star (centralized coordination). The system includes 27+ cognitive models with WASM SIMD acceleration for neural pattern recognition, enabling agents to learn from successful workflows and adapt their strategies over time.

A new SQLite-based memory system (`.swarm/memory.db`) with 12 specialized tables provides persistent context across sessions, allowing agents to maintain knowledge between different development tasks and share insights through a distributed memory architecture.

## New agent types and specializations in v91

Version 91 introduces a comprehensive 64-agent system organized into 16 specialized categories. The core development agents include the Coder (implementation specialist), Planner (strategic orchestration), Researcher (information analysis), Reviewer (quality assurance), and Tester (validation expert). These foundational agents form the backbone of most development workflows.

Swarm coordination agents manage different topology patterns: Hierarchical-Coordinator for queen-led structures, Mesh-Coordinator for peer-to-peer networks, and Adaptive-Coordinator for dynamic topology switching. The consensus systems category adds seven specialized agents including Byzantine-Coordinator for fault tolerance, Raft-Manager for leader election, and CRDT-Synchronizer for conflict-free data management.

GitHub integration receives substantial expansion with 13 specialized agents handling everything from PR-Manager for pull request lifecycles to Multi-Repo-Swarm for cross-repository coordination. Performance optimization agents include Load-Balancer with work-stealing algorithms, Performance-Monitor for real-time metrics, and Topology-Optimizer for dynamic swarm reconfiguration.

## Updated command-line parameters

The v91 release introduces enhanced command-line parameters focusing on batch operations and parallel execution. The critical new pattern requires using the Task tool for agent execution with specific syntax:

```bash
# NEW v91 Pattern (Required)
Task("Researcher", "Analyze market trends", "researcher")
Task("Coder", "Implement features", "coder") 
Task("Tester", "Create test suite", "tester")

# Batch operations (mandatory for performance)
TodoWrite { todos: [5-10+ todos in single call] }

# MCP coordination setup only
mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 8 }
```

Global options now include enhanced configuration management with `--config`, verbosity control with `--verbose` and `--json` output formats, and performance monitoring through `--monitor` flags. The system supports concurrent agent limits up to 10 in Claude Code with configurable memory limits and resource allocation parameters.

## Automatic agent composition features

Version 91's automatic agent composition employs intelligent spawning logic that determines optimal agent counts (3-12) based on task complexity analysis. The system uses capability-based assignment, matching agent specializations to task requirements automatically without manual configuration. All agents must spawn in a single message for the 300% performance improvement, utilizing the new batch operation paradigm.

The composition system supports four strategies: parallel execution for independent tasks, sequential processing for dependent workflows, adaptive coordination that switches between modes dynamically, and hybrid workflows combining multiple strategies. Task decomposition automatically breaks complex projects into manageable subtasks with intelligent dependency management and conflict resolution.

Dynamic scaling adjusts agent counts based on workload demands, with configurable min/max limits and automatic resource allocation. The system includes namespace management for isolating different features or projects, enabling multiple hives to operate independently without interference.

## Performance improvements and hive-mind system

The hive-mind spawning system achieves an 84.8% SWE-Bench solve rate through coordinated multi-agent problem-solving, representing a 2.8-4.4x speed improvement over traditional approaches. Token usage reduces by 32.3% through intelligent optimization and caching, while operational costs decrease by over 30% via modular task distribution.

The queen-led architecture features a central Queen agent orchestrating specialized workers including Architect, Coder, Tester, Analyst, and Researcher agents. This hierarchical command structure enables efficient task delegation with clear responsibility boundaries. Session persistence allows resuming interrupted workflows with full context restoration, maintaining productivity across development sessions.

Real neural network modules (ruv-fann.wasm and ruv_swarm_simd.wasm) provide actual machine learning capabilities rather than simulated intelligence, enabling genuine pattern recognition and adaptive learning from successful workflows.

## Current best practices for v91

Best practices emphasize starting simple with basic swarm initialization before scaling to complex multi-agent workflows. The critical v91 pattern requires executing all agents in a single message using the Task tool, with MCP tools reserved exclusively for coordination setup. Batch operations must include 5-10+ todos in single TodoWrite calls to achieve optimal performance.

Memory coordination serves as the primary mechanism for cross-agent communication, with mandatory saves after each significant step. The system benefits from frequent session clearing to manage token usage effectively. File organization follows strict patterns, never saving to root directories and maintaining proper project structure through the `.claude/` directory hierarchy.

The SPARC methodology provides 17 specialized modes for different development approaches, from architectural design to test-driven development, each optimized for specific workflow patterns and project requirements.

## Breaking changes from alpha.86

The most significant breaking change involves MCP tool usage: tools like `mcp__claude-flow__agent_spawn` previously used for execution now serve coordination purposes only. All agent execution must use the Task tool pattern, fundamentally altering how developers interact with the system. This change requires updating all existing workflows and scripts.

File organization becomes stricter, prohibiting root directory saves and enforcing structured project layouts. Batch operation requirements mandate combining multiple operations into single calls rather than sequential individual operations. The command documentation system now creates all 91 command files during initialization instead of partial sets, ensuring complete feature availability from setup.

Agent spawning patterns changed from sequential to parallel, requiring all agents to spawn simultaneously in a single message. This change improves performance but requires restructuring existing multi-step agent initialization workflows.

## Configuration options and agent profiles

Version 91 introduces comprehensive configuration through `claude-flow.config.json` for system-wide settings and `.claude/settings.json` for project-specific Claude Code integration. The orchestrator configuration supports topology selection, concurrent agent limits, and strategy definitions. Memory backend options include SQLite with configurable cache sizes and persistence settings.

Agent profiles use YAML frontmatter with markdown documentation, defining capabilities, priorities, tool assignments, and specialized prompts. The hierarchical configuration system prioritizes project-level agents (`.claude/agents/`) over user-level definitions (`~/.claude/agents/`), enabling project-specific customization while maintaining global defaults.

Hook configurations provide automated workflows with pre/post execution triggers, automatic agent assignment based on file types, and performance monitoring integration. The system supports 87 MCP tools for comprehensive orchestration capabilities, with explicit permission management for security and resource control.

## Examples and use cases for v91

Practical implementation demonstrates remarkable capabilities, exemplified by Adrian Cockcroft's house consciousness system delivering 150,000+ lines of production-ready code in under two days. The system generated comprehensive database layers, natural language device discovery, digital twin intelligence for IoT devices, complete APIs with 25+ endpoints, and full deployment infrastructure with enterprise-grade security.

Common use cases include rapid prototyping of full-stack applications in hours rather than weeks, legacy code modernization analyzing hundreds of files simultaneously, and enterprise development coordinating up to 10 agents for complex projects. The test suite generation capability creates comprehensive testing strategies automatically, reducing QA time by orders of magnitude.

Example workflows showcase the power of parallel coordination:
```bash
# Enterprise microservices development
./claude-flow swarm "Build microservices architecture" \
  --strategy development \
  --max-agents 8 \
  --topology hierarchical \
  --namespace services

# Parallel feature development
batchtool run --parallel \
  "./claude-flow sparc architect 'design payment system'" \
  "./claude-flow sparc code 'implement stripe integration'" \
  "./claude-flow sparc tdd 'create payment tests'"
```

These patterns demonstrate how v91's enhanced coordination capabilities enable development teams to achieve 24x task completion acceleration through intelligent agent orchestration and parallel processing.