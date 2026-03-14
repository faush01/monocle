
## Build Docker
```
docker build -t monocle-service .
```

## Deploy Docker
```
docker volume create monocle-docker

docker volume inspect monocle-docker
sudo ls -la /var/lib/docker/volumes/monocle-docker/_data

docker run --rm --name monocle_service -p 3456:3456 --env=DbFilePath=/monocle_data --volume=monocle-docker:/monocle_data monocle-service:latest

```

## Github Pull
```
docker image pull ghcr.io/faush01/monocle/monocleservice:develop

docker run --rm --name monocle_service -p 3456:3456 --env=DbFilePath=/monocle_data --volume=monocle-docker:/monocle_data ghcr.io/faush01/monocle/monocleservice:develop

```
