# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11.3-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install git
RUN apt-get update \
&& apt install -y git \
&& apt-get clean 

# Copy local code to the container image
WORKDIR /src
COPY ./src/awsLambda awsLambda
COPY ./src/common common

# Install pip requirements
RUN python -m pip install -r common/requirements.txt
RUN python -m pip install -r awsLambda/requirements.txt

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /src
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD ["python", "awsLambda/views/main.py"]
