import requests
import csv

def get_api_key():
    # Prompt the user to enter their API key
    return input("Please enter your API key: ")

def get_csv_path():
    # Prompt the user to enter the path to the CSV file containing account IDs
    return input("Please enter the path to the CSV file containing account IDs: ")

def read_csv(csv_path):
    # Read the CSV file and extract the account IDs
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        account_ids = [row[0] for row in reader]
    return account_ids

def run_query(api_key, account_id):
    # Construct and execute the GraphQL query to retrieve policies for a given account
    headers = {'Api-Key': api_key}
    query = '''
    {
      actor {
        account(id: %s) {
          alerts {
            policiesSearch {
              policies {
                id
                name
                incidentPreference
              }
            }
          }
        }
      }
    }
    ''' % account_id

    response = requests.post('https://api.newrelic.com/graphql', json={'query': query}, headers=headers)
    return response.json()

def run_mutation(api_key, account_id, policy_id):
    # Construct and execute the GraphQL mutation to delete a policy
    headers = {'Api-Key': api_key}
    mutation = '''
    mutation {
      alertsPolicyDelete(accountId: %s, id: "%s") {
        id
      }
    }
    ''' % (account_id, policy_id)

    response = requests.post('https://api.newrelic.com/graphql', json={'query': mutation}, headers=headers)
    return response.json()

def main():
    # Main function to orchestrate the process
    api_key = get_api_key()
    csv_path = get_csv_path()
    account_ids = read_csv(csv_path)

    # Iterate through each account ID
    for account_id in account_ids:
        # Retrieve policies for the current account
        query_response = run_query(api_key, account_id)
        
        # Check for errors in the response
        if 'errors' in query_response:
            print(f"Error occurred for account {account_id}: {query_response['errors'][0]['message']}")
            continue

        # Extract policies from the response
        try:
            policies = query_response['data']['actor']['account']['alerts']['policiesSearch']['policies']
            print("Policies:", policies)  # Debugging

            # Iterate through each policy and delete it
            for policy in policies:
                policy_id = policy['id']
                mutation_response = run_mutation(api_key, account_id, policy_id)
                print(f"Deleted policy with ID {policy_id} in account {account_id}")
        except KeyError:
            print(f"No policies found in account {account_id}")

if __name__ == "__main__":
    main()
