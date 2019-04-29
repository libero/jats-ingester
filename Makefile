help:
	@echo "start - starts all services"
	@echo "stop  - stops all services and removes anonymous volumes"
	@echo "shell - runs an instance of the 'app' service and presents a bash prompt"

start:
	docker-compose up

stop:
	docker-compose down -v

shell:
	docker-compose run --rm app /bin/bash
