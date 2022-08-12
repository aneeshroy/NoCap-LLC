
import string
import pytest
import requests


api_host = 'localhost'
api_port = '5000'
api_prefix = f'http://{api_host}:{api_port}'


def test_help():
    route = f'{api_prefix}/info'
    response = requests.get(route)

    assert (response.ok) == True

    assert isinstance(response, string)

def test_load_data():
    route = f'{api_prefix}/load-data'
    response = requests.post(route)

    assert response.ok == True

    assert isinstance(response,string)


def test_topics():
    route = f'{api_prefix}/topics'
    
    response = requests.get(route)

    assert response.ok == True

    assert isinstance(response.json(), list) == True


def test_sentiment():
    route = f'{api_prefix}/sentiment'
    response = requests.get(route)

    assert response.ok == True

    assert isinstance(response, string) == True

def test_update_info():
    route = f'{api_prefix}/update_info'
    response = requests.get(route)

    assert response.ok == True

    assert isinstance(response, string) == True

def test_sources():
    route = f'{api_prefix}/sources'
    response = requests.get(route)

    assert response.ok == True

    assert isinstance(response, string) == True
