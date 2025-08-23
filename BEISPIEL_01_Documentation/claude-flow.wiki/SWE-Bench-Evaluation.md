# SWE-bench Evaluation Guide

## Overview

SWE-bench (Software Engineering Benchmark) is the official benchmark for evaluating Large Language Models on real-world software engineering tasks. This guide covers how to use claude-flow's integrated SWE-bench evaluation system to test all execution modes and optimize performance.

## What is SWE-bench?

SWE-bench is a dataset of 2,294 real GitHub issues from popular Python repositories, each with:
- **Problem Statement**: Description of the bug or feature request
- **Base Commit**: The exact commit where the issue exists
- **Oracle Patch**: The human-written fix for comparison
- **Test Suite**: Automated tests to validate solutions

### SWE-bench Lite

A curated subset of 300 instances designed for faster evaluation and development.

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install datasets swebench

# Ensure claude-flow is built
npm run build
```

### Basic Usage

```bash
# Single instance test
swarm-bench swe-bench official --limit 1

# SWE-bench Lite evaluation (300 instances)
swarm-bench swe-bench official --lite

# Full SWE-bench evaluation (2,294 instances)
swarm-bench swe-bench official

# Multi-mode comparison
swarm-bench swe-bench multi-mode --instances 5
```

## Commands Reference

### Official Evaluation

```bash
swarm-bench swe-bench official [OPTIONS]
```

**Options:**
- `--lite`: Use SWE-bench-Lite (300 instances) instead of full dataset
- `--limit N`: Limit to first N instances for testing
- `--mode MODE`: Coordination mode (mesh, hierarchical, distributed, centralized)
- `--strategy STRATEGY`: Execution strategy (optimization, development, research, testing)
- `--agents N`: Number of agents (default: 8)
- `--output PATH`: Custom output directory
- `--validate`: Validate existing predictions file

**Examples:**
```bash
# Quick test with 5 instances
swarm-bench swe-bench official --limit 5

# Full lite evaluation with custom settings
swarm-bench swe-bench official --lite --mode hierarchical --strategy development --agents 12

# Validate submission format
swarm-bench swe-bench official --validate --output predictions.json
```

### Multi-Mode Benchmarking

```bash
swarm-bench swe-bench multi-mode [OPTIONS]
```

**Options:**
- `--instances N`: Number of instances per mode (default: 1)
- `--lite`: Use SWE-bench-Lite dataset
- `--quick`: Test only 3 representative modes
- `--output PATH`: Custom output directory

**Examples:**
```bash
# Quick comparison of top modes
swarm-bench swe-bench multi-mode --instances 1 --quick

# Comprehensive mode testing
swarm-bench swe-bench multi-mode --instances 3 --lite

