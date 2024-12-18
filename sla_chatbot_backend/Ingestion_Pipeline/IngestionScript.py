import os
import time
import math
from watchdog.observers import Observer
from dateutil.relativedelta import relativedelta
from watchdog.events import FileSystemEventHandler
from typing import List
import re
from pypdf import PdfReader
from openpyxl import load_workbook
import pandas as pd
import numpy as np
from datetime import timedelta
from sympy import symbols,sympify

def extract_guardrail_data(file_path: str):
    # Load the workbook and select the specific sheet
    workbook = load_workbook(file_path)
    sheet = workbook["MSRE - Linux"]
    # Define the data range and extract data
    data_range = sheet['C4:D16']
    extracted_guardrail_data = []
    for row in data_range:
        extracted_row = [cell.value for cell in row]
        extracted_guardrail_data.append(extracted_row)
    # Define the C3 guardrail to be removed
    C3_guardrail = ['Min', 0.994]
    # Remove C3 guardrail if it exists
    if C3_guardrail in extracted_guardrail_data:
        extracted_guardrail_data.remove(C3_guardrail)
    # Convert maximums to minimums
    for item in extracted_guardrail_data:
        if item[0] == 'Max':
            item[0] = 'Min'
            item[1] = 1 - item[1]
    return extracted_guardrail_data

def read_pdf(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        return f"File {pdf_path} does not exist."
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            num_pages = len(reader.pages)
            text = ""
            for i in range(num_pages):
                try:
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    if page_text is not None:
                        text += page_text.encode('utf-8', 'ignore').decode('utf-8')
                    # print(f"Processed page {i+1}/{num_pages} successfully")
                except Exception as page_error:
                    print(f"Error processing page {i+1}: {str(page_error)}")
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        return text
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return ""
def filter_chunks(chunks: List[str]) -> List[str]:
    filtered_chunks = []
    keywords = ['=', 'SLO calculation']
    for chunk in chunks:
        if any(keyword in chunk for keyword in keywords):
            filtered_chunks.append(chunk)
    return filtered_chunks
def chunk_text(text: str, chunk_size: int = 512) -> List[str]:
    # Define a regex pattern to match numbered paragraphs (e.g., "1. ", "2. ", etc.)
    pattern = r'^\d+\.\s+'
    # Check if the text contains the pattern
    if re.search(pattern, text, flags=re.MULTILINE):
        return custom_chunk_text(text, chunk_size)
    else:
        return nltk_chunk_text(text, chunk_size)


def nltk_chunk_text(text: str, chunk_size: int = 512) -> List[str]:
    # Use NLTK to tokenize by paragraphs
    paragraphs = blankline_tokenize(text)
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) <= chunk_size:
            current_chunk += paragraph + "\n\n"  # Adding \n\n to separate paragraphs
        else:
            chunks.append(current_chunk)
            current_chunk = paragraph + "\n\n"
    # Append the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
    
def custom_chunk_text(text: str, chunk_size: int = 512) -> List[str]:
    # Pattern to match numbered paragraphs (e.g., "1. ", "2. ", etc.)
    pattern = r'^\d+\.\s+'
    chunks = []
    current_chunk = []
    # Split text into lines
    lines = text.splitlines()
    for line in lines:
        if re.match(pattern, line.strip()):
            # Start a new chunk if we encounter a numbered paragraph
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
        current_chunk.append(line.strip())
    # Append the last chunk
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks
def extract_relevant_chunks(chunks: List[str]) -> List[str]:
    filtered_chunks = []
    keywords = ['=', 'SLO calculation']
    for chunk in chunks:
        if any(keyword in chunk for keyword in keywords):
            filtered_chunks.append(chunk)
    return filtered_chunks

