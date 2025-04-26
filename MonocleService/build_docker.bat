docker build -t monocle-service .

rem docker run --env=DbFilePath=/monocle_data --volume=C:\Temp\monocle-docker:/monocle_data --env=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --env=DOTNET_RUNNING_IN_CONTAINER=true --network=bridge --workdir=/app -p 3456:3456 --runtime=runc -d monocle-service:latest
