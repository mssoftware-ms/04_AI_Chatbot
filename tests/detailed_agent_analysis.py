#!/usr/bin/env python3
"""
Detailed Agent Analysis - Account for naming convention differences
"""

import csv
import re
from collections import defaultdict

def normalize_agent_name(name):
    """Convert descriptive names to hyphenated IDs"""
    # Common mappings
    mappings = {
        'hive queen': 'queen-orchestrator',
        'system architect': 'system-architect',
        'backend developer': 'backend-dev',
        'frontend developer': 'frontend-dev', 
        'code reviewer': 'reviewer',
        'test engineer': 'tester',
        'technical writer': 'documenter',
        'devops engineer': 'devops',
        'coder': 'coder',
        'hierarchical coordinator': 'hierarchical-coordinator',
        'mesh coordinator': 'mesh-coordinator',
        'adaptive coordinator': 'adaptive-coordinator',
        'collective intelligence coordinator': 'collective-intelligence-coordinator',
        'swarm memory manager': 'swarm-memory-manager',
        'byzantine coordinator': 'byzantine-coordinator',
        'raft manager': 'raft-manager',
        'gossip coordinator': 'gossip-coordinator',
        'consensus builder': 'consensus-builder',
        'crdt synchronizer': 'crdt-synchronizer',
        'quorum manager': 'quorum-manager',
        'security manager': 'security-manager',
        'performance analyzer': 'perf-analyzer',
        'performance benchmarker': 'performance-benchmarker',
        'task orchestrator': 'task-orchestrator',
        'memory coordinator': 'memory-coordinator',
        'smart agent': 'smart-agent',
        'github modes': 'github-modes',
        'pr manager': 'pr-manager',
        'code review swarm': 'code-review-swarm',
        'issue tracker': 'issue-tracker',
        'release manager': 'release-manager',
        'workflow automation': 'workflow-automation',
        'project board sync': 'project-board-sync',
        'repository architect': 'repo-architect',
        'multi-repository swarm': 'multi-repo-swarm',
        'sparc coordinator': 'sparc-coord',
        'sparc coder': 'sparc-coder',
        'specification': 'specification',
        'pseudocode': 'pseudocode',
        'architecture': 'architecture',
        'refinement': 'refinement',
        'mobile developer': 'mobile-dev',
        'ml developer': 'ml-developer',
        'ci/cd engineer': 'cicd-engineer',
        'api documentation': 'api-docs',
        'code analyzer': 'code-analyzer',
        'base template generator': 'base-template-generator',
        'tdd london swarm': 'tdd-london-swarm',
        'production validator': 'production-validator',
        'migration planner': 'migration-planner',
        'swarm initializer': 'swarm-init'
    }
    
    name_lower = name.lower().strip()
    if name_lower in mappings:
        return mappings[name_lower]
    
    # Generic conversion for unknown names
    # Remove special characters and convert to hyphenated
    normalized = re.sub(r'[^\w\s-]', '', name_lower)
    normalized = re.sub(r'\s+', '-', normalized.strip())
    return normalized

