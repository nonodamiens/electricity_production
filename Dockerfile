FROM python:slim

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

# uncomment and fill credentials infos for use with Azure webapp services
# ENV COMPUTER_VISION_ENDPOINT=<azure_endpoint>
# ENV COMPUTER_VISION_SUBSCRIPTION_KEY=<azure_key>
# EXPOSE 5000

ENTRYPOINT [ "python" ]
CMD [ "electricity.py" ]