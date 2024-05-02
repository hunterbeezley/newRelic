import csv
import json
import requests

# Replace with your New Relic user key
API_KEY = 'api_key_here'

# GraphQL endpoint
ENDPOINT = 'https://api.newrelic.com/graphql'

# GraphQL mutation template
MUTATION_TEMPLATE = '''
mutation {{
  changeTrackingCreateDeployment(
    deployment: {{ version: "0.0.1", entityGuid: "{}" }}
  ) {{
    deploymentId
    entityGuid
  }}
}}
'''

def execute_graphql_mutation(guid):
    mutation_query = MUTATION_TEMPLATE.format(guid)
    payload = {
        'query': mutation_query
    }
    headers = {
        'Content-Type': 'application/json',
        'API-Key': API_KEY
    }
    response = requests.post(ENDPOINT, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        print(f'Successfully executed mutation for GUID: {guid}')
        print('Response:', response_json)
    else:
        print(f'Failed to execute mutation for GUID: {guid}')
        print('Status Code:', response.status_code)
        print('Response:', response.text)

# Replace with the path to your CSV file
CSV_FILE_PATH = 'Path_here'

# Read GUIDs from CSV and execute GraphQL mutations
with open(CSV_FILE_PATH, 'r') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) > 0:
            guid = row[0]
            execute_graphql_mutation(guid)
