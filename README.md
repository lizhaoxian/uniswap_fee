
## Storage
sqlite database is used to store txns data
default location is data/db.db
docker compose will map to this location

## Run with docker compose

```
docker compose --file compose.yaml up --build
```
This will setup 
1. backend to query more txns (historically and fill up to current)
2. swagger rest api server at (0.0.0.0:8080, you can try access here http://0.0.0.0:8080/api/v1/ui/)

## Test with docker compose

```
docker compose --file compose-test.yaml up --build
```
This will trigger test
1. unittest for backend code
2. integration test for rest api
3. timeout entire test operation at 2 minutes

## Run directly
To run directly, you need to setup the environment at ./environment/ and install pyenv requirement.txt

```
# servering swagger REST API
bash loop_swagger.sh
```

```
# backend query historical & current txns
bash txns_query.sh
```