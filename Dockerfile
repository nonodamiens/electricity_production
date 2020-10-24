FROM python

COPY . /app
WORKDIR /app

# odbc driver install
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
	&& curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
	&& apt-get update \
	&& ACCEPT_EULA=Y apt-get install msodbcsql17 -y

# pyodbc necessary libs install
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    unixodbc \
    libpq-dev

# statsmodels necessary libs
RUN apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran -y 

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "electricity.py" ]