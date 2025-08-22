#!/usr/bin/env python3
"""
A script to easily and cleanly fetch all parent accounts within an org. 
This script...
* queries all accounts in an org
* filters to show us only the accounts that have a parent account
* cleanly/clearly displays each accountId/ParentId
* also lists account Ids that have parent accounts as comma-seperated 
* asks to export to a CSV
* supports large orgs bby utilizing next cursor

This was developed as a proof of concept for large customer organizations

This script is EXPERIMENTAL meaning it is not garunteed to work (or be accurate 100% of the time) and comes with no expectations for ongoing maintence or support. 
This merely illustrates what is possible, though it is a working expample.
"""

import requests
import json
import sys
import csv
from datetime import datetime
from typing import List, Dict, Optional, Tuple


def get_user_input() -> Tuple[str, str]:
    """
    Get API key and Organization ID from user input.
    
    Returns:
        Tuple of (api_key, organization_id)
    """
    print("\nPlease provide your New Relic credentials:")
    print("-" * 40)
    
    api_key = input("Enter your New Relic User API Key: ").strip()
    if not api_key:
        print("Error: API Key is required")
        raise ValueError("API Key is required")
    
    org_id = input("Enter your Organization ID: ").strip()
    if not org_id:
        print("Error: Organization ID is required")
        raise ValueError("Organization ID is required")
    
    return api_key, org_id


def build_graphql_query(org_id: str, cursor: Optional[str] = None) -> str:
    """
    Build the GraphQL query for fetching accounts.
    
    Args:
        org_id: Organization ID
        cursor: Optional cursor for pagination
    
    Returns:
        GraphQL query string
    """
    cursor_param = f', cursor: "{cursor}"' if cursor else ""
    
    query = f"""{{
  customerAdministration {{
    accounts(
      filter: {{organizationId: {{eq: "{org_id}"}}}}
      {cursor_param}
    ) {{
      items {{
        id
        name
        parentId
        regionCode
        status
      }}
      nextCursor
    }}
  }}
}}"""
    
    return query


