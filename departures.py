import yaml
import requests
import os
import argparse
from datetime import datetime
import pytz
from urllib.parse import urlencode
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='./logs/departures.log', filemode='a')


def validate_config(config):
    """Validate the structure and values of the configuration."""

    logging.info("Config validation....")

    required_keys = ['golemio', 'zivyobraz', 'departure_settings']
    golemio_keys = ['api_url']
    zivyobraz_keys = ['api_base_url']
    departure_settings_keys = ['ids', 'minutes_before', 'minutes_after', 'include_metro_trains', 'air_condition',
                               'preferred_timezone', 'mode', 'order', 'filter_value', 'skip', 'max_entries']

    # Validate required top-level keys
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required key '{key}' in configuration.")
            raise ValueError(f"Missing required key '{key}' in configuration.")

    # Validate nested keys and types
    for key in golemio_keys:
        if key not in config['golemio']:
            logging.error(f"Missing required key 'golemio.{key}' in configuration.")
            raise ValueError(f"Missing required key 'golemio.{key}' in configuration.")

    for key in zivyobraz_keys:
        if key not in config['zivyobraz']:
            logging.error(f"Missing required key 'zivyobraz.{key}' in configuration.")
            raise ValueError(f"Missing required key 'zivyobraz.{key}' in configuration.")

    for key in departure_settings_keys:
        if key not in config['departure_settings']:
            logging.error(f"Missing required key 'departure_settings.{key}' in configuration.")
            raise ValueError(f"Missing required key 'departure_settings.{key}' in configuration.")

    if config['departure_settings']['minutes_before'] < 0 or config['departure_settings']['minutes_before'] > 30:
        logging.error(f"Invalid 'departure_settings.minutes_before' value [0..30].")
        raise ValueError(f"Invalid 'departure_settings.minutes_before' value [0..30].")

    if config['departure_settings']['minutes_after'] <= 0 or config['departure_settings']['minutes_after'] > 300:
        logging.error(f"Invalid 'departure_settings.minutes_after' value (0..300].")
        raise ValueError(f"Invalid 'departure_settings.minutes_after' value (0..300].")

    if config['departure_settings']['mode'] not in ['departures', 'arrivals', 'mixed']:
        logging.error(f"Invalid 'departure_settings.mode' value ['departures', 'arrivals', 'mixed'].")
        raise ValueError(f"Invalid 'departure_settings.mode' value ['departures', 'arrivals', 'mixed'].")

    if config['departure_settings']['order'] not in ['real', 'timetable']:
        logging.error(f"Invalid 'departure_settings.order' value ['real', 'timetable'].")
        raise ValueError(f"Invalid 'departure_settings.order' value ['real', 'timetable'].")

    if config['departure_settings']['skip'] not in ['canceled', 'atStop', 'untracked']:
        logging.error(f"Invalid 'departure_settings.skip' value ['canceled', 'atStop', 'untracked].")
        raise ValueError(f"Invalid 'departure_settings.skip' value ['canceled', 'atStop', 'untracked].")


def load_config(filename):
    """Load and validate configuration from a YAML file."""

    logging.info(f"Try to load config file {filename}....")

    if not os.path.exists(filename):
        logging.error(f"Configuration file '{filename}' not found.")
        raise FileNotFoundError(f"Configuration file '{filename}' not found.")

    with open(filename, 'r') as file:
        try:
            result = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            logging.error(f"Error parsing YAML file: {exc}")
            raise ValueError(f"Error parsing YAML file: {exc}")

    validate_config(result)
    return result


# Set up argument parsing
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-c', '--config', type=str, help='Path to the configuration file',
                    default='./config/departures.yml')

# Parse arguments
args = parser.parse_args()

# Load configuration
loaded_config = load_config(args.config)

# Extracting settings from the config
GOLEMIO_API_URL = loaded_config['golemio']['api_url']
ZIVYOBRAZ_API_BASE_URL = loaded_config['zivyobraz']['api_base_url']
DEPARTURE_SETTINGS = loaded_config['departure_settings']


