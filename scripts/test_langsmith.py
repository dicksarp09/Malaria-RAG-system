from simple_langsmith_v2 import tracer

print("Testing LangSmith tracer...")
print(f"Enabled: {tracer.enabled}")

if tracer.enabled:
    run_id = tracer.log_query(
        query="Test query about malaria treatment",
        country="Ghana",
        top_k=5,
        chunks_retrieved=3,
        is_insufficient=False,
        latency_ms=1500.5,
        answer="This is a test answer about malaria treatment in Ghana using ACT therapy.",
    )

    if run_id:
        print(f"✓ Successfully logged test run: {run_id}")
        print("✓ Check LangSmith dashboard: https://smith.langchain.com/")
    else:
        print("✗ Failed to log run - check API key and permissions")
else:
    print("LangSmith is not enabled")