def extract_equations_and_variables(text):
    # Extract equations
    equation_pattern =r'(\w+(?:\s*Credit)?)\s*=\s*((?:[A-Z]|\d+)(?:\s*[\+\-\*\/x]\s*(?:[A-Z]|\d+))*)'
    equations = re.findall(equation_pattern, text)
    formatted_equations = [f"{eq[0]}={eq[1]}" for eq in equations]
    # Extract variable definitions
    variable_defs = re.findall(r'([A-Z])\s*=\s*([^0-9$%\n].+?)(?=\n|$)', text)
    # Create dictionary of variable definitions
    var_dict = {}
    for var, definition in variable_defs:
        # Remove leading/trailing whitespace and any trailing periods
        cleaned_def = definition.strip().rstrip('.')
        if var not in var_dict:
            var_dict[var] = cleaned_def
        elif len(cleaned_def) > len(var_dict[var]):
            # If we find a longer definition, use that instead
            var_dict[var] = cleaned_def

    return formatted_equations, var_dict

def normalize_equation(equation):
    """Normalize the equation by replacing 'x' with '*' and removing spaces."""
    equation = equation.replace('x', '*')
    return re.sub(r'\s+', '', equation)

def filter_and_prepare_equations(equations):
    """Filter and prepare equations, returning a list of unique normalized equations."""
    unique_equations = {}
    
    for equation in equations:
        if re.search(r'\d', equation):  # Skip equations containing digits
            continue
        
        parts = equation.split('=')
        if len(parts) != 2:  # Ensure there are exactly two parts
            continue
        
        left, right = parts
        normalized_right = normalize_equation(right)
        
        if normalized_right not in unique_equations:
            unique_equations[normalized_right] = {
                'left': left.strip(),
                'right': right.strip(),
                'variables': [var for var in re.findall(r'[A-Za-z]', normalized_right) if var != 'x']
            }
    
    return list(unique_equations.values())

def compute_function(equation, values):
    """Calculate the result of the equation using the provided variable values."""
    left = equation['left']
    right = equation['right'].replace('x', '*')
    
    # Create symbolic variables
    sympy_vars = {var: symbols(var) for var in equation['variables']}
    sympy_expr = sympify(right)
    
    # Substitute values into the expression
    result = sympy_expr.subs(values)
    return result,f"{left} = {result}"

def calculate_equation(equations_list, parameters):
    """Main function to filter equations and calculate results based on available parameters."""
    filtered_equations = filter_and_prepare_equations(equations_list)

    print("Filtered and prepared equations:")
    for eq in filtered_equations:
        print(f"Left: {eq['left']}, Right: {eq['right']}, Variables: {eq['variables']}")

    # print("\nCalculations:")
    for eq in filtered_equations:
        required_vars = set(eq['variables'])
        available_vars = set(parameters.keys())
        if required_vars.issubset(available_vars):
            result,result_string = compute_function(eq, parameters)
            return result,result_string,eq
    else:
        print("No equations could be calculated with the available parameters.")
        return None,None,None
def calc_parameters(variables):
    # This function simulates getting parameters from an external source - Will need to implement later.
    return {"D": 30000, "B": 0.02, "C": 0.05}

def count_total_items(df, filename, category):
    df = pd.read_excel(filename)
    if category == 'Risk and Compliance-Vulnerabilities Assigned Remidiated':
        return df.shape[0]
    elif category == "Service Operations-EOC Calls responded within 5 min":
        return df.shape[0]
    elif category.startswith('Service Operations-'):
        if 'EOC Captured Impact/Urgency' in df.columns:
            incident_level = {
                'Service Operations-Moderate Incidents Restoration within 6 hours': 'Medium/Medium',
                'Service Operations-High Incidents Restoration within 4 hours': 'High/High',
                'Service Operations-Critical Incidents Restoration within 4 hours': 'Critical/Critical'
            }.get(category, '')
            return df[df['EOC Captured Impact/Urgency'] == incident_level].shape[0]
    return 0

import math

