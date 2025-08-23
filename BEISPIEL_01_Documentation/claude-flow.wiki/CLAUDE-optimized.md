# Claude Code Configuration for Claude Flow

## 🚨 CRITICAL: CONCURRENT EXECUTION RULES

**ABSOLUTE RULE**: ALL operations MUST be concurrent/parallel in ONE message:

### 🔴 Mandatory Patterns:
1. **TodoWrite**: ALWAYS batch 5-10+ todos in ONE call
2. **Task tool**: ALWAYS spawn ALL agents in ONE message
3. **File operations**: ALWAYS batch ALL reads/writes/edits
4. **Bash commands**: ALWAYS batch ALL terminal operations
5. **Memory operations**: ALWAYS batch ALL store/retrieve

### ⚡ Golden Rule: "1 MESSAGE = ALL RELATED OPERATIONS"

✅ **CORRECT**: Everything in ONE message
```javascript
[Single Message]:
  - TodoWrite { todos: [10+ todos with all statuses/priorities] }
  - Task("Agent 1"), Task("Agent 2"), Task("Agent 3")
  - Read("file1.js"), Read("file2.js"), Read("file3.js")
  - Write("output1.js"), Write("output2.js")
  - Bash("npm install"), Bash("npm test"), Bash("npm build")
```

❌ **WRONG**: Multiple messages (6x slower!)

## 🎯 Role Separation: Claude Code vs MCP Tools

| **Claude Code (Executor)** | **MCP Tools (Coordinator)** |
|----------------------------|------------------------------|
| ALL file operations | Coordination & planning |
| Code generation | Memory management |
| Bash commands | Performance tracking |
| TodoWrite & tasks | Swarm orchestration |
| Git operations | GitHub integration |
| Implementation work | Intelligence insights |

**Key Principle**: MCP coordinates, Claude Code executes!

## 📦 Core Commands

| Command | Purpose |
|---------|---------|
| `npx claude-flow sparc modes` | List development modes |
| `npx claude-flow sparc run <mode> "<task>"` | Execute mode |
| `npx claude-flow automation mle-star --dataset data.csv --target price --claude` | ML workflow |
| `npm run build/test/lint/typecheck` | Standard builds |

## 🤖 Agent Reference (64 Total)

### Core Categories:
- **Development** (5): coder, reviewer, tester, planner, researcher
- **Coordination** (8): hierarchical/mesh/adaptive coordinators, memory managers
- **GitHub** (13): PR management, code review, release automation
- **Performance** (6): monitoring, load balancing, optimization
- **Consensus** (7): Byzantine, Raft, Gossip protocols
- **Specialized** (25): ML, mobile, backend, security, etc.

## 🚀 Quick Setup (MCP Integration)

### 1. Add MCP Server
```bash
claude mcp add claude-flow npx claude-flow@alpha mcp start
```

### 2. Key MCP Tools
| Tool | Purpose |
|------|---------|
| `mcp__claude-flow__swarm_init` | Setup coordination |
| `mcp__claude-flow__agent_spawn` | Create agents |
| `mcp__claude-flow__task_orchestrate` | Coordinate tasks |
| `mcp__claude-flow__memory_usage` | Persistent memory |
| `mcp__claude-flow__github_*` | Repository management |

## 🧠 Swarm Orchestration Pattern

### Agent Count Rules:
1. **Check CLI args first**: `--agents 5` = use 5 agents
2. **Auto-decide**: Simple (3-4), Medium (5-7), Complex (8-12)

### Mandatory Agent Protocol (Every Agent MUST):

**Before Starting:**
```bash
npx claude-flow@alpha hooks pre-task --description "[task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
```

**During Work:**
```bash
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "agent/[step]"
npx claude-flow@alpha hooks notify --message "[decision]"
```

**After Completion:**
```bash
npx claude-flow@alpha hooks post-task --task-id "[task]" --analyze-performance true
npx claude-flow@alpha hooks session-end --export-metrics true
```

## ⚡ Parallel Execution Examples

### ✅ Correct Pattern:
```javascript
// SINGLE MESSAGE with ALL operations
[BatchTool - Message 1]:
  // MCP coordination setup
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }
  
  // Claude Code execution
  Task("Researcher: Research API patterns. MUST use hooks.")
  Task("Coder: Implement endpoints. MUST use hooks.")
  Task("Tester: Write tests. MUST use hooks.")
  
  TodoWrite { todos: [
    {id: "research", content: "Research patterns", status: "in_progress", priority: "high"},
    {id: "implement", content: "Build endpoints", status: "pending", priority: "high"},
    {id: "test", content: "Write tests", status: "pending", priority: "medium"},
    {id: "docs", content: "Documentation", status: "pending", priority: "low"}
  ]}
  
  // File operations
  Write("api/package.json", content)
  Write("api/server.js", content)
  Bash("mkdir -p api/{routes,tests}")
  Bash("npm install")
```

### ❌ Wrong Pattern (NEVER DO):
```javascript
// Multiple messages - 6x slower!
Message 1: mcp__claude-flow__swarm_init
Message 2: Task("researcher")
Message 3: TodoWrite (single todo)
Message 4: Write (single file)
```

## 📋 TodoWrite Requirements

**CRITICAL**: Always include 5-10+ todos in ONE call:
```javascript
TodoWrite { todos: [
  { id: "1", content: "Task 1", status: "completed", priority: "high" },
  { id: "2", content: "Task 2", status: "in_progress", priority: "high" },
  { id: "3", content: "Task 3", status: "pending", priority: "high" },
  { id: "4", content: "Task 4", status: "pending", priority: "medium" },
  { id: "5", content: "Task 5", status: "pending", priority: "medium" },
  { id: "6", content: "Task 6", status: "pending", priority: "low" },
  // ... continue to 10+ todos
]}
```

## 🔗 NEW: Automation & Stream Chaining

### Automation Commands:
```bash
# Auto-spawn optimal agents
claude-flow automation auto-agent --task-complexity enterprise

# ML engineering workflow
claude-flow automation mle-star --dataset data.csv --target price --claude

# Stream chaining (agent-to-agent piping)
claude-flow automation mle-star --dataset data.csv --target price --claude --output-format stream-json
```

### Stream Chaining Benefits:
- **Real-time processing**: 40-60% faster than file-based
- **Context preservation**: Full conversation history flows
- **Memory efficient**: No intermediate storage

## 📊 Progress Tracking Format

```
📊 Progress Overview
├── Total: X | ✅ Complete: X | 🔄 Active: X | ⭕ Todo: X
└── Priority: 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW
```

## 🎯 Best Practices Summary

### DO:
- ✅ Batch ALL operations in single messages
- ✅ Use MCP for coordination, Claude Code for execution
- ✅ Include 5-10+ todos in every TodoWrite
- ✅ Use hooks for agent coordination
- ✅ Enable stream chaining for complex workflows

### DON'T:
- ❌ Split related operations across messages
- ❌ Use MCP tools for file operations
- ❌ Make single-todo TodoWrite calls
- ❌ Skip agent coordination hooks
- ❌ Use sequential execution when parallel is possible

## 🔧 Performance Tips

1. **Agent Count**: CLI args first, then auto-decide (3-12 range)
2. **Batch Operations**: Multiple ops = single message
3. **Memory Coordination**: Store ALL decisions for cross-agent sync
4. **Hook Integration**: Use pre/post hooks for automation
5. **Stream Chaining**: Enable for 40-60% speed improvement

---

**Remember**: Claude Flow coordinates, Claude Code creates! Start with `mcp__claude-flow__swarm_init` for optimal development workflows.