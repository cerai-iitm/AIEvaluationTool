FROM python:3.12-slim

RUN mkdir -p /usr/src/app/lib/utils

COPY requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

# logger.py is hard-link to the logger.py in the utils directory
COPY logger.py /usr/src/app/lib/utils/
COPY main.py /usr/src/app/
COPY translator.py /usr/src/app/
COPY generator.py /usr/src/app/

EXPOSE 8000

CMD ["python3", "/usr/src/app/main.py"]

