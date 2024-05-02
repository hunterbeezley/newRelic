import requests
import json
import csv

# New Relic Nerdgraph API endpoint
api_url = "https://api.newrelic.com/graphql"

# GraphQL query
graphql_query = """
{
  actor {
    organization {
      userManagement {
        authenticationDomains {
          authenticationDomains {
            users {
              users {
                email
                id
                lastActive
              }
            }
          }
        }
      }
    }
  }
}
"""

# Prepare the request headers
headers = {
    "Content-Type": "application/json",
    "Api-Key": "USER_API_KEY_HERE"  # Replace with your New Relic API key
}

# Make the HTTP POST request to the Nerdgraph API
response = requests.post(api_url, headers=headers, data=json.dumps({"query": graphql_query}))

# Check if the request was successful
if response.status_code == 200:
    data = response.json()["data"]["actor"]["organization"]["userManagement"]["authenticationDomains"]

    # Specify the output file name
    output_filename = "user_data.tsv"  # or "user_data.csv" for CSV

    # Write the data to a TSV or CSV file
    with open(output_filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")  # For TSV: delimiter="\t", For CSV: delimiter=","
        # Write header
        writer.writerow(["Email", "ID", "LastActive"])
        # Iterate through authentication domains and users
        for domain in data["authenticationDomains"]:
            for user in domain["users"]["users"]:
                writer.writerow([user["email"], user["id"], user["lastActive"]])
    print(f"Data saved to {output_filename}")
else:
    print("Error: Unable to retrieve data. HTTP status code:", response.status_code)