def analyze_csv_agents():
    """Perform detailed analysis of the CSV agents"""
    csv_path = "/mnt/d/03_GIT/02_Python/04_AI_Chatbot/.ai_exchange/agents_comprehensive_list.csv"
    
    print("🔍 DETAILED AGENT ANALYSIS")
    print("=" * 60)
    
    # Read CSV
    agents_in_csv = []
    category_counts = defaultdict(int)
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                agent_name = row.get('Agent_Name', '').strip()
                category = row.get('Category', '').strip()
                normalized_name = normalize_agent_name(agent_name)
                
                agents_in_csv.append({
                    'original': agent_name,
                    'normalized': normalized_name,
                    'category': category
                })
                category_counts[category] += 1
    
        print(f"✅ Successfully read CSV with {len(agents_in_csv)} agents")
        print(f"📁 Categories found: {len(category_counts)}")
        
        # Expected agents from CLAUDE.md
        expected_agents = {
            "Core Development": ["coder", "reviewer", "tester", "planner", "researcher"],
            "Swarm Coordination": ["hierarchical-coordinator", "mesh-coordinator", "adaptive-coordinator", "collective-intelligence-coordinator", "swarm-memory-manager"],
            "Consensus & Distributed": ["byzantine-coordinator", "raft-manager", "gossip-coordinator", "consensus-builder", "crdt-synchronizer", "quorum-manager", "security-manager"],
            "Performance & Optimization": ["perf-analyzer", "performance-benchmarker", "task-orchestrator", "memory-coordinator", "smart-agent"],
            "GitHub & Repository": ["github-modes", "pr-manager", "code-review-swarm", "issue-tracker", "release-manager", "workflow-automation", "project-board-sync", "repo-architect", "multi-repo-swarm"],
            "SPARC Methodology": ["sparc-coord", "sparc-coder", "specification", "pseudocode", "architecture", "refinement"],
            "Specialized Development": ["backend-dev", "mobile-dev", "ml-developer", "cicd-engineer", "api-docs", "system-architect", "code-analyzer", "base-template-generator"],
            "Testing & Validation": ["tdd-london-swarm", "production-validator"],
            "Migration & Planning": ["migration-planner", "swarm-init"]
        }
        
        # Create normalized expected set
        expected_normalized = set()
        for agents in expected_agents.values():
            expected_normalized.update(agents)
        
        # Create CSV normalized set
        csv_normalized = {agent['normalized'] for agent in agents_in_csv}
        
        # Analysis
        found_expected = expected_normalized & csv_normalized
        missing_expected = expected_normalized - csv_normalized
        extra_agents = csv_normalized - expected_normalized
        
        coverage_percentage = (len(found_expected) / len(expected_normalized)) * 100
        
        print(f"\n📊 COVERAGE ANALYSIS:")
        print(f"   Expected agents: {len(expected_normalized)}")
        print(f"   Found in CSV: {len(csv_normalized)}")
        print(f"   Matched: {len(found_expected)}")
        print(f"   Coverage: {coverage_percentage:.1f}%")
        
        if coverage_percentage >= 80:
            print("✅ EXCELLENT coverage (≥80%)")
        elif coverage_percentage >= 60:
            print("✅ GOOD coverage (≥60%)")
        else:
            print("⚠️  LOW coverage (<60%)")
        
        print(f"\n📈 CATEGORY BREAKDOWN:")
        for category, count in sorted(category_counts.items()):
            print(f"   {category}: {count} agents")
        
        if missing_expected:
            print(f"\n❌ MISSING EXPECTED AGENTS ({len(missing_expected)}):")
            for agent in sorted(missing_expected):
                print(f"   - {agent}")
        
        if extra_agents:
            print(f"\n➕ ADDITIONAL AGENTS ({len(extra_agents)}):")
            for agent in sorted(extra_agents):
                print(f"   - {agent}")
        
        # Final assessment
        print(f"\n{'='*60}")
        total_agents = len(agents_in_csv)
        min_requirement_met = total_agents >= 54
        good_coverage = coverage_percentage >= 70
        
        if min_requirement_met and good_coverage:
            print("🎉 VALIDATION PASSED!")
            print(f"   ✅ {total_agents} agents (≥54 required)")
            print(f"   ✅ {coverage_percentage:.1f}% coverage")
            status = "PASSED"
        elif min_requirement_met:
            print("⚠️  PARTIAL VALIDATION PASSED")
            print(f"   ✅ {total_agents} agents (≥54 required)")
            print(f"   ⚠️  {coverage_percentage:.1f}% coverage (could be better)")
            status = "PARTIAL"
        else:
            print("❌ VALIDATION FAILED")
            print(f"   ❌ Only {total_agents} agents (<54 required)")
            status = "FAILED"
        
        print("="*60)
        return status
        
    except Exception as e:
        print(f"❌ Error analyzing CSV: {str(e)}")
        return "ERROR"

if __name__ == "__main__":
    analyze_csv_agents()