def populate_comments(df, eoc_file_names, risk_file_names):
    for index, row in df.iterrows():
        category = row['category']
        actual = row['actual_service_level']
        expected = row['service_target']
        month = row['actual_service_date']

        # Skip if actual service level is NaN
        if math.isnan(actual):
            continue

        if category == 'Availability-C4 Platforms':
            if actual == 100:
                df.at[index, 'Comments'] = "There was no business outage"
            elif actual < expected:
                df.at[index, 'Comments'] = "The availability is below the threshold."
            elif actual > expected:
                df.at[index, 'Comments'] = "The availability is above the threshold"

        elif category == 'Risk and Compliance-Vulnerabilities Assigned Remidiated':
            filename = risk_file_names.get(month, '')
            if filename:
                total_vulnerabilities = count_total_items(df, filename, category)
                missed_sla = round(total_vulnerabilities * (1 - actual / 100))
                df.at[index, 'Comments'] = f"{missed_sla} out of {total_vulnerabilities} vulnerabilities missed the SLA"

        elif category in ['Service Operations-Moderate Incidents Restoration within 6 hours',
                          'Service Operations-High Incidents Restoration within 4 hours',
                          'Service Operations-Critical Incidents Restoration within 4 hours']:
            filename = eoc_file_names.get(month, '')
            if filename:
                total_incidents = count_total_items(df, filename, category)
                missed_sla = round(total_incidents * (1 - actual / 100))
                df.at[index, 'Comments'] = f"{missed_sla} out of {total_incidents} incidents missed the response time SLA"

        elif category == 'Service Operations-EOC Calls responded within 5 min':
            filename = eoc_file_names.get(month, '')
            if filename:
                total_calls = count_total_items(df, filename, category)
                # print(total_calls)
                if actual == 100:
                    df.at[index, 'Comments'] = "All EoC calls answered within 5 mins"
                else:
                    missed_sla = round(total_calls * (1 - actual / 100))
                    df.at[index, 'Comments'] = f"{missed_sla} out of {total_calls} incidents missed the response time SLA"

    return df

# Define function to calculate actual service level for EOC Calls responded within 5 min
def calculate_actual_service_level_eoc(df,filename):
    df = pd.read_excel(filename)
    total_rows = df.shape[0]
    if total_rows == 0:
        return np.nan  # If no rows, return NaN
    # Convert 'Response Time- dummy data' to timedelta format
    df['Response Time- dummy data'] = pd.to_timedelta(df['Response Time- dummy data'])
    # Calculate percentage of rows with response time less than 5 minutes
    count_less_than_5_min = (df['Response Time- dummy data'] < pd.Timedelta(minutes=5)).sum()
    actual_service_level = round((count_less_than_5_min / total_rows) * 100,2)
    return actual_service_level

# Define function to calculate actual service level for incident restoration categories
def calculate_actual_service_level_restoration(df,filename, threshold_hours, incident_level):
    df = pd.read_excel(filename)
    # Convert 'Engagement Time- dummy data' to timedelta format
    df['Engagement Time- dummy data'] = pd.to_timedelta(df['Engagement Time- dummy data'])
    # Filter rows based on incident level and calculate actual service level
    filtered_df = df[df['EOC Captured Impact/Urgency'] == incident_level]
    total_rows = filtered_df.shape[0]
    if total_rows == 0:
        return np.nan  # If no rows, return NaN
    # Calculate percentage of rows with engagement time less than threshold
    count_less_than_threshold = (filtered_df['Engagement Time- dummy data'] < pd.Timedelta(hours=threshold_hours)).sum()
    actual_service_level = round((count_less_than_threshold / total_rows) * 100,2)
    return actual_service_level

def calculate_risk(df,filename):
    try:
        df = pd.read_excel(filename)
        # Function to extract number of days from INCIDENT_AGE
        def extract_days(age_str):
            # print(age_str)
            days_pattern = r'(\d+) day'
            days_match = re.search(days_pattern, age_str)
            if days_match:
                return int(days_match.group(1))
            else:
                return 0
        # Convert INCIDENT_AGE to number of days
        df['INCIDENT_AGE_days'] = df['INCIDENT_AGE'].apply(extract_days)
        # Calculate risk percentage based on Priority and INCIDENT_AGE_days
        total_rows = df.shape[0]
        if total_rows == 0:
            return np.nan
        met_count = 0
        for index, row in df.iterrows():
            if row['Priority '] == 5:
                if row['INCIDENT_AGE_days'] < 48:
                    met_count += 1
            else:
                if row['INCIDENT_AGE_days'] < 30:
                    met_count += 1
        percentage_met = round((met_count / total_rows) * 100, 2)
        return percentage_met
    
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return np.nan

