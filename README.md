# Libero eLife-style Content Adapter Prototype

This project is an implementation of Libero eLife-style Content Adapter.

Contents:
 - [Dependencies](#dependencies)
 - [Getting Started](#getting-started)
 - [Getting help](#getting-help)

## Dependencies

* [Docker](https://www.docker.com/)

## Getting started
This project provides a `Makefile` with short commands to run common tasks.
Typically, MacOS and most Linux distributions come with [gnu make](https://www.gnu.org/software/make/)
installed. If are unable to run the commands below because your system doesn't 
have `gnu make` installed, you can try to install it or copy and paste commands
found in the `Makefile` into your command line interface.

* `make help` for a full list of commands.
* `make start` builds and/or runs the site locally configured for development purposes.
* `make stop` stops containers and cleans up any anonymous volumes.

Once services are running, you can view what's happening in Airflow by visiting
`http://localhost:8080` and localstack's S3 at `http://localhost:8081` in your
browser.

## Getting help

- Report a bug or request a feature on [GitHub](https://github.com/libero/libero/issues/new/choose).
- Ask a question on the [Libero Community Slack](https://libero.pub/join-slack).
- Read the [code of conduct](https://libero.pub/code-of-conduct).