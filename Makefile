.PHONY: help
help:
	@echo "start                      - Run the project locally"
	@echo "stop                       - Stop all running containers and remove anonymous volumes"
	@echo "tests                      - Runs all tests"
	@echo "python-tests               - Runs python tests"
	@echo "js-tests                   - Runs javascript tests"
	@echo "debug-js-tests             - Runs javascript tests using node inspect"
	@echo "js-integration-tests       - Runs javascript tests using services to make real calls"
	@echo "debug-js-integration-tests - Runs javascript tests using services to make real calls using node inspect"
	@echo "shell                      - Enter test container shell"

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

.PHONY: js-integration-tests
js-integration-tests:
	docker-compose -f docker-compose.integration-tests.yml run --rm --service-ports run-tests
	docker-compose down -v

.PHONY: debug-js-integration-tests
debug-js-integration-tests:
	docker-compose -f docker-compose.integration-tests.yml run --rm --service-ports run-tests /bin/bash -c "/wait && sleep 3 && node inspect node_modules/.bin/jest /airflow/tests/js/integration/ --runInBand"
	docker-compose down -v

.PHONY: tests
tests: js-tests js-integration-tests python-tests

.PHONY: shell
shell:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests bash