def get_current_time():
    """Fetches the current time formatted for API requests."""

    tz = pytz.timezone(DEPARTURE_SETTINGS['preferred_timezone'].replace('_', '/'))
    return datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S')


def fetch_departures():
    """Fetches departure information from the Golemio API."""

    logging.info("Fetch departure information from the Golemio API.")

    params = {
        'minutesBefore': DEPARTURE_SETTINGS['minutes_before'],
        'minutesAfter': DEPARTURE_SETTINGS['minutes_after'],
        'timeFrom': get_current_time(),
        'includeMetroTrains': str(DEPARTURE_SETTINGS['include_metro_trains']).lower(),
        'airCondition': str(DEPARTURE_SETTINGS['air_condition']).lower(),
        'preferredTimezone': DEPARTURE_SETTINGS['preferred_timezone'],
        'mode': DEPARTURE_SETTINGS['mode'],
        'order': DEPARTURE_SETTINGS['order'],
        'filter': DEPARTURE_SETTINGS['filter_value'],
        'skip': DEPARTURE_SETTINGS['skip'],
        'limit': DEPARTURE_SETTINGS['max_entries'],
        'total': DEPARTURE_SETTINGS['max_entries']
    }

    formatted_ids = "&".join([f"ids[]={rid}" for rid in DEPARTURE_SETTINGS['ids']])
    url = f"{GOLEMIO_API_URL}?{formatted_ids}&{urlencode(params)}&offset=0"
    headers = {
        'accept': 'application/json',
        'X-Access-Token': os.getenv('GOLEMIO_API_ACCESS_TOKEN')
    }
    response = requests.get(url, headers=headers)

    logging.info(f"Golemio API - status: {response.status_code}, response: {response.text}")

    return response.json()


def process_and_send_departures(departures):
    """Processes and sends departure information to the Zivyobraz API."""

    logging.info("Send departure information to Zivyobraz API")

    filtered_departures = [departure for departure in departures['departures']
                           if 'ignore' not in DEPARTURE_SETTINGS or
                           departure.get('trip', {}).get('headsign') not in DEPARTURE_SETTINGS['ignore']]

    num_filtered = len(filtered_departures)
    if num_filtered < DEPARTURE_SETTINGS['max_entries']:
        filtered_departures.extend([{}] * (DEPARTURE_SETTINGS['max_entries'] - num_filtered))

    for i, departure in enumerate(filtered_departures, start=1):

        if departure:
            route = departure.get('route', {}).get('short_name', 'N/A')
            if departure.get('arrival_timestamp', {}).get('scheduled'):
                arrival = departure.get('arrival_timestamp', {}).get('scheduled', 'T+00:00').split('T')[1].split('+')[
                              0][:5]
            else:
                arrival = departure.get('departure_timestamp', {}).get('scheduled', 'T+00:00').split('T')[1].split('+')[
                              0][:5]
            delay = departure.get('delay', {}).get('minutes', 0) if (departure.get('delay', {})
                                                                     .get('is_available', False)) else 0
            headsign = departure.get('trip', {}).get('headsign', 'N/A').replace(' ', ' ')
            delay = f'+{delay} min'
        else:
            route = '...'
            arrival = '.....'
            delay = '.....'
            headsign = '.....'

        params = {
            'import_key': os.getenv('ZIVYOBRAZ_API_IMPORT_KEY'),
            f'departures.{i}.route': route,
            f'departures.{i}.arrival': arrival,
            f'departures.{i}.delay': delay,
            f'departures.{i}.headsign': headsign
        }

        full_url = f"{ZIVYOBRAZ_API_BASE_URL}?{urlencode(params)}"
        send_response = requests.get(full_url)

        logging.info(f"Sending import {i}: Route: {params[f'departures.{i}.route']}, Arrival: "
                     f"{params[f'departures.{i}.arrival']}, Delay: {params[f'departures.{i}.delay']}, "
                     f"Headsign: {params[f'departures.{i}.headsign']}")
        logging.info(f"Sending import {i}: Status code {send_response.status_code}")


def main():
    loaded_departures = fetch_departures()
    process_and_send_departures(loaded_departures)
    pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error("An error occurred", exc_info=True)
