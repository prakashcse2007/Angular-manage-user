import requests
from collections import defaultdict

# Sample list of dictionaries with serial numbers and other data
data = [
    {"serial": "123", "other_data1": "A", "other_data2": "X"},
    {"serial": "456", "other_data1": "B", "other_data2": "Y"},
    {"serial": "789", "other_data1": "A", "other_data2": "X"},  # Same combination
    {"serial": "012", "other_data1": "C", "other_data2": "Z"},
]

# Mock API URL (replace with your actual API endpoint)
API_URL = "https://example.com/api"

def call_api(key):
    """Function to call the API with the given key."""
    # Assume the key is a tuple (e.g., ('A', 'X')) and use it to build the query
    other_data1, other_data2 = key
    response = requests.get(f"{API_URL}?data1={other_data1}&data2={other_data2}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for input: {key}")
        return None

def main(data):
    # Group dictionaries by a tuple of 'other_data1' and 'other_data2'
    grouped_data = defaultdict(list)
    for item in data:
        key = (item["other_data1"], item["other_data2"])  # Use tuple as key
        grouped_data[key].append(item)

    # Store API responses for unique combinations
    responses = {}
    for key in grouped_data:
        response = call_api(key)
        if response is not None:
            responses[key] = response

    # Append API responses to the original dictionaries
    result = []
    for key, items in grouped_data.items():
        for item in items:
            item["api_response"] = responses.get(key, {})
            result.append(item)

    return result

if __name__ == "__main__":
    updated_data = main(data)
    for item in updated_data:
        print(item)
