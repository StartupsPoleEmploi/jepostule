# Je Postule, par Pôle emploi

![Build status](https://img.shields.io/travis/StartupsPoleEmploi/jepostule.svg)
![GitHub](https://img.shields.io/github/license/StartupsPoleEmploi/jepostule.svg)


:fr: Je Postule est un outil de candidature simplifiée pour les demandeurs d'emploi et de réponse aux candidatures pour les employeurs. Je Postule peut être intégré à de nombreuses applications, comme [La Bonne Boite](https://labonneboite.pole-emploi.fr) (entreprises fortement susceptibles d'embaucher), [La Bonne Alternance](https://labonnealternance.pole-emploi.fr) (toutes les entreprises qui recrutent regulièrement en alternance) ou [Memo](https://memo.pole-emploi.fr) (toutes vos candidatures en un clin d'œil).

:gb: Je Postule ("I apply") allows job seekers to apply directly and quickly to companies, which in turn can provide quick answers to applications. Je Postule can be integrated to many applications, such as [La Bonne Boite](https://labonneboite.pole-emploi.fr) (companies likely to hire in the coming months), [La Bonne Alternance](https://labonnealternance.pole-emploi.fr) (companies that are apprenticeship-friendly) ou [Memo](https://memo.pole-emploi.fr) (your personal job application dashboard).

- [How does it work?](#how-does-it-work)
- [Development](#development)
  - [Quickstart](#quickstart)
  - [Install](#install)
  - [Testing](#testing)
  - [Running a local development server](#running-a-local-development-server)
  - [Updating requirements](#updating-requirements)
  - [Application attachments](#application-attachments)
- [Administration](#administration)
  - [Admin user creation](#admin-user-creation)
  - [Client platform creation](#client-platform-creation)
  - [Running asynchronous tasks](#running-asynchronous-tasks)
  - [Re-processing delayed tasks](#re-processing-delayed-tasks)
  - [Failed tasks](#failed-tasks)
  - [Debugging attachments from job applications](#debugging-attachments-from-job-applications)
  - [Dump job application answers to CSV](#dump-job-application-answers-to-csv)
- [Django administration](#django-administration)
- [Email delivery services](#email-delivery-services)
- [Docker](#docker)
- [License](#license)
- [How to contribute](#how-to-contribute)


## How does it work?

On partner websites, the user can click on "Je Postule" buttons for each displayed company. An application iframe is then inserted in the partner website, where users can fill their personal details and add attachments (resume, application letter, etc.). The application email is then sent directly to the company with links to quick answers: "Let's meet", "Application rejected", "You're hired", etc. Job seekers can follow each step of the process with personalised emails.

## Development

### Quickstart

    pip install -r requirements/dev.txt
    npm install
    make services
    make test
    ./manage.py migrate
    ./manage.py createsuperuser
    ./manage.py runserver
    ./manage.py consumetopics all
    ./manage.py dequeuedelayed

NodeJS version: `12.8.0` (see [`Dockerfile`](/Dockerfile) and [`package.json`](/package.json)).
Python requirements: see the [requirements](/requirements) folder. This project uses Python `3.6`.

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

#### Environment-specific settings

Some settings that are likely to vary between deploys can be configured through environment variables:

    export JEPOSTULE_BASE_URL='http://127.0.0.1:8000'

    export POSTGRES_PORT='5433'
    export POSTGRES_HOST='127.0.0.1'
    export POSTGRES_DB='jepostule'
    export POSTGRES_USER='jepostule'
    export POSTGRES_PASSWORD='mdp'

    export REDIS_HOST='localhost'
    export REDIS_PORT='6380'
    export REDIS_DB='0'

    export KAFKA_PORT='9092'
    export KAFKA_BOOTSTRAP_SERVERS='localhost:9092'

    export ZOOKEEPER_PORT='2181'

    export JEPOSTULE_PORT='8000'


Find them in `config/settings` and choose your environment:
- `base.py`: default file when running `manage.py runserver`. Also used as a basis when activating another environment.
- `debug.py`: use it to activate the debug mode locally and have access to the Django debug toolbar.
- `test.py`: tests-specific configuration.
- `local-sample.py`: an example of a settings file to be used in production.
- `local.py`: used in production and when using `Dockerfile` to build Docker images. Ignored by git.

There's a `make` command for each environment!
- `base.py`: `make run` starts a server with the default configuration.
- `debug.py`: `make debug` starts a server with debug mode activated.
- `test.py`: `make test` runs tests.


#### Database migrations

Apply SQL migrations and create Kakfa topics:

    make migrate



### Testing

#### Unit tests

Run unit tests:

    make test

Run unit tests with code coverage:

    make test-coverage


#### Manually testing the user path

##### Locally

The home page should redirect you to the embed demo page (useful to test if your installation worked!).
To make it work, you must:
- create a client platform (see section [Client platform creation](#client-platform-creation))
- add these parameters to the demo page URL: `client_id` and `client_secret`.

Example: `/embed/demo/?client_id=<client_id>&client_secret=<client_secret>`


##### In production

You can't create a client platform in production! Just ask one of your colleagues for the following credentials:
- client_id
- client_secret

This is useful to test the emailing service as you will receive the emails sent both to the job seeker and to the recruiter.

Test url: `https://jepostule.labonneboite.pole-emploi.fr/embed/demo/?client_id=<client_id>&client_secret=<client_secret>&candidate_email=<your_email>&employer_email=<your_email>`.


### Running a local development server

    make run

You can then view a demo of Je Postule at [http://127.0.0.1:8000/embed/demo](http://127.0.0.1:8000/embed/demo).  However, this will return a 404 unless you create a demo user (see below).

### Updating requirements

Python dependencies must be declared in `requirements/base.in`, `dev.in` or `prod.in`. After modifying these files, the requirements list must be recompiled:

    make compile-requirements


### Application attachments

A user can attach one or many files to his application (a resume, a cover letter, ...). They are stored in Kafka and deleted 30 days after their sending. For more details, see [`kafka/bin/create-topics.sh`](/kafka/bin/create-topics.sh).
To know how to debug application attachments, [read this section](#debugging-attachments-from-job-applications).


## Administration

### Admin user creation

    ./manage.py createsuperuser

### Client platform creation

Client platforms, such as La Bonne Boite, Memo, etc. can be created and updated from the command line:

    ./manage.py createclientplatform lbb

The client ID and secret are then printed to stdout. To access the demo, create a demo user:

    # DO NOT RUN THIS ON A PRODUCTION PLATFORM
    ./manage.py createclientplatform demo

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

Error handling in asynchronous tasks is **critical**: application emails must be guaranteed to be sent with minimal delay. Whenever a task failure occurs, an error log is produced and the failed task is stored in SQL. Those failed tasks can be viewed in the [Django admin](#django-admin) interface: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin). Note that you will have to [create an admin user](#admin-user-creation) to access this interface.

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

### Failed tasks

Sometimes, tasks fail for several reasons. You can see a list of them in the [Django Admin](#django-admin) and choose different actions to apply. The most common one, and the one we advised SAVers to do in their daily routine, is to `delete and retry` them. This way, the task is deleted and a new one is created. If it continues to fail, you probably have a bug! ;-)



### Debugging attachments from job applications

The `forwardattachments` command will email the attachments associated to a specific job application to the right email addresses:

```
➭ ./manage.py forwardattachments --help
usage: manage.py forwardattachments job_application_id emails [emails ...]

Find a specific job application and forward attachments for debugging
purposes. Note that the attachments may not be found if they were removed from the
Kafka queue.

positional arguments:
  job_application_id    Job application to find
  emails                Email addresses to send attachments to
```

### Dump job application answers to csv

```
➭ ./manage.py dumpanswers --help
usage: manage.py dumpanswers client_id dst

Dump answer information with related job application to CSV.

positional arguments:
  client_id             Platform client ID of the platform (e.g: 'lbb')
  dst                   Destination csv file path
```



## Django administration

Je Postule has a content management system powered by Django at this address: `<domain-name>/admin`. It displays several informations about applications made with Je postule and is used daily by SAVers.

![Django admin home page](/README_images/django-admin.png)

Je Postule Auth:
- Client platforms: platforms able to use Je Postule services.

Je Postule Pipeline:
- Answer interviews: answers made by recruiters to applications and leading to interviews.
- Answer rejection: refusals made by recruiters to applications.
- Answer request infos: answers by recruiters asking for more information about applications.
- Answers: all kind of answers.
- Job application events: list of all status changes made to applications (application sent, refusal, ...)
- Job applications: applications list. Very useful to see applications details (email content, status, job seeker information, ...)

Queue:
- Delayed messages: list of delayed tasks (see [Re-processing delayed tasks](#re-processing-delayed-tasks))
- Failed messages: list of failed tasks (see [Failed tasks](#failed-tasks))


## Email delivery services

Emails are a very important part of Je Postule. Here is when they are sent:
- If a job seeker checks "I want to receive a copy of my application".
- After an application, a mail is sent to the recruiter.
- If an answer is made by the recruiter (interview proposal, refusal or further information needed), a mail is sent to the job seeker.

Two services are available: Django and Mailjet (see [Services](/jepostule/email/services) list). The default one is Django.


### Sending emails in production

In production, we use [Mailjet](https://www.mailjet.com/) to manage emails. Ask one of your coworkers for the credentials and then change the settings:

```
EMAIL_DELIVERY_SERVICE = 'mailjet'
MAILJET_API_KEY = "setme"
MAILJET_API_SECRET = "setme"
```

:point_right: To receive emails in your inbox and see what they look like, you can to use [this trick](#manually-testing-the-user-path).

:art: The email sent to a recruiter (after an application is made) is based on a Mailjet template editable in their platform (click on "Transactional" > "My transactional models" in the main menu). Its ID is a global variable editable in [the settings](/config/settings).


### If Mailjet limits your account

Mailjet can decide to restrict the number of emails your account can send if it thinks you don't follow their guidelines ([French guidelines](https://app.mailjet.com/support/pourquoi-une-limite-d-envoi-a-t-elle-ete-appliquee-a-mon-compte,479.htm) - [English guidelines](https://app.mailjet.com/support/why-do-i-have-a-sending-limit-imposed-on-my-account,481.htm)).

You need to contact their support team to cancel this limit.

Here is an email example (in French):

```
Bonjour,

Je vous contacte en tant que développeur du service JePostule de Pole-emploi.fr. Ce service permet aux demandeurs d'emploi de candidater spontanément via le service https://labonneboite.pole-emploi.fr/ à des entreprises qui les intéressent. JePostule permet un échange par email entre le demandeur d'emploi et l'entreprise à laquelle il candidate spontanément.

Nous utilisons votre service Mailjet pour envoyer ces emails entre le demandeur d'emploi et les recruteurs, entre lesquels nous jouons le rôle d'intermédiaire facilitateur.

J'insiste sur le fait que nous n'envoyons aucune campagne d'emailing ou autre newsletter. Tous les emails envoyés via votre service sont des échanges en temps réel entre un candidat et un recruteur qui aboutissent régulièrement à des entretiens et des embauches.

99% des jours de l'année notre taux de mise en spam reste très en dessous du seuil de 0.08%. Mais exceptionnellement et en dehors de notre contrôle il peut arriver qu'un utilisateur nous marque comme spam suite à une mauvaise compréhension de notre service. C'est probablement ce qui est arrivé le <date> de <heure> à <heure> avec les <nombre> mises en spam que vous mentionnez dans votre interface.

<détails du souci>

J'insiste sur le fait que notre service est resté identique autour de cette date et n'a subi aucune modification ou autre mise en production. Cette mise en spam ponctuelle a donc tout d'un évènement improbable et exceptionnel.

Pourriez-vous svp débloquer nos envois ?

```

:information_source: Mailjet may ask you for further information on the user path before they restore the service. Here is [a demo](https://www.evernote.com/l/ABLEL6O-zB5HI4ctsHSTYedWhoeRx5Bc9nM) sent to convince them that we're not aggressive towards our users.

:point_up: This process may last some days. In the meanwhile, we strongly recommend you to deactivate Je Postule on your websites using it.

## Docker

This project is totally dockerized. Have a look at the `Makefile` to see a list of available commands using Docker.

:information_source: While developing, you may want to use only third-party services and not all the containers. To do so, run `make build` and then `make services`. Perfect! You're ready to start the server with `make run`!


## License

This project is licensed under the [GNU Affero General Public License](./LICENSE).

## How to contribute

We are open to comments, questions and contributions! Feel free to [open an issue](github.com/StartupsPoleEmploi/jepostule/issues/new), fork the code, make changes and [open a pull request](https://github.com/StartupsPoleEmploi/labonneboite/pulls).
