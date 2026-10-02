#!/usr/bin/env python3
"""
New Relic User Deletion Script
Safely deletes users via NerdGraph API with confirmation prompts and error handling.
"""

import json
import os
import sys
import requests
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class DeletionResult:
    """Store results of deletion operations"""
    user_id: str
    success: bool
    error_message: str = None


class NewRelicUserDeleter:
    """Handle New Relic user deletions via NerdGraph API"""
    
    NERDGRAPH_URL = "https://api.newrelic.com/graphql"
    
    def __init__(self, api_key: str):
        """Initialize with API key"""
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'API-Key': api_key
        }
    
    def load_user_ids(self, json_file_path: str) -> Set[str]:
        """
        Load and validate user IDs from JSON file.
        Returns a set of unique user IDs.
        """
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # If it's a list of user IDs
                user_ids = set(str(uid).strip() for uid in data if uid)
            elif isinstance(data, dict):
                # If it's a dict with a 'userIds' or 'users' key
                if 'userIds' in data:
                    user_ids = set(str(uid).strip() for uid in data['userIds'] if uid)
                elif 'users' in data:
                    user_ids = set(str(uid).strip() for uid in data['users'] if uid)
                elif 'userId' in data:
                    # Single user in dict
                    user_ids = {str(data['userId']).strip()}
                else:
                    # Assume keys are user IDs
                    user_ids = set(str(key).strip() for key in data.keys() if key)
            else:
                raise ValueError("Unsupported JSON format")
            
            # Filter out empty strings
            user_ids = {uid for uid in user_ids if uid}
            
            if not user_ids:
                raise ValueError("No valid user IDs found in JSON file")
            
            return user_ids
            
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def delete_user(self, user_id: str) -> DeletionResult:
        """
        Delete a single user via NerdGraph API.
        Returns DeletionResult with success status and any error message.
        """
        mutation = """
        mutation {
          userManagementDeleteUser(deleteUserOptions: {id: "%s"}) {
            deletedUser {
              id
            }
          }
        }
        """ % user_id
        
        payload = {
            "query": mutation,
            "variables": ""
        }
        
        try:
            response = requests.post(
                self.NERDGRAPH_URL,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check for GraphQL errors
            if 'errors' in result:
                error_msg = '; '.join([err.get('message', 'Unknown error') 
                                      for err in result['errors']])
                return DeletionResult(user_id, False, error_msg)
            
            # Check if deletion was successful
            if result.get('data', {}).get('userManagementDeleteUser', {}).get('deletedUser'):
                return DeletionResult(user_id, True)
            else:
                return DeletionResult(user_id, False, "No deleted user returned in response")
            
        except requests.exceptions.RequestException as e:
            return DeletionResult(user_id, False, f"Request failed: {str(e)}")
        except Exception as e:
            return DeletionResult(user_id, False, f"Unexpected error: {str(e)}")
    
    def delete_users_batch(self, user_ids: Set[str]) -> Dict[str, List[DeletionResult]]:
        """
        Delete multiple users and return results.
        Returns dict with 'successful' and 'failed' lists.
        """
        results = {
            'successful': [],
            'failed': []
        }
        
        total = len(user_ids)
        for idx, user_id in enumerate(user_ids, 1):
            print(f"Deleting user {idx}/{total}: {user_id}...", end=' ')
            
            result = self.delete_user(user_id)
            
            if result.success:
                print("✓ Success")
                results['successful'].append(result)
            else:
                print(f"✗ Failed: {result.error_message}")
                results['failed'].append(result)
        
        return results


def load_api_key(config_path: str = None) -> str:
    """
    Load API key from config file.
    Searches in order:
    1. Provided config_path
    2. ./config/api_key.txt
    3. ~/.newrelic/api_key.txt
    4. Environment variable NEWRELIC_API_KEY
    """
    # Try environment variable first
    api_key = os.environ.get('NEWRELIC_API_KEY')
    if api_key:
        return api_key.strip()
    
    # Try config file paths
    search_paths = []
    if config_path:
        search_paths.append(config_path)
    
    search_paths.extend([
        './config/api_key.txt',
        os.path.expanduser('~/.newrelic/api_key.txt')
    ])
    
    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        return api_key
            except Exception as e:
                print(f"Warning: Could not read API key from {path}: {e}")
    
    raise ValueError(
        "API key not found. Please either:\n"
        "1. Set NEWRELIC_API_KEY environment variable\n"
        "2. Create ./config/api_key.txt with your API key\n"
        "3. Create ~/.newrelic/api_key.txt with your API key"
    )


def get_user_confirmation(prompt: str) -> bool:
    """Get yes/no confirmation from user"""
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response == 'y':
            return True
        elif response == 'n':
            return False
        else:
            print("Please enter 'y' or 'n'")


def print_summary(results: Dict[str, List[DeletionResult]]):
    """Print summary of deletion results"""
    print("\n" + "="*60)
    print("DELETION SUMMARY")
    print("="*60)
    print(f"Total successful: {len(results['successful'])}")
    print(f"Total failed: {len(results['failed'])}")
    
    if results['failed']:
        print("\nFailed deletions:")
        for result in results['failed']:
            print(f"  - User ID: {result.user_id}")
            print(f"    Error: {result.error_message}")
    
    print("="*60 + "\n")


def main():
    """Main execution function"""
    print("New Relic User Deletion Script")
    print("="*60)
    
    try:
        # Load API key
        print("Loading API key...")
        api_key = load_api_key()
        print("✓ API key loaded successfully\n")
        
        deleter = NewRelicUserDeleter(api_key)
        
        while True:
            # Get JSON file path
            json_file = input("Enter path to JSON file with user IDs: ").strip()
            
            if not json_file:
                print("No file path provided. Exiting.")
                break
            
            try:
                # Load user IDs
                print(f"\nLoading user IDs from {json_file}...")
                user_ids = deleter.load_user_ids(json_file)
                print(f"✓ Loaded {len(user_ids)} unique user ID(s)\n")
                
                # Show preview of user IDs
                print("User IDs to be deleted:")
                for idx, uid in enumerate(sorted(user_ids)[:10], 1):
                    print(f"  {idx}. {uid}")
                if len(user_ids) > 10:
                    print(f"  ... and {len(user_ids) - 10} more")
                print()
                
                # Get confirmation
                if not get_user_confirmation(
                    f"Would you like to proceed with permanently deleting {len(user_ids)} user(s)?"
                ):
                    print("Deletion cancelled.\n")
                    if not get_user_confirmation("Would you like to run this again for a new JSON file?"):
                        print("Exiting.")
                        break
                    continue
                
                # Perform deletions
                print("\nStarting deletion process...\n")
                results = deleter.delete_users_batch(user_ids)
                
                # Print summary
                print_summary(results)
                
                # Ask to continue
                if not get_user_confirmation("Would you like to run this again for a new JSON file?"):
                    print("Exiting.")
                    break
                print()
                
            except (FileNotFoundError, ValueError) as e:
                print(f"Error: {e}\n")
                if not get_user_confirmation("Would you like to try again with a different file?"):
                    print("Exiting.")
                    break
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
