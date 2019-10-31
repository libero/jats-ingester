.PHONY: help
help:
	@echo "start                             - Run the project locally"
	@echo "start-all-assets                  - Run the project locally with multiple archive formats"
	@echo "stop                              - Stop all running containers and remove anonymous volumes"
	@echo "shell                             - Enter test container shell"
	@echo "tests                             - Runs all tests"
	@echo "python-tests                      - Runs python tests"
	@echo "js-tests                          - Runs javascript tests"
	@echo "js-integration-tests              - Runs javascript tests using services to make real calls"
	@echo "debug-js-tests                    - Runs javascript tests using node inspect"
	@echo "debug-js-integration-tests        - Runs javascript tests using services to make real calls using node inspect"
	@echo "remote-debug-js-tests             - Runs javascript tests using node inspect accessible remotely"
	@echo "remote-debug-js-integration-tests - Runs javascript tests using services to make real calls using node inspect accessible remotely"

.PHONY: start
start:
	docker-compose up

.PHONY: start-all-assets
start-all-assets:
	docker-compose -f docker-compose.yml -f docker-compose.all-assets.yml up

.PHONY: stop
stop:
	docker-compose down -v

.PHONY: shell
shell:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports debug-js-integration-tests bash

.PHONY: python-tests
python-tests:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports python-unit-tests

.PHONY: js-tests
js-tests:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports js-unit-tests

.PHONY: js-integration-tests
js-integration-tests:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports js-integration-tests
	docker-compose down -v

.PHONY: tests
tests: js-tests js-integration-tests python-tests

.PHONY: debug-js-tests
debug-js-tests:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports debug-js-unit-tests

.PHONY: debug-js-integration-tests
debug-js-integration-tests:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports debug-js-integration-tests
	docker-compose down -v

.PHONY: remote-debug-js-tests
remote-debug-js-tests:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports remote-debug-js-unit-tests

.PHONY: remote-debug-js-integration-tests
remote-debug-js-integration-tests:
	docker-compose -f docker-compose.tests.yml run --rm --service-ports remote-debug-js-integration-tests
	docker-compose down -v
