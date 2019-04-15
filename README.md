# Ticket API

## Run tests

Setup development dependencies:

```bash
pipenv install --dev
```

Run tests:

```bash
pipenv run ./manage.py test
```

## Run dev stand in Docker

Start containers (_-d_ is for background run):

```bash
docker-compose up -d
```

Wait a few seconds before containers starts.

Apply migrations to DB:

```bash
docker-compose exec backend ./manage.py migrate
```

Create superuser:

```bash
docker-compose exec backend ./manage.py createsuperuser \
    --email admin@example.com
```

Visit welcome page at http://localhost:8080/ 

## API documentation

### User registration

To register superuser use shell command given above.

Regular users should register itself at 
http://localhost:8080/api/auth/register/

### Authentication

For authentication [JWT](https://en.wikipedia.org/wiki/JSON_Web_Token) is used.

#### Get pair of tokens

```bash
curl -XPOST \
    -H 'Content-Type: application/json' \
    -d '{"email": "<email>", "password": "<password>"}' \
    'http://localhost:8080/api/auth/token/'
```

**Response:**

```json
{
  "access": "<access token>",
  "refresh": "<refresh token>"
}
```

_Access token_ lives about 5 minutes and _refresh token_ about 1 day. 

#### Renew expired _access token_ by using _refresh token_:

```bash
curl -XPOST \
    -H 'Content-Type: application/json' \
    -d '{"refresh": "<refresh token>"}' \
    'http://localhost:8080/api/auth/token/refresh/'
```

**Response:**

```json
{
  "access": "<access token>",
  "refresh": "<refresh token>"
}
```

As the result we got two renewed tokens.

#### Check that _access token_ is valid

```bash
curl -XPOST \
    -H 'Content-Type: application/json' \
    -d '{"token": "<access token>"}' \
    'http://localhost:8080/api/auth/token/verify/'
```

Response _200 OK_ with empty body means token is still valid. 
Otherwise detailed message returns.


#### How to use _access token_

Access token must specified in _Authorization_ header with type _Bearer_.

For example:

```bash
curl -XGET \
    -H 'Authorization: Bearer <access_token>' \
    -H 'Content-Type: application/json' \
    'http://localhost:8080/api/tickets/'
```


### API Documentation

#### Current user information

```bash
curl -XGET \
    -H 'Authorization: Bearer <access_token>' \
    -H 'Content-Type: application/json' \
    'http://localhost:8080/api/user-info/'
```
