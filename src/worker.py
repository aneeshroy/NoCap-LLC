from jobs import rd, q, hdb, add_job, get_job_by_id, update_job_status
import time
import matplotlib.pyplot as plt
import numpy as np
import os

@q.worker
def execute_job(jid):
    update_job_status(jid, 'in progress')

    data = rd.hgetall(f'job.{jid}')

    parameter = data["parameter"]
    value = data["value"]

    line = [0]
    counter = 0

    if parameter == "topic" or parameter == "ticker":
        for i in rd.keys():
            if value in rd.get(i)[parameter]:
                if rd.get(i)["sentiment"] == "Positive":
                    counter += 1
                    line.append(counter)
                elif rd.get(i)["sentiment"] == "Negative":
                    counter -= 1
                    line.append(counter)
                else:
                    line.append(counter)

    else:
        for i in rd.keys():
            if value == rd.get(i)[parameter]:
                if rd.get(i)["sentiment"] == "Positive":
                    counter += 1
                    line.append(counter)
                elif rd.get(i)["sentiment"] == "Negative":
                    counter -= 1
                    line.append(counter)
                else:
                    line.append(counter)

    line.reverse()
    for i in line:
        i -= line[0]
    
    plt.plot(len(line), line)
    title = "Sentiment for " + value + " Over Time"
    

    update_job_status(jid, 'complete')