def execute_graphql_query(api_key: str, query: str) -> Dict:
    """
    Execute a GraphQL query against New Relic API.
    
    Args:
        api_key: New Relic User API Key
        query: GraphQL query string
    
    Returns:
        Response data as dictionary
    
    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If the response contains errors
    """
    url = "https://api.newrelic.com/graphql"
    
    headers = {
        'Content-Type': 'application/json',
        'API-Key': api_key
    }
    
    payload = {
        "query": query,
        "variables": ""
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for GraphQL errors
        if 'errors' in data:
            error_msg = "GraphQL errors:\n" + "\n".join([error.get('message', str(error)) for error in data['errors']])
            raise ValueError(error_msg)
        
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        raise


def filter_accounts_with_parent_id(accounts: List[Dict]) -> List[Dict]:
    """
    Filter accounts to only include those with a parentId.
    
    Args:
        accounts: List of account dictionaries
    
    Returns:
        Filtered list of accounts that have a parentId
    """
    return [account for account in accounts if account.get('parentId') is not None]


def fetch_all_accounts_with_parent_id(api_key: str, org_id: str) -> List[Dict]:
    """
    Fetch all accounts with parentId, handling pagination.
    
    Args:
        api_key: New Relic User API Key
        org_id: Organization ID
    
    Returns:
        List of all accounts that have a parentId
    """
    all_accounts_with_parent = []
    cursor = None
    page_count = 0
    
    print(f"\nFetching accounts for organization: {org_id}")
    print("-" * 50)
    
    while True:
        page_count += 1
        print(f"Fetching page {page_count}{'with cursor: ' + cursor[:20] + '...' if cursor else ''}")
        
        try:
            # Build and execute query
            query = build_graphql_query(org_id, cursor)
            response_data = execute_graphql_query(api_key, query)
            
            # Extract accounts data
            accounts_data = response_data.get('data', {}).get('customerAdministration', {}).get('accounts', {})
            accounts = accounts_data.get('items', [])
            next_cursor = accounts_data.get('nextCursor')
            
            print(f"  Retrieved {len(accounts)} accounts")
            
            # Filter accounts with parentId
            accounts_with_parent = filter_accounts_with_parent_id(accounts)
            all_accounts_with_parent.extend(accounts_with_parent)
            
            print(f"  Found {len(accounts_with_parent)} accounts with parentId")
            
            # Check if we need to continue pagination
            if not next_cursor:
                print("  No more pages to fetch")
                break
            
            cursor = next_cursor
            
        except (ValueError, KeyError) as e:
            print(f"Error processing response: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return all_accounts_with_parent


def display_results(accounts: List[Dict]):
    """
    Display the filtered account results.
    
    Args:
        accounts: List of account dictionaries
    """
    print(f"\n{'='*60}")
    print(f"RESULTS: Found {len(accounts)} accounts with parentId")
    print(f"{'='*60}")
    
    if not accounts:
        print("No accounts found with parentId attribute.")
        return
    
    # Display summary
    print(f"\nAccount IDs with parentId:")
    print("-" * 30)
    
    for i, account in enumerate(accounts, 1):
        print(f"{i:3d}. Account ID: {account['id']}")
        print(f"     Name: {account.get('name', 'N/A')}")
        print(f"     Parent ID: {account.get('parentId', 'N/A')}")
        print(f"     Region: {account.get('regionCode', 'N/A')}")
        print(f"     Status: {account.get('status', 'N/A')}")
        print()
    
    # Display just the account IDs for easy copying
    print(f"Account IDs only:")
    print("-" * 20)
    account_ids = [str(account['id']) for account in accounts]
    print(", ".join(account_ids))


def export_to_csv(accounts: List[Dict], org_id: str) -> str:
    """
    Export accounts data to a CSV file.
    
    Args:
        accounts: List of account dictionaries
        org_id: Organization ID for filename
    
    Returns:
        Filename of the created CSV file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"newrelic_accounts_with_parent_{org_id}_{timestamp}.csv"
    
    fieldnames = ['id', 'name', 'parentId', 'regionCode', 'status']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for account in accounts:
                # Only write the fields we want to the CSV
                row = {field: account.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        return filename
    
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        raise


def get_yes_no_input(prompt: str) -> bool:
    """
    Get yes/no input from user.
    
    Args:
        prompt: The prompt to display to the user
    
    Returns:
        True for yes, False for no
    """
    while True:
        response = input(f"\n{prompt} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def handle_post_processing(accounts: List[Dict], org_id: str) -> bool:
    """
    Handle post-processing options: export to CSV and/or run again.
    
    Args:
        accounts: List of account dictionaries
        org_id: Organization ID
    
    Returns:
        True if user wants to run script again, False to exit
    """
    # Ask about CSV export
    if get_yes_no_input("Would you like to export these results to CSV?"):
        try:
            filename = export_to_csv(accounts, org_id)
            print(f"\nResults exported successfully to: {filename}")
        except Exception as e:
            print(f"Failed to export CSV: {e}")
    
    # Ask about running again
    return get_yes_no_input("Would you like to run this script again?")


def run_single_query() -> bool:
    """
    Run a single query cycle.
    
    Returns:
        True if user wants to run again, False to exit
    """
    try:
        # Get user input
        api_key, org_id = get_user_input()
        
        # Fetch all accounts with parentId
        accounts_with_parent = fetch_all_accounts_with_parent_id(api_key, org_id)
        
        # Display results
        display_results(accounts_with_parent)
        
        # Handle post-processing options
        run_again = handle_post_processing(accounts_with_parent, org_id)
        return run_again
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return False
    except ValueError as e:
        print(f"\nInput error: {e}")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return False


def main():
    """
    Main function to orchestrate the account querying process with loop support.
    """
    print("New Relic Account Query Tool")
    print("=" * 35)
    
    while True:
        run_again = run_single_query()
        
        if not run_again:
            print("\nThank you for using the New Relic Account Query Tool!")
            return  # Exit the function completely
        
        print("\n" + "="*60)
        print("STARTING NEW QUERY")
        print("="*60)
    """
    Main function to orchestrate the account querying process.
    """
    try:
        # Get user input
        api_key, org_id = get_user_input()
        
        # Fetch all accounts with parentId
        accounts_with_parent = fetch_all_accounts_with_parent_id(api_key, org_id)
        
        # Display results
        display_results(accounts_with_parent)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()