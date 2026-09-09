.PHONY: help up down demo test validate evaluation-report

help:
	@echo "PeriopUDI — make targets"
	@echo "  up                  Bring up the full stack (docker-compose up --build)"
	@echo "  down                Stop the stack"
	@echo "  demo                Reset state and bring up the full demo stack"
	@echo "  test                Run all service test suites                          (Phase 2+)"
	@echo "  validate            Validate FHIR output against US Core v8.0.1          (Phase 2/7)"
	@echo "  evaluation-report   Run the evaluation notebook and emit a report        (Phase 8)"

up:
	docker-compose up --build

down:
	docker-compose down

demo: down
	docker-compose up --build -d
	@echo "Stack starting. gudid-core: http://localhost:8090"

test:
	@echo "Phase 2+: run pytest across services once tests exist."
	@find services -name tests -type d -exec sh -c 'echo "--- {} ---"' \;

validate:
	@echo "Phase 2/7: run services/fhir-bridge/tests/validate_against_ig.py once implemented."

evaluation-report:
	@echo "Phase 8: run eval/usability_study/analysis.ipynb once implemented."
