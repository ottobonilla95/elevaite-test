import json
import os

def load_schema(schema_file_name):
   current_file_dir = os.path.dirname(os.path.abspath(__file__))
   schema_path = os.path.join(current_file_dir, 'schemas', schema_file_name)
   with open(schema_path, 'r') as file:
      return json.load(file)
