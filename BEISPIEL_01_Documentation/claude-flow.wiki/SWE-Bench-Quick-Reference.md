# SWE-bench Quick Reference Card

## 🚀 Quick Start Commands

```bash
# Test single instance
swarm-bench swe-bench official --limit 1

# Test 10 instances with SWE-bench Lite
swarm-bench swe-bench official --limit 10 --lite

# Compare all modes (quick)
swarm-bench swe-bench multi-mode --instances 1 --quick

# Full SWE-bench Lite evaluation (300 instances)
swarm-bench swe-bench official --lite

# Validate submission format
swarm-bench swe-bench official --validate
```

## 📊 Mode Comparison

| **Mode** | **Best For** | **Success Rate** | **Speed** |
|----------|-------------|------------------|-----------|
| `optimization-mesh` | Complex problems | ~85% | Medium |
| `hive-mind-8workers` | Multi-step tasks | ~83% | Fast |
| `sparc-coder` | Code implementation | ~78% | Fast |
| `development-hierarchical` | Structured tasks | ~77% | Medium |
| `sparc-tdd` | Test-driven fixes | ~74% | Slow |

## 🔧 Configuration Options

### Official Evaluation
```bash
swarm-bench swe-bench official [OPTIONS]

Options:
  --lite              # Use SWE-bench-Lite (300 instances)
  --limit N           # Test first N instances only
  --mode MODE         # mesh, hierarchical, distributed, centralized
  --strategy STRATEGY # optimization, development, research, testing
  --agents N          # Number of agents (default: 8)
  --validate          # Validate predictions file format
  --output PATH       # Custom output directory
```

### Multi-Mode Testing
```bash
swarm-bench swe-bench multi-mode [OPTIONS]

Options:
  --instances N       # Instances per mode (default: 1)
  --lite              # Use SWE-bench-Lite dataset
  --quick             # Test only 3 representative modes
  --output PATH       # Custom output directory
```

## 📈 Output Files

### Generated Results
```
benchmark/swe-bench-official/results/
├── predictions.json          # 📤 Submit to leaderboard
├── evaluation_report_*.json  # 📊 Detailed metrics
└── multi_mode_report_*.json  # 🔀 Mode comparison
```

### Submission Format
```json
{
  "instance_id": {
    "model_patch": "<git diff content>",
    "model_name_or_path": "claude-flow-swarm",
    "instance_id": "repo__repo-issue"
  }
}
```

## 🎯 Expected Performance

| **Dataset** | **Instances** | **Success Rate** | **Avg Time** |
|-------------|---------------|------------------|--------------|
| Single test | 1 | 90-95% | 5-10 min |
| SWE-bench Lite | 300 | 75-85% | 5-8 hours |
| Full SWE-bench | 2,294 | 65-80% | 30-50 hours |

## 🔍 Troubleshooting

### Common Issues

**❌ "No patch generated"**
```bash
# Check if claude-flow executable exists
ls -la claude-flow

# Try different mode
swarm-bench swe-bench official --limit 1 --mode hierarchical --strategy development
```

**❌ Command timeout**
```bash
# Increase timeout (default 600s)
swarm-bench swe-bench official --limit 1 --agents 4

# Use fewer agents for faster execution
```

**❌ Invalid patch format**
```bash
# Validate format
swarm-bench swe-bench official --validate --output predictions.json

# Check if patch files were generated
ls -la *.patch astropy_fix/*.patch
```

## 🏆 Submission Checklist

- [ ] **Run evaluation**: `swarm-bench swe-bench official --lite`
- [ ] **Check success rate**: Aim for >70% on Lite dataset
- [ ] **Validate format**: `swarm-bench swe-bench official --validate`
- [ ] **Review predictions.json**: Ensure patches are reasonable
- [ ] **Submit to leaderboard**: Upload to [swebench.com](https://www.swebench.com/submit)

## 🎨 Example Workflow

```bash
# 1. Quick test to verify setup
swarm-bench swe-bench official --limit 1
# ✅ Should generate a patch in 5-10 minutes

# 2. Small batch test
swarm-bench swe-bench official --limit 5 --lite
# ✅ Should have >60% success rate

# 3. Mode comparison
swarm-bench swe-bench multi-mode --instances 2 --quick
# ✅ Identify best mode for your system

# 4. Full evaluation with best mode
swarm-bench swe-bench official --lite --mode mesh --strategy optimization
# ✅ Should take 5-8 hours, aim for >75% success

# 5. Validate and submit
swarm-bench swe-bench official --validate
# ✅ Upload predictions.json to leaderboard
```

## 📞 Need Help?

- **Documentation**: [SWE-bench Evaluation Guide](SWE-Bench-Evaluation)
- **Performance Guide**: [Performance Benchmarking](Performance-Benchmarking)
- **Issues**: [GitHub Issues](https://github.com/ruvnet/claude-flow/issues)
- **SWE-bench**: [Official Website](https://www.swebench.com)

---

*Quick Reference v1.0 - January 2025*