import requests

print("SCIM USER DELETE TOOL")
api_key = input("Please enter your API key: ")
email = input("Please enter the user email: ")
url = 'https://scim-provisioning.service.newrelic.com/scim/v2/Users'

while True:
    response = requests.get(url, headers={'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'}, params={'filter': f'userName eq "{email}"'})
    
    if response.status_code != 200:
        print("Error occurred: ", response.json())
        break
        
    user_data = response.json()['Resources']
    
    if not user_data:
        print("user email not found in this authentication domain")
        email = input("Please enter the user email: ")
        continue
    
    user_id = user_data[0]['id']
    print(f"User ID: {user_id}")
    
    while True:
        choice = input("Would you like to delete this user? y/n: ").lower()
        
        if choice == 'y':
            delete_url = f'https://scim-provisioning.service.newrelic.com/scim/v2/Users/{user_id}'
            delete_response = requests.delete(delete_url, headers={'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'})
            
            if delete_response.status_code != 204:
                print("Error occurred while deleting the user:", delete_response.json())
                break
                
            print("User deleted successfully!")
            while True:
                choice = input("Would you like to use this tool for another user? y/n: ").lower()
                if choice == 'y':
                    email = input("Please enter the user email: ")
                    break
                elif choice == 'n':
                    print("Okie dokie! Until next time!!")
                    exit()
                else:
                    print("Sorry, was that 'y' or 'n'?")
            break
        elif choice == 'n':
            while True:
                choice = input("Would you like to use this tool for another user? y/n: ").lower()
                if choice == 'y':
                    email = input("Please enter the user email: ")
                    break
                elif choice == 'n':
                    print("Okie dokie! Until next time!!")
                    exit()
                else:
                    print("Sorry, was that 'y' or 'n'?")
            break
        else:
            print("Sorry, was that 'y' or 'n'?")