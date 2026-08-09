# Nifty 100 Financial Intelligence Platform Makefile

.PHONY: load ratios test report dashboard api clean

# Default target
all: load test

load:
	$(PYTHON) src/etl/loader.py

test:
	$(PYTEST) tests/

ratios:
	@echo "Running Ratio Engine..."
	@echo "This target is part of Sprint 2 and will be implemented then."

report:
	@echo "Generating PDF tearsheets and portfolio reports..."
	@echo "This target is part of Sprint 5 and will be implemented then."

dashboard:
	@echo "Starting Streamlit Dashboard on port 8501..."
	@echo "This target is part of Sprint 4 and will be implemented then."

api:
	@echo "Starting FastAPI REST API server on port 8000..."
	@echo "This target is part of Sprint 6 and will be implemented then."

clean:
	@echo "Cleaning temporary files and cache..."
	powershell -Command "Remove-Item -Path **/__pycache__, **/Thumbs.db, .pytest_cache -Recurse -Force -ErrorAction SilentlyContinue"
	@echo "Clean completed."
