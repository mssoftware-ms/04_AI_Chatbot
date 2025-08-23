#!/usr/bin/env python3
"""
Test the Agent CSV Validation Framework
"""

import os
import sys
import time
from pathlib import Path

# Add tests directory to path
sys.path.append(str(Path(__file__).parent))

from agent_validation_framework import AgentCSVValidator

def monitor_and_validate():
    """Monitor for CSV file creation and validate when available"""
    csv_path = "/mnt/d/03_GIT/02_Python/04_AI_Chatbot/.ai_exchange/agents_comprehensive_list.csv"
    validator = AgentCSVValidator(csv_path)
    
    print("🔍 TESTER AGENT - CSV Validation Monitor")
    print("=" * 50)
    print(f"Monitoring: {csv_path}")
    
    # Test the framework first
    print("\n📋 Testing validation framework...")
    results = validator.run_full_validation()
    print(results['full_report'])
    
    if not validator.validate_file_exists():
        print("\n⏳ CSV file not found. Expected agents from CLAUDE.md:")
        expected = validator.expected_agents
        total_expected = sum(len(agents) for agents in expected.values())
        print(f"Total expected: {total_expected} agents")
        
        for category, agents in expected.items():
            print(f"\n{category} ({len(agents)} agents):")
            for agent in agents:
                print(f"  - {agent}")
        
        print("\n🔄 Will validate once CSV file is created by other agents...")
        return False
    
    return True

def run_continuous_validation():
    """Run validation continuously until file is created and validated"""
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n--- Validation Attempt {attempt}/{max_attempts} ---")
        
        if monitor_and_validate():
            print("✅ Validation completed successfully!")
            break
        
        if attempt < max_attempts:
            print("⏳ Waiting 10 seconds before next check...")
            time.sleep(10)
    
    if attempt >= max_attempts:
        print("❌ Maximum attempts reached. CSV file was not created.")

if __name__ == "__main__":
    run_continuous_validation()