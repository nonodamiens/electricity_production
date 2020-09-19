import requests
import os
import json
import datetime

# set the start and end default date data selection
date_inter = datetime.date.today()
if date_inter.month == 1:
    default_end_date = str(date_inter.replace(year = date_inter.year - 1, month = 12)) + 'T00:00:00+00:00'
else:
    default_end_date = str(date_inter.replace(month = date_inter.month - 1)) + 'T00:00:00+00:00'

default_start_date = '2015-01-01T00:00:00+00:00' # Can't go before

api_key = os.environ['API_KEY']

def db_update(start_date=default_start_date, end_date=default_end_date, sandbox=False):
    """ Get raw data from RTE API and save it to DB
    
    parameters:
    - start_date = The starting date of datas
    - end_date = The ending date of datas
    - sandbox = To test the API, do not need period dates
    
    The minimum period is one day"""
    # Get Token
    headers_token = {
        'Authorization': 'Basic ' + api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    url_token = 'https://digital.iservices.rte-france.com/token/oauth/'
    response_token = requests.post(url_token, headers=headers_token)
    json_response_token = json.loads(response_token.text)
    token = json_response_token['access_token']

    # Make the rte request
    headers = {
        'Authorization': 'Bearer ' + token
    }
    url_sandbox = 'https://digital.iservices.rte-france.com/open_api/actual_generation/v1/sandbox/actual_generations_per_production_type'
    url = 'https://digital.iservices.rte-france.com/open_api/actual_generation/v1/actual_generations_per_production_type?start_date=' + start_date + '&end_date=' + end_date

    response = requests.get(url, headers=headers)

    print(response)

    print(response.text)
    return response.text

# test (to decomment to execute)
db_update('2016-01-02T13:00:00+00:00', '2016-01-02T15:00:00+00:00')

print(default_end_date)