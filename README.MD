## TEST TASK

## Yahoo API
Object of this task is to create a REST API service, which will deliver data with companies trade info. Source of the data for API is Yahoo Finance service.

## Set up and run project:

First, you should configure your database url and redis host name.

In ```config.py``` you should set ```database_url``` and ```redis_host``` variables(by default set for running app using Docker).

If you are not going to run the application with Docker you should change those variables from ```docker``` to ```local```.

### Using Docker
You should change your working directory to 'test_yahoo' and run command:
```
docker-compose up
```

### Without Docker

You should change your work directory to 'test_yahoo', activate your virtual environment(if you are using it) and run commands:
```
pip install -r req.txt
uvicorn db.main:app --reload
```
After all you will be able to make requests to API. All available endpoints you can find at ```/docs```. 

You can also visit index page in your browser ```/``` and run some test examples with simple UI.


