import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

server = os.getenv('SERVER')
database = os.getenv('DB')
username = os.getenv('SUPERADMIN')
password = os.getenv('PASS')
driver= '{ODBC Driver 17 for SQL Server}'

with pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
	with conn.cursor() as cursor:

 # ------------ SELECT statement (decomment to use) ---------------------------
		# cursor.execute("SELECT * FROM Users")
        # row = cursor.fetchone()
        # while row:
        #     print (str(row[0]) + " " + str(row[1]))
        #     row = cursor.fetchone()

# ------------- CREATE TABLE (decomment to use) -------------------------------
		cursor.execute("""
			CREATE TABLE Users_info(
			user_id INT NOT NULL,
			name VARCHAR(25),
			surname VARCHAR(25),
			address VARCHAR(50),
			postal INT,
			city VARCHAR(25),
			phone INT,
			birth DATE,
			company VARCHAR(25)
			)""")
		conn.commit()