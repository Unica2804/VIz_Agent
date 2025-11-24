"""
Test script for the data_extractor tool.
"""
from .. agents.tools.data_extractor import data_parser
import pandas as pd
import json


def test_csv_example():
    
    result = data_parser("/home/unica/Developer/Ml_Program/ML_Full_Projects/Viz_Agent/data/housing.csv")
    print("CSV Test Result:")
    print(json.dumps(result, indent=2))
    print()





if __name__ == "__main__":
    print("=" * 60)
    print("Testing Data Extractor Tool")
    print("=" * 60)
    print()
    
    test_csv_example()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
