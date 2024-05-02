import requests
import json
import csv
import os

# Prompt the user for the API key
while True:
    api_key = input("Please enter your API key: ")
    if not api_key:
        print("API key cannot be empty.")
    else:
        break

# Prompt the user for the CSV file path
while True:
    csv_path = input("Please enter the path to the CSV file: ")
    if not csv_path:
        print("CSV file path cannot be empty.")
    elif not os.path.exists(csv_path):
        print("Invalid CSV file path. Please try again.")
    else:
        break

# Set up the headers for the API call
headers = {
    "Content-Type": "application/json",
    "API-Key": api_key
}

# Open the CSV file and loop through each row
with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Get the user ID and new email from the current row
        user_id = row['ID']
        new_user_email = row['Email']

        # Construct the API call payload
        payload = {
            "query": "mutation {\n  userManagementUpdateUser(updateUserOptions: {id: \"" + user_id + "\", email: \"" + new_user_email + "\"}) {\n    user {\n      id\n      email\n    }\n  }\n}\n",
            "variables": ""
        }

        # Make the API call
        response = requests.post("https://api.newrelic.com/graphql", headers=headers, data=json.dumps(payload))

        # Check for errors in the response
        if "errors" in response.json():
            # Print the error messages
            print("Errors found:")
            for error in response.json()["errors"]:
                print(error["message"])
        else:
            # Print success message with user ID
            print("User ID " + user_id + " has been updated successfully")
