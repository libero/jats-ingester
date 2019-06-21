.PHONY: help
help:
	@echo "start  - Run the project locally."
	@echo "stop   - Stop all running containers and remove anonymous volumes"
	@echo "tests  - Run unit tests"
	@echo "shell  - Enter test container shell"

.PHONY: start
start:
	docker-compose up

.PHONY: stop
stop:
	docker-compose down -v

.PHONY: tests
tests:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests

.PHONY: shell
shell:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests bash