def availability_list_creation(availability_file):
    availability_df = pd.read_excel(availability_file)
    availability_list = {}
    
    # Convert 'Month' column to datetime and format it
    availability_df['Month'] = pd.to_datetime(availability_df['Month'], format='%b-%y')
    availability_df['formatted_date'] = availability_df['Month'].dt.strftime('%b %Y')
    
    # Create the availability list and formatted dates list
    for _, row in availability_df.iterrows():
        month = row['formatted_date']
        availability = row['Availability'] # Remove the % sign
        availability_list[month] = availability*100
    
    formatted_dates = availability_df['formatted_date'].tolist()
    print(formatted_dates)
    return availability_list, formatted_dates
    
def dataframe_creation(formatted_dates, categories, availability_list, data_sources, expected_thresholds):
    data = []
    for date in formatted_dates:
        for idx, category in enumerate(categories):
            actual_service_level = availability_list[date] if category == 'Availability-C4 Platforms' else float('nan')
            data.append({
                'actual_service_date': date,
                'category': category,
                'data_source': data_sources[idx],
                'service_target': expected_thresholds[idx],
                'actual_service_level': actual_service_level,
                'service_credits': float('nan'),
                'breach_detected':'',
                'Comments': '',
                'Equation': '',
                'Earnback': float('nan')
            })
    new_dataframe = pd.DataFrame(data)
    return new_dataframe

def Actual_service_level_calculation(new_dataframe, eoc_file_names, risk_file_names):
    # Calculate actual_service_level for EOC calls responded
    for date, filename in eoc_file_names.items():
        idx_eoc = new_dataframe[(new_dataframe['actual_service_date'] == date) & (new_dataframe['category'] == 'Service Operations-EOC Calls responded within 5 min')].index
        if not idx_eoc.empty:
            actual_service_level_eoc = calculate_actual_service_level_eoc(new_dataframe, filename)
            new_dataframe.loc[idx_eoc, 'actual_service_level'] = actual_service_level_eoc

    # Calculate actual_service_level for incident restoration categories
    for date, filename in eoc_file_names.items():
        # For 'Service Operations-High Incidents Restoration within 4 hours'
        idx_high = new_dataframe[(new_dataframe['actual_service_date'] == date) & (new_dataframe['category'] == 'Service Operations-High Incidents Restoration within 4 hours')].index
        if not idx_high.empty:
            actual_service_level_high = calculate_actual_service_level_restoration(new_dataframe, filename, 4, 'High/High')
            new_dataframe.loc[idx_high, 'actual_service_level'] = actual_service_level_high
    
        # For 'Service Operations-Critical Incidents Restoration within 4 hours'
        idx_critical = new_dataframe[(new_dataframe['actual_service_date'] == date) & (new_dataframe['category'] == 'Service Operations-Critical Incidents Restoration within 4 hours')].index
        if not idx_critical.empty:
            actual_service_level_critical = calculate_actual_service_level_restoration(new_dataframe, filename, 4, 'Critical/Critical')
            new_dataframe.loc[idx_critical, 'actual_service_level'] = actual_service_level_critical
    
        # For 'Service Operations-Moderate Incidents Restoration within 6 hours'
        idx_moderate = new_dataframe[(new_dataframe['actual_service_date'] == date) & (new_dataframe['category'] == 'Service Operations-Moderate Incidents Restoration within 6 hours')].index
        if not idx_moderate.empty:
            actual_service_level_moderate = calculate_actual_service_level_restoration(new_dataframe, filename, 6, 'Medium/Medium')
            new_dataframe.loc[idx_moderate, 'actual_service_level'] = actual_service_level_moderate

    # Calculate actual_service_level for Risk
    for date, filename in risk_file_names.items():
        try:
            idx_high = new_dataframe[(new_dataframe['actual_service_date'] == date) & (new_dataframe['category'] == 'Risk and Compliance-Vulnerabilities Assigned Remidiated')].index
            if not idx_high.empty:
                actual_risk = calculate_risk(new_dataframe, filename)
                new_dataframe.loc[idx_high, 'actual_service_level'] = actual_risk
                # print("Date:", date, "Risk:", actual_risk)
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    return new_dataframe