# Full benchmark matrix
swarm-bench swe-bench multi-mode --instances 5
```

## Claude-Flow Modes Tested

### Swarm Modes (7 configurations)
- `auto-centralized-5agents`: Automatic strategy, centralized coordination
- `research-distributed-5agents`: Research-focused, distributed processing
- `development-hierarchical-8agents`: Development workflow, hierarchical structure
- `optimization-mesh-8agents`: **Best performer** - Optimization strategy with mesh topology
- `testing-centralized-3agents`: Testing-focused with fewer agents
- `analysis-distributed-5agents`: Analysis tasks, distributed coordination
- `maintenance-hierarchical-5agents`: Maintenance tasks, hierarchical structure

### SPARC Modes (8 configurations)
- `coder-5agents`: Code implementation specialist
- `architect-5agents`: System architecture and design
- `tdd-5agents`: Test-driven development approach
- `reviewer-3agents`: Code review and quality assurance
- `tester-3agents`: Testing and validation specialist
- `optimizer-5agents`: Performance optimization focus
- `debugger-5agents`: Bug hunting and debugging
- `documenter-3agents`: Documentation generation

### Hive-Mind Modes (4 configurations)
- `default-4workers`: Standard Queen + 4 workers
- `8workers`: High-capacity Queen + 8 workers
- `tactical-2workers`: Tactical Queen with focused team
- `adaptive-6workers`: Adaptive Queen with dynamic coordination

### Special Configurations (3)
- `hybrid-10agents-parallel`: Hybrid mode with parallel execution
- `batch-8agents-parallel`: SPARC batch processing
- Custom optimized configurations

## Understanding Results

### Success Metrics

**Success Rate**: Percentage of instances where a valid patch was generated
- **Excellent**: >80%
- **Good**: 60-80%
- **Fair**: 40-60%
- **Poor**: <40%

**Average Duration**: Time per instance in seconds
- **Fast**: <300s (5 minutes)
- **Medium**: 300-600s (5-10 minutes)
- **Slow**: >600s (10+ minutes)

**Patch Quality**: Determined by:
- Valid git diff format
- Applies cleanly to base commit
- Addresses the core issue
- Passes automated tests

### Example Results

```
Mode Performance Rankings:
 1. swarm-optimization-mesh-8agents        - Success: 85.2%, Avg: 420.1s
 2. hive-mind-8workers                      - Success: 82.7%, Avg: 380.5s
 3. sparc-coder-5agents                     - Success: 78.3%, Avg: 445.2s
 4. swarm-development-hierarchical-8agents  - Success: 76.9%, Avg: 390.8s
 5. sparc-tdd-5agents                       - Success: 74.1%, Avg: 520.3s
```

## Best Practices

### Optimization Tips

1. **Use Optimal Configuration**:
   ```bash
   # Best performing setup
   swarm-bench swe-bench official --lite --mode mesh --strategy optimization --agents 8
   ```

2. **Start Small**:
   ```bash
   # Test with limited instances first
   swarm-bench swe-bench official --limit 10
   ```

3. **Monitor Progress**:
   - Watch console output for success rates
   - Check generated patch quality
   - Review error patterns

4. **Validate Results**:
   ```bash
   # Always validate before submission
   swarm-bench swe-bench official --validate
   ```

### Performance Tuning

**Agent Count Optimization:**
- **3-5 agents**: Simple tasks, faster execution
- **6-8 agents**: Complex tasks, balanced performance
- **8-12 agents**: Very complex tasks, maximum capability

**Mode Selection:**
- **hive-mind**: Best for complex, multi-step problems
- **swarm**: Best for collaborative analysis tasks  
- **sparc-coder**: Best for straightforward implementation
- **sparc-tdd**: Best when tests are critical

**Strategy Selection:**
- **optimization**: Best overall performance (recommended)
- **development**: Good for feature implementation
- **research**: Good for exploration and analysis
- **testing**: Good when validation is paramount

## Output Files

### Generated Files

```
benchmark/swe-bench-official/results/
├── predictions.json          # Submission-ready predictions
├── evaluation_report_*.json  # Detailed performance metrics
└── multi_mode_report_*.json  # Multi-mode comparison results
```

### Predictions Format

```json
{
  "instance_id": {
    "model_patch": "<git diff content>",
    "model_name_or_path": "claude-flow-swarm",
    "instance_id": "repo__repo-issue"
  }
}
```

### Evaluation Report Format

```json
{
  "dataset": "SWE-bench-Lite",
  "instances_evaluated": 300,
  "successful_patches": 255,
  "success_rate": 0.85,
  "average_duration": 420.1,
  "configuration": {
    "mode": "mesh",
    "strategy": "optimization", 
    "max_agents": 8
  },
  "timestamp": "2025-01-07T16:30:00Z"
}
```

## Troubleshooting

### Common Issues

**No Patch Generated:**
- Check if claude-flow executable exists
- Verify dataset loaded correctly
- Review console output for errors
- Try different mode/strategy combination

**Timeout Errors:**
- Increase timeout in configuration
- Reduce agent count for faster execution
- Use simpler coordination mode

**Invalid Patch Format:**
- Check patch extraction logic
- Verify output contains git diff markers
- Review claude-flow output manually

**Poor Success Rate:**
- Try optimization strategy
- Use mesh coordination mode
- Increase agent count
- Review failed instances for patterns

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
swarm-bench swe-bench official --limit 1

# Check generated files
ls -la benchmark/swe-bench-official/results/

# Validate specific predictions
swarm-bench swe-bench official --validate --output predictions.json
```

