"""
Test script for the data_extractor tool.
"""
from tools.data_extractor import data_parser
import pandas as pd
import json


def test_csv_example():
    """Test with a CSV file."""
    # Create a sample CSV for testing
    sample_data = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'Los Angeles', 'Chicago']
    })
    sample_data.to_csv('test_data.csv', index=False)
    
    result = data_parser('test_data.csv')
    print("CSV Test Result:")
    print(json.dumps(result, indent=2))
    print()


def test_json_example():
    """Test with a JSON file."""
    # Create a sample JSON for testing
    sample_data = [
        {'id': 1, 'product': 'Laptop', 'price': 1200},
        {'id': 2, 'product': 'Mouse', 'price': 25},
        {'id': 3, 'product': 'Keyboard', 'price': 75}
    ]
    with open('test_data.json', 'w') as f:
        json.dump(sample_data, f)
    
    result = data_parser('test_data.json')
    print("JSON Test Result:")
    print(json.dumps(result, indent=2))
    print()


def test_url_example():
    """Test with a URL (example - may need valid URL)."""
    # Example with a public CSV URL
    url = "https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv"
    
    try:
        result = data_parser(url)
        print("URL Test Result:")
        print(json.dumps(result, indent=2))
        print()
    except Exception as e:
        print(f"URL test failed (expected if no internet): {e}")
        print()


def test_auto_detect():
    """Test auto file type detection."""
    sample_data = pd.DataFrame({
        'Column1': [1, 2, 3],
        'Column2': ['A', 'B', 'C']
    })
    sample_data.to_csv('auto_detect.csv', index=False)
    
    # Call without specifying file_type
    result = data_parser('auto_detect.csv', file_type=None)
    print("Auto-detect Test Result:")
    print(json.dumps(result, indent=2))
    print()


def test_error_handling():
    """Test error handling with non-existent file."""
    result = data_parser('non_existent_file.csv')
    print("Error Handling Test Result:")
    print(json.dumps(result, indent=2))
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Data Extractor Tool")
    print("=" * 60)
    print()
    
    test_csv_example()
    test_json_example()
    test_auto_detect()
    test_error_handling()
    # test_url_example()  # Uncomment if you have internet access
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
