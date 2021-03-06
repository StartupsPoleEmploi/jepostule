.DEFAULT_GOAL := help

##########################
######### BUILDS #########
##########################

build: build-jepostule build-kafka ## build all necessary docker images

build-jepostule:
	docker build -t jepostule:latest .

build-kafka:
	docker build -t kafka:latest ./kafka

##########################
######### ASSETS #########
##########################

assets: ## copy vendor assets
	cp node_modules/jquery/dist/jquery.min.js jepostule/static/vendor/
	cd node_modules/jquery-datetimepicker/build/ && cp jquery.datetimepicker.full.js jquery.datetimepicker.min.css ../../../jepostule/static/vendor/
	mkdir -p jepostule/static/vendor/tarteaucitron && cd node_modules/tarteaucitronjs/ && cp -r tarteaucitron.js tarteaucitron.services.js lang css ../../jepostule/static/vendor/tarteaucitron

##########################
######## SERVICES ########
##########################

services: build-kafka ## start 3rd party services, such as kafka
	KAFKA_LISTENERS=localhost docker-compose up --detach kafka postgres redis

stop: ## stop all services
	docker-compose rm --stop --force

clean: ## remove containers, volumes and networks.
	docker-compose down -v

delete-kafka-group: ## delete Kafka 'jepostule' group in its Docker container
	until docker-compose exec kafka bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --delete --group jepostule | grep "Deletion of requested consumer groups ('jepostule') was successful.";\
	do \
		echo "Waiting for Kafka to delete 'jepostule' group...";\
		sleep 5; \
	done

##########################
####### SERVER RUN #######
##########################

run: ## run a local server
	./manage.py runserver

run-with-local-settings: ## run a local server with local settings
	./manage.py runserver --settings=config.settings.local

debug: ## run a local server with debug settings
	./manage.py runserver --settings=config.settings.debug

##########################
######### TESTS ##########
##########################

test: ## run unit tests
	./manage.py test --settings=config.settings.test --noinput

test-coverage: ## run unit tests and produce a code coverage report in html format
	coverage run --include=./jepostule/* ./manage.py test --settings=config.settings.test --noinput
	coverage html
	@echo "Open the coverage report by running: xdg-open htmlcov/index.html"

test-custom:
	@echo "To run a specific test, adapt and run this example command:"
	@echo "$ ./manage.py test --settings=config.settings.test --noinput jepostule.pipeline.tests.test_application.ApplicationTests"

test-e2e-local:  ## End to end tests using Selenium
	@# First run? Have a cup of coffee and read this Bash script:
	bash jepostule/tests/end_to_end/scripts/run_e2e_local.sh

test-e2e-travis: ## end to end tests executed in Travis CI.
	bash jepostule/tests/end_to_end/scripts/run_e2e_travis.sh

##########################
####### MIGRATIONS #######
##########################

migrate: migrate-postgres migrate-kafka

migrate-postgres: services ## run postgres migrations
	./manage.py migrate

migrate-kafka: services ## create and configure required kafka topics
	docker-compose run --rm kafka bash create-topics.sh

##########################
####### UTILITIES ########
##########################

compile-requirements: ## generate .txt requirements files from .in files
	pip-compile --output-file requirements/base.txt requirements/base.in
	pip-compile --output-file requirements/dev.txt requirements/dev.in
	pip-compile --output-file requirements/prod.txt requirements/prod.in

DUMPSTATS_BEGIN_DATETIME = 20190701-00:00:00
DUMPSTATS_END_DATETIME = 20190731-23:59:59
dumpstats:
	./manage.py dumpstats --min-date $(DUMPSTATS_BEGIN_DATETIME) --max-date $(DUMPSTATS_END_DATETIME)

help: ## generate this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

platform: build ## Run a simple but complete platform with docker-compose
	# /!\ Broken for the moment. TODO: fix it.
	docker-compose up

platform-migrate: migrate-kafka
	docker-compose run --rm jepostule ./manage.py migrate
