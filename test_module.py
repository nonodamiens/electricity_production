# test for csv uploads in db

import pandas as pd

def csv_upload(csv_file):
    ''' Method for uploading csv file to database

    The csv file must be separated with ';'

    arguments:
    - csv_file: links to the file (string)
    '''
    
    df = pd.read_csv(csv_file, sep=';')
    
    return df.groupby('Date').sum()

print(csv_upload('./csv_files/test.csv'))