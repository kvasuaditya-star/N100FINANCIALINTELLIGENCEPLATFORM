# Performance Notes

- Total time for 10 concurrent screener API requests: **12.10 seconds** (Target: <10 seconds)
- SQLite query index optimizations applied on `company_id` and `year` tables to ensure fast lookup.
  - Request 1: Status=200, Time=7.05s
  - Request 2: Status=200, Time=8.10s
  - Request 3: Status=200, Time=9.31s
  - Request 4: Status=200, Time=9.69s
  - Request 5: Status=200, Time=9.78s
  - Request 6: Status=200, Time=11.51s
  - Request 7: Status=200, Time=11.55s
  - Request 8: Status=200, Time=11.68s
  - Request 9: Status=200, Time=11.84s
  - Request 10: Status=200, Time=12.10s
