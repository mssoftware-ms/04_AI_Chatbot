#!/usr/bin/env python3
"""
CSV Agent Validation Framework
Validates the comprehensive agents CSV file once created.
"""

import csv
import os
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter

class AgentCSVValidator:
    """Comprehensive validation for agents CSV file"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.expected_agents = self._get_expected_agents()
        self.validation_results = {}
        
    def _get_expected_agents(self) -> Dict[str, List[str]]:
        """Extract expected agents from CLAUDE.md categories"""
        return {
            "Core Development": [
                "coder", "reviewer", "tester", "planner", "researcher"
            ],
            "Swarm Coordination": [
                "hierarchical-coordinator", "mesh-coordinator", "adaptive-coordinator", 
                "collective-intelligence-coordinator", "swarm-memory-manager"
            ],
            "Consensus & Distributed": [
                "byzantine-coordinator", "raft-manager", "gossip-coordinator", 
                "consensus-builder", "crdt-synchronizer", "quorum-manager", "security-manager"
            ],
            "Performance & Optimization": [
                "perf-analyzer", "performance-benchmarker", "task-orchestrator", 
                "memory-coordinator", "smart-agent"
            ],
            "GitHub & Repository": [
                "github-modes", "pr-manager", "code-review-swarm", "issue-tracker", 
                "release-manager", "workflow-automation", "project-board-sync", 
                "repo-architect", "multi-repo-swarm"
            ],
            "SPARC Methodology": [
                "sparc-coord", "sparc-coder", "specification", "pseudocode", 
                "architecture", "refinement"
            ],
            "Specialized Development": [
                "backend-dev", "mobile-dev", "ml-developer", "cicd-engineer", 
                "api-docs", "system-architect", "code-analyzer", "base-template-generator"
            ],
            "Testing & Validation": [
                "tdd-london-swarm", "production-validator"
            ],
            "Migration & Planning": [
                "migration-planner", "swarm-init"
            ]
        }
    
    def validate_file_exists(self) -> bool:
        """Check if CSV file exists"""
        exists = os.path.exists(self.csv_path)
        self.validation_results['file_exists'] = exists
        return exists
    
    def validate_csv_format(self) -> Tuple[bool, List[str]]:
        """Validate CSV structure and formatting"""
        errors = []
        
        if not self.validate_file_exists():
            errors.append("CSV file does not exist")
            return False, errors
            
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                # Check if file is empty
                content = file.read()
                if not content.strip():
                    errors.append("CSV file is empty")
                    return False, errors
                
                file.seek(0)
                reader = csv.reader(file)
                
                # Check header row
                try:
                    headers = next(reader)
                    if not headers:
                        errors.append("No header row found")
                    else:
                        required_fields = ['agent_name', 'category', 'description'] 
                        # Also accept 'name' as alias for 'agent_name'
                        header_lower = [h.lower() for h in headers]
                        missing_fields = []
                        for field in required_fields:
                            if field == 'agent_name':
                                if 'agent_name' not in header_lower and 'name' not in header_lower:
                                    missing_fields.append(field)
                            elif field.lower() not in header_lower:
                                missing_fields.append(field)
                        if missing_fields:
                            errors.append(f"Missing required fields: {missing_fields}")
                except StopIteration:
                    errors.append("Empty CSV file - no rows found")
                    return False, errors
                
                # Validate data rows
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    row_count += 1
                    if len(row) != len(headers):
                        errors.append(f"Row {row_num}: Incorrect number of columns")
                    
                    # Check for empty required fields
                    for i, value in enumerate(row):
                        if i < len(headers) and headers[i].lower() in required_fields:
                            if not value.strip():
                                errors.append(f"Row {row_num}: Empty {headers[i]} field")
                
                self.validation_results['csv_format'] = {
                    'valid': len(errors) == 0,
                    'headers': headers,
                    'row_count': row_count,
                    'errors': errors
                }
                
        except Exception as e:
            errors.append(f"Error reading CSV file: {str(e)}")
            return False, errors
        
        return len(errors) == 0, errors
    
    def count_agents(self) -> Dict[str, int]:
        """Count total agents and by category"""
        counts = {'total': 0, 'by_category': defaultdict(int)}
        
        if not self.validate_file_exists():
            return counts
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    counts['total'] += 1
                    # Check both 'Category' and 'category' columns
                    category = None
                    if 'Category' in row:
                        category = row['Category'].strip()
                    elif 'category' in row:
                        category = row['category'].strip()
                    
                    if category:
                        counts['by_category'][category] += 1
        except Exception as e:
            self.validation_results['count_error'] = str(e)
        
        self.validation_results['agent_counts'] = counts
        return counts
    
    def validate_agent_coverage(self) -> Tuple[bool, Dict]:
        """Validate that all expected agents are present"""
        if not self.validate_file_exists():
            return False, {'error': 'File does not exist'}
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                found_agents = set()
                
                for row in reader:
                    # Check both 'Agent_Name' and 'name' columns
                    agent_name = None
                    if 'Agent_Name' in row:
                        agent_name = row['Agent_Name'].strip()
                    elif 'name' in row:
                        agent_name = row['name'].strip()
                    elif 'agent_name' in row:
                        agent_name = row['agent_name'].strip()
                    
                    if agent_name:
                        found_agents.add(agent_name.lower())
        
            # Check coverage
            expected_all = set()
            for category_agents in self.expected_agents.values():
                expected_all.update(agent.lower() for agent in category_agents)
            
            missing_agents = expected_all - found_agents
            extra_agents = found_agents - expected_all
            
            coverage = {
                'total_expected': len(expected_all),
                'total_found': len(found_agents),
                'missing_agents': list(missing_agents),
                'extra_agents': list(extra_agents),
                'coverage_percentage': (len(expected_all - missing_agents) / len(expected_all)) * 100
            }
            
            self.validation_results['agent_coverage'] = coverage
            return len(missing_agents) == 0, coverage
            
        except Exception as e:
            error_info = {'error': str(e)}
            self.validation_results['agent_coverage'] = error_info
            return False, error_info
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 60)
        report.append("AGENT CSV VALIDATION REPORT")
        report.append("=" * 60)
        
        # File existence
        if self.validation_results.get('file_exists', False):
            report.append("✅ CSV file exists")
        else:
            report.append("❌ CSV file does not exist")
            return "\n".join(report)
        
        # Format validation
        format_result = self.validation_results.get('csv_format', {})
        if format_result.get('valid', False):
            report.append("✅ CSV format is valid")
            report.append(f"   Headers: {', '.join(format_result.get('headers', []))}")
            report.append(f"   Rows: {format_result.get('row_count', 0)}")
        else:
            report.append("❌ CSV format issues found:")
            for error in format_result.get('errors', []):
                report.append(f"   - {error}")
        
        # Agent counts
        counts = self.validation_results.get('agent_counts', {})
        total_agents = counts.get('total', 0)
        report.append(f"\n📊 AGENT STATISTICS:")
        report.append(f"   Total agents: {total_agents}")
        
        if total_agents >= 54:
            report.append("✅ Meets minimum requirement of 54 agents")
        else:
            report.append(f"❌ Below minimum requirement (found: {total_agents}, required: 54)")
        
        # Category breakdown
        by_category = counts.get('by_category', {})
        if by_category:
            report.append("\n   Agents by category:")
            for category, count in sorted(by_category.items()):
                report.append(f"   - {category}: {count}")
        
        # Coverage analysis
        coverage = self.validation_results.get('agent_coverage', {})
        if 'error' not in coverage:
            coverage_pct = coverage.get('coverage_percentage', 0)
            report.append(f"\n🎯 COVERAGE ANALYSIS:")
            report.append(f"   Expected agents: {coverage.get('total_expected', 0)}")
            report.append(f"   Found agents: {coverage.get('total_found', 0)}")
            report.append(f"   Coverage: {coverage_pct:.1f}%")
            
            if coverage_pct >= 100:
                report.append("✅ All expected agents are present")
            else:
                report.append(f"❌ Missing {len(coverage.get('missing_agents', []))} expected agents")
            
            missing = coverage.get('missing_agents', [])
            if missing:
                report.append(f"\n   Missing agents:")
                for agent in sorted(missing):
                    report.append(f"   - {agent}")
            
            extra = coverage.get('extra_agents', [])
            if extra:
                report.append(f"\n   Extra agents (not in expected list):")
                for agent in sorted(extra):
                    report.append(f"   - {agent}")
        
        # Final assessment
        report.append("\n" + "=" * 60)
        all_passed = (
            self.validation_results.get('file_exists', False) and
            self.validation_results.get('csv_format', {}).get('valid', False) and
            total_agents >= 54 and
            coverage.get('coverage_percentage', 0) >= 100
        )
        
        if all_passed:
            report.append("🎉 VALIDATION PASSED - CSV file is valid and complete!")
        else:
            report.append("🔴 VALIDATION FAILED - Issues found that need to be addressed")
        
        report.append("=" * 60)
        return "\n".join(report)
    
    def run_full_validation(self) -> Dict:
        """Run all validation checks"""
        # Run all validations
        self.validate_file_exists()
        self.validate_csv_format()
        self.count_agents()
        self.validate_agent_coverage()
        
        # Generate report
        report = self.generate_validation_report()
        self.validation_results['full_report'] = report
        
        return self.validation_results

if __name__ == "__main__":
    # Test the validation framework
    csv_path = "/mnt/d/03_GIT/02_Python/04_AI_Chatbot/.ai_exchange/agents_comprehensive_list.csv"
    validator = AgentCSVValidator(csv_path)
    results = validator.run_full_validation()
    print(results['full_report'])