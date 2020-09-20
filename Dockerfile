FROM python:3.8.1-slim-buster

COPY requirements.txt /

# install the libs we need to run the app
RUN pip install -r /requirements.txt

# copy all the files and change the working directory
COPY . /
WORKDIR /

EXPOSE 80
CMD ["python", "-m", "flask", "run", "-h", "0.0.0.0", "-p", "80"]
