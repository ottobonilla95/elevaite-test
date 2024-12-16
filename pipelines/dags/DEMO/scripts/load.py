# Upload vectors to vector DB
print('INFO: load script running...')

def load_data(transformed_data_uri):
    # Simulate loading data
    print(f"Loading data from: {transformed_data_uri}")
    print("Data loaded successfully.")

if __name__ == "__main__":
    transformed_data_uri = "data/transformed_data.csv"  # This would be passed as an input variable
    load_data(transformed_data_uri)
