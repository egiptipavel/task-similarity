FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./web /code/web
COPY ./main.py /code

EXPOSE 8000
CMD ["python3", "main.py"]