FROM python

COPY . /app
WORKDIR /app

# odbc driver install
RUN apt-get update && apt-get upgrade \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install msodbcsql17 -y

# pyodbc l=necessary libs install
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    unixodbc \
    libpq-dev

RUN pip install --no-cache-dir -r requirements.txt

ENV SERVER=<host_name>
ENV DB=<db_name>
ENV SUPERADMIN=<superadmin_name>
ENV PWD=<password>
ENV KEY=<key_value>

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "electricity.py" ]