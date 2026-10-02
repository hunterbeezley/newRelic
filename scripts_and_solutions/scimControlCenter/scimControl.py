import requests
import getpass

def fetch_scim_users(token):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    response = requests.get('https://scim-provisioning.service.newrelic.com/scim/v2/Users', headers=headers)

    if response.status_code == 200:
        json_response = response.json()
        users = [{'username': user['userName'], 
                  'id': user['id'], 
                  'name': user.get('name', {}), 
                  'emails': user.get('emails', [])} for user in json_response.get('Resources', [])]
        return users
    else:
        print(f"Failed to fetch users: {response.status_code} {response.text}")
        return None

def update_scim_user(token, user_id, attribute, value):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        attribute: value,
    }

    response = requests.put(f'https://scim-provisioning.service.newrelic.com/scim/v2/Users/{user_id}', headers=headers, json=data)

    if response.status_code == 200:
        print("User updated successfully.")
    else:
        print(f"Failed to update user: {response.status_code} {response.text}")

def delete_scim_user(token, user_id):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    response = requests.delete(f'https://scim-provisioning.service.newrelic.com/scim/v2/Users/{user_id}', headers=headers)

    if response.status_code == 204:
        print("User deleted successfully.")
    else:
        print(f"Failed to delete user: {response.status_code} {response.text}")

def main():
    print("Welcome to the SCIM Control Center")
    token = getpass.getpass("Enter your SCIM API Token: ").strip()

    while True:
        print("\nChoose an option:")
        print("1. Fetch All SCIM Users")
        print("2. Update User Attributes")
        print("3. Delete User")
        
        option = input("Enter the number of the option: ").strip()

        if option == '1':
            users = fetch_scim_users(token)
            if users is not None:
                print("\nSCIM Users:")
                for user in users:
                    username = user['username']
                    user_id = user['id']
                    user_name = user['name']
                    user_email = user['emails'][0]['value'] if user['emails'] else 'N/A'
                    print(f"Username: {username}, SCIM ID: {user_id}, Name: {user_name}, Email: {user_email}")
            else:
                print("No users found or failed to fetch users.")

        elif option == '2':
            user_id = input("Enter the SCIM ID of the user: ").strip()
            print("Choose the attribute to update:")
            print("1. Name")
            print("2. Email")
            print("3. Timezone")

            attr_option = input("Enter the number of the attribute: ").strip()

            if attr_option == '1':
                attribute = "name"
                value = {
                    "givenName": input("Enter given name: ").strip(),
                    "familyName": input("Enter family name: ").strip()
                }
            elif attr_option == '2':
                attribute = "emails"
                value = [{"value": input("Enter email: ").strip(), "primary": True}]
            elif attr_option == '3':
                attribute = "timezone"
                value = input("Enter timezone: ").strip()
            else:
                print("Invalid option. Please try again.")
                continue

            update_scim_user(token, user_id, attribute, value)

        elif option == '3':
            user_id = input("Enter the SCIM ID of the user to delete: ").strip()
            delete_scim_user(token, user_id)

        else:
            print("Invalid option. Please try again.")

        cont = input("\nDo you want to perform another operation? (y/n): ").strip().lower()
        if cont != 'y':
            break

if __name__ == "__main__":
    main()