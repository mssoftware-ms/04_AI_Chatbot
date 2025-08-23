#!/usr/bin/env python3
"""
Performance Benchmark für WhatsApp AI Chatbot
Generiert durch KI-Analyse
"""

import time
import sys
import os
import json
import timeit
import importlib.util
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def benchmark_import_times() -> Dict[str, float]:
    """Benchmark import times for main modules"""
    modules_to_test = [
        'main',
        'app',
        'src.main',
        'src.core.chunking',
        'src.core.embeddings',
        'src.core.retrieval',
        'src.api.websocket',
        'src.database.models',
    ]
    
    results = {}
    for module_name in modules_to_test:
        try:
            start = time.perf_counter()
            spec = importlib.util.find_spec(module_name)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            end = time.perf_counter()
            results[module_name] = round(end - start, 4)
        except Exception as e:
            results[module_name] = f"Error: {str(e)[:50]}"
    
    return results

def benchmark_database_operations() -> Dict[str, float]:
    """Benchmark database operations"""
    results = {}
    
    try:
        from src.database import models
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Create in-memory database for testing
        engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        
        # Benchmark insert
        def insert_test():
            session = Session()
            user = models.User(email="test@example.com", username="test")
            session.add(user)
            session.commit()
            session.close()
        
        results['db_insert'] = timeit.timeit(insert_test, number=100) / 100
        
        # Benchmark query
        def query_test():
            session = Session()
            session.query(models.User).first()
            session.close()
        
        results['db_query'] = timeit.timeit(query_test, number=100) / 100
        
    except Exception as e:
        results['database'] = f"Error: {str(e)[:50]}"
    
    return results

def benchmark_text_processing() -> Dict[str, float]:
    """Benchmark text processing operations"""
    results = {}
    
    try:
        from src.core.chunking import ChunkingStrategy, RecursiveChunker
        
        sample_text = "Lorem ipsum dolor sit amet. " * 100
        
        # Benchmark chunking
        def chunk_test():
            chunker = RecursiveChunker(chunk_size=500, chunk_overlap=50)
            list(chunker.chunk(sample_text))
        
        results['text_chunking'] = timeit.timeit(chunk_test, number=10) / 10
        
    except Exception as e:
        results['text_processing'] = f"Error: {str(e)[:50]}"
    
    return results

def benchmark_api_response() -> Dict[str, float]:
    """Benchmark API response times"""
    results = {}
    
    try:
        import asyncio
        from fastapi.testclient import TestClient
        
        # Try to import the app
        try:
            from main import app
        except:
            from app import app
        
        client = TestClient(app)
        
        # Benchmark health check
        def health_test():
            response = client.get("/health")
            return response.status_code
        
        results['api_health_check'] = timeit.timeit(health_test, number=10) / 10
        
    except Exception as e:
        results['api'] = f"Error: {str(e)[:50]}"
    
    return results

def generate_performance_report(results: Dict[str, Any]) -> str:
    """Generate performance report"""
    report = []
    report.append("=" * 80)
    report.append("PERFORMANCE BENCHMARK REPORT")
    report.append("=" * 80)
    report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Import times
    report.append("MODULE IMPORT TIMES:")
    report.append("-" * 40)
    for module, time_val in results.get('import_times', {}).items():
        if isinstance(time_val, float):
            status = "✅" if time_val < 1.0 else "⚠️" if time_val < 2.0 else "❌"
            report.append(f"{status} {module}: {time_val:.4f}s")
        else:
            report.append(f"❌ {module}: {time_val}")
    report.append("")
    
    # Database operations
    report.append("DATABASE OPERATIONS:")
    report.append("-" * 40)
    for op, time_val in results.get('database', {}).items():
        if isinstance(time_val, float):
            status = "✅" if time_val < 0.01 else "⚠️" if time_val < 0.05 else "❌"
            report.append(f"{status} {op}: {time_val:.6f}s")
        else:
            report.append(f"❌ {op}: {time_val}")
    report.append("")
    
    # Text processing
    report.append("TEXT PROCESSING:")
    report.append("-" * 40)
    for op, time_val in results.get('text_processing', {}).items():
        if isinstance(time_val, float):
            status = "✅" if time_val < 0.1 else "⚠️" if time_val < 0.5 else "❌"
            report.append(f"{status} {op}: {time_val:.6f}s")
        else:
            report.append(f"❌ {op}: {time_val}")
    report.append("")
    
    # API Response
    report.append("API RESPONSE TIMES:")
    report.append("-" * 40)
    for endpoint, time_val in results.get('api', {}).items():
        if isinstance(time_val, float):
            status = "✅" if time_val < 0.05 else "⚠️" if time_val < 0.1 else "❌"
            report.append(f"{status} {endpoint}: {time_val:.6f}s")
        else:
            report.append(f"❌ {endpoint}: {time_val}")
    report.append("")
    
    # Performance Score
    total_tests = sum(len(v) if isinstance(v, dict) else 1 for v in results.values())
    passed_tests = sum(
        1 for v in results.values() 
        if isinstance(v, dict) 
        for val in v.values() 
        if isinstance(val, float)
    )
    
    score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    report.append("PERFORMANCE SUMMARY:")
    report.append("-" * 40)
    report.append(f"Total Tests: {total_tests}")
    report.append(f"Passed Tests: {passed_tests}")
    report.append(f"Performance Score: {score:.1f}%")
    
    if score >= 80:
        report.append("Status: ✅ EXCELLENT - Production Ready")
    elif score >= 60:
        report.append("Status: ⚠️ GOOD - Minor Optimizations Needed")
    elif score >= 40:
        report.append("Status: ⚠️ FAIR - Significant Optimizations Needed")
    else:
        report.append("Status: ❌ POOR - Major Performance Issues")
    
    report.append("")
    report.append("=" * 80)
    report.append("Generated by AI Performance Analyzer")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """Run all benchmarks"""
    print("Starting performance benchmarks...")
    print("-" * 40)
    
    results = {}
    
    # Run import benchmarks
    print("Testing module import times...")
    results['import_times'] = benchmark_import_times()
    
    # Run database benchmarks
    print("Testing database operations...")
    results['database'] = benchmark_database_operations()
    
    # Run text processing benchmarks
    print("Testing text processing...")
    results['text_processing'] = benchmark_text_processing()
    
    # Run API benchmarks
    print("Testing API response times...")
    results['api'] = benchmark_api_response()
    
    # Generate report
    report = generate_performance_report(results)
    
    # Save report
    output_dir = Path(__file__).parent
    
    # Save text report
    with open(output_dir / "performance_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    # Save JSON report
    with open(output_dir / "performance_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + report)
    print(f"\nReports saved to {output_dir}")
    
    return results

if __name__ == "__main__":
    main()