
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

At frist run, the txns data will be build from most recent txns and adding historical/current data gradually

At 2nd or more run, the txns data will be built from where it was left previously (./data/db.db keeps this data)

## Test with docker compose

```
docker compose --file compose-test.yaml up --build
```
This will trigger test
1. unittest for backend code
2. integration test for rest api
3. timeout entire test operation at 2 minutes (all test should have been finished)

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

## Query Fee
This query service is implemented by swagger, you can discover more from the swagger UI.

query the txn by its hash value

```
http://0.0.0.0:8080/api/v1/tx/{hash}
```

query the txn by from_timestamp, the result display the 100 records >= from_timestamp

```
http://0.0.0.0:8080/api/v1/tx?from_timestamp={value}
```

## Batch Job
To download historical txns for a period of time.

Modify file Dockerfile.txns_query_batch, to set timestamp for the period

Trigger below command to download, current api is at 6 seconds per 100 records, 
faster download will require better API key.
```
docker compose --file compose-batch.yaml up --build
```

## Real & Historical Txns Recording
Image Txns are stored as a time ordered queue, the backend code will gradually fill up the queue's 
head & tail step by step. Head is the earliest txns stored, tail is the most recent txns stored.