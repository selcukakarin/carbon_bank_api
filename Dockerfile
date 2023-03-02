FROM python:3

ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY . /code/
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["gunicorn","--chdir","carbon_bank","--bind",":8000","carbon_bank.wsgi:application","--reload"]
