import json
import os
from uuid import uuid4
from flask import Flask, request
import redis
from hotqueue import HotQueue


redis_ip = "127.0.0.1"

rd = redis.Redis(host=redis_ip, port=6379, db=0, decode_responses=True)
q = HotQueue("queue", host=redis_ip, port=6379, db=1)
hdb = redis.Redis(host=redis_ip, port=6379, db=2)

def _generate_jid():
    """
    Generate a pseudo-random identifier for a job.
    """

    return str(uuid4())

def _generate_job_key(jid):
    """
    Generate the redis key from the job id to be used when storing, retrieving or updating
    a job in the database.
    """

    return 'job.{}'.format(jid)

def _instantiate_job(jid, status, parameter, value):
    """
    Create the job object description as a python dictionary. Requires the job id, status,
    parameter, and value.
    """

    if type(jid) == str:
        return {
                'id': jid,
                'status': status,
                'parameter': parameter,
                'value': value,
               }
    return {
            'id': jid.decode('utf-8'),
            'status': status.decode('utf-8'),
            'parameter': parameter.decode('utf-8'),
            'value': value.decode('utf-8'),
           }

def _save_job(job_key, job_dict):
    """
    Save a job object in the Redis database.
    """

    rd.hset(job_key, mapping=job_dict)
    return

def _queue_job(jid):
    """
    Add a job to the redis queue.
    """

    q.put(jid)
    return

def add_job(parameter, value, status='submitted'):
    """
    Add a job to the redis queue.
    """

    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, parameter, value)
    _save_job(_generate_job_key(jid), job_dict)
    _queue_job(jid)
    return job_dict

def get_job_by_id(jid):
    """
    Returns the job dictionary from ID
    """

    return (rd.hgetall(_generate_job_key(jid).encode('utf-8')))

def update_job_status(jid, status):
    """
    Update the status of job with job id `jid` to status `status`.
    """

    job = get_job_by_id(jid)
    if job:
        job['status'] = status
        _save_job(_generate_job_key(jid), job)

    else:
        raise Exception()
