import requests
import os
import json
import datetime
import pandas as pd
import numpy as np
from statsmodels.tsa.api import ExponentialSmoothing
import statsmodels.api as sm

# Mandatory API key
api_key = os.getenv('API_KEY')

def db_update(start_date=None, end_date=None, sandbox=False):
    """ Get raw data from RTE API and save it to DB
    
    parameters:
    - start_date = The starting date of datas
    - end_date = The ending date of datas
    - sandbox = To test the API, do not need period dates
    
    The minimum period is one day
    The maximum period is 155 days"""
    
    # Make dates if necessary
    date_inter = datetime.date.today()
    if start_date == None:
        if date_inter.month == 1:
            start_date = str(date_inter.replace(year = date_inter.year - 1, month = 12, day = 1)) + 'T00:00:00+00:00'
        else:
            start_date = str(date_inter.replace(month = date_inter.month - 1, day = 1)) + 'T00:00:00+00:00'
    if end_date == None:
        end_date = str(date_inter.replace(day = 1) - datetime.timedelta(days = 1)) + 'T23:59:59+00:00'

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

    # print(response.text)
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
            try:
                dataframe['Date'] = pd.to_datetime(dataframe['Date'], format='%d/%m/%Y')
            except:
                error = True
                response = 'error, date not in dd/mm/aaaa format'

                return (error, response)
            dataframe.dropna(subset=['Consommation'], inplace=True)
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
    df_per_month = df_by_date.groupby([(df_by_date.index.year), (df_by_date.index.month)]).sum()
    labels = [str(d[1] - 8) + '-' + str(d[0] + 1) if d[1] in [9, 10, 11, 12] else str(d[1] + 4) + '-' + str(d[0]) for d in df_per_month.index.to_list()]

    hw = sm.load("hotwinter.pickle")
    hw_pred = hw.forecast(4)
    hw_pred = list(map(int, hw_pred))

    values = df_per_month.production_mw.to_list()[4:] + ['NaN'] * 4
    predictions = ['NaN'] * 8 + hw_pred

    # To test let's calculate an uncertainly interval about 5%
    maximum = [int(v * 1.05) if type(v) == int else v for v in predictions]
    minimum = [int(v * 0.95) if type(v) == int else v for v in predictions]

    print(values)
    print(predictions)
    print(maximum)
    print(minimum)

    return labels, values, predictions, maximum, minimum

def training(data):
    ''' Make and train the machine learning model '''

    df = pd.DataFrame([x for x in data], columns = ['date', 'prod'])
    df.date = pd.to_datetime(df.date)
    df = df.set_index('date')
    df = df.sort_index()
    df = df.groupby(pd.Grouper(freq='M')).sum()
    df = df.set_index(df.index.to_period("M"))

    hw = ExponentialSmoothing(np.asarray(df["prod"]), seasonal_periods=12, trend='mul', seasonal='mul').fit()
    hw_pred = hw.forecast(4)
    hw.save("hotwinter.pickle")

    return 'hotwinter model have been trained and saved'