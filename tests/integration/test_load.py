import threading
import time

import httpx

from src.api.main import app


def run_concurrent_test():
    url = "http://localhost:8000/api/v1/screener?min_roe=15"

    # Run uvicorn inside thread to avoid port conflicts and start simply
    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()
    time.sleep(2.0)  # Wait for server startup

    print("Starting load test of 10 concurrent requests to /api/v1/screener...")

    results = []

    def worker():
        t0 = time.time()
        try:
            with httpx.Client() as client:
                r = client.get(url, timeout=15.0)
                elapsed = time.time() - t0
                results.append((r.status_code, elapsed))
        except Exception:
            results.append((500, time.time() - t0))

    threads = []
    start_time = time.time()
    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total_time = time.time() - start_time
    print(f"Total time for 10 concurrent requests: {total_time:.2f} seconds")

    for i, (status, elapsed) in enumerate(results, 1):
        print(f"Request {i}: Status={status}, Time={elapsed:.2f}s")

    with open("output/perf_notes.md", "w") as f:
        f.write("# Performance Notes\n\n")
        f.write(
            f"- Total time for 10 concurrent screener API requests: **{total_time:.2f} seconds** (Target: <10 seconds)\n"
        )
        f.write(
            "- SQLite query index optimizations applied on `company_id` and `year` tables to ensure fast lookup.\n"
        )
        for i, (status, elapsed) in enumerate(results, 1):
            f.write(f"  - Request {i}: Status={status}, Time={elapsed:.2f}s\n")

    print("Performance notes documented in output/perf_notes.md")


if __name__ == "__main__":
    run_concurrent_test()
