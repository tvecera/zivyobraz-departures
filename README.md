
# ZivyObraz.eu Departures

This project contains a Python script for downloading bus stop departure tables and uploading the data through the API to zivyobraz.eu.

## Files in the Project

- `departures.py`: The main script for downloading and uploading data.
- `run.sh`: A simple shell script for repeatedly executing `departures.py`.
- `Dockerfile`: Use this if you want to create your own Docker image.

## Configuration

The script can be easily configured through the `departures.yml` file located in the `config` directory.

## Running with Docker on Raspberry Pi (ARM 64)

To run the script using Docker on a Raspberry Pi:

1. Create directories:
   - `zivyobraz-departures/config`
   - `zivyobraz-departures/logs`
2. Copy the modified `departures.yml` configuration into the `config` directory.
3. Set environment variables (replace with your actual tokens):
   ```
   set +o history
   export GOLEMIO_API_ACCESS_TOKEN=eyJhbG...
   export ZIVYOBRAZ_API_IMPORT_KEY=aNO...
   set -o history
   ```

4. In the `zivyobraz-departures` directory, run the Docker container using the command:

   ```
   docker run -d --name departures --restart=always -e GOLEMIO_API_ACCESS_TOKEN=$GOLEMIO_API_ACCESS_TOKEN -e ZIVYOBRAZ_API_IMPORT_KEY=$ZIVYOBRAZ_API_IMPORT_KEY -v ./config:/usr/src/app/config -v ./logs:/usr/src/app/logs ghcr.io/tvecera/zivyobraz-departures:$VERSION
   ```

## Building and Running Your Own Local Docker Image

1. Clone the repository:
   ```
   git clone git@github.com:tvecera/zivyobraz-departures.git
   ```
2. Build the Docker image:
   ```
   docker build -t departures:latest .
   ```
3. Set environment variables (replace with your actual tokens):
   ```
   set +o history
   export GOLEMIO_API_ACCESS_TOKEN=eyJhbG...
   export ZIVYOBRAZ_API_IMPORT_KEY=aNO...
   set -o history
   ```
4. Run the Docker container:
   ```
   sudo docker run -d --name departures --restart=always -e GOLEMIO_API_ACCESS_TOKEN=$GOLEMIO_API_ACCESS_TOKEN -e ZIVYOBRAZ_API_IMPORT_KEY=$ZIVYOBRAZ_API_IMPORT_KEY -v ./config:/usr/src/app/config -v ./logs:/usr/src/app/logs departures:latest
   ```

## Links
- [Živý obraz](https://zivyobraz.eu/)
- [Golemio API](https://api.golemio.cz/pid/docs/openapi/#/%F0%9F%95%90%20Public%20Vehicle%20Positions%20(experimental)/get_public_vehiclepositions)