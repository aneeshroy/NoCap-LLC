import string
from flask import Flask, request, send_file
import redis
import json
import csv
import logging
from jobs import rd, q, add_job, get_job_by_id, hdb
from uuid import uuid4

app = Flask(__name__)

@app.route('/load_data', methods=['POST'])
def data():

    """
    This loads the csv file into the redis database

    Returns:

        A string indicating the data was committed to the redis database
    """
    global crypto_news

    logging.info("loading files into redis")

    rd.flushdb
    
    with open('crypto_news_api.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            article = dict(row)
            del article["news_url"]
            del article["image_url"]
            del article["type"]
            rd.set(article["title"], article)

    return "data loaded into database\n"


@app.route('/help', methods=['GET'])
def help():
    '''
    A route that gives all available routes to take in the application

    Returns:
        String defining all routes available
    '''
    logging.info("printing instructions")

    output = "/help - (GET) - output these instructions"
    output += "\n/load_data - (POST) -  loads data into the Redis database"
    output += "\n/topics - (GET) -  Returns all topics available in dataset"
    output += "\n/topics/<topic> - (GET) -  Returns all article titles about <topic>, "
    output += "\n/sentiment - (GET) - Returns how to get a graph indicating the sentiment (starting at neutral) over time for different parameters"
    output += "\n/sources - (GET) - Returns all sources available in dataset"
    output += "\\n/sources/<source> - (GET) - Returns all article titles from <source> "
    output += "\n/sources/<source>/sentiment - (GET) - Returns the overall sentiments from a specific source in total percentage"
    output += "\n/sources/<source>/remove - (DELETE) - Deletes all articles from a specific source"
    output += "\n/<article-title> - (GET) - Returns all of the information about an article"
    output += "\n/update_info - (GET) - Returns how to update an article"
    output += "\n/create_info - (GET) - Returns how to create an article"

    return output


@app.route('/jobs', methods=['POST'])
def jobs_api():
    """
    API route for creating a new job for sentiment analysiss

    Returns:
        JSON string indicating job has been queued.
    """

    try:
        job = request.get_json(force=True)
    except Exception as e:
        return json.dumps({'status': "Error", 'message': 'Invalid JSON: {}.'.format(e)})

    return json.dumps(add_job(job['parameter'],job['value']), indent = 1) + '\n'


@app.route('/jobs/<job_uuid>', methods=['GET'])
def job_status(job_uuid: str):
    """
    Checks the status of a given job 

    Args:
        job_uuid: job UUID

    Returns:
        JSON string of the job status
    """

    return json.dumps(get_job_by_id(job_uuid), indent = 1) + '\n'


@app.route('/job_list', methods=['GET'])
def get_job_list():
    """
    Gives list of jobs that have happened in the app.

    Returns:
        JSON string of job list

    """

    logging.info('listing jobs')

    job_list = []
    for item in rd.keys():
        if " " in item:
            continue
        job_list.append(rd.hgetall(item))

    return json.dumps(job_list, indent = 1)


@app.route('/download/<jobid>', methods=['GET'])
def download(jobid: str):

    """
    Downloads png file of line graph from a specific job.

    Args:
        jobid: job ID

    Returns:
        PNG file of graph
    """
    path = f'/app/{jobid}.png'
    with open(path, 'wb') as f:
        f.write(hdb.get(jobid))
    return send_file(path, mimetype='image/png', as_attachment=True)



@app.route('/topics', methods=['GET'])
def topics():

    """
    Returns a list of all of the topics in the dataset.

    Returns:
        List containing all of the topics from the CSV file
    """

    logging.info("getting topics")

    topics = []
    for i in rd.keys():
        topics.extend(rd.get(i)["topics"])

    unique_topics = list(set(topics))

    return json.dumps(unique_topics, indent = 1)

    
@app.route('topics/<topic>', methods=['GET'])
def topic_info(topic: str):

    """
    Gives all of the article titles pertaining to a certain topic

    Args:
        topic: name of specific topic

    Returns:
        titles: JSON string containing all article titles for that topic
    """

    logging.info("getting titles for " + topic)

    titles = []
    for i in rd.keys():
        if topic in rd.get(i)["topics"]:
            titles.append(rd.get(i)["title"])

    return json.dumps(titles, indent = 1)


@app.route('/sentiment', methods=['GET'])
def how_sentiment():
    """
    Info route for sending a job

    Returns: String dictating how to file a job for the database

    """

    return """
    This job wil generate a line graph showing the sentiment analysis for a parameter you select.

    to submit, send

    curl localhost:5000/jobs -X POST  -H "Content-Type: application/json" -d '{"param": "<VALUE>", "value": "<VALUE>"}'

    replace <VALUE> with your input.

    options:
    param: can be "topic", "source", or "ticker" (ticker)
    value: the string for the prior parameter (BTC)
    """

@app.route('/sources', methods=['GET'])
def sources():
       
    """
    Lists the sources of the news in the dataset

    Returns:
        JSON string containing all of the sources from the CSV file
    """

    logging.info("getting sources")

    sources = []
    for i in rd.keys():
        sources.append(rd.get(i)["source_name"])

    unique_sources = list(set(sources))

    return json.dumps(unique_sources, indent = 1)


@app.route('/sources/<source>', methods=['GET'])
def source_info(source: str):

    """
    Gives all of the article titles from a certain source

    Args:
        source: name of specific source

    Returns:
        titles: JSON string containing all article titles for that source
    """

    logging.info("getting titles for " + source)

    titles = []
    for i in rd.keys():
        if rd.get(i)["source_name"] == source:
            titles.append(rd.get(i)["title"])

    return json.dumps(titles, indent = 1)


@app.route('/sources/<source>/sentiment', methods=['GET'])
def source_sentiment(source: str):

    """
    Gives percentages of a source and its overall crypto sentiment

    Args:
        source: name of the source

    Returns:
        percentages: JSON string containing percentages for that sentiment
    """

    logging.info("getting sentiment for " + source)

    percentages = {"Positive": 0.0, "Negative": 0.0, "Neutral": 0.0}
    for i in rd.keys():
        if rd.get(i)["source_name"] == source:
            if rd.get(i)["sentiment"] == "Positive":
                percentages['Positive'] += 1
            if rd.get(i)["sentiment"] == "Negative":
                percentages['Negative'] += 1
            if rd.get(i)["sentiment"] == "Neutral":
                percentages['Neutral'] += 1
    
    total += percentages['Negative'] + percentages['Neutral'] + percentages['Positive']

    percentages['Negative'] = percentages['Negative']/total * 100
    percentages['Neutral'] = percentages['Neutral']/total * 100
    percentages['Positive'] = percentages['Positive']/total * 100

    return json.dumps(percentages, indent = 1)

@app.route('/sources/<source>/remove', methods=['DELETE'])
def remove_source(source: str):

    """
    Removes all articles from a specific source

    Args:
        source: name of source being removed

    Returns:
        String indicating completion
    """

    logging.info("deleting articles from " + source)

    for i in rd.keys():
        if rd.get(i)["source_name"] == source:
            rd.DEL(i)

    return "source removed"

@app.route('/<article-title>', methods=['GET'])
def article(title: str):

    """
    Returns all info about a specific article, through its title

    Args:
        title: string of the title from database

    Returns:
        JSON string containing everything from the article
    """

    return json.dumps(rd.get(title), indent = 1)

@app.route('/update_info', methods=['GET'])
def update_info():
  
    """
    Shows how to use the update route to update an article in the dataset.
    
    Returns:
        string explaining the format needed
    """
    return """
    How to use /update
    
    The command looks like
    
    /title/<article-title>/update/<parameter>/<value>
    
    replace with your input.

    What the inputs can be:
    article-title: string title from the dataset
    parameter: any valid parameter from the set
    value: value for the parameter you want to change

    Please check /create-info to see what parameters there are, and the formatting for their values.
    """


@app.route('/title/<article-title>/update/<parameter>/<value>', methods=['GET'])
def article_update(title: str, param: str, value: str):

    """
    Updates an article in the database.

    Args:
        title: title of the article
        param: field being changed
        value: new data
    
    Returns:
        String denoting update completion
    """

    updated = rd.get(title)
    
    if param == "Topics":
        values = string.split(value)
        updated[param] = values
        rd.set(title, updated)
        return "updated"

    updated[param] = value
    rd.set(title, updated)
    return "updated"

@app.route('/create_info', methods=['GET'])
def create_info():
    
    """
    Shows how to use the create route to get the desired data input.
    
    Returns:
        string explaining the format needed
    """
    return """
    How to use /create
    
    The command looks like
    
    /create/new_entry -X POST -H "Content-Type: application/json"  -d '{"title": "VALUE", "text": "VALUE", "source_name": "VALUE", "date": "VALUE", "topics": "VALUE", "sentiment": "VALUE"}'
    
    replace VALUE with your input.

    What the inputs can be:
    title: string title ("Crypto Boomer Hedges Millions")
    text: string text ("A lifetime trader...making money.")
    source_name: string source ("Coindesk")
    date: date format ("Mon, 18 Apr 2022 17:33:06 -0400")
    topics: topics separate by space ("Bitcoin Altcoin Mining")
    Sentiment: Can be positive, negative, or neutral ("Neutral")
    """


@app.route('/create', methods=['POST'])
def create_article():
    """
    creates article with user input.
    
    Input:
        VALUE: the specific value for each field which the user is creating in the new data entry.
    Returns:
        a confirmation of the addition.
    """
    
    temp_data = json.loads(rd.get('articles'))

    try:
        params = request.get_json(force=True)
    except Exception as e:
        return json.dumps({'status': "Error", 'message': 'Invalid JSON: {}.'.format(e)})
    
    try:
        title = params['title']
        text = params['text']
        source = params['source_name']
        date = params['date']
        topics = params['topics']
        sentiment = params['sentiment']

    except Exception as e:
        return "Please check your formatting for the input. Check /"

    data_new = {}

    data_new['title'] = title
    data_new['text'] = text
    data_new['source_name'] = source
    data_new['date'] = date
    data_new['topics'] = string.split(topics)
    data_new['sentiment'] = sentiment
    data_new['tickers'] = []

    temp_data['vehicle_emissions'].append(data_new)
    rd.set('vehicle_emissions', json.dumps(temp_data))
    
    return "article created."

if __name__ == "__main__":

    crypto_news = {}
    crypto_news["articles"] = []

    with open('crypto_news_api.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            article = dict(row)
            del article["news_url"]
            del article["image_url"]
            crypto_news['articles'].append(article)

    for i in crypto_news['articles'] :
        print(i["type"])

   #app.run(debug = True, host = '0.0.0.0')