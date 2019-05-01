import json
import sys
from urllib.request import urlopen

HEALTHY = 'healthy'
url = 'http://airflow_webserver:8080/health'

response = urlopen(url)
if response.status != 200:
    sys.exit(1)

data = json.loads(response.read())
if data['metadatabase']['status'] != HEALTHY:
    sys.exit(1)
if data['scheduler']['status'] != HEALTHY:
    sys.exit(1)

sys.exit(0)