def has_non_zero(value):
    return value != 0

def get_previous_month(date_str):
    date = pd.to_datetime(date_str, format='%b %Y')
    prev_date = date - relativedelta(months=1)
    return prev_date.strftime('%b %Y')



def check_slo_breach(df, df_row, Amount):
    actual_service_level = df_row['actual_service_level']
    service_target = df_row['service_target']
    category = df_row['category']
    current_date = df_row['actual_service_date']

    if pd.notna(actual_service_level):
        threshold_value = service_target
        chargeback = 0.0
        if actual_service_level < threshold_value:
            
            penalty_percentage = 100  # Default penalty percentage
            prev_month = get_previous_month(current_date)
            prev_prev_month = get_previous_month(prev_month)
            prev_prev_prev_month = get_previous_month(prev_prev_month)

            # Check for consecutive breaches
            if prev_month in df['actual_service_date'].values:
                prev_month_penalty = df[(df['actual_service_date'] == prev_month) & (df['category'] == category)]['service_credits']
                if has_non_zero(prev_month_penalty.values[0]):
                    penalty_percentage = 125

            if prev_prev_month in df['actual_service_date'].values:
                prev_prev_month_penalty = df[(df['actual_service_date'] == prev_prev_month) & (df['category'] == category)]['service_credits']
                if has_non_zero(prev_prev_month_penalty.values[0]):
                    prev_month_penalty = df[(df['actual_service_date'] == prev_month) & (df['category'] == category)]['service_credits']
                    if has_non_zero(prev_month_penalty.values[0]):
                        penalty_percentage = 150
                    else:
                        penalty_percentage = 100  # Reset to 100 if not consecutive

            if prev_prev_prev_month in df['actual_service_date'].values:
                prev_prev_prev_month_penalty = df[(df['actual_service_date'] == prev_prev_prev_month) & (df['category'] == category)]['service_credits']
                if has_non_zero(prev_prev_prev_month_penalty.values[0]):
                    prev_prev_month_penalty = df[(df['actual_service_date'] == prev_prev_month) & (df['category'] == category)]['service_credits']
                    if has_non_zero(prev_prev_month_penalty.values[0]):
                        prev_month_penalty = df[(df['actual_service_date'] == prev_month) & (df['category'] == category)]['service_credits']
                        if has_non_zero(prev_month_penalty.values[0]):
                            penalty_percentage = 150
                        else:
                            penalty_percentage = 100  # Reset to 100 if not consecutive
                    else:
                        penalty_percentage = 100  # Reset to 100 if not consecutive

            slo_breach_penalty = float(Amount) * (penalty_percentage / 100)
            multiplier = f"{penalty_percentage/100}"
            return slo_breach_penalty, multiplier, chargeback, 'Yes'

    
    # if pd.notna(actual_service_level):
    #     threshold_value = service_target
    #     chargeback = 0.0
    #     if actual_service_level < threshold_value:
            
    #         penalty_percentage = 100  # Default penalty percentage
    #         prev_month = get_previous_month(current_date)
    #         prev_prev_month = get_previous_month(prev_month)

    #         if prev_month in df['actual_service_date'].values:
    #             prev_month_penalty = df[(df['actual_service_date'] == prev_month) & (df['category'] == category)]['service_credits']
    #             if has_non_zero(prev_month_penalty.values[0]):
    #                 penalty_percentage = 125
            
    #         if prev_prev_month in df['actual_service_date'].values:
    #             prev_prev_month_penalty = df[(df['actual_service_date'] == prev_prev_month) & (df['category'] == category)]['service_credits']
    #             if has_non_zero(prev_prev_month_penalty.values[0]):
    #                 prev_month_penalty = df[(df['actual_service_date'] == prev_month) & (df['category'] == category)]['service_credits']
    #                 if has_non_zero(prev_month_penalty.values[0]):
    #                     penalty_percentage = 150 
    #                 else:
    #                     penalty_percentage = 125
            
    #         slo_breach_penalty = float(Amount) * (penalty_percentage / 100)
    #         multiplier = f"{penalty_percentage/100}"
    #         return slo_breach_penalty, multiplier, chargeback, 'Yes'
        
        else:
            prev_month = get_previous_month(current_date)
            prev_prev_month = get_previous_month(prev_month)
            prev_prev_prev_month = get_previous_month(prev_prev_month)
            
            if prev_month in df['actual_service_date'].values and prev_prev_month in df['actual_service_date'].values:
                prev_month_penalty = df[(df['actual_service_date'] == prev_month) & (df['category'] == category)]['service_credits']
                prev_prev_month_penalty = df[(df['actual_service_date'] == prev_prev_month) & (df['category'] == category)]['service_credits']
                if has_non_zero(prev_prev_month_penalty.values[0]) and not has_non_zero(prev_month_penalty.values[0]):
                    chargeback = round(0.4 * Amount, 2)

            if all(month in df['actual_service_date'].values for month in [prev_month, prev_prev_month, prev_prev_prev_month]):
                pm_penalty = df[(df['actual_service_date'] == prev_month) & (df['category'] == category)]['service_credits']
                ppm_penalty = df[(df['actual_service_date'] == prev_prev_month) & (df['category'] == category)]['service_credits']
                pppm_penalty = df[(df['actual_service_date'] == prev_prev_prev_month) & (df['category'] == category)]['service_credits']
                if has_non_zero(pppm_penalty.values[0]) and not has_non_zero(ppm_penalty.values[0]) and not has_non_zero(pm_penalty.values[0]): 
                    chargeback = round(0.45 * Amount, 2) 
            
            return 0, None, chargeback, 'No'
    
    return None, None, None, 'No'

