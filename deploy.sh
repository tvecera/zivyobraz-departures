#!/bin/sh

VERSION="latest"

# pass zivyobraz/GITHUB_TOKEN | docker login ghcr.io --username docker-registry --password-stdin

docker pull ghcr.io/tvecera/zivyobraz-departures:$VERSION
sudo docker run -d --name departures --restart=always -e GOLEMIO_API_ACCESS_TOKEN="$(pass zivyobraz/GOLEMIO_API_ACCESS_TOKEN)" -e ZIVYOBLAZ_API_IMPORT_KEY="$(pass zivyobraz/ZIVYOBLAZ_API_IMPORT_KEY)" -v ./config:/usr/src/app/config -v ./logs:/usr/src/app/logs ghcr.io/tvecera/zivyobraz-departures:$VERSION
