import csv
import requests

# Function to run the NerdGraph query
def run_nerdgraph_query(query, api_key):
    headers = {
        'Content-Type': 'application/json',
        'API-Key': api_key
    }
    response = requests.post('https://api.newrelic.com/graphql', headers=headers, json={'query': query})
    return response.json()

# Function to run the NerdGraph mutation
def run_nerdgraph_mutation(mutation, api_key):
    headers = {
        'Content-Type': 'application/json',
        'API-Key': api_key
    }
    response = requests.post('https://api.newrelic.com/graphql', headers=headers, json={'query': mutation})
    return response.json()

# Get the user's API key
api_key = input("Please enter your New Relic API key: ")

# Get the CSV file of account IDs
csv_file = input("Please enter the path to the CSV file with account IDs: ")

# Read the account IDs from the CSV file
account_ids = []
with open(csv_file, 'r') as file:
    reader = csv.reader(file)
    # next(reader)  # Skip the header row
    for row in reader:
        account_ids.append(int(row[0]))

# Loop through each account ID and run the NerdGraph queries and mutations
for account_id in account_ids:
    print(f"\nProcessing account ID: {account_id}")

    # Run the NerdGraph query
    query = """
    {
      actor {
        account(id: %d) {
          aiNotifications {
            destinations {
              entities {
                id
              }
            }
          }
        }
      }
    }
    """ % account_id
    response = run_nerdgraph_query(query, api_key)

    # Process the response and run the NerdGraph mutation
    if 'data' in response and response['data']['actor']['account']:
        destinations = response['data']['actor']['account']['aiNotifications']['destinations']['entities']
        if destinations:
            for destination in destinations:
                destination_id = destination['id']
                mutation = """
                mutation {
                  aiNotificationsDeleteDestination(
                    accountId: %d
                    destinationId: "%s"
                  ) {
                    ids
                    error {
                      details
                    }
                  }
                }
                """ % (account_id, destination_id)
                mutation_response = run_nerdgraph_mutation(mutation, api_key)
                if 'errors' in mutation_response:
                    print(f"Error deleting destination {destination_id}: {mutation_response['errors'][0]['message']}")
                else:
                    print(f"Successfully deleted destination {destination_id}")
        else:
            print("No AI notification destinations found.")
    else:
        print(f"No data found for account ID {account_id} or access denied.")
