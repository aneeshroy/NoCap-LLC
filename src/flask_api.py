import string
from turtle import title
import requests
from flask import Flask, request, send_file
import redis
import json
import csv
import logging
from jobs import rd, add_job, get_job_by_id, hdb


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
    
    url = "https://crypto-news16.p.rapidapi.com/news/all"

    headers = {
        "X-RapidAPI-Key": "c0f32eda55msh6e6142a38e758a8p104cc9jsn794b80ee3296",
        "X-RapidAPI-Host": "crypto-news16.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    return response


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
    output += "\n/topics/<topic> - (GET) -  Returns all article titles about <topic> "
    output += "\n/sentiment - (GET) - Returns how to get a graph indicating the sentiment (starting at neutral) over time for different parameters"
    output += "\n/sources - (GET) - Returns all sources available in dataset"
    output += "\\n/sources/<source> - (GET) - Returns all article titles from <source> "
    output += "\n/sources/<source>/sentiment - (GET) - Returns the overall sentiments from a specific source in total percentage"
    output += "\n/sources/<source>/remove - (DELETE) - Deletes all articles from a specific source"
    output += "\n/<article-title> - (GET) - Returns all of the information about an article"
    output += "\n/update_info - (GET) - Returns how to update an article"
    output += "\n/create_info - (GET) - Returns how to create an article"
    output += "/jobs - (POST) - submit job"
    output += "/jobs/<jobid> - (GET) - get info on job"
    output += "/job_list - (GET) - see all past and current jobs"
    output += "/download/<jobid> - (GET) - see plots from completed jobs"

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

# def flagger():
#     notification = ""

#     for i in 
    
    
@app.route('/topics/<topic>', methods=['GET'])
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

#@app.route('/title/<article-title>', methods=['GET'])
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


#@app.route('/title/<article-title>/update/<parameter>/<value>', methods=['GET'])
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

   #app.run(debug = True, host = '0.0.0.0')

    response = data()
    data = json.loads(response.text)

    hack_words = ['hack', 'breach', 'compromise', 'annoyance', 'stole', 'steal', 'attack', 'scam', 'lost', 'lose', 'bankrupt']
    protocols = ['maker', 'uniswap', 'aave', 'curve', 'convex finance', 'compound', 'instadapp', 'balancer', 'bancor', 'bancor-wip', 'liquity', 'alpha homora',
    'yearn.finance', 'dydx', 'tornadocash', 'nexus mutual', 'fei protocol', 'sushiswap', 'flexa', 'defi saver', 'olympus', 'xdai', 'notional finance', 'opyn',
    'index coop', 'sablier', 'lightning network', 'ribbon', 'set protocol', 'loopring', 'kyber', 'reflexer', 'origin dollar', 'b.protocol', 'mstable', 'badger dao',
    'idle finance', 'harvest finance', 'vesper', 'strike', 'defi swap', 'keep network', 'tbtc', 'o3 swap', 'metronome', 'deversifi', 'defidollar', 'saddle', 
    'c.r.e.a.m. finance', 'cream finance', 'dodo', 'truefi']
    exchanges = ['binance', 'coinbase', 'ftx','kraken', 'kucoin', 'binance.us', 'gate.io', 'bitfinex', 'huobi', 'huobi global', 'gemini', 'ftx us', 'bitstamp',
    'bitflyer', 'lbank' ,'crypto.com', 'coincheck', 'mexc', 'okx', 'coinone', 'bithumb', 'liquid', 'poloniex', 'xt.com', 'bitmex', 'bitrue', 'binance tr', 'bitmart',
    'blockchain.com', 'okcoin', 'upbit', 'zaif', 'korbit', 'bittrex', 'coinlist pro', 'whitebit', 'bigone', 'aax', 'btcex', 'bybit', 'probit', 'probit global',
    'ascendex', 'bitmax', 'coinw', 'hotcoin global', 'deepcoin', 'currency.com', 'bkex', 'digifinex', 'bitwell', 'fmfw.io']
    wallets = ['coinbase wallet', 'myetherwallet', 'trustwallet', 'zengo', 'stakedwallet.io', 'exodus', 'metamask', 'ambire wallet', 'electrum wallet', 'jaxx',
    'trezor wallet', 'coinomi', 'bitcoin core client', 'luno', 'bitgo cryptocurrency wallet', 'coinpayments wallet', 'blockchain.com' , 'xapo wallet', 'atomic wallet',
    'bitso', 'simplehold', 'bread wallet', 'crypterium', 'guarda wallet', 'mycelium wallet', 'coinjar wallet', 'counterwallet', 'cryptx wallet', 'kcash wallet', 'omniwallet',
    'usdx wallet', 'airbitz bitcoin wallet', 'copay', 'daedalus', 'imtoken', 'lumi wallet', 'wirex wallet', 'xeth ether wallet', 'armory wallet', 'block.io wallet',
    'carbon wallet', 'coins', 'crypto storage', 'crypvestor', 'fireblocks', 'indie square', 'infinito wallet', 'infinity wallet', 'parity', 'poolin wallet']

    protocol_articles = []
    negatives = []

    for i in data:
        for j in data[i]:
            for k in protocols:
                if k in j["description"]:
                    protocol_articles.append(j)


    for i in data:
        for j in data[i]:
            for k in hack_words:
                if k in j["description"]:
                    negatives.append(j)
    # for i in data:

    #     for j in hack_words:
    #         if j in i["description"]:
    #             negatives.append(i)

    # count = 0
    # for i in data:
    #     count += 1

    print(protocol_articles)





   