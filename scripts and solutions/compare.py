import csv
import json
import sys

def compare_users(tsv_file, json_file):
    try:
        # Read TSV file
        tsv_users = set()
        with open(tsv_file, 'r') as tsv:
            reader = csv.DictReader(tsv, delimiter='\t')
            if 'ID' not in reader.fieldnames:
                raise ValueError("TSV file does not have an 'ID' column")
            for row in reader:
                tsv_users.add(str(row['ID']))  # Convert to string

        # Read JSON file
        with open(json_file, 'r') as json_data:
            data = json.load(json_data)
            if 'users_moved' not in data:
                raise ValueError("JSON file does not have a 'users_moved' key")
            json_users = set(str(user) for user in data['users_moved'])  # Convert to string

        # Compare users
        discrepancies = tsv_users.symmetric_difference(json_users)

        # Report discrepancies
        if not discrepancies:
            print("No discrepancies found.")
        else:
            print("Discrepancies found:")
            for user in sorted(discrepancies, key=lambda x: int(x) if x.isdigit() else x):
                if user in tsv_users:
                    print(f"- {user} (in TSV but not in JSON)")
                else:
                    print(f"- {user} (in JSON but not in TSV)")

        print(f"\nTotal discrepancies: {len(discrepancies)}")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError:
        print("Error: Invalid JSON file")
    except csv.Error:
        print("Error: Invalid TSV file")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    tsv_file = input("Enter the path to the TSV file: ").strip()
    json_file = input("Enter the path to the JSON file: ").strip()

    compare_users(tsv_file, json_file)

if __name__ == "__main__":
    main()