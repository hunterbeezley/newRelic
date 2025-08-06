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
          displayName: "NrGlobalAdmin"
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

# NEW FUNCTION
def get_all_account_ids(api_key, org_id):
    endpoint = "https://api.newrelic.com/graphql"

    query = """
    {
      customerAdministration {
        accounts(filter: {organizationId: {eq: "%s"}, status: {eq: ACTIVE}}) {
          items {
            id
          }
        }
      }
    }
    """ % org_id

    headers = {
        "Content-Type": "application/json",
        "Api-Key": api_key
    }

    try:
        response = requests.post(endpoint, json={"query": query}, headers=headers)
        response.raise_for_status()

        data = response.json()
        account_ids = [item["id"] for item in data["data"]["customerAdministration"]["accounts"]["items"]]
        print(f"Fetched {len(account_ids)} active accounts.")
        return account_ids
    except requests.exceptions.RequestException as e:
        print("Failed to fetch account IDs.")
        print("Error:", str(e))
        return None

def main():
    api_key = input("Enter your New Relic API key: ")
    org_id = input("Enter your New Relic Organization ID: ")

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

    # Get all account IDs for the organization
    account_ids = get_all_account_ids(api_key, org_id)
    if not account_ids:
        print("Failed to get account IDs. Exiting.")
        return

    # Process each account ID
    for account_id in account_ids:
        execute_api_mutation(api_key, account_id, group_id)

if __name__ == "__main__":
    main()