def categorize_files(folder):
    risk_file_names = {}
    eoc_file_names = {}
    availability_file = None
    guardrail_file = None
    contract_file = None
    files = os.listdir(folder)
    
    for file in files:
        filepath = os.path.join(folder, file)
        if file.startswith('Availability'):
            availability_file = filepath
        elif 'Risk' in file:
            date = extract_date(file)
            if date:
                risk_file_names[date] = filepath
        elif 'EOC' in file:
            date = extract_date(file)
            if date:
                eoc_file_names[date] = filepath
        elif file.lower() == 'cips - slo data.xlsx':
            guardrail_file = filepath
        elif 'contract' in file.lower():
            contract_file = filepath
    return risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file
    
def extract_date(filename):
    # Extracting the date in the format 'MMM YYYY' from the filename
    parts = filename.split('_')
    if len(parts) >= 3:
        month_part = parts[1]  # This should be the month (e.g., 'Apr')
        year_part = parts[2][-4:]  # Extracting the last 4 characters for the year (e.g., '2024')
        return f"{month_part} {year_part}"  # Return in 'MMM YYYY' format
    return None

def process_new_file(filepath, risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file):
    try:
        filename = os.path.basename(filepath)
        if filename.startswith('Availability'):
            availability_file = filepath
        elif 'Risk' in filename:
            date = extract_date(filename)
            if date:
                risk_file_names[date] = filepath
        elif 'EOC' in filename:
            date = extract_date(filename)
            if date:
                eoc_file_names[date] = filepath
        elif filename.lower() == 'cips - slo data.xlsx':
            guardrail_file = filepath
        elif 'contract' in filename.lower():
            contract_file = filepath
        # Call process_files with updated file lists
        process_files(risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file)

    except Exception as e:
        logging.error(f"Error processing file {filepath}: {str(e)}")

class MyHandler(FileSystemEventHandler):
    def __init__(self, risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file):
        self.risk_file_names = risk_file_names
        self.eoc_file_names = eoc_file_names
        self.availability_file = availability_file
        self.guardrail_file = guardrail_file
        self.contract_file = contract_file

    def on_created(self, event):
        if not event.is_directory:
            # Handle new file creation
            filepath = event.src_path
            process_new_file(filepath, self.risk_file_names, self.eoc_file_names, 
                             self.availability_file, self.guardrail_file, self.contract_file)

def start_monitoring(folder, risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file):
    event_handler = MyHandler(risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file)
    observer = Observer()
    observer.schedule(event_handler, folder, recursive=False)
    observer.start()
    print(f"Monitoring folder '{folder}' for new files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    
def process_files(risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file):
    categories = [
        'Availability-C4 Platforms',
        'Risk and Compliance-Vulnerabilities Assigned Remidiated',
        'Service Operations-EOC Calls responded within 5 min',
        'Service Operations-Critical Incidents Restoration within 4 hours',
        'Service Operations-High Incidents Restoration within 4 hours',
        'Service Operations-Moderate Incidents Restoration within 6 hours',
        'Service Operations-No of High/Critical Incidents due to missed alerts',
        'Service Operations-No of High/Critical Incidents due to Change Requests / Process Errors',
        'Service Operations-Repetition of hardware failures within 24 hours'
    ]
    data_sources = [
        'CHAIN', 'SCRM Dashboard/Infosec', 'SINATRA/Webex space', 'Sinatra', 'Sinatra',
        'Sinatra', 'Smartsheet', 'ESP', 'ESP'
    ]
    extracted_guardrail_data = extract_guardrail_data(guardrail_file)
    expected_thresholds = [value[1]*100 for value in extracted_guardrail_data]
    contract_text = read_pdf(pdf_path=contract_file)
    chunks = chunk_text(contract_text)
    Relevant_chunks = extract_relevant_chunks(chunks)
    equations_list, variables = extract_equations_and_variables(Relevant_chunks[0])
    # print(variables)
    filtered_equations = filter_and_prepare_equations(equations_list)
    # print("Filtered Equations:", filtered_equations)
    # print("Variable definitions found:", variables)
    result, result_string, equation_used = calculate_equation(equations_list, calc_parameters(variables))
    # print("output of calculation:", result_string)
    availability_list, formatted_dates = availability_list_creation(availability_file)
    
    # Creation of Dataframe
    new_dataframe = dataframe_creation(formatted_dates, categories, availability_list, data_sources, expected_thresholds)
    # Actual Service Level 
    new_dataframe = Actual_service_level_calculation(new_dataframe, eoc_file_names, risk_file_names)
    # Comment section
    new_dataframe = populate_comments(new_dataframe, eoc_file_names, risk_file_names)
    # Penalty Calculation
    Amount = result
    
    # Iterate over the DataFrame rows
    for i in range(len(new_dataframe)):
        slo_breach_penalty, multiplier, chargeback, breach = check_slo_breach(new_dataframe, new_dataframe.iloc[i], Amount)
        if chargeback:
            chargeback = float(chargeback)
        else:
            chargeback = 0.0
        
        new_dataframe.at[i, 'breach_detected'] = breach
        new_dataframe.at[i, 'service_credits'] = slo_breach_penalty
        if multiplier:
            values = calc_parameters(equation_used['variables'])
            var_definitions = [
                f"{var}: {variables[var]} (Value: {values.get(var, 'Not available')})"
                for var in equation_used['variables']
            ]
            var_definition_str = "; ".join(var_definitions)
            new_dataframe.at[i, 'Equation'] = f"{equation_used['left']} = ({equation_used['right']}) * {multiplier}; Here the variables used are {var_definition_str}"
        new_dataframe.at[i, 'Earnback'] = chargeback

    # Removing Rows where we don't have data.
    new_dataframe = new_dataframe.dropna(subset=['actual_service_level'])
    
    # Write File to CSV and JSON
    new_dataframe.to_csv('Test.csv', index=False)
    new_dataframe.to_json('../event_payload.json', orient='records')
    print("JSON File Created")
    print("Continuing to monitor the folder for new files...")
    return

if __name__ == "__main__":
    input_folder = 'Ingest_Input'
    # output_folder = 'Ingest_Output'
    # Initialize file lists
    risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file = categorize_files(input_folder)
    # Process initial files
    process_files(risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file)
    # Start monitoring the input folder for new files
    start_monitoring(input_folder, risk_file_names, eoc_file_names, availability_file, guardrail_file, contract_file)
