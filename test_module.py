# test for csv uploads in db

import pandas as pd

def csv_upload(csv_file):
    ''' Method for uploading csv file to database
    '''
    df = pd.read_csv(csv_file)
    return df

print(csv_upload('./csv_files/test.csv'))