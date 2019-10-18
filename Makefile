.PHONY: help
help:
	@echo "start           - Run the project locally"
	@echo "stop            - Stop all running containers and remove anonymous volumes"
	@echo "tests           - Runs all tests"
	@echo "python-tests    - Runs all python tests"
	@echo "js-tests        - Runs all javascript tests"
	@echo "debug-js-tests  - Runs all javascript tests using node inspect"
	@echo "shell           - Enter test container shell"

.PHONY: start
start:
	docker-compose up

.PHONY: stop
stop:
	docker-compose down -v

.PHONY: python-tests
python-tests:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests

.PHONY: js-tests
js-tests:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests npm test

.PHONY: debug-js-tests
debug-js-tests:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests npm run debug

.PHONY: tests
tests: js-tests python-tests

.PHONY: shell
shell:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests bash
