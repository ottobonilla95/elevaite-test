import pandas as pd

# Check what's actually in your Excel file
excel_path = "temp/MTMs For Dashboard.xlsx"
df = pd.read_excel(excel_path)

print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print("First few rows:")
print(df.head(3))