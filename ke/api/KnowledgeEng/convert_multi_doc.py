import json
from copy import deepcopy


input_file ="C:\\Users\\muthu\\Projects\\elevaite\\elevaite\\input-file.json"
output_file="output.json"

# Read input JSON
with open(input_file, 'r', encoding='utf8') as f:
    input_json = json.load(f)

doc_comm_fields = {}

step_fields = []

output_dict = {}
output_list = []


# Define root node of JSon
doc_node = "Document"

# Define step field
step_node = "Steps"

# Parse the Document node and split the common and Step fields separately
def json_read(data):
    for key,value in data.items():
        if (isinstance(value, str)):
            common_fields_write(key, value)
        if isinstance(value, dict):
            json_read(value)
        elif isinstance(value, list):
            if (key == step_node):
                global step_fields
                step_fields = deepcopy(value)
            else:
                for val in value:                
                    if isinstance(val, str):
                        pass
                    elif isinstance(val, list):
                        pass
                    else:
                        json_read(val)

# Store common fields of document node separately
def common_fields_write(key, value):
    doc_comm_fields[key] = value

# Function to split the input as Document node wise
def document_split(data):     
     for key,value in data.items():
        if isinstance(value, list):
            if (key == doc_node):
                for key, val in enumerate(value):
                    json_read(val)                
                    json_write()

# Write the nodes into list object
def json_write():
    global output_dict, step_fields    
    for key, val in enumerate(step_fields):        
        output_dict = deepcopy(doc_comm_fields)
        for key1, val1 in val.items():
               output_dict[key1] = val1              
        output_list.append(output_dict)
    doc_comm_fields.clear()
    output_dict.clear()
    step_fields.clear()

document_split(input_json)

# Write list into the json format
with open (output_file, 'w') as f:
    # Removing any empty array in list (Ugly Way ?)
    while {} in output_list:
       output_list.remove({}) 
    json.dump(output_list, f)