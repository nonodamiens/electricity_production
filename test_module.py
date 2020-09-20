# test for csv uploads in db

import pandas as pd

def csv_upload(csv_file):
    ''' Method for uploading csv file to database

    The csv file must be separated with ';'

    arguments:
    - csv_file: links to the file (string)
    '''

    dataframe = pd.read_csv(csv_file, sep=';')
    
    dataframe_columns_list = dataframe.columns.tolist()
    mandatory_columns_list = ['Consommation', 'Prévision J', 'Fioul',\
         'Charbon', 'Gaz', 'Nucléaire', 'Eolien', 'Solaire', 'Hydraulique',\
              'Pompage', 'Bioénergies', 'Ech. physiques', 'Taux de Co2']

    # Validity check
    for column_name in mandatory_columns_list:
        if column_name not in dataframe_columns_list:
            return 'error, csv file not conform to database'
    
    dataframe_by_day = dataframe.groupby('Date').sum()
    dataframe_by_day = dataframe_by_day[mandatory_columns_list]

    return dataframe_by_day

print(csv_upload('./csv_files/test.csv'))