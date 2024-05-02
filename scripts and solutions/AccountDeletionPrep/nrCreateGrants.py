import requests
import csv

def execute_api_mutation(api_key, account_id, group_id):
    endpoint = "https://api.newrelic.com/graphql"

    # Convert account_id to integer
    account_id = int(account_id)

    mutation = """
    mutation {
      authorizationManagementGrantAccess(
        grantAccessOptions: {
          groupId: "%s"
          accountAccessGrants: {
            accountId: %d
            roleId: "1254"
          }
        }
      ) {
        roles {
          displayName
          accountId
        }
      }
    }
    """ % (group_id, account_id)

    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }

    try:
        response = requests.post(endpoint, json={"query": mutation}, headers=headers)
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            print(f"Error occurred for account ID: {account_id}")
            print("Error message:", data["errors"][0]["message"])
        else:
            print(f"Access granted for account ID: {account_id}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to grant access for account ID: {account_id}")
        print("Error:", str(e))

def create_group(api_key, auth_domain_id):
    endpoint = "https://api.newrelic.com/graphql"

    mutation = """
    mutation {
      userManagementCreateGroup(
        createGroupOptions: {
          authenticationDomainId: "%s"
          displayName: "NrDeletionGroup"
        }
      ) {
        group {
          displayName
          id
        }
      }
    }
    """ % auth_domain_id

    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }

    try:
        response = requests.post(endpoint, json={"query": mutation}, headers=headers)
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            print("Error occurred while creating group:")
            print("Error message:", data["errors"][0]["message"])
            return None
        else:
            group_id = data["data"]["userManagementCreateGroup"]["group"]["id"]
            print("Group created successfully.")
            return group_id
    except requests.exceptions.RequestException as e:
        print("Failed to create group.")
        print("Error:", str(e))
        return None

def get_default_auth_domain_id(api_key):
    endpoint = "https://api.newrelic.com/graphql"

    query = """
    {
      actor {
        organization {
          authorizationManagement {
            authenticationDomains {
              authenticationDomains {
                id
                name
              }
            }
          }
        }
      }
    }
    """

    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }

    try:
        response = requests.post(endpoint, json={"query": query}, headers=headers)
        response.raise_for_status()

        data = response.json()
        auth_domains = data["data"]["actor"]["organization"]["authorizationManagement"]["authenticationDomains"]["authenticationDomains"]
        default_auth_domain_id = None
        for auth_domain in auth_domains:
            if auth_domain["name"] == "Default":
                default_auth_domain_id = auth_domain["id"]
                break
        return default_auth_domain_id
    except requests.exceptions.RequestException as e:
        print("Failed to fetch default authentication domain ID.")
        print("Error:", str(e))
        return None

def main():
    api_key = input("Enter your New Relic API key: ")

    # Get default authentication domain ID
    auth_domain_id = get_default_auth_domain_id(api_key)
    if not auth_domain_id:
        print("Failed to get default authentication domain ID. Exiting.")
        return

    # Create group
    group_id = create_group(api_key, auth_domain_id)
    if not group_id:
        print("Failed to create group. Exiting.")
        return

    csv_file_path = input("Enter the path to the CSV file: ")

    try:
        with open(csv_file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row if exists
            for row in reader:
                account_id = row[0]  # Assuming the account ID is in the first column
                execute_api_mutation(api_key, account_id, group_id)
    except FileNotFoundError:
        print("Error: CSV file not found.")
    except IndexError:
        print("Error: CSV file is empty or malformed.")

if __name__ == "__main__":
    main()
