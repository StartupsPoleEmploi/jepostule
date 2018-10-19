# Je Postule, par Pôle Emploi 

![Build status](https://img.shields.io/travis/StartupsPoleEmploi/jepostule.svg)
![GitHub](https://img.shields.io/github/license/StartupsPoleEmploi/jepostule.svg)


:fr: Je Postule est un outil de candidature simplifiée pour les demandeurs d'emploi et de réponse aux candidatures pour les employeurs. Je Postule peut être intégré à de nombreuses applications, comme [La Bonne Boite](https://labonneboite.pole-emploi.fr) (entreprises fortement susceptibles d'embaucher), [La Bonne Alternance](https://labonnealternance.pole-emploi.fr) (toutes les entreprises qui recrutent regulièrement en alternance) ou [Memo](https://memo.pole-emploi.fr) (toutes vos candidatures en un clin d'œil).

:gb: Je Postule ("I apply") allows job seekers to apply directly and quickly to companies, which in turn can provide quick answers to applications. Je Postule can be integrated to many applications, such as [La Bonne Boite](https://labonneboite.pole-emploi.fr) (companies likely to hire in the coming months), [La Bonne Alternance](https://labonnealternance.pole-emploi.fr) (companies that are apprenticeship-friendly) ou [Memo](https://memo.pole-emploi.fr) (your personal job application dashboard).

Ce projet est en cours de développement et n'est pas encore fonctionnel. Notamment:

- L'upload de pièces jointes ne fonctionne pas encore
- Les maquettes ne sont pas encore intégrées

## How does it work?

On partner websites, the user can click on "Je Postule" buttons for each displayed company. An application iframe is then inserted in the partner website, where users can fill their personal details and add attachments (resume, application letter, etc.). The application email is then sent directly to the company with links to quick answers: "Let's meet", "Application rejected", "You're hired", etc. Job seekers can follow each step of the process with personalised emails. 

## Development

### Quickstart

    pip install -r requirements/dev.txt
    make test
    ./manage.py migrate
    ./manage.py createsuperuser
    ./manage.py runserver
    ./manage.py consumetopics all
    ./manage.py dequeuedelayed

### Install

#### System dependencies

On Ubuntu:

    sudo apt install make postgresql-client-common python3 python3-virtualenv python3-pip

#### Python dependencies

Python dependencies should be installed in a virtual environment:

    virtualenv --python=python3.6 ./venv
    source venv/bin/activate
    pip install -r requirements/dev.txt

#### Running 3rd-party services

Je Postule depends on several services. To start these services, run:

    make services

- [Postgres](https://www.postgresql.org/): the SQL database is used for storage of data with strong resilience constraints, such as users, failed tasks, etc.
- [Kafka](http://kafka.apache.org/): a messaging queue to process tasks asynchronously. Messages are sorted in different topics and processed by consumers.
- [Redis](https://redis.io): we use this key-value store to enforce per-address email rate limits. There is no strong resilience constraint on the data stored in redis.

#### Database migrations

Apply SQL migrations and create Kakfa topics:

    make migrate

### Testing

Run unit tests:

    make test

Run unit tests with code coverage:

    make test-coverage

### Running a local development server

    ./manage.py runserver

You can then view a demo of Je Postule at [http://127.0.0.1:8000/embed/demo](http://127.0.0.1:8000/embed/demo).

### Updating requirements

Python dependencies must be declared in `requirements/base.in`, `dev.in` or `prod.in`. After modifying these files, the requirements list must be recompiled:

    make compile-requirements

## Administration

### Admin user creation

    ./manage.py createsuperuser

### Running asynchronous tasks

A lot of jepostule code is executed asynchronously by "consumers". For instance, email sending will not be performed until you consume messages. To do so, you must run the `consumetopics` command:

```
➭ ./manage.py consumetopics -h
usage: manage.py consumetopics topics [topics ...]

Consume asynchronous tasks

positional arguments:
  topics                Topics to process. Specify 'all' to consume all
                        existing topics.
```
    
For instance, in parallel to `runserver`, you could run:

    ./manage.py consumetopics all

Error handling in asynchronous tasks is **critical**: application emails must be guaranteed to be sent with minimal delay. Whenever a task failure occurs, an error log is produced and the failed task is stored in SQL. Those failed tasks can be viewed in the django admin interface: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin). Note that you will have to [create an admin user](#admin-user-creation) to access this interface.

### Re-processing delayed tasks

Some tasks may be delayed for rate-limiting reasons. For instance, a user may not send too many emails per second. In such cases, a delayed message is created in the database. These delayed message must be re-emitted, when it's time. To do so, run the `dequeuedelayed` command:

```
➭ ./manage.py dequeuedelayed -h
usage: manage.py dequeuedelayed [-d FAIL_DELAY]

Re-emit delayed messages

optional arguments:
  -d FAIL_DELAY, --fail-delay FAIL_DELAY
                        In case a message fails be re-emitted, re-emit it with
                        this delay (in seconds). Defaults to 10 minutes.
```

## Running in production

Copy the configuration file:

    cp config/settings/local-sample.py config/settings/local.py
    
Note that on a production platform **this file must imperatively be modified**. Changes to `local.py` will not be versioned.

Build docker images:

    make build

Run migrations:

    make platform-migrate

Run the platform:

    make platform

## License

This project is licensed under the [GNU Affero General Public License](./LICENSE).

## How to contribute

We are open to comments, questions and contributions! Feel free to [open an issue](github.com/StartupsPoleEmploi/jepostule/issues/new), fork the code, make changes and [open a pull request](https://github.com/StartupsPoleEmploi/labonneboite/pulls).
