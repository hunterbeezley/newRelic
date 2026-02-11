#!/usr/bin/env python3
"""
SendGrid Suppression Removal Script

This script removes email addresses from SendGrid's suppression lists
using one of three modes:
  1. Single email: --email user@example.com
  2. Bulk CSV: --csv emails.csv
  3. Domain-based: --domain @newrelic.com

SendGrid has multiple suppression lists:
- global: Global suppressions (unsubscribes)
- bounces: Hard bounces (email doesn't exist)
- blocks: Temporary blocks from ISPs
- spam_reports: Users marked email as spam
- invalid_emails: Failed email validation

By default, removes from ALL lists. Use --lists to target specific lists.

Usage:
    # Single email
    python3 remove_suppressions.py --email user@example.com [--dry-run] [--no-verify-ssl]

    # Bulk CSV
    python3 remove_suppressions.py --csv emails.csv [--dry-run] [--lists bounces blocks] [--no-verify-ssl]

    # Domain-based (always exports details to CSV)
    python3 remove_suppressions.py --domain @newrelic.com [--dry-run] [--no-verify-ssl]

Safety Features:
    - Dry-run mode to preview operations without making changes
    - Email validation before processing
    - Rate limiting with configurable delay
    - Confirmation prompt before execution
    - Detailed error logging and summary report
"""

import csv
import os
import sys
import time
import argparse
import logging
import re
from datetime import datetime
from typing import List, Dict, Tuple
import requests
from pathlib import Path


class SendGridSuppressionRemover:
    """Handles removal of email addresses from SendGrid suppressions."""

    BASE_URL = "https://api.sendgrid.com"

    # All suppression list endpoints
    SUPPRESSION_ENDPOINTS = {
        "global": "/v3/asm/suppressions/global",
        "bounces": "/v3/suppression/bounces",
        "blocks": "/v3/suppression/blocks",
        "spam_reports": "/v3/suppression/spam_reports",
        "invalid_emails": "/v3/suppression/invalid_emails"
    }

    def __init__(self, api_keys: Dict[str, str], dry_run: bool = False, delay: float = 0.1, verify_ssl: bool = True, lists: List[str] = None):
        """
        Initialize the suppression remover.

        Args:
            api_keys: Dict mapping account name to SendGrid API key
            dry_run: If True, no actual API calls are made
            delay: Delay in seconds between API calls (rate limiting)
            verify_ssl: If False, SSL certificate verification is disabled (corporate networks)
            lists: List of suppression types to remove from (default: all)
        """
        self.api_keys = api_keys
        self.dry_run = dry_run
        self.delay = delay
        self.verify_ssl = verify_ssl

        # Determine which lists to process
        if lists:
            self.target_lists = {k: v for k, v in self.SUPPRESSION_ENDPOINTS.items() if k in lists}
        else:
            self.target_lists = self.SUPPRESSION_ENDPOINTS.copy()

        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Statistics tracking (overall)
        self.stats = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }

        # Per-account statistics
        self.account_stats = {account: {"successful": 0, "failed": 0} for account in api_keys.keys()}

        # Results tracking
        self.results: List[Dict] = []

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging to both file and console."""
        # Ensure logs directory exists
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = log_dir / f"suppression_removal_{timestamp}.log"

        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info(f"Logging to file: {log_filename}")
        if self.dry_run:
            self.logger.info("DRY RUN MODE: No actual API calls will be made")
        if not self.verify_ssl:
            self.logger.warning("SSL verification disabled - USE ONLY in corporate networks with SSL inspection")

        account_names = ", ".join(self.api_keys.keys())
        self.logger.info(f"SendGrid accounts: {account_names}")

        list_names = ", ".join(self.target_lists.keys())
        self.logger.info(f"Target suppression lists: {list_names}")

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format using regex.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None

    def read_csv(self, csv_path: str) -> List[str]:
        """
        Read emails from CSV file.

        Args:
            csv_path: Path to CSV file containing emails

        Returns:
            List of email addresses

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV file is empty or invalid
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        emails = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)

            # Try to detect if first row is header
            first_row = next(reader, None)
            if not first_row:
                raise ValueError("CSV file is empty")

            # Check if first row looks like a header
            if first_row[0].lower() in ['email', 'emails', 'email address', 'address']:
                self.logger.info(f"Detected header row: {first_row}")
            else:
                # First row is data, add it
                emails.append(first_row[0].strip())

            # Read remaining rows
            for row in reader:
                if row and row[0].strip():
                    emails.append(row[0].strip())

        if not emails:
            raise ValueError("No emails found in CSV file")

        self.logger.info(f"Read {len(emails)} emails from {csv_path}")
        return emails

    def fetch_list_suppressions(self, list_name: str, endpoint: str, headers: Dict = None, max_pages: int = 500, account_name: str = None) -> List[Dict]:
        """
        Fetch all suppressions from a specific list (with pagination).

        Args:
            list_name: Name of the list (for logging)
            endpoint: API endpoint path
            headers: Optional headers dict (if None, uses self.headers)
            max_pages: Maximum number of pages to fetch (safety limit, default 500 = 250k records)
            account_name: Account name for logging purposes

        Returns:
            List of suppression dictionaries
        """
        all_suppressions = []
        offset = 0
        limit = 500  # SendGrid's max per page
        page_count = 0

        # Create progress label
        progress_label = f"{account_name} / {list_name}" if account_name else list_name

        # Log start of fetch
        self.logger.info(f"Fetching: {progress_label}")

        if headers is None:
            # Use first account's headers if not provided (backward compatibility)
            first_key = list(self.api_keys.values())[0]
            headers = {
                "Authorization": f"Bearer {first_key}",
                "Content-Type": "application/json"
            }

        while True:
            try:
                # Safety check to prevent infinite loops
                page_count += 1
                if page_count > max_pages:
                    self.logger.warning(f"Reached maximum page limit ({max_pages}) for {progress_label}. Stopping fetch.")
                    self.logger.warning(f"If this is legitimate, increase max_pages parameter.")
                    break

                url = f"{self.BASE_URL}{endpoint}?limit={limit}&offset={offset}"
                response = requests.get(url, headers=headers, timeout=30, verify=self.verify_ssl)

                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch {progress_label}: Status {response.status_code}")
                    break

                data = response.json()

                # Different lists have different response formats
                if isinstance(data, list):
                    batch = data
                elif isinstance(data, dict) and 'result' in data:
                    batch = data['result']
                else:
                    batch = []

                if not batch:
                    break

                all_suppressions.extend(batch)

                # Show progress every 10,000 records
                if len(all_suppressions) % 10000 == 0 and len(all_suppressions) > 0:
                    self.logger.info(f"  Progress: {len(all_suppressions):,} records...")

                # If we got fewer than the limit, we're done
                if len(batch) < limit:
                    break

                offset += limit
                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                self.logger.error(f"Error fetching {progress_label}: {str(e)}")
                break

        # Log completion
        self.logger.info(f"  Complete: {len(all_suppressions):,} records")
        return all_suppressions

    def check_email_suppressions(self, email: str) -> Dict[str, List[Dict]]:
        """
        Check which suppression lists contain a specific email across all accounts.

        Args:
            email: Email address to check

        Returns:
            Dict mapping account name to list of suppression details
        """
        self.logger.info(f"Checking suppression lists for: {email}")

        account_details = {}

        for account_name, api_key in self.api_keys.items():
            self.logger.info(f"  Checking account: {account_name}")

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            details = []

            for list_name, endpoint in self.target_lists.items():
                try:
                    url = f"{self.BASE_URL}{endpoint}/{email}"
                    response = requests.get(url, headers=headers, timeout=10, verify=self.verify_ssl)

                    if response.status_code == 200:
                        # Possible email found - need to verify response has actual data
                        try:
                            data = response.json()

                            # Handle different response formats
                            if isinstance(data, list):
                                if data:
                                    item = data[0]
                                else:
                                    # Empty list means NOT in suppression list
                                    continue
                            else:
                                item = data

                            # Check if we have meaningful data (not empty dict)
                            if not item or (isinstance(item, dict) and not any(item.values())):
                                # Empty dict or no data means NOT in suppression list
                                continue

                            detail = {
                                'account': account_name,
                                'list': list_name,
                                'reason': item.get('reason', 'N/A'),
                                'created': item.get('created', item.get('created_at', 'N/A')),
                                'status': item.get('status', 'N/A')
                            }
                            details.append(detail)
                            self.logger.info(f"    Found in {list_name}: {detail['reason']}")
                        except Exception as e:
                            self.logger.warning(f"    Found in {list_name} but couldn't parse details: {e}")
                            details.append({
                                'account': account_name,
                                'list': list_name,
                                'reason': 'Present in list',
                                'created': 'N/A',
                                'status': 'N/A'
                            })
                    elif response.status_code != 404:
                        self.logger.warning(f"    Error checking {list_name}: Status {response.status_code}")

                except Exception as e:
                    self.logger.error(f"    Exception checking {list_name}: {str(e)}")

            if details:
                account_details[account_name] = details

        return account_details

    def find_emails_by_domain(self, domain: str) -> Tuple[List[str], Dict[str, List[Dict]]]:
        """
        Find all emails matching a domain across all accounts and suppression lists.

        Args:
            domain: Domain to search for (e.g., '@newrelic.com' or 'newrelic.com')

        Returns:
            Tuple of (list of unique email addresses, dict mapping email to suppression details)
        """
        # Normalize domain
        domain = domain.lower()
        if not domain.startswith('@'):
            domain = '@' + domain

        self.logger.info(f"Searching for emails with domain: {domain}")
        self.logger.info(f"NOTE: Script must download ALL suppressions then filter by domain (SendGrid API limitation)")
        self.logger.info("")

        all_emails = set()
        email_details = {}  # Maps email -> list of {account, list_name, reason, created, etc}

        for account_name, api_key in self.api_keys.items():
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            for list_name, endpoint in self.target_lists.items():
                # Fetch with account name for better progress logging
                suppressions = self.fetch_list_suppressions(list_name, endpoint, headers, account_name=account_name)

                # Count domain matches in this list
                matches_before = len(all_emails)

                for item in suppressions:
                    # Extract email from different possible fields
                    email = item.get('email') or item.get('Email') or item.get('address')

                    if email and email.lower().endswith(domain):
                        email_lower = email.lower()
                        all_emails.add(email_lower)

                        # Store suppression details
                        if email_lower not in email_details:
                            email_details[email_lower] = []

                        # Extract relevant details
                        details = {
                            'account': account_name,
                            'list': list_name,
                            'reason': item.get('reason', 'N/A'),
                            'created': item.get('created', item.get('created_at', 'N/A')),
                            'status': item.get('status', 'N/A')
                        }

                        email_details[email_lower].append(details)

                # Log domain matches found in this list
                matches_found = len(all_emails) - matches_before
                if matches_found > 0:
                    self.logger.info(f"  ✓ Found {matches_found} domain match(es) | Total unique: {len(all_emails)}")
                else:
                    self.logger.info(f"  - No domain matches found")
                self.logger.info("")

        return sorted(list(all_emails)), email_details

    def remove_from_list(self, email: str, list_name: str, endpoint: str, api_key: str = None) -> Tuple[bool, str, int]:
        """
        Remove an email from a specific suppression list.

        Args:
            email: Email address
            list_name: Name of the list (for logging)
            endpoint: API endpoint path
            api_key: API key to use (if None, uses first account's key)

        Returns:
            Tuple of (success: bool, message: str, status_code: int)
        """
        if api_key is None:
            api_key = list(self.api_keys.values())[0]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            url = f"{self.BASE_URL}{endpoint}/{email}"
            response = requests.delete(url, headers=headers, timeout=10, verify=self.verify_ssl)

            if response.status_code == 204:
                return True, f"Removed from {list_name}", 204
            elif response.status_code == 404:
                return True, f"Not in {list_name}", 404
            elif response.status_code == 401:
                return False, f"{list_name}: Auth failed", 401
            elif response.status_code == 403:
                return False, f"{list_name}: Permission denied", 403
            else:
                return False, f"{list_name}: Error {response.status_code}", response.status_code

        except requests.exceptions.Timeout:
            return False, f"{list_name}: Timeout", 0
        except requests.exceptions.SSLError as e:
            return False, f"{list_name}: SSL error", 0
        except requests.exceptions.ConnectionError as e:
            return False, f"{list_name}: Connection error", 0
        except Exception as e:
            return False, f"{list_name}: {str(e)}", 0

    def remove_suppression(self, email: str) -> Tuple[bool, str, int]:
        """
        Remove a single email from all configured suppression lists across all accounts.

        Args:
            email: Email address to remove from suppressions

        Returns:
            Tuple of (success: bool, message: str, status_code: int)
        """
        if self.dry_run:
            accounts_str = ", ".join(self.api_keys.keys())
            lists_str = ", ".join(self.target_lists.keys())
            return True, f"DRY RUN - Would remove from {len(self.api_keys)} account(s) ({accounts_str}) and {len(self.target_lists)} list(s) ({lists_str})", 204

        account_results = {}
        overall_removed = []
        overall_not_in = []
        overall_errors = []

        # Try removing from each account
        for account_name, api_key in self.api_keys.items():
            removed_from = []
            not_in = []
            errors = []

            # Try removing from each configured list in this account
            for list_name, endpoint in self.target_lists.items():
                success, message, status_code = self.remove_from_list(email, list_name, endpoint, api_key)

                if success:
                    if status_code == 204:
                        removed_from.append(list_name)
                        overall_removed.append(f"{account_name}/{list_name}")
                        self.account_stats[account_name]["successful"] += 1
                    elif status_code == 404:
                        not_in.append(list_name)
                else:
                    errors.append(f"{list_name}: {message}")
                    overall_errors.append(f"{account_name}/{list_name}: {message}")
                    self.account_stats[account_name]["failed"] += 1

            # Store results for this account
            account_results[account_name] = {
                "removed_from": removed_from,
                "not_in": not_in,
                "errors": errors
            }

        # Build summary message
        if overall_errors:
            return False, f"Errors: {'; '.join(overall_errors[:3])}" + (" ..." if len(overall_errors) > 3 else ""), 0

        parts = []
        if overall_removed:
            # Group by account for cleaner display
            by_account = {}
            for item in overall_removed:
                acc, lst = item.split('/', 1)
                if acc not in by_account:
                    by_account[acc] = []
                by_account[acc].append(lst)

            account_summaries = [f"{acc}:({','.join(lists)})" for acc, lists in by_account.items()]
            parts.append(f"Removed from: {' '.join(account_summaries)}")

        if not parts:
            # Email not in any lists
            return True, "Not in any suppression lists", 404

        return True, " | ".join(parts), 204

    def process_emails(self, emails: List[str], batch_size: int = None) -> Dict:
        """
        Process list of emails and remove from suppressions.

        Args:
            emails: List of email addresses to process
            batch_size: Optional batch size for processing (for display purposes)

        Returns:
            Dictionary with statistics and results
        """
        self.stats["total"] = len(emails)

        self.logger.info(f"Starting processing of {len(emails)} emails...")

        for idx, email in enumerate(emails, 1):
            # Validate email
            if not self.validate_email(email):
                self.logger.warning(f"[{idx}/{len(emails)}] Invalid email format: {email}")
                self.stats["skipped"] += 1
                self.results.append({
                    "email": email,
                    "status": "skipped",
                    "message": "Invalid email format",
                    "status_code": None
                })
                continue

            # Remove suppression
            success, message, status_code = self.remove_suppression(email)

            if success:
                self.logger.info(f"[{idx}/{len(emails)}] ✓ {email} - {message}")
                self.stats["successful"] += 1
                self.results.append({
                    "email": email,
                    "status": "success",
                    "message": message,
                    "status_code": status_code
                })
            else:
                self.logger.error(f"[{idx}/{len(emails)}] ✗ {email} - {message}")
                self.stats["failed"] += 1
                self.results.append({
                    "email": email,
                    "status": "failed",
                    "message": message,
                    "status_code": status_code
                })

            # Rate limiting
            if idx < len(emails):  # Don't delay after the last email
                time.sleep(self.delay)

        return {
            "stats": self.stats,
            "results": self.results
        }

    def print_summary(self):
        """Print summary of processing results."""
        self.logger.info("\n" + "="*60)
        self.logger.info("SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Total emails processed: {self.stats['total']}")
        self.logger.info(f"Successful removals:    {self.stats['successful']}")
        self.logger.info(f"Failed removals:        {self.stats['failed']}")
        self.logger.info(f"Skipped (invalid):      {self.stats['skipped']}")
        self.logger.info("="*60)

        if self.stats['failed'] > 0:
            self.logger.info("\nFailed emails:")
            for result in self.results:
                if result['status'] == 'failed':
                    self.logger.info(f"  - {result['email']}: {result['message']}")


def load_api_keys() -> Dict[str, str]:
    """
    Load all SendGrid API keys from .env file.

    Returns:
        Dict mapping account name to API key

    Raises:
        ValueError: If no valid keys found or .env file missing
    """
    env_path = Path(__file__).parent / '.env'

    if not env_path.exists():
        raise ValueError(f".env file not found at {env_path}")

    api_keys = {}

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Look for SENDGRID_*_KEY variables
            if line.startswith('SENDGRID_') and '_KEY=' in line:
                key_name, api_key = line.split('=', 1)
                api_key = api_key.strip().strip("'\"")

                # Extract friendly account name from variable name
                # SENDGRID_PARENT_KEY -> parent
                # SENDGRID_NEWRELIC_NOTIFICATIONS_PRODUCTION_KEY -> newrelic.notifications.production
                account_parts = key_name.replace('SENDGRID_', '').replace('_KEY', '').lower().split('_')

                # Convert underscores to dots for display
                if account_parts == ['parent']:
                    account_name = 'parent'
                elif 'newrelic' in account_parts and 'notifications' in account_parts:
                    idx = account_parts.index('notifications')
                    remaining = account_parts[idx+1:]
                    if 'eu' in remaining:
                        account_name = 'newrelic.notifications.eu-production'
                    else:
                        account_name = 'newrelic.notifications.' + '.'.join(remaining)
                elif 'issues' in account_parts:
                    account_name = 'issues.newrelic.com'
                elif 'noreply' in account_parts and 'gnar' in account_parts:
                    account_name = 'noreply_gnar'
                elif 'authentication' in account_parts:
                    account_name = 'authentication.newrelic'
                else:
                    account_name = '.'.join(account_parts)

                # Validate API key format
                if not api_key.startswith('SG.'):
                    raise ValueError(f"Invalid API key format for {account_name} (should start with 'SG.')")

                # Only add if key is not placeholder
                if not api_key.endswith('your_key_here'):
                    api_keys[account_name] = api_key

    if not api_keys:
        raise ValueError("No valid SendGrid API keys found in .env file. Make sure keys start with 'SG.' and are not placeholder values.")

    return api_keys


def confirm_execution(email_count: int, dry_run: bool) -> bool:
    """
    Ask user to confirm execution.

    Args:
        email_count: Number of emails to process
        dry_run: Whether this is a dry run

    Returns:
        True if user confirms, False otherwise
    """
    if dry_run:
        print(f"\nDRY RUN MODE: About to simulate removal of {email_count} emails from suppressions.")
    else:
        print(f"\n⚠️  WARNING: About to remove {email_count} emails from SendGrid global suppressions.")
        print("This will allow emails to be sent to these addresses again.")

    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Remove email addresses from SendGrid suppressions (supports single email, bulk CSV, or domain-based removal)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single email
  python3 remove_suppressions.py --email user@example.com --dry-run --no-verify-ssl

  # Bulk CSV - Dry run (preview without making changes)
  python3 remove_suppressions.py --csv emails.csv --dry-run --no-verify-ssl

  # Bulk CSV - Remove from ALL suppression lists (default)
  python3 remove_suppressions.py --csv emails.csv --no-verify-ssl

  # Bulk CSV - Remove only from bounces
  python3 remove_suppressions.py --csv emails.csv --lists bounces --no-verify-ssl

  # Bulk CSV - Remove from bounces and blocks only
  python3 remove_suppressions.py --csv emails.csv --lists bounces blocks --no-verify-ssl

  # Domain-based - Find and remove all @newrelic.com emails (auto-exports details to CSV)
  python3 remove_suppressions.py --domain @newrelic.com --dry-run --no-verify-ssl

  # Domain-based - Remove from specific lists (auto-exports details to CSV)
  python3 remove_suppressions.py --domain newrelic.com --lists bounces blocks --no-verify-ssl
        """
    )

    # Input mode (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--email',
        help='Single email address to remove from suppressions'
    )
    input_group.add_argument(
        '--csv',
        help='Path to CSV file containing email addresses (one per line or in first column)'
    )
    input_group.add_argument(
        '--domain',
        help='Domain to search for (e.g., "@newrelic.com" or "newrelic.com"). Will find and remove all matching emails.'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview operations without making actual API calls'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=0.1,
        help='Delay in seconds between API calls (default: 0.1)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for display purposes (default: 100)'
    )

    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt (use with caution)'
    )

    parser.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL certificate verification (for corporate networks with SSL inspection)'
    )

    parser.add_argument(
        '--lists',
        nargs='+',
        choices=['global', 'bounces', 'blocks', 'spam_reports', 'invalid_emails', 'all'],
        default=['all'],
        help='Suppression lists to remove from (default: all). Options: global, bounces, blocks, spam_reports, invalid_emails, all'
    )

    parser.add_argument(
        '--export',
        action='store_true',
        help='[DEPRECATED] Export is now automatic for domain mode. This flag is kept for backward compatibility but has no effect.'
    )

    args = parser.parse_args()

    # Handle 'all' in lists
    if 'all' in args.lists:
        args.lists = None  # None means all lists

    try:
        # Load API keys
        print("Loading SendGrid API keys from .env...")
        api_keys = load_api_keys()
        print(f"✓ Loaded {len(api_keys)} account(s): {', '.join(api_keys.keys())}")

        # Initialize remover
        remover = SendGridSuppressionRemover(
            api_keys=api_keys,
            dry_run=args.dry_run,
            delay=args.delay,
            verify_ssl=not args.no_verify_ssl,
            lists=args.lists
        )

        # Gather emails based on input mode
        emails = []

        if args.email:
            # Single email mode
            print(f"\nMode: Single email")
            if not remover.validate_email(args.email):
                print(f"❌ Invalid email format: {args.email}")
                return 1
            emails = [args.email]
            print(f"✓ Email: {args.email}")

            # Check which suppression lists contain this email
            print("\nChecking suppression lists across all accounts...")
            print("-" * 80)
            account_suppressions = remover.check_email_suppressions(args.email)

            if account_suppressions:
                total_findings = sum(len(details) for details in account_suppressions.values())
                print(f"\n✓ Found in {len(account_suppressions)} account(s), {total_findings} list(s) total:\n")

                for account_name, details in account_suppressions.items():
                    print(f"  {account_name}:")
                    for detail in details:
                        print(f"    └─ List: {detail['list']:<20} Reason: {detail['reason']:<30} Created: {detail['created']}")
            else:
                print(f"\n✓ Email not found in any suppression lists across all accounts")
                print("  Nothing to remove - email can already receive messages")
                return 0

            print("-" * 80)

        elif args.csv:
            # Bulk CSV mode
            print(f"\nMode: Bulk CSV")
            print(f"Reading emails from {args.csv}...")
            emails = remover.read_csv(args.csv)
            print(f"✓ Found {len(emails)} emails")

            # Check suppression details for each email
            print("\nChecking suppression lists across all accounts for each email...")
            print("-" * 80)

            email_suppression_map = {}  # Maps email -> dict of {account: [details]}
            emails_with_suppressions = []

            for idx, email in enumerate(emails, 1):
                if not remover.validate_email(email):
                    print(f"[{idx}/{len(emails)}] ⚠️  Skipping invalid email: {email}")
                    continue

                account_details = remover.check_email_suppressions(email)

                if account_details:
                    email_suppression_map[email] = account_details
                    emails_with_suppressions.append(email)
                    total_findings = sum(len(details) for details in account_details.values())
                    print(f"[{idx}/{len(emails)}] ✓ {email} - Found in {len(account_details)} account(s), {total_findings} list(s)")
                else:
                    print(f"[{idx}/{len(emails)}] - {email} - Not in any suppression lists")

            print("-" * 80)

            if not emails_with_suppressions:
                print("\n✓ None of the emails are in any suppression lists")
                print("  Nothing to remove - all emails can already receive messages")
                return 0

            # Show detailed summary for first 10 emails with suppressions
            print(f"\nSuppression details for emails found ({len(emails_with_suppressions)} total):\n")
            for email in emails_with_suppressions[:10]:
                print(f"  {email}")
                for account_name, details in email_suppression_map[email].items():
                    print(f"    {account_name}:")
                    for detail in details:
                        print(f"      └─ List: {detail['list']:<20} Reason: {detail['reason']:<30} Created: {detail['created']}")

            if len(emails_with_suppressions) > 10:
                print(f"\n  ... and {len(emails_with_suppressions) - 10} more emails")

            print("-" * 80)

            # Update emails list to only include those with suppressions
            emails = emails_with_suppressions

        elif args.domain:
            # Domain-based mode
            print(f"\nMode: Domain-based search")
            print(f"Searching for emails matching domain: {args.domain}")
            print("This will scan all suppression lists and may take a few minutes...")
            print("-" * 60)

            emails, email_details = remover.find_emails_by_domain(args.domain)

            if not emails:
                print(f"\n✓ No emails found matching domain: {args.domain}")
                return 0

            print(f"\n✓ Found {len(emails)} emails matching domain: {args.domain}")
            print("\nMatching emails with suppression details:")
            print("-" * 80)

            # Show first 10 with details
            for email in emails[:10]:
                print(f"\n  {email}")
                for detail in email_details[email]:
                    print(f"    {detail['account']}:")
                    print(f"      └─ List: {detail['list']:<20} Reason: {detail['reason']:<30} Created: {detail['created']}")

            if len(emails) > 10:
                print(f"\n  ... and {len(emails) - 10} more emails")

            # Always export to CSV for domain mode
            export_path = f"domain_suppressions_{args.domain.replace('@', '').replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Email', 'Account', 'Suppression List', 'Reason', 'Created', 'Status'])
                for email in emails:
                    for detail in email_details[email]:
                        writer.writerow([
                            email,
                            detail['account'],
                            detail['list'],
                            detail['reason'],
                            detail['created'],
                            detail['status']
                        ])
            print(f"\n✓ Full details exported to: {export_path}")
            print("  This file can be shared with customers to explain suppression reasons.")

        # Confirm execution
        if not args.no_confirm:
            if not confirm_execution(len(emails), args.dry_run):
                print("\nOperation cancelled by user.")
                return 0

        # Process emails
        print("\nProcessing emails...")
        print("-" * 60)
        remover.process_emails(emails, batch_size=args.batch_size)

        # Print summary
        remover.print_summary()

        # Exit code based on failures
        return 1 if remover.stats['failed'] > 0 else 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user (Ctrl+C)")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
