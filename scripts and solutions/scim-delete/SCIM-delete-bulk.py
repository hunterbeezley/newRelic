import requests
import csv

def delete_users(api_key, user_emails):
    url = 'https://scim-provisioning.service.newrelic.com/scim/v2/Users'
    delete_ids = []

    for user_email in user_emails:
        response = requests.get(
            url,
            headers={'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'},
            params={'filter': f'emails eq "{user_email}"'}
        )

        print("API Response:", response.content)  # Print response content for debugging

        if response.status_code == 200:
            user_data = response.json()['Resources']
            if user_data:
                delete_ids.append(user_data[0]['id'])
            else:
                print(f"User with email '{user_email}' not found in this authentication domain")

        else:
            print("Error occurred: ", response.json())

    if delete_ids:
        choice = input(f"Would you like to delete {len(delete_ids)} user(s)? y/n: ").lower()
        if choice == 'y':
            for user_id in delete_ids:
                delete_url = f'https://scim-provisioning.service.newrelic.com/scim/v2/Users/{user_id}'
                delete_response = requests.delete(
                    delete_url,
                    headers={'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'}
                )

                if delete_response.status_code == 204:
                    print(f"User with ID {user_id} deleted successfully!")
                else:
                    print(f"Error occurred while deleting the user with ID {user_id}:",
                          delete_response.json())
    else:
        print("No users to delete.")

def main():
    print("SCIM USER DELETE TOOL")
    api_key = input("Please enter your SCIM Bearer Token: ")
    
    while True:
        csv_file = input("Please enter the path to the CSV file: ")
        
        try:
            with open(csv_file, 'r') as file:
                reader = csv.reader(file)
                user_emails = [row[0].strip() for row in reader]
                delete_users(api_key, user_emails)
        except FileNotFoundError:
            print("File not found. Please enter a valid file path.")
        except Exception as e:
            print("An error occurred:", str(e))
        
        choice = input("Would you like to use this tool for another CSV file? y/n: ").lower()
        if choice != 'y':
            print("Okie dokie! Until next time!!")
            break

if __name__ == "__main__":
    main()
