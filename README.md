# Carbon Bank API Demo

Demo for carbpn bank system API.
Built on top of python stack using Django, Gunicorn, PostgreSQL and Nginx


### Setup and installation (Docker):

- Build docker image
 ```sh
    $ make build
 ```

- Start banking system service
 ```sh
    $ make start
 ```

- Stop banking system service
 ```sh
    $ make stop
 ```

- Run tests for this project
 ```sh
    $ make test
 ```

- make command usage details
 ```sh
     $ make help
 ```

### API Docs.

Endpoints for this project are documented in `<hostname>/swagger/`



![Swagger](https://github.com/selcukakarin/carbon_bank_api/blob/master/Carbon-Bank-API.png)