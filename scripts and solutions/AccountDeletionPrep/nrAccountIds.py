import requests
import csv

def get_account_ids(api_key):
    headers = {
        'API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    query = '''
    {
      actor {
        organization {
          accountManagement {
            managedAccounts {
              name
              id
              regionCode
              isCanceled
            }
          }
        }
      }
    }
    '''
    
    url = 'https://api.newrelic.com/graphql'
    try:
        response = requests.post(url, json={'query': query}, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print("Error making API request:", e)
        return [], None
    
    if response.status_code == 200:
        data = response.json()
        try:
            accounts = data['data']['actor']['organization']['accountManagement']['managedAccounts']
            filtered_accounts = [(account['id'], account['regionCode']) for account in accounts if not account.get('isCanceled')]
            region_codes = set(account[1] for account in filtered_accounts)
            return filtered_accounts, region_codes
        except KeyError:
            print("Unexpected response format.")
            return [], None
    else:
        print("Unexpected response status code:", response.status_code)
        return [], None

def write_to_csv(account_ids, filename, target_region):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for account_id, region_code in account_ids:
            if region_code == target_region:
                writer.writerow([account_id])

if __name__ == '__main__':
    # Prompt user for API key
    api_key = input("Enter your New Relic API key: ")
    
    # Get account IDs
    account_ids, region_codes = get_account_ids(api_key)
    
    if account_ids:
        for region_code in region_codes:
            # Determine filename based on region codes
            filename = f'account_ids_{region_code}.csv'
            # Write account IDs to CSV for the specific region
            write_to_csv(account_ids, filename, region_code)
            print(f"Account IDs for region {region_code} successfully saved to {filename}")
    else:
        print("No active account IDs found. Check your API key and try again.")