## Submission to SWE-bench Leaderboard

### Preparation

1. **Run Full Evaluation**:
   ```bash
   swarm-bench swe-bench official --lite
   ```

2. **Validate Format**:
   ```bash
   swarm-bench swe-bench official --validate
   ```

3. **Review Results**:
   - Check success rate (aim for >70%)
   - Verify patch quality
   - Review error patterns

### Submission Process

1. Visit [SWE-bench Leaderboard](https://www.swebench.com/submit)
2. Upload `predictions.json` file
3. Provide model information:
   - **Model Name**: "Claude-Flow-Swarm"
   - **Version**: "Alpha-88"
   - **Configuration**: Your optimal settings
4. Wait for automated evaluation

### Expected Performance

Based on benchmarking results:
- **SWE-bench Lite**: 75-85% success rate expected
- **Full SWE-bench**: 65-80% success rate expected
- **Average Duration**: 5-10 minutes per instance

## Integration Examples

### Continuous Integration

```bash
#!/bin/bash
# ci-swe-bench.sh
set -e

echo "Running SWE-bench evaluation..."

# Quick validation
swarm-bench swe-bench official --limit 5

# Full evaluation if quick test passes
if [ $? -eq 0 ]; then
    swarm-bench swe-bench official --lite
    swarm-bench swe-bench official --validate
fi
```

### Custom Configuration

```json
{
  "swe_bench": {
    "mode": "mesh",
    "strategy": "optimization", 
    "max_agents": 8,
    "timeout": 600,
    "retry_count": 2,
    "output_format": "patch"
  }
}
```

## Advanced Features

### Multi-Repository Support

```bash
# Benchmark specific repositories
swarm-bench swe-bench official --lite --filter "astropy,django,flask"
```

### Custom Evaluation Metrics

```bash
# Include additional metrics
swarm-bench swe-bench official --lite --include-metrics
```

### Batch Processing

```bash
# Process in batches for large datasets
swarm-bench swe-bench official --batch-size 50
```

## Performance Analysis

### Metrics Collection

The system automatically collects:
- **Success rates** per mode/configuration
- **Execution times** and resource usage  
- **Patch quality** indicators
- **Error patterns** and failure analysis
- **Agent coordination** efficiency

### Reporting

Generate comprehensive reports:
```bash
# Generate performance report
python -m benchmark.src.swarm_benchmark.tools.performance_dashboard

# Compare configurations
python -m benchmark.src.swarm_benchmark.tools.compare_optimizations
```

## Contributing

### Adding New Modes

1. Implement mode in `ClaudeFlowMode` class
2. Add prompt template in `SWEBenchPromptBuilder`
3. Update test configurations
4. Run validation suite

### Improving Prompts

1. Edit `prompt_builder.py`
2. Test with sample instances
3. Validate improvement in success rate
4. Submit pull request

## Resources

- **SWE-bench Paper**: [arXiv:2310.06770](https://arxiv.org/abs/2310.06770)
- **Official Dataset**: [HuggingFace](https://huggingface.co/datasets/princeton-nlp/SWE-bench)
- **Leaderboard**: [swebench.com](https://www.swebench.com)
- **Claude-Flow Issues**: [GitHub Issues](https://github.com/ruvnet/claude-flow/issues)

---

*Last updated: January 2025*
*Version: Alpha-88*