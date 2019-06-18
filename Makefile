.PHONY: help
help:
	@echo "start  - Run the project locally."
	@echo "stop   - Stop all running containers and remove anonymous volumes"
	@echo "tests  - Run unit tests"

.PHONY: start
start:
	docker-compose up

.PHONY:stop
stop:
	docker-compose down -v

.PHONY: tests
tests:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests
