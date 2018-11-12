.DEFAULT_GOAL := help

build: build-jepostule build-kafka ## build all necessary docker images
build-jepostule:
	docker build -t jepostule:latest .
build-kafka:
	docker build -t kafka:latest ./kafka

services: build-kafka ## start 3rd party services, such as kafka
	KAFKA_LISTENERS=localhost docker-compose up --detach kafka postgres redis

stop: ## stop all services
	docker-compose rm --stop --force

test: ## run unit tests
	./manage.py test --settings=config.settings.test --noinput
test-coverage: ## run unit tests and produce a code coverage report in html format
	coverage run --include=./jepostule/* ./manage.py test --settings=config.settings.test --noinput
	coverage html
	@echo "Open the coverage report by running: xdg-open htmlcov/index.html"

migrate: migrate-postgres migrate-kafka
migrate-postgres: services ## run postgres migrations
	./manage.py migrate
migrate-kafka: services ## create and configure required kafka topics
	docker-compose run --rm kafka bash create-topics.sh

compile-requirements: ## generate .txt requirements files from .in files
	pip-compile --output-file requirements/base.txt requirements/base.in
	pip-compile --output-file requirements/dev.txt requirements/base.in requirements/dev.in
	pip-compile --output-file requirements/prod.txt requirements/base.in requirements/prod.in

platform-migrate: migrate-kafka
	docker-compose run --rm jepostule ./manage.py migrate
platform: ## Run a simple but complete platform with docker-compose
	docker-compose up

help: ## generate this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
