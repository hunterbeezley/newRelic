# Account Deletion Prep

These scripts were first created to be used individually and have not yet been updated to be run together. This means executing each script needs to be done manually, and each script will ask for both user keys and CSV of accounts. The upside of this is that you are free to run these scripts as needed.

The directions in this ReadMe assume you are intending on deleting all alertable entities in every account in a single organization. If you are here to use only one script, then you may not be following these steps exactly. If needed, work with Hunter or proceed at your own caution.

## Getting Started

**Note:** This repo was written for internal NR employees to leverage. Therefore, the readMe instructions below are written for NR employees to follow.

Only use this when:
- The customer is looking to delete the entire organization and all accounts.
- The customer cannot reasonably self-serve ensure all alerts are disabled (i.e., they have an unreasonable amount).
- All users have already been removed from the Org.
- You are a Sr.TSE or are directly working with a Sr.TSE.

### Reactivate Accounts (if cancelled, otherwise skip this step):
- This can be done via RPM-Admin manually one-by-one; or potentially scripted with #help-authorization (TBD).

## Initial Setup

### Get Added as User:
- Login as V2 NR Admin and navigate to the organization in question > user management UI.
- Select “add user” and input a test email or alias of your NR email (e.g., hbeezley+deleteorg@newrelic.com).

### Give Yourself Initial Permissions:
- If the org already has a group that provides all product admin role to every account, assign yourself to this and skip the below step ‘give all product admin permissions to every account:’
- Otherwise, you’ll need at least Org manager and All Product admin for the reporting account ID to get started. If the org already has 

### Create User API Key:
- In API UI, select “create key” for the reporting account ID.

## Clone Repository

### Get All Scripts:
- Clone repo https://github.com/hunterbeezley/AccountDeletionPrep.git to get all relevant scripts.

### Move to the Directory Where You Cloned Scripts:
- `cd path`

## Running Scripts

### Run Script to Create CSV of All Active Accounts in Org:
- Open terminal at enclosing folder and run `nraccountids.py`.
- This will output a CSV in the same directory of all account ID’s that are not cancelled. This file will be used for all subsequent scripts.
- If the script outputs only one CSV it will be named ‘account_ids.csv’ however if multiple regions are found, the script will create two CSVs for each region code. 
- Rename the US region code CSV ‘account_ids.csv’ (this is what all subsequent scripts expect).

**IF THE SCRIPT CREATED A LIST OF EU ACCOUNTS, I DO NOT HAVE SCRIPTS IN THIS REPO MODIFIED TO HANDLE EU ENDPOINTS. SORRY, YOU’RE IN UNCHARTED WATERS IN THIS CASE; EITHER DEAL WITH THE EU ACCOUNTS MANUALLY OR MODIFY THE SCRIPT ENDPOINTS YOURSELF OR REACH HUNTER**

### Run Script to Give All Product Admin Permissions to Every Account:
- Run `python nrCreateGrants.py`.
- The script will take in the CSV `account_ids.csv` you just created.

### Run Script to Delete All Channels:
- Run `python nrDeleteChannels.py`.

### Run Script to Delete All Destinations:
- Run `python nrDeleteDestinations.py`.

### Run Script to Delete All Policies:
- Run `python nrDeletePolicies.py`.

_PR's and feedback welcome! Never hesitate to reach out to me if needed_
