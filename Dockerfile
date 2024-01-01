#From https://towardsdatascience.com/docker-for-python-dash-r-shiny-6097c8998506

# FROM python:3.9-slim-buster
# Use a base image that supports your application (e.g., Python, Debian, etc.)
FROM python:3.9

# Install ODBC Driver 17 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# set working directory in container
WORKDIR /usr/src/app

# Copy and install packages
COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

# Copy app folder to app folder in container
COPY /. /usr/src/app/

# Changing to non-root user
RUN useradd -m appUser
USER appUser
EXPOSE 8000
# Run locally
CMD gunicorn --bind 0.0.0.0:8000 app:server