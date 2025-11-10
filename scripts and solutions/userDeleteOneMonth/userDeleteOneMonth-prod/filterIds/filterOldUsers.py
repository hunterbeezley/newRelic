#!/usr/bin/env python3
"""
New Relic User Filter Script
Filters users from metadata JSON based on createdAt date (older than 1 month)
and outputs unique user IDs in the format expected by massDeleteUsers.py
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Set, Dict, Any, List


class UserFilter:
    """Filter users based on createdAt date"""
    
    def __init__(self, days_threshold: int = 30):
        """
        Initialize with date threshold.
        
        Args:
            days_threshold: Number of days ago to use as cutoff (default: 30)
        """
        self.days_threshold = days_threshold
        self.cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
    
    def load_user_metadata(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        Load user metadata from JSON file.
        Handles various JSON structures.
        """
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Already a list of user objects
                return data
            elif isinstance(data, dict):
                # Check for common keys that might contain user list
                for key in ['users', 'data', 'results', 'items']:
                    if key in data:
                        if isinstance(data[key], list):
                            return data[key]
                        elif isinstance(data[key], dict):
                            # If it's a dict, try to extract values as list
                            return list(data[key].values())
                
                # If no recognized keys, treat the dict itself as a single user
                return [data]
            else:
                raise ValueError("Unsupported JSON format")
                
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def parse_date(self, date_value: Any) -> datetime:
        """
        Parse various date formats to datetime object.
        Supports:
        - ISO 8601 strings (with or without timezone)
        - Unix timestamps (seconds or milliseconds)
        - Common date string formats
        """
        if not date_value:
            return None
        
        # If it's already a datetime object
        if isinstance(date_value, datetime):
            if date_value.tzinfo is None:
                return date_value.replace(tzinfo=timezone.utc)
            return date_value
        
        # If it's a number (Unix timestamp)
        if isinstance(date_value, (int, float)):
            # Check if it's in milliseconds (>10 digits)
            if date_value > 10000000000:
                date_value = date_value / 1000
            try:
                return datetime.fromtimestamp(date_value, tz=timezone.utc)
            except (ValueError, OSError):
                return None
        
        # If it's a string
        if isinstance(date_value, str):
            # Try ISO 8601 format
            for fmt in [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
            
            # Try parsing with fromisoformat (Python 3.7+)
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, AttributeError):
                pass
        
        return None
    
    def extract_user_id(self, user_obj: Dict[str, Any]) -> str:
        """
        Extract user ID from user object.
        Tries common field names.
        """
        # Common field names for user ID
        id_fields = ['id', 'userId', 'user_id', 'ID', 'UserId', 'USER_ID']
        
        for field in id_fields:
            if field in user_obj and user_obj[field]:
                return str(user_obj[field]).strip()
        
        return None
    
    def extract_created_date(self, user_obj: Dict[str, Any]) -> datetime:
        """
        Extract createdAt date from user object.
        Tries common field names.
        """
        # Common field names for creation date
        date_fields = [
            'createdAt', 'created_at', 'createdat', 'CREATED_AT',
            'dateCreated', 'date_created', 'created', 'creationDate',
            'creation_date', 'timestamp', 'createdDate'
        ]
        
        for field in date_fields:
            if field in user_obj and user_obj[field]:
                parsed_date = self.parse_date(user_obj[field])
                if parsed_date:
                    return parsed_date
        
        return None
    
    def filter_users(self, user_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Filter users based on createdAt date and return statistics.
        
        Returns:
            Dict containing:
                - filtered_user_ids: Set of user IDs that match criteria
                - stats: Dict with filtering statistics
        """
        filtered_user_ids = set()
        stats = {
            'total_users': len(user_metadata),
            'users_with_id': 0,
            'users_with_created_date': 0,
            'users_older_than_threshold': 0,
            'users_missing_id': 0,
            'users_missing_date': 0,
            'users_too_recent': 0,
            'invalid_dates': 0,
            'duplicate_ids_found': 0
        }
        
        seen_ids = set()
        
        for user in user_metadata:
            if not isinstance(user, dict):
                continue
            
            # Extract user ID
            user_id = self.extract_user_id(user)
            if not user_id:
                stats['users_missing_id'] += 1
                continue
            
            stats['users_with_id'] += 1
            
            # Track duplicates
            if user_id in seen_ids:
                stats['duplicate_ids_found'] += 1
                continue
            seen_ids.add(user_id)
            
            # Extract and parse created date
            created_date = self.extract_created_date(user)
            if not created_date:
                stats['users_missing_date'] += 1
                continue
            
            stats['users_with_created_date'] += 1
            
            # Check if date is older than threshold
            try:
                if created_date < self.cutoff_date:
                    filtered_user_ids.add(user_id)
                    stats['users_older_than_threshold'] += 1
                else:
                    stats['users_too_recent'] += 1
            except Exception:
                stats['invalid_dates'] += 1
        
        return {
            'filtered_user_ids': filtered_user_ids,
            'stats': stats
        }
    
    def save_filtered_users(self, user_ids: Set[str], output_path: str):
        """
        Save filtered user IDs to JSON file in massDeleteUsers.py expected format.
        Format: {"userIds": ["id1", "id2", ...]}
        """
        output_data = {
            "userIds": sorted(list(user_ids))
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
    
    def print_stats(self, stats: Dict[str, Any], cutoff_date: datetime):
        """Print filtering statistics"""
        print("\n" + "="*70)
        print("FILTERING STATISTICS")
        print("="*70)
        print(f"Cutoff date (must be older than): {cutoff_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Days threshold: {self.days_threshold} days ago")
        print()
        print(f"Total users in input file:       {stats['total_users']}")
        print(f"Users with valid ID:              {stats['users_with_id']}")
        print(f"Users with created date:          {stats['users_with_created_date']}")
        print()
        print(f"✓ Users older than threshold:     {stats['users_older_than_threshold']}")
        print(f"✗ Users too recent (< {self.days_threshold} days):    {stats['users_too_recent']}")
        print(f"✗ Users missing ID:                {stats['users_missing_id']}")
        print(f"✗ Users missing created date:      {stats['users_missing_date']}")
        print(f"✗ Invalid dates:                   {stats['invalid_dates']}")
        print(f"✗ Duplicate IDs (skipped):         {stats['duplicate_ids_found']}")
        print("="*70 + "\n")


def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} ({default_str}): ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


def main():
    """Main execution function"""
    print("New Relic User Filter Script")
    print("Filters users by createdAt date (older than X days)")
    print("="*70)
    
    try:
        while True:
            # Get input file path
            input_file = get_user_input("\nEnter path to JSON file with user metadata")
            
            if not input_file:
                print("No file path provided. Exiting.")
                break
            
            # Get days threshold
            days_str = get_user_input("Enter days threshold (users older than X days)", "30")
            try:
                days_threshold = int(days_str)
                if days_threshold <= 0:
                    print("Error: Days threshold must be positive. Using default of 30.")
                    days_threshold = 30
            except ValueError:
                print("Error: Invalid number. Using default of 30 days.")
                days_threshold = 30
            
            try:
                # Initialize filter
                user_filter = UserFilter(days_threshold=days_threshold)
                
                print(f"\nLoading user metadata from {input_file}...")
                user_metadata = user_filter.load_user_metadata(input_file)
                print(f"✓ Loaded {len(user_metadata)} user record(s)")
                
                # Filter users
                print(f"\nFiltering users created before {user_filter.cutoff_date.strftime('%Y-%m-%d')}...")
                result = user_filter.filter_users(user_metadata)
                filtered_ids = result['filtered_user_ids']
                stats = result['stats']
                
                # Print statistics
                user_filter.print_stats(stats, user_filter.cutoff_date)
                
                if not filtered_ids:
                    print("⚠️  No users found matching the criteria.")
                    if not get_yes_no("\nWould you like to try again with different parameters?"):
                        print("Exiting.")
                        break
                    continue
                
                # Show preview of filtered IDs
                print(f"Preview of filtered user IDs ({len(filtered_ids)} total):")
                for idx, uid in enumerate(sorted(list(filtered_ids))[:10], 1):
                    print(f"  {idx}. {uid}")
                if len(filtered_ids) > 10:
                    print(f"  ... and {len(filtered_ids) - 10} more")
                print()
                
                # Get output file path
                default_output = Path(input_file).stem + "_filtered.json"
                output_file = get_user_input(f"Enter output file path", default_output)
                
                # Save filtered users
                user_filter.save_filtered_users(filtered_ids, output_file)
                print(f"\n✓ Filtered user IDs saved to: {output_file}")
                print(f"  Format: {{'userIds': [...]}} - ready for massDeleteUsers.py")
                
                # Ask to continue
                if not get_yes_no("\nWould you like to filter another file?"):
                    print("Exiting.")
                    break
            
            except (FileNotFoundError, ValueError) as e:
                print(f"\nError: {e}")
                if not get_yes_no("Would you like to try again?"):
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
