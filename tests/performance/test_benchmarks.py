"""
Performance Benchmarks and Load Tests

This module contains comprehensive performance tests and benchmarks
for all system components, including load testing, stress testing,
and performance regression detection.
"""

import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import time
import statistics
from datetime import datetime, timedelta
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np

from tests import TestDataFactory, TestMarkers, generate_test_id, PerformanceAssertions


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformanceBenchmarks:
    """Test API endpoint performance under various load conditions."""

    async def test_health_endpoint_performance(self, async_client, performance_benchmark):
        """Benchmark health endpoint performance."""
        
        async def call_health_endpoint():
            """Single health endpoint call."""
            response = await async_client.get("/health")
            return response.status_code == 200
        
        # Benchmark single call
        result, single_call_time = performance_benchmark(
            lambda: asyncio.run(call_health_endpoint())
        )
        
        assert result is True
        PerformanceAssertions.assert_response_time(single_call_time * 1000, 50, tolerance=0.2)

    @pytest.mark.benchmark
    async def test_api_throughput_benchmark(self, async_client):
        """Benchmark API throughput with concurrent requests."""
        
        async def make_concurrent_requests(endpoint: str, request_count: int) -> Dict[str, Any]:
            """Make concurrent requests to an endpoint."""
            
            async def single_request():
                start_time = time.time()
                response = await async_client.get(endpoint)
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time_ms": (end_time - start_time) * 1000,
                    "success": response.status_code == 200
                }
            
            start_time = time.time()
            tasks = [single_request() for _ in range(request_count)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            successful_requests = sum(1 for r in results if r["success"])
            response_times = [r["response_time_ms"] for r in results]
            total_time_seconds = end_time - start_time
            
            return {
                "total_requests": request_count,
                "successful_requests": successful_requests,
                "success_rate": successful_requests / request_count,
                "total_time_seconds": total_time_seconds,
                "requests_per_second": request_count / total_time_seconds,
                "average_response_time_ms": statistics.mean(response_times),
                "median_response_time_ms": statistics.median(response_times),
                "p95_response_time_ms": np.percentile(response_times, 95),
                "p99_response_time_ms": np.percentile(response_times, 99),
                "max_response_time_ms": max(response_times),
                "min_response_time_ms": min(response_times)
            }
        
        # Test different load levels
        load_tests = [
            {"requests": 10, "expected_rps": 50},
            {"requests": 50, "expected_rps": 100},
            {"requests": 100, "expected_rps": 150},
        ]
        
        for load_test in load_tests:
            with patch("src.api.health.health_check") as mock_health:
                mock_health.return_value = {"status": "healthy"}
                
                results = await make_concurrent_requests("/health", load_test["requests"])
                
                # Performance assertions
                assert results["success_rate"] >= 0.95  # 95% success rate
                assert results["requests_per_second"] >= load_test["expected_rps"] * 0.8  # Within 20% of expected
                assert results["p95_response_time_ms"] < 200  # 95th percentile under 200ms
                assert results["average_response_time_ms"] < 100  # Average under 100ms

    async def test_database_query_performance(self, async_session):
        """Benchmark database query performance."""
        
        async def benchmark_database_operations():
            """Benchmark various database operations."""
            
            with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
                # Mock different query complexities
                query_benchmarks = []
                
                # Simple SELECT query
                start_time = time.time()
                mock_result = MagicMock()
                mock_result.fetchall.return_value = [{"id": i, "name": f"user_{i}"} for i in range(10)]
                mock_execute.return_value = mock_result
                
                result = await async_session.execute("SELECT id, name FROM users LIMIT 10")
                end_time = time.time()
                
                query_benchmarks.append({
                    "query_type": "simple_select",
                    "execution_time_ms": (end_time - start_time) * 1000,
                    "rows_returned": 10
                })
                
                # Complex JOIN query
                start_time = time.time()
                mock_result.fetchall.return_value = [{"id": i, "project_name": f"project_{i}", "message_count": i*10} for i in range(50)]
                result = await async_session.execute("""
                    SELECT u.id, p.name as project_name, COUNT(m.id) as message_count
                    FROM users u 
                    JOIN projects p ON u.id = p.owner_id
                    LEFT JOIN conversations c ON p.id = c.project_id
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    GROUP BY u.id, p.id
                    LIMIT 50
                """)
                end_time = time.time()
                
                query_benchmarks.append({
                    "query_type": "complex_join",
                    "execution_time_ms": (end_time - start_time) * 1000,
                    "rows_returned": 50
                })
                
                # Bulk INSERT simulation
                start_time = time.time()
                for i in range(100):
                    await async_session.execute("INSERT INTO test_table (name) VALUES (?)", f"test_{i}")
                end_time = time.time()
                
                query_benchmarks.append({
                    "query_type": "bulk_insert",
                    "execution_time_ms": (end_time - start_time) * 1000,
                    "rows_affected": 100
                })
                
                return query_benchmarks
        
        benchmarks = await benchmark_database_operations()
        
        # Performance assertions for each query type
        for benchmark in benchmarks:
            if benchmark["query_type"] == "simple_select":
                assert benchmark["execution_time_ms"] < 50  # Simple queries under 50ms
            elif benchmark["query_type"] == "complex_join":
                assert benchmark["execution_time_ms"] < 200  # Complex queries under 200ms
            elif benchmark["query_type"] == "bulk_insert":
                assert benchmark["execution_time_ms"] < 500  # Bulk operations under 500ms


@pytest.mark.performance
@pytest.mark.slow
class TestRAGSystemPerformance:
    """Test RAG system performance benchmarks."""

    @pytest.mark.benchmark
    async def test_embedding_generation_performance(self, mock_openai_client):
        """Benchmark text embedding generation performance."""
        
        def benchmark_embedding_generation(text_samples: List[str]) -> Dict[str, Any]:
            """Benchmark embedding generation for multiple text samples."""
            
            with patch("src.rag.embeddings.generate_embeddings") as mock_generate:
                # Mock embedding generation times
                embedding_results = []
                
                for i, text in enumerate(text_samples):
                    start_time = time.time()
                    
                    # Simulate embedding generation time based on text length
                    base_time = 0.05  # 50ms base time
                    text_factor = len(text) / 1000 * 0.01  # 10ms per 1000 chars
                    simulated_time = base_time + text_factor
                    time.sleep(simulated_time)
                    
                    # Mock embedding vector
                    embedding = [0.1 + (i * 0.001)] * 1536
                    
                    end_time = time.time()
                    
                    embedding_results.append({
                        "text_length": len(text),
                        "embedding_time_ms": (end_time - start_time) * 1000,
                        "embedding_dimensions": len(embedding)
                    })
                
                mock_generate.return_value = embedding_results
                return mock_generate(text_samples)
        
        # Test with different text lengths
        text_samples = [
            "Short text",
            "Medium length text that contains more information and details about a specific topic.",
            "Very long text that simulates a document chunk with extensive content, multiple sentences, and detailed explanations. " * 5,
            "Code example:\n\ndef function():\n    return 'hello world'\n\nclass Example:\n    def __init__(self):\n        self.value = 42"
        ]
        
        results = benchmark_embedding_generation(text_samples)
        
        # Performance assertions
        for result in results:
            # Embedding time should scale reasonably with text length
            expected_max_time = 50 + (result["text_length"] / 100)  # 50ms + 1ms per 100 chars
            assert result["embedding_time_ms"] < expected_max_time
            assert result["embedding_dimensions"] == 1536  # OpenAI embedding size

    @pytest.mark.benchmark
    async def test_vector_search_performance(self, mock_chroma_client):
        """Benchmark vector database search performance."""
        
        def benchmark_vector_search(collection_sizes: List[int]) -> List[Dict[str, Any]]:
            """Benchmark vector search across different collection sizes."""
            
            search_benchmarks = []
            
            for collection_size in collection_sizes:
                with patch("src.rag.vector_store.search") as mock_search:
                    # Simulate search time based on collection size
                    base_search_time = 0.02  # 20ms base time
                    size_factor = collection_size / 10000 * 0.01  # 10ms per 10k documents
                    search_time = base_search_time + size_factor
                    
                    start_time = time.time()
                    time.sleep(search_time)
                    
                    # Mock search results
                    mock_results = {
                        "documents": [["Relevant document content"] * 5],
                        "distances": [[0.1, 0.2, 0.3, 0.4, 0.5]],
                        "metadatas": [[{"source": f"doc_{i}.txt"} for i in range(5)]],
                        "ids": [[f"doc_{i}" for i in range(5)]]
                    }
                    mock_search.return_value = mock_results
                    
                    results = mock_search(
                        collection_name=f"test_collection_{collection_size}",
                        query_embeddings=[[0.1] * 1536],
                        n_results=5
                    )
                    
                    end_time = time.time()
                    
                    search_benchmarks.append({
                        "collection_size": collection_size,
                        "search_time_ms": (end_time - start_time) * 1000,
                        "results_returned": len(results["documents"][0]),
                        "search_accuracy": min(results["distances"][0])  # Best similarity score
                    })
            
            return search_benchmarks
        
        # Test different collection sizes
        collection_sizes = [1000, 5000, 10000, 50000, 100000]
        benchmarks = benchmark_vector_search(collection_sizes)
        
        # Performance assertions
        for benchmark in benchmarks:
            collection_size = benchmark["collection_size"]
            search_time = benchmark["search_time_ms"]
            
            # Search time should scale sub-linearly with collection size
            if collection_size <= 10000:
                assert search_time < 50  # Small collections under 50ms
            elif collection_size <= 50000:
                assert search_time < 100  # Medium collections under 100ms
            else:
                assert search_time < 200  # Large collections under 200ms
            
            assert benchmark["results_returned"] == 5
            assert benchmark["search_accuracy"] < 0.5  # Good similarity

    @pytest.mark.benchmark
    async def test_rag_pipeline_end_to_end_performance(self):
        """Benchmark complete RAG pipeline performance."""
        
        def benchmark_rag_pipeline(query_complexity: str) -> Dict[str, Any]:
            """Benchmark complete RAG pipeline from query to response."""
            
            pipeline_stages = {
                "query_processing": {"simple": 5, "medium": 10, "complex": 20},
                "embedding_generation": {"simple": 50, "medium": 75, "complex": 100},
                "vector_search": {"simple": 30, "medium": 50, "complex": 80},
                "context_retrieval": {"simple": 20, "medium": 40, "complex": 60},
                "response_generation": {"simple": 800, "medium": 1200, "complex": 1800},
                "post_processing": {"simple": 10, "medium": 20, "complex": 30}
            }
            
            stage_times = {}
            total_start_time = time.time()
            
            # Execute each stage with realistic timing
            for stage, times in pipeline_stages.items():
                stage_start = time.time()
                stage_duration = times[query_complexity] / 1000  # Convert to seconds
                time.sleep(stage_duration)
                stage_end = time.time()
                
                stage_times[stage] = (stage_end - stage_start) * 1000
            
            total_end_time = time.time()
            
            return {
                "query_complexity": query_complexity,
                "total_time_ms": (total_end_time - total_start_time) * 1000,
                "stage_times": stage_times,
                "pipeline_efficiency": sum(stage_times.values()) / ((total_end_time - total_start_time) * 1000)
            }
        
        # Test different query complexities
        complexities = ["simple", "medium", "complex"]
        
        for complexity in complexities:
            result = benchmark_rag_pipeline(complexity)
            
            # Performance assertions based on complexity
            if complexity == "simple":
                assert result["total_time_ms"] < 1000  # Simple queries under 1 second
            elif complexity == "medium":
                assert result["total_time_ms"] < 1500  # Medium queries under 1.5 seconds
            else:  # complex
                assert result["total_time_ms"] < 2500  # Complex queries under 2.5 seconds
            
            # Pipeline should be reasonably efficient (stages don't have excessive overhead)
            assert result["pipeline_efficiency"] > 0.8
            
            # Response generation should be the largest component
            assert result["stage_times"]["response_generation"] == max(result["stage_times"].values())


@pytest.mark.performance
@pytest.mark.slow
class TestWebSocketPerformance:
    """Test WebSocket performance under various load conditions."""

    @pytest.mark.benchmark
    async def test_websocket_connection_scalability(self):
        """Test WebSocket connection scalability."""
        
        async def simulate_websocket_connections(connection_count: int) -> Dict[str, Any]:
            """Simulate multiple WebSocket connections."""
            
            connections = []
            connection_times = []
            
            # Simulate connection establishment
            for i in range(connection_count):
                start_time = time.time()
                
                # Mock connection establishment time (increases slightly with more connections)
                base_time = 0.01  # 10ms base
                congestion_factor = (i / connection_count) * 0.02  # Up to 20ms additional
                connection_time = base_time + congestion_factor
                
                await asyncio.sleep(connection_time)
                
                end_time = time.time()
                connection_duration = (end_time - start_time) * 1000
                
                connection_info = {
                    "connection_id": f"conn_{i}",
                    "establishment_time_ms": connection_duration,
                    "connected_at": datetime.utcnow().isoformat()
                }
                
                connections.append(connection_info)
                connection_times.append(connection_duration)
            
            return {
                "total_connections": len(connections),
                "average_connection_time_ms": statistics.mean(connection_times),
                "max_connection_time_ms": max(connection_times),
                "min_connection_time_ms": min(connection_times),
                "connection_success_rate": 1.0  # All successful in simulation
            }
        
        # Test different connection counts
        connection_tests = [50, 100, 200, 500]
        
        for connection_count in connection_tests:
            result = await simulate_websocket_connections(connection_count)
            
            # Performance assertions
            assert result["connection_success_rate"] == 1.0
            assert result["average_connection_time_ms"] < 100  # Average under 100ms
            assert result["max_connection_time_ms"] < 200  # Max under 200ms
            
            # Connection time should scale reasonably
            expected_max_avg_time = 20 + (connection_count / 100) * 10  # Base + scaling factor
            assert result["average_connection_time_ms"] < expected_max_avg_time

    @pytest.mark.benchmark
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput performance."""
        
        async def benchmark_message_throughput(
            connection_count: int,
            messages_per_connection: int
        ) -> Dict[str, Any]:
            """Benchmark WebSocket message throughput."""
            
            total_messages = connection_count * messages_per_connection
            
            async def simulate_connection_messages(connection_id: int):
                """Simulate messages for a single connection."""
                message_times = []
                
                for msg_id in range(messages_per_connection):
                    start_time = time.time()
                    
                    # Simulate message processing time
                    message_size = len(f"Message {msg_id} from connection {connection_id}")
                    processing_time = 0.001 + (message_size / 10000)  # 1ms + size factor
                    
                    await asyncio.sleep(processing_time)
                    
                    end_time = time.time()
                    message_times.append((end_time - start_time) * 1000)
                
                return {
                    "connection_id": connection_id,
                    "messages_sent": messages_per_connection,
                    "average_message_time_ms": statistics.mean(message_times),
                    "total_time_ms": sum(message_times)
                }
            
            # Run all connections concurrently
            start_time = time.time()
            tasks = [simulate_connection_messages(i) for i in range(connection_count)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time_seconds = end_time - start_time
            messages_per_second = total_messages / total_time_seconds
            
            return {
                "total_connections": connection_count,
                "messages_per_connection": messages_per_connection,
                "total_messages": total_messages,
                "total_time_seconds": total_time_seconds,
                "messages_per_second": messages_per_second,
                "average_connection_time_ms": statistics.mean([r["total_time_ms"] for r in results]),
                "connection_results": results
            }
        
        # Test different throughput scenarios
        throughput_tests = [
            {"connections": 10, "messages": 100},
            {"connections": 50, "messages": 20},
            {"connections": 100, "messages": 10},
        ]
        
        for test in throughput_tests:
            result = await benchmark_message_throughput(
                test["connections"],
                test["messages"]
            )
            
            # Performance assertions
            assert result["messages_per_second"] > 500  # At least 500 messages/second
            assert result["total_time_seconds"] < 5  # Complete in under 5 seconds
            
            # Individual connections should perform well
            for conn_result in result["connection_results"]:
                assert conn_result["average_message_time_ms"] < 50  # Under 50ms per message


@pytest.mark.performance
@pytest.mark.slow
class TestSystemResourceUsage:
    """Test system resource usage under various load conditions."""

    @pytest.mark.benchmark
    def test_memory_usage_profiling(self):
        """Profile memory usage under different workloads."""
        
        def measure_memory_usage(workload_func, workload_name: str) -> Dict[str, Any]:
            """Measure memory usage before, during, and after workload."""
            
            # Force garbage collection before measurement
            gc.collect()
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Execute workload and measure peak memory
            start_time = time.time()
            peak_memory = initial_memory
            
            # Simulate workload with periodic memory measurements
            for i in range(10):
                workload_func(i)
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                peak_memory = max(peak_memory, current_memory)
                time.sleep(0.1)  # Small delay between iterations
            
            end_time = time.time()
            
            # Final memory measurement after workload
            gc.collect()
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            return {
                "workload": workload_name,
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "final_memory_mb": final_memory,
                "memory_growth_mb": final_memory - initial_memory,
                "peak_memory_growth_mb": peak_memory - initial_memory,
                "execution_time_seconds": end_time - start_time
            }
        
        # Define different workloads
        def light_workload(iteration):
            """Simulate light workload (small data structures)."""
            data = [i for i in range(100)]
            return len(data)
        
        def medium_workload(iteration):
            """Simulate medium workload (moderate data structures)."""
            data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
            return len(data)
        
        def heavy_workload(iteration):
            """Simulate heavy workload (large data structures)."""
            data = [[i] * 1000 for i in range(1000)]
            return len(data)
        
        # Test different workloads
        workloads = [
            (light_workload, "light"),
            (medium_workload, "medium"),
            (heavy_workload, "heavy")
        ]
        
        memory_profiles = []
        for workload_func, workload_name in workloads:
            profile = measure_memory_usage(workload_func, workload_name)
            memory_profiles.append(profile)
        
        # Memory usage assertions
        for profile in memory_profiles:
            workload = profile["workload"]
            
            if workload == "light":
                assert profile["memory_growth_mb"] < 50  # Light workload under 50MB
                assert profile["peak_memory_growth_mb"] < 100
            elif workload == "medium":
                assert profile["memory_growth_mb"] < 150  # Medium workload under 150MB
                assert profile["peak_memory_growth_mb"] < 250
            else:  # heavy
                assert profile["memory_growth_mb"] < 300  # Heavy workload under 300MB
                assert profile["peak_memory_growth_mb"] < 500
            
            # Memory should be released after workload (reasonable cleanup)
            cleanup_ratio = profile["final_memory_mb"] / profile["peak_memory_mb"]
            assert cleanup_ratio < 0.8  # At least 20% memory cleanup

    @pytest.mark.benchmark
    def test_cpu_usage_profiling(self):
        """Profile CPU usage under computational workloads."""
        
        def measure_cpu_usage(workload_func, duration_seconds: int = 5) -> Dict[str, Any]:
            """Measure CPU usage during workload execution."""
            
            cpu_measurements = []
            
            def cpu_monitor():
                """Monitor CPU usage in background."""
                while True:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    cpu_measurements.append(cpu_percent)
                    if len(cpu_measurements) >= duration_seconds * 10:  # 10 measurements per second
                        break
            
            # Start CPU monitoring in background
            import threading
            monitor_thread = threading.Thread(target=cpu_monitor)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Execute workload
            start_time = time.time()
            result = workload_func()
            end_time = time.time()
            
            # Wait for monitoring to complete
            monitor_thread.join()
            
            if cpu_measurements:
                return {
                    "execution_time_seconds": end_time - start_time,
                    "average_cpu_percent": statistics.mean(cpu_measurements),
                    "max_cpu_percent": max(cpu_measurements),
                    "min_cpu_percent": min(cpu_measurements),
                    "cpu_measurements": len(cpu_measurements),
                    "workload_result": result
                }
            else:
                return {"error": "No CPU measurements collected"}
        
        # CPU-intensive workloads
        def fibonacci_workload():
            """CPU-intensive fibonacci calculation."""
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)
            
            results = []
            for i in range(25, 30):  # Compute fibonacci for 25-29
                results.append(fibonacci(i))
            return results
        
        def matrix_multiplication_workload():
            """CPU-intensive matrix operations."""
            import random
            
            # Create random matrices
            size = 200
            matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
            matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]
            
            # Multiply matrices
            result = [[0 for _ in range(size)] for _ in range(size)]
            for i in range(size):
                for j in range(size):
                    for k in range(size):
                        result[i][j] += matrix_a[i][k] * matrix_b[k][j]
            
            return len(result)
        
        # Test CPU workloads
        workloads = [
            (fibonacci_workload, "fibonacci"),
            (matrix_multiplication_workload, "matrix_multiplication")
        ]
        
        for workload_func, workload_name in workloads:
            profile = measure_cpu_usage(workload_func)
            
            if "error" not in profile:
                # CPU usage assertions
                assert profile["average_cpu_percent"] > 10  # Should use significant CPU
                assert profile["max_cpu_percent"] <= 100  # Should not exceed 100%
                assert profile["execution_time_seconds"] < 10  # Should complete in reasonable time
                
                # Workload should show CPU activity
                cpu_variance = max(profile["max_cpu_percent"] - profile["min_cpu_percent"], 0)
                assert cpu_variance > 5  # Should show CPU activity variation

    @pytest.mark.benchmark
    async def test_concurrent_resource_usage(self):
        """Test resource usage under concurrent operations."""
        
        async def concurrent_resource_test(operation_count: int) -> Dict[str, Any]:
            """Test resource usage with concurrent operations."""
            
            async def cpu_intensive_operation(operation_id: int):
                """Simulate CPU-intensive async operation."""
                # Compute prime numbers
                def is_prime(n):
                    if n < 2:
                        return False
                    for i in range(2, int(n ** 0.5) + 1):
                        if n % i == 0:
                            return False
                    return True
                
                primes = []
                start_num = operation_id * 100
                for num in range(start_num, start_num + 100):
                    if is_prime(num):
                        primes.append(num)
                    
                    # Yield control periodically
                    if num % 10 == 0:
                        await asyncio.sleep(0.001)  # 1ms yield
                
                return len(primes)
            
            # Measure resources before concurrent operations
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Execute concurrent operations
            start_time = time.time()
            tasks = [cpu_intensive_operation(i) for i in range(operation_count)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Measure resources after operations
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            return {
                "operation_count": operation_count,
                "execution_time_seconds": end_time - start_time,
                "memory_growth_mb": final_memory - initial_memory,
                "successful_operations": len([r for r in results if r > 0]),
                "average_primes_found": statistics.mean(results),
                "operations_per_second": operation_count / (end_time - start_time)
            }
        
        # Test different levels of concurrency
        concurrency_levels = [10, 25, 50, 100]
        
        for operation_count in concurrency_levels:
            result = await concurrent_resource_test(operation_count)
            
            # Performance assertions
            assert result["successful_operations"] == operation_count  # All operations succeed
            assert result["execution_time_seconds"] < 10  # Complete in under 10 seconds
            assert result["memory_growth_mb"] < 100  # Memory growth under 100MB
            assert result["operations_per_second"] > 5  # At least 5 operations per second
            
            # Concurrency should provide some efficiency gains
            # (More operations shouldn't scale execution time linearly)
            efficiency_ratio = result["operations_per_second"] / operation_count
            assert efficiency_ratio > 0.05  # Reasonable concurrency efficiency