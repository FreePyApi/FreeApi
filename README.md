<div align="center">
  <h1>FreeApi</h1>
  
  <img alt="GitHub License" src="https://img.shields.io/github/license/FreePyApi/FreeApi">
  <img alt="GitHub Release" src="https://img.shields.io/github/v/release/FreePyApi/FreeApi">
  <img alt="GitHub Downloads (all assets, all releases)" src="https://img.shields.io/github/downloads/FreePyApi/FreeApi/total">
</div>

FreeAPI is a free and open-source API that provides access to various data and services. It is designed to be easy to use and integrate into your applications.

## Running the API

> It's recommended to run the API yourself, because the hosted version may have limitations and may not be able to process all requests.
> You can try the api at [freeapi.szabee.me](https://freeapi.szabee.me), but it's recommended to run it yourself for better performance and reliability.

### Using Docker

You can run the API using Docker. Make sure you have Docker installed on your machine, then navigate to the `docker` directory and run the following command:

```bash
mkdir -p freeapi
cd freeapi
curl -O https://raw.githubusercontent.com/freepyapi/freeapi/main/docker/docker-compose.yml
curl -o .env https://raw.githubusercontent.com/freepyapi/freeapi/main/docker/.env.example
nano .env # edit the .env file
docker-compose up -d
```

This will build the Docker image and start the API in a container. The API will be accessible at `http://localhost:8000`.

### Using Podman

If you prefer using Podman, you can run the API with the following command:
(Podman supports docker images, so you can use the same docker-compose.yml file)

```bash
mkdir -p freeapi
cd freeapi
curl -o podman-compose.yml https://raw.githubusercontent.com/freepyapi/freeapi/main/docker/docker-compose.yml
curl -o .env https://raw.githubusercontent.com/freepyapi/freeapi/main/docker/.env.example
nano .env # edit the .env file
podman-compose up -d
```

### Running with Python locally

You can also run the API locally using Python. Make sure you have Python 3.10 or higher installed, then navigate to the project directory and run the following command:

```bash
git clone -b main --single-branch https://github.com/FreePyApi/FreeApi.git
cd FreeApi
# make a virtual environment and activate it, it's recommended to use a virtual environment to avoid conflicts with other packages
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

This will start the API, and it will be accessible at `http://localhost:8000`.

### Security configuration

- Rate limiting is enabled only when `ENV=prod` or `ENV=production`.
- Optional OAuth2 login is enabled when both `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` are present in `.env`.
- The OAuth access token is stored in an `HttpOnly` cookie.
- By default the OAuth flow uses GitHub endpoints; you can override them with `OAUTH_AUTHORIZE_URL`, `OAUTH_TOKEN_URL`, `OAUTH_USERINFO_URL`, and `OAUTH_REDIRECT_URI`.

## API Documentation

The API documentation is available at `http://localhost:8000/docs` when you run the API locally. It provides detailed information about the available endpoints, request parameters, and response formats. You can also access the documentation online at [freeapi.szabee.me/docs](https://freeapi.szabee.me/docs).
