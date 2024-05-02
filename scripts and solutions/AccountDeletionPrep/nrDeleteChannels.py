import requests
import csv

# Function to get New Relic API key from user input
def get_api_key():
    return input("Enter your New Relic API key: ")

# Function to read account IDs from a CSV file
def read_csv(file_path):
    account_ids = []
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            account_ids.append(int(row[0]))  # Assuming the first column contains the account IDs
    return account_ids

# Function to query channel IDs for a given account ID
def query_channel_ids(api_key, account_id):
    url = "https://api.newrelic.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }
    query = '''
    {
      actor {
        account(id: %d) {
          aiNotifications {
            channels(filters: {}) {
              entities {
                id
                name
              }
            }
          }
        }
      }
    }
    ''' % account_id

    response = requests.post(url, headers=headers, json={"query": query})
    
    if response.status_code != 200:
        print(f"Failed to query channels for account {account_id}. Status code: {response.status_code}")
        return None
    
    try:
        data = response.json()
        if data is None:
            print(f"Error: Received empty response for account {account_id}")
            return None
        
        actor_data = data.get('data', {}).get('actor', {})
        account_data = actor_data.get('account', {})
        ai_notifications_data = account_data.get('aiNotifications', {})
        channels_data = ai_notifications_data.get('channels', {}).get('entities', [])
        if not channels_data:
            print(f"No channels found for account {account_id}")
            return None
        return channels_data
    except Exception as e:
        print(f"Error processing response for account {account_id}: {e}")
        return None

# Function to delete channels for a given account ID
def delete_channels(api_key, account_id, channel_ids):
    if not channel_ids:
        print(f"No channels found for account {account_id}")
        return

    url = "https://api.newrelic.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }

    for channel_id in channel_ids:
        mutation = '''
        mutation {
          aiNotificationsDeleteChannel(
            accountId: %d
            channelId: "%s"
          ) {
            ids
            error {
              details
            }
          }
        }
        ''' % (account_id, channel_id['id'])

        response = requests.post(url, headers=headers, json={"query": mutation})
        data = response.json()
        if 'error' in data:
            print(f"Error deleting channel {channel_id['id']} for account {account_id}: {data['error']['details']}")
        else:
            print(f"Channel {channel_id['id']} deleted successfully for account {account_id}")

# Main function to orchestrate the process
def main():
    api_key = get_api_key()
    csv_file_path = input("Enter the path to the CSV file containing account IDs: ")
    account_ids = read_csv(csv_file_path)
    
    for account_id in account_ids:
        print(f"Processing account ID: {account_id}")
        channels = query_channel_ids(api_key, account_id)
        if channels is not None:
            delete_channels(api_key, account_id, channels)

if __name__ == "__main__":
    main()
