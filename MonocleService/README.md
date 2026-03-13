
## Build Docker

```
docker build -t monocle-service .
```

## Deploy Docker

```
docker volume create monocle-docker

docker run --rm --name monocle_service -p 3456:3456 --env=DbFilePath=/monocle_data --volume=monocle-docker:/monocle_data monocle-service:latest



```

