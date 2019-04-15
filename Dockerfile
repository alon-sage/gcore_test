FROM python:3.6

ENV PYTHONBUFERED 1

COPY docker_entrypoint.sh /
RUN chmod +x /docker_entrypoint.sh

WORKDIR /code

RUN pip install pipenv
RUN pipenv --python 3.6
COPY Pipfile Pipfile.lock /code/
RUN pipenv install --deploy --system

COPY . /code/

RUN ./manage.py collectstatic

EXPOSE 80/tcp

ENTRYPOINT ["/docker_entrypoint.sh"]
CMD ["gunicorn", "ticket_api.wsgi", "--log-file", "-"]