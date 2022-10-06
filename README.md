# Crypto Critic: Analyzing Sentiments and Predictions Through News Aggregation

## Description

This project was created to help analyze the crazy world of crypto today. The goal of this project was to develop a sentiment analysis application through the crypto news cycle, to determine different currencies, projects, and possibly areas of improvement in the industry. The dataset of crypto news articles and the analysis methods highlighted later in this paper aim to accomplish this. This Flask Application combines the functionality of simple Python functions with the distribution and availability of a Docker container, so that the application may be used anywhere and by anyone. The data is stored in a continually updating Redis Database as well to ensure data security and containerized options.

## Files

The application is made up of 7 separate files, not including the datasets. They are `flask_api.py`, `test_api.py`, `job.py`, `worker.py`, `Dockerfile.api`, `Dockerfile.wrk`, and `Makefile`. `flask_api.py` makes up the heart of the program, as it holds the routes that organize, splice, and analyze the data into an accessible format through the different Flask routes. Flask itself is a microframework that can be used to develop APIs and microservices for general use. Decorating regular python functions gives them the power to be used in Flask applications, as it gives each route a unique URL ID. there are many different routes that are available to a user when the app is running.

### flask_api.py

This is the main python file that houses all of the code functions to run the api. It includes the functions for reading and writing into the database and inputting it into the Airtable files that we use to communicate with the frontend. The sentiment algorithm for calculating 

## Instructions

Clone this repository onto your local machine. Make sure that you are in the same directory as your files, and run the main file with

```
python3 flask_api.py
```

Additionally, you can run the Dockerfile to build you own image of the application and containerize it. 

```
docker build 
```

Once running, the redis server and the Flask server should be up and running. Instructions for each command is available in the file through

```
$ curl localhost:5000/help
```

The first command after that should be to load the data, through

```
$ curl localhost:5000/read-data -X POST
```
## Citations

(2022, April 19). Crypto News Recent. Kaggle. LFSCHMID.
www.kaggle.com/datasets/lukasschmidt/crypto-news-recent
