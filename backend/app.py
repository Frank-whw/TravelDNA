import requests
import os
from dotenv import load_dotenv
load_dotenv()

KEY = os.environ.get('KEY')
UNIT = os.environ.get('UNIT')
LANGUAGE = os.environ.get('LANGUAGE')
API = os.environ.get('API')

# print(KEY, UNIT, LANGUAGE, API)

LOCATION = input('请输入城市:')

def fetchWeather(location):
    result = requests.get(API, params={
        'key': KEY,
        'location': location,
        'language': LANGUAGE,
        'unit': UNIT
    }, timeout=1)
    return result.text


if __name__ == '__main__':
    result = fetchWeather(LOCATION)
    print(result)