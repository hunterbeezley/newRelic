# New Relic SCIM User Management Tool

## Overview

This Python script provides a simple interface for managing users in New Relic via the SCIM (System for Cross-domain Identity Management) API. It allows users to perform basic operations such as fetching, updating, and deleting user attributes.

## 🚧 Work in Progress

**Current Limitations:**
- Does not support SCIM user group queries or mutations.
- Future versions will include this functionality.

## Features

- Fetch SCIM users
- Update user attributes
- Delete users

## Requirements

- Python 3.x
- `requests` library (install via `pip install requests`)

## Quick Start

1. Install dependencies:
   ```bash
   pip install requests
2. Run the script:
   ```bash
   python scimControl.py
3. Follow the prompts to manage New Relic users.

## Note
This tool is specifically designed for New Relic user management via the SCIM API. Contributions and feedback are welcome as we expand its capabilities.
