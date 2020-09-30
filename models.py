import requests
import os
import json
import datetime
import pandas as pd

# set the start and end default date data selection
# For the default ending date takes the month before the actual date  
date_inter = datetime.date.today()
if date_inter.month == 1:
    default_end_date = str(date_inter.replace(year = date_inter.year - 1, month = 12)) + 'T00:00:00+00:00'
else:
    default_end_date = str(date_inter.replace(month = date_inter.month - 1)) + 'T00:00:00+00:00'
default_start_date = '2015-01-01T00:00:00+00:00' # Can't go before

# Mandatory API key
api_key = os.environ['API_KEY']

def db_update(start_date=default_start_date, end_date=default_end_date, sandbox=False):
    """ Get raw data from RTE API and save it to DB
    
    parameters:
    - start_date = The starting date of datas
    - end_date = The ending date of datas
    - sandbox = To test the API, do not need period dates
    
    The minimum period is one day
    The maximum period is 155 days"""
    
    # Get Token
    headers_token = {
        'Authorization': 'Basic ' + api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    url_token = 'https://digital.iservices.rte-france.com/token/oauth/'
    response_token = requests.post(url_token, headers=headers_token)
    json_response_token = json.loads(response_token.text)
    token = json_response_token['access_token']

    # Make the RTE API request
    headers = {
        'Authorization': 'Bearer ' + token
    }
    url_sandbox = 'https://digital.iservices.rte-france.com/open_api/actual_generation/v1/sandbox/actual_generations_per_production_type'
    url = 'https://digital.iservices.rte-france.com/open_api/actual_generation/v1/actual_generations_per_production_type?start_date=' + start_date + '&end_date=' + end_date

    if sandbox:
        response = requests.get(url_sandbox, headers=headers)
    else:
        response = requests.get(url, headers=headers)

    print(response)

    print(response.text)
    return response.text

# test (to decomment to execute)
# db_update('2016-01-02T13:00:00+00:00', '2016-01-02T15:00:00+00:00')

def csv_upload(csv_file):
    ''' Method for uploading csv file to database

    The csv file must be separated with ';'

    arguments:
    - csv_file: links to the file (string)
    '''
    try:
        dataframe = pd.read_csv(csv_file, sep=';', dayfirst=True)
    except:
        error = True
        response = 'File error, Make sure it is a CSV file'
        return (error, response)

    dataframe_columns_list = dataframe.columns.tolist()
    mandatory_columns_list = ['Consommation', 'Prévision J', 'Fioul',\
         'Charbon', 'Gaz', 'Nucléaire', 'Eolien', 'Solaire', 'Hydraulique',\
              'Pompage', 'Bioénergies', 'Ech. physiques', 'Taux de Co2']

    # Validity check
    for column_name in mandatory_columns_list:
        if column_name not in dataframe_columns_list:
            error = True
            response = 'error, csv file not conform to spécifications'
            
            return (error, response)
        else:
            error = False
            dataframe['Date'] = pd.to_datetime(dataframe['Date'], format='%d/%m/%Y')
            dataframe_by_day = dataframe.groupby('Date').sum()
            dataframe_by_day = dataframe_by_day[mandatory_columns_list]
            response = dataframe_by_day
            
            return (error, response)        

# Testing line decomment to execute
# print(csv_upload('./csv_files/test.csv'))

def get_data(dates, productions):
    ''' Make a dataframe of data '''
    df = pd.DataFrame({'date': dates, 'production_mw': productions})
    df['date'] = pd.to_datetime(df['date'])
    df_by_date = df.groupby('date').sum()
    print(df_by_date)
    df_per_month = df_by_date.groupby([(df_by_date.index.year), (df_by_date.index.month)]).sum()
    print(df_per_month)
    labels = [str(d[1]) + '-' + str(d[0]) for d in df_per_month.index.to_list()]
    values = df_per_month.production_mw.to_list()[:-4]
    predictions = df_per_month.production_mw.to_list()[-4:]

    return labels, values, predictions