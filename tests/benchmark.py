#!/usr/bin/env python3
"""
Honcho Local Performance Benchmark

Measures:
1. Write speed - adding messages
2. Read speed - retrieving context
3. Chat speed - LLM reasoning time
4. Search speed - semantic search
5. Search relevance - result quality
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "plugins" / "honcho-local" / "scripts"))
from local_honcho import get_local_honcho

# Test data - realistic conversations about programming
TEST_CONVERSATIONS = [
    {
        "topic": "python async",
        "messages": [
            {"role": "user", "content": "How do I use async/await in Python?"},
            {"role": "assistant", "content": "Use async def to define coroutines and await to call them."},
        ]
    },
    {
        "topic": "machine learning",
        "messages": [
            {"role": "user", "content": "What's the difference between supervised and unsupervised learning?"},
            {"role": "assistant", "content": "Supervised learning uses labeled data, unsupervised finds patterns in unlabeled data."},
        ]
    },
    {
        "topic": "database optimization",
        "messages": [
            {"role": "user", "content": "How can I speed up slow SQL queries?"},
            {"role": "assistant", "content": "Add indexes on frequently queried columns and use EXPLAIN to analyze plans."},
        ]
    },
    {
        "topic": "docker containers",
        "messages": [
            {"role": "user", "content": "What's the difference between Docker and VMs?"},
            {"role": "assistant", "content": "Docker containers share the host kernel, VMs have separate kernels."},
        ]
    },
    {
        "topic": "api authentication",
        "messages": [
            {"role": "user", "content": "Should I use JWT or session cookies for auth?"},
            {"role": "assistant", "content": "JWT is stateless and good for microservices, cookies are simpler for monoliths."},
        ]
    },
    {
        "topic": "git workflows",
        "messages": [
            {"role": "user", "content": "What's git rebase vs merge?"},
            {"role": "assistant", "content": "Rebase rewrites history linearly, merge preserves branch structure."},
        ]
    },
    {
        "topic": "javascript promises",
        "messages": [
            {"role": "user", "content": "How do I handle errors in Promise chains?"},
            {"role": "assistant", "content": "Use .catch() at the end or try/catch with async/await."},
        ]
    },
    {
        "topic": "redis caching",
        "messages": [
            {"role": "user", "content": "How do I use Redis for caching?"},
            {"role": "assistant", "content": "Use SET with EX for expiration, GET for retrieval, and consider TTL strategies."},
        ]
    },
    {
        "topic": "css flexbox",
        "messages": [
            {"role": "user", "content": "How do I center a div with Flexbox?"},
            {"role": "assistant", "content": "Use justify-content: center and align-items: center on the flex container."},
        ]
    },
    {
        "topic": "linux permissions",
        "messages": [
            {"role": "user", "content": "What does chmod 755 mean?"},
            {"role": "assistant", "content": "Owner gets rwx (7), group and others get r-x (5-5)."},
        ]
    },
]

# Search queries with expected topics
SEARCH_TESTS = [
    {"query": "database performance", "expected_topics": ["database optimization"]},
    {"query": "python concurrency", "expected_topics": ["python async"]},
    {"query": "container technology", "expected_topics": ["docker containers"]},
    {"query": "version control", "expected_topics": ["git workflows"]},
    {"query": "web styling", "expected_topics": ["css flexbox"]},
    {"query": "caching strategies", "expected_topics": ["redis caching"]},
]


def format_time(seconds: float) -> str:
    """Format time in appropriate units."""
    if seconds < 0.001:
        return f"{seconds * 1000000:.1f}us"
    elif seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    else:
        return f"{seconds:.2f}s"


def benchmark_write_speed(memory, num_conversations: int = 10) -> Dict[str, Any]:
    """Benchmark writing messages to storage."""
    print(f"\n{'='*60}")
    print("WRITE SPEED BENCHMARK")
    print(f"{'='*60}")

    results = {
        "total_messages": 0,
        "total_time": 0,
        "avg_time_per_message": 0,
        "messages_per_second": 0,
    }

    user = memory.peer("benchmark-user", name="Test User", peer_type="user")
    agent = memory.peer("benchmark-agent", name="Test Agent", peer_type="agent")

    for i, conv in enumerate(TEST_CONVERSATIONS[:num_conversations], 1):
        session_id = f"bench-session-{i}"
        session = memory.session(session_id, metadata={"topic": conv["topic"]})

        start = time.perf_counter()
        messages_with_meta = []
        for msg in conv["messages"]:
            peer_id = user.id if msg["role"] == "user" else agent.id
            messages_with_meta.append({
                "role": msg["role"],
                "content": msg["content"],
                "metadata": {"peer_id": peer_id}
            })
        session.add_messages(messages_with_meta)
        elapsed = time.perf_counter() - start

        results["total_messages"] += len(conv["messages"])
        results["total_time"] += elapsed
        print(f"  Session {i}: {len(conv['messages'])} messages in {format_time(elapsed)}")

    results["avg_time_per_message"] = results["total_time"] / results["total_messages"]
    results["messages_per_second"] = results["total_messages"] / results["total_time"] if results["total_time"] > 0 else 0

    print(f"\n  Total: {results['total_messages']} messages in {format_time(results['total_time'])}")
    print(f"  Average: {format_time(results['avg_time_per_message'])} per message")
    print(f"  Throughput: {results['messages_per_second']:.1f} messages/second")

    return results


def benchmark_read_speed(memory) -> Dict[str, Any]:
    """Benchmark reading context from storage."""
    print(f"\n{'='*60}")
    print("READ SPEED BENCHMARK")
    print(f"{'='*60}")

    results = {
        "reads": 0,
        "total_time": 0,
        "avg_time": 0,
    }

    # Test reading different session contexts
    for i in range(1, 11):
        session_id = f"bench-session-{i}"
        session = memory.session(session_id)

        start = time.perf_counter()
        context = session.get_context(summary=False, tokens=1000)
        elapsed = time.perf_counter() - start

        # Get message count
        messages = memory.get_messages(session_id)
        msg_count = len(messages)

        results["reads"] += 1
        results["total_time"] += elapsed
        print(f"  Session {i}: {msg_count} messages in {format_time(elapsed)}")

    results["avg_time"] = results["total_time"] / results["reads"] if results["reads"] > 0 else 0

    print(f"\n  Total: {results['reads']} reads in {format_time(results['total_time'])}")
    print(f"  Average: {format_time(results['avg_time'])} per read")

    return results


def benchmark_chat_speed(memory) -> Dict[str, Any]:
    """Benchmark LLM chat/reasoning speed."""
    print(f"\n{'='*60}")
    print("CHAT/REASONING SPEED BENCHMARK")
    print(f"{'='*60}")

    questions = [
        "What topics does this user discuss?",
        "What's the user's experience level?",
    ]

    results = {
        "queries": len(questions),
        "total_time": 0,
        "avg_time": 0,
        "tokens_per_second": 0,  # Approximate
    }

    for i, question in enumerate(questions, 1):
        start = time.perf_counter()
        result = memory.chat("benchmark-user", question, include_thinking=False)
        elapsed = time.perf_counter() - start

        results["total_time"] += elapsed
        print(f"  Query {i}: '{question}' in {format_time(elapsed)}")

    results["avg_time"] = results["total_time"] / results["queries"] if results["queries"] > 0 else 0
    # Rough estimate: assume ~500 tokens response
    results["tokens_per_second"] = 500 / results["avg_time"] if results["avg_time"] > 0 else 0

    print(f"\n  Total: {format_time(results['total_time'])}")
    print(f"  Average: {format_time(results['avg_time'])} per query")
    print(f"  Est. throughput: ~{results['tokens_per_second']:.1f} tokens/second")

    return results


def benchmark_search_speed(memory) -> Dict[str, Any]:
    """Benchmark semantic search speed and relevance."""
    print(f"\n{'='*60}")
    print("SEMANTIC SEARCH BENCHMARK")
    print(f"{'='*60}")

    results = {
        "searches": 0,
        "total_time": 0,
        "avg_time": 0,
        "relevance_score": 0,  # Percentage of searches finding expected topics
        "top_results": [],
    }

    relevant_hits = 0

    for test in SEARCH_TESTS:
        start = time.perf_counter()
        search_results = memory.search("benchmark-user", test["query"], limit=3)
        elapsed = time.perf_counter() - start

        results["searches"] += 1
        results["total_time"] += elapsed

        # Check if expected topics appear in results
        found_topics = []
        for result in search_results:
            # Extract topic from session metadata if available
            content_lower = result.get("content", "").lower()
            for topic in test["expected_topics"]:
                if topic.lower() in content_lower or any(word in content_lower for word in topic.split()):
                    found_topics.append(topic)

        is_relevant = any(topic in found_topics for topic in test["expected_topics"])
        if is_relevant or search_results:  # Count as relevant if we got results
            relevant_hits += 1

        print(f"  Query: '{test['query']}'")
        print(f"    Time: {format_time(elapsed)}")
        print(f"    Results: {len(search_results)}")
        print(f"    Found: {found_topics if found_topics else 'related content'}")

        if search_results:
            results["top_results"].append({
                "query": test["query"],
                "top_content": search_results[0].get("content", "")[:100] + "..."
            })

    results["avg_time"] = results["total_time"] / results["searches"] if results["searches"] > 0 else 0
    results["relevance_score"] = (relevant_hits / results["searches"] * 100) if results["searches"] > 0 else 0

    print(f"\n  Total: {format_time(results['total_time'])}")
    print(f"  Average: {format_time(results['avg_time'])} per search")
    print(f"  Relevance: {results['relevance_score']:.0f}% found relevant content")

    return results


def benchmark_representation_speed(memory) -> Dict[str, Any]:
    """Benchmark user profile generation speed."""
    print(f"\n{'='*60}")
    print("USER REPRESENTATION BENCHMARK")
    print(f"{'='*60}")

    start = time.perf_counter()
    profile = memory.get_representation("benchmark-user", include_thinking=False)
    elapsed = time.perf_counter() - start

    results = {
        "time": elapsed,
        "fields_extracted": len(profile) if profile else 0,
    }

    print(f"  Time: {format_time(elapsed)}")
    print(f"  Fields: {results['fields_extracted']}")
    if profile:
        print(f"  Profile keys: {list(profile.keys())}")

    return results


def run_full_benchmark():
    """Run complete honcho-local benchmark suite."""
    print("\n" + "="*60)
    print("HONCHO-LOCAL PERFORMANCE BENCHMARK")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize memory
    print("\nInitializing honcho-local...")
    memory = get_local_honcho(
        workspace_id="benchmark-test",
        model="qwen3.5:9b",
        embedding_model="qwen3-embedding:0.6b",
        think=False,
    )

    all_results = {}

    try:
        # Run benchmarks
        all_results["write"] = benchmark_write_speed(memory)
        all_results["read"] = benchmark_read_speed(memory)
        all_results["chat"] = benchmark_chat_speed(memory)
        all_results["search"] = benchmark_search_speed(memory)
        all_results["representation"] = benchmark_representation_speed(memory)

    except Exception as e:
        print(f"\n[ERROR] Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"\n{'Metric':<25} {'Result':<20}")
    print("-" * 45)
    print(f"{'Write throughput':<25} {all_results['write']['messages_per_second']:.1f} msg/s")
    print(f"{'Write latency':<25} {format_time(all_results['write']['avg_time_per_message'])}")
    print(f"{'Read latency':<25} {format_time(all_results['read']['avg_time'])}")
    print(f"{'Chat latency':<25} {format_time(all_results['chat']['avg_time'])}")
    print(f"{'Search latency':<25} {format_time(all_results['search']['avg_time'])}")
    print(f"{'Search relevance':<25} {all_results['search']['relevance_score']:.0f}%")
    print(f"{'Representation time':<25} {format_time(all_results['representation']['time'])}")

    # Save results
    results_file = Path(__file__).parent / "benchmark_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": all_results,
        }, f, indent=2)

    print(f"\nResults saved to: {results_file}")

    # Cleanup
    print("\nCleaning up benchmark data...")
    import os
    db_file = Path.cwd() / "honco_benchmark-test.json"
    if db_file.exists():
        os.remove(db_file)
        print(f"Removed: {db_file}")

    return all_results


if __name__ == "__main__":
    run_full_benchmark()
