.DEFAULT_GOAL := help

build: build-jepostule build-kafka ## build all necessary docker images
build-jepostule:
	docker build -t jepostule:latest .
build-kafka:
	docker build -t kafka:latest ./kafka

assets: ## copy vendor assets
	cp node_modules/jquery/dist/jquery.min.js jepostule/static/vendor/
	cd node_modules/jquery-datetimepicker/build/ && cp jquery.datetimepicker.full.js jquery.datetimepicker.min.css ../../../jepostule/static/vendor/
	mkdir -p jepostule/static/vendor/tarteaucitron && cd node_modules/tarteaucitronjs/ && cp -r tarteaucitron.js tarteaucitron.services.js lang css ../../jepostule/static/vendor/tarteaucitron

services: build-kafka ## start 3rd party services, such as kafka
	KAFKA_LISTENERS=localhost docker-compose up --detach kafka postgres redis

stop: ## stop all services
	docker-compose rm --stop --force

run: ## run a local server
	./manage.py runserver

debug: ## run a local server with debug settings
	./manage.py runserver --settings=config.settings.debug

test: ## run unit tests
	./manage.py test --settings=config.settings.test --noinput
test-coverage: ## run unit tests and produce a code coverage report in html format
	coverage run --include=./jepostule/* ./manage.py test --settings=config.settings.test --noinput
	coverage html
	@echo "Open the coverage report by running: xdg-open htmlcov/index.html"
test-custom:
	@echo "To run a specific test, adapt and run this example command:"
	@echo "$ ./manage.py test --settings=config.settings.test --noinput jepostule.pipeline.tests.test_application.ApplicationTests"

migrate: migrate-postgres migrate-kafka
migrate-postgres: services ## run postgres migrations
	./manage.py migrate
migrate-kafka: services ## create and configure required kafka topics
	docker-compose run --rm kafka bash create-topics.sh

compile-requirements: ## generate .txt requirements files from .in files
	pip-compile --output-file requirements/base.txt requirements/base.in
	pip-compile --output-file requirements/dev.txt requirements/dev.in
	pip-compile --output-file requirements/prod.txt requirements/prod.in

platform-migrate: migrate-kafka
	docker-compose run --rm jepostule ./manage.py migrate
platform: ## Run a simple but complete platform with docker-compose
	docker-compose up

help: ## generate this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
