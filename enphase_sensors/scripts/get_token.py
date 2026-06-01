import json
import requests
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

user = config['account']['user']
password = config['account']['password']
envoy_serial = config['account']['envoy_serial']

enlighten_url = 'https://enlighten.enphaseenergy.com/login/login.json'
entrez_url = 'https://entrez.enphaseenergy.com/tokens'

data = {'user[email]': user, 'user[password]': password}

response = requests.post(enlighten_url, data=data)
response_data = json.loads(response.text)

data = {
        'session_id': response_data['session_id'], 
        'serial_num': envoy_serial, 
        'username': user}

response = requests.post(entrez_url, json=data)
token_raw = response.text
print(token_raw)

config['token']['access_token'] = token_raw

# save the access token
with open('config.yaml', 'w') as f:
    yaml.dump(config, f)
