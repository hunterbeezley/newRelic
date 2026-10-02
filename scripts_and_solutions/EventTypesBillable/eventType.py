import csv
import json
import requests

def run_nerdgraph_query(event_type):
    query = '''
    {{
        actor {{
            account(id: 313870) {{
                nrql(query: "FROM ArchiveFile SELECT uniques(storedEventNamespace) WHERE storedEventType IN ('{}') FACET storedEventType") {{
                    results
                }}
            }}
        }}
    }}
    '''.format(event_type)

    headers = {
        'Content-Type': 'application/json',
        'API-Key': 'REDACTED'
    }

    response = requests.post('https://api.newrelic.com/graphql', json={'query': query}, headers=headers)
    return response.json()

def parse_namespaces(results):
    namespaces = []
    for result in results:
        if 'uniques.storedEventNamespace' in result:
            namespaces.extend(result['uniques.storedEventNamespace'])
    return namespaces

def check_ingest_billable(namespace, namespaces_file):
    with open(namespaces_file, 'r') as file:
        content = file.read()
        namespace_blocks = content.split('-')
        for block in namespace_blocks:
            lines = block.strip().split('\n')
            if lines and lines[0].strip() == f"namespace: '{namespace}'":
                for line in lines[1:]:
                    if 'ingestBillable:' in line:
                        return line.split('ingestBillable:')[1].strip().lower() == 'true'
    return False  # Default to False if not found

def main():
    output_data = []
    with open('event_types.csv', 'r') as csv_file:
        event_types = csv.reader(csv_file)
        for event_type in event_types:
            event_type = event_type[0]  # Assuming one event type per row
            print(f"Processing event type: {event_type}")
            try:
                response = run_nerdgraph_query(event_type)
                print(f"API Response for {event_type}: {json.dumps(response, indent=2)}")
                results = response['data']['actor']['account']['nrql']['results']
                namespaces = parse_namespaces(results)
                print(f"Namespaces found for {event_type}: {namespaces}")
                
                for namespace in namespaces:
                    ingest_billable = check_ingest_billable(namespace, 'namespaces.txt')
                    output_data.append([event_type, namespace, ingest_billable])
                    print(f"Added to output: {event_type}, {namespace}, {ingest_billable}")
            except Exception as e:
                print(f"Error processing {event_type}: {str(e)}")

    print(f"Total rows to write: {len(output_data)}")

    # Write results to CSV
    with open('event_type_results.csv', 'w', newline='') as output_file:
        csv_writer = csv.writer(output_file)
        csv_writer.writerow(['Event Type', 'Namespace', 'Ingest Billable'])  # Updated header
        csv_writer.writerows(output_data)

    print(f"Results have been written to event_type_results.csv")
    print(f"First few rows of output_data: {output_data[:5]}")

if __name__ == "__main__":
    main()
