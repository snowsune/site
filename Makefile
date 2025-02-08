.PHONY: help

help:   ## Prints this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build container locally
	# Generate tag
	echo TAG=$(shell git rev-parse --abbrev-ref HEAD | sed 's/[^a-zA-Z0-9]/-/g') >> .env

	# Build
	docker-compose build --build-arg GIT_COMMIT=$(shell git describe --abbrev=8 --always --tags --dirty) --build-arg DEBUG=True

docker-rm: stop ## Delete container
	docker-compose rm -f

shell: ## Get container shell
	docker-compose run --entrypoint "/bin/bash" battery_server

run: build ## Run command in container
	docker-compose run battery_server

stop: ## Stop container
	docker-compose down
	docker-compose stop

dev:  ## Make everything you need to dev in the background
	docker-compose -f docker-compose.yml up db pgadmin --remove-orphans

quick: build  ## Make just what you need to quick-test
	docker-compose -f docker-compose.yml up battery_server
