import json
import sys
from urllib.request import urlopen

HEALTHY = 'healthy'
url = 'http://localhost:8080/health'

response = urlopen(url)
if response.status != 200:
    sys.exit('Airflow webserver is unhealthy')

data = json.loads(response.read())
database_status = data['metadatabase']['status']
scheduler_status = data['scheduler']['status']

if database_status == HEALTHY and scheduler_status == HEALTHY:
    sys.exit()

if database_status != HEALTHY:
    sys.exit('Airflow database connection is unhealthy')
if scheduler_status != HEALTHY:
    sys.exit('Airflow scheduler is unhealthy')
