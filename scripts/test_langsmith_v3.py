from simple_langsmith_v3 import log_query

print("Testing LangSmith tracer with @traceable...")

# Simulate multiple queries with varying latencies
test_cases = [
    (1200, "fast query"),
    (1500, "medium query"),
    (2500, "slow query"),
    (1800, "another medium query"),
    (3200, "very slow query"),
]

for latency_ms, query_desc in test_cases:
    result = log_query(
        query=f"Test query about malaria treatment - {query_desc}",
        country="Ghana",
        top_k=5,
        chunks_retrieved=3,
        is_insufficient=False,
        latency_ms=latency_ms,
        answer="This is a test answer about malaria treatment in Ghana using ACT therapy.",
    )
    print(f"Logged: {query_desc} ({latency_ms}ms)")

print("\nCheck LangSmith dashboard: https://smith.langchain.com/")
