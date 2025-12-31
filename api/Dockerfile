
FROM python:3.11-slim-bookworm
# Set environment variables
ENV DOCKER_RUNNING=true

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN mkdir /api 

WORKDIR /api
# Install required library libmysqlclient (and build-essential for building mysqlclient python extension)

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

# Copy and install dependencies
COPY requirements.txt /api/requirements.txt
RUN pip install --no-cache-dir -r /api/requirements.txt
#added here
COPY . /api


#EXPOSE 8000

#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
#added something