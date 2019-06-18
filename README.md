# Libero JATS Ingester

This project is an implementation of Libero JATS Ingester.

Contents:
 - [Dependencies](#dependencies)
 - [Getting Started](#getting-started)
 - [Running Tests Locally](#running-tests-locally)
 - [Other useful commands](#other-useful-commands)
 - [Getting help](#getting-help)

## Dependencies

* [Docker](https://www.docker.com/)

## Getting started
This project provides a `Makefile` with short commands to run common tasks.
Typically, MacOS and most Linux distributions come with [gnu make](https://www.gnu.org/software/make/)
installed. If you are unable to run the commands below because your system doesn't 
have `gnu make` installed, you can try to install it or copy and paste commands
found in the `Makefile` into your command line interface.

* `make start` builds and/or runs the site locally configured for development purposes.
* `make stop` stops containers and cleans up any anonymous volumes.

Once services are running, you can view what's happening in services that expose
a web interface by navigating to the following in your web browser:
 
Airflow
 - `http://localhost:8080`
 
Localstack
 - `http://localhost:8081`
 
 ## Running tests locally

* `make tests` runs unit tests.

## Getting help

- Report a bug or request a feature on [GitHub](https://github.com/libero/libero/issues/new/choose).
- Ask a question on the [Libero Community Slack](https://libero.pub/join-slack).
- Read the [code of conduct](https://libero.pub/code-of-conduct).