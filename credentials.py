import json
import os

with open(os.path.dirname(__file__) + '/credentials.json', 'r') as f:
    credentials = json.load(f)
