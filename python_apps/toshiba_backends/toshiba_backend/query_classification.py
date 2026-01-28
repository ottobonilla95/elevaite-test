import pandas as pd
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from abbreviation_dict import ABBREVIATION_TABLE
load_dotenv('.env.local')

HEADER_LOC = 1000
NUM_ROWS_TO_PROCESS = 1000

class QueryClassifier:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.classification_prompt = """
You are an expert information extractor specialized in TGCS (Toshiba Global Commerce Solutions) field engineering operations queries.

Analyze the following user query or message: "{input_text_here}".

Extract or infer the following details as key-value pairs in a JSON object. Your output must adhere strictly to TGCS guidelines:

    •	"query_type": Must be exactly one of the following predefined types (choose the single best match; if none fit perfectly, use "miscellaneous"):
  - "part number" (for queries that provide a part number or describe a part. Note: any 7-digit or 11-digit alphanumeric code is also a part number. For example, 80Y1564, 3AC01587100, 3AC01548000, etc.)
  - "how-to" (for queries about installation, troubleshooting, or similar guidance)
  - "definition" (for queries seeking definitions or explanations of terms/concepts)
  - "client advocates" (for queries seeking client advocate, etc)
  - "sql" (for queries seeking SQL data)
  - "troubleshooting" (for queries seeking troubleshooting steps)
  - "miscellaneous" (for all other queries that don't fall in any of the above categories)

    •	"machine_type": The type and model of any TGCS-related machine, device, or product mentioned (e.g., "6200" or "4610"). If none is mentioned or it's not TGCS-specific, use "not specified".
    •	"machine_model": The model of any TGCS-related machine, device, or product mentioned (e.g., "1NR" or "080"). If none is mentioned or it's not TGCS-specific, use "not specified".
    •	"machine_name": The name of any TGCS-related machine, device, or product mentioned (e.g., "SureBase" or "NetVista"). If none is mentioned or it's not TGCS-specific, use "not specified".
    Here is the list of all machine types and models:
    {abbreviation_table}

    •	"customer_name": The name of the customer or client mentioned (e.g., "Kroger", "Walgreens"). Match or infer from this exhaustive list of known TGCS clients, canonicalizing any aliases to the primary name: Walgreens, Kroger (including Harris Teeter), Sam's Club, Tractor Supply, Dollar General, Wegmans, Ross, Costco, Whole Foods, BJs or BJ's, Alex Lee, Badger, Best Buy, CAM, Hudson News, IDKIDS, Saks, CVS, At Home, Harbor Freight, Spartan Nash, Event network, Foodland, Cost Plus World Market, Enterprise, Red Apple, Bealls, Disney, Ovation Foods, Yum Brands (including KFC), Nike, ABC Stores, Tommy Bahama, Gordon Food Service, Michaels, Dunn Edwards, BP, Northern Tool, Winn Dixie, PVH, Tommy Hilfiger, Calvin Klein, Ahold, Stop & Shop, Giant Martin's, Bfresh, Fresh Market, Times Supermarkets, MLSE (Maple Leaf Sports & Entertainment), Coach, TCA (Travel Centers of America), Bass Pro, Kirkland, Simmons Bank, GNC, Zara, STCR, Boston Pizza, LCBO (Liquor Control Board of Ontario), NLLC (Newfoundland and Labrador Liquor Corporation), Husky, Princess Auto, Albertson (including Safeway), Signature Aviation, New Brunswick Liquor Corporation (Alcool NB Liquor Corporation or ANBL). If none is mentioned, no match is found in the list, or it's anonymous, use "not provided".

Output only the JSON object, nothing else. Ensure it's valid JSON.
"""

    def classify_query(self, query_text):
        """Classify a single query using OpenAI API"""
        try:
            prompt = self.classification_prompt.format(input_text_here=query_text, abbreviation_table=ABBREVIATION_TABLE)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            result = response.choices[0].message.content.strip()
            # print(f"Raw API response: {result[:200]}...")  # Debug output

            if not result:
                raise ValueError("Empty response from API")

            # Remove markdown code block formatting if present
            if result.startswith('```json'):
                result = result[7:]  # Remove ```json
            if result.startswith('```'):
                result = result[3:]  # Remove ```
            if result.endswith('```'):
                result = result[:-3]  # Remove trailing ```
            result = result.strip()

            return json.loads(result)
        
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # print(f"Raw response: {result if 'result' in locals() else 'No response'}")
            return {
                "query_type": "miscellaneous",
                "machine_type": "not specified",
                "machine_model": "not specified", 
                "machine_name": "not specified",
                "customer_name": "not provided"
            }
        except Exception as e:
            print(f"Error classifying query: {e}")
            return {
                "query_type": "miscellaneous",
                "machine_type": "not specified",
                "machine_model": "not specified",
                "machine_name": "not specified", 
                "customer_name": "not provided"
            }

    def process_excel_file(self, file_path, num_rows=NUM_ROWS_TO_PROCESS):
        """Process Excel file and classify queries"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Limit to specified number of rows
            df = df.iloc[HEADER_LOC:HEADER_LOC+num_rows]
            
            results = []
            
            for index, row in df.iterrows():
                original_request = str(row.get('Original Request', ''))
                processed_request = str(row.get('Processed Request', ''))
                
                # Use processed request if available, otherwise original
                query_to_classify = processed_request if processed_request and processed_request != 'nan' else original_request
                
                print(f"Processing row {index + 1}/{num_rows}: {query_to_classify[:100]}...")
                
                classification = self.classify_query(query_to_classify)
                
                result = {
                    'query_id': row.get('Query ID', ''),  # Primary key from input file
                    'row_index': index,
                    'original_request': original_request,
                    'processed_request': processed_request,
                    'query_used_for_classification': query_to_classify,
                    **classification
                }
                
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error processing Excel file: {e}")
            return []

def main():
    classifier = QueryClassifier()

    # Process the Excel file
    results = classifier.process_excel_file('no_feedback_queries.xlsx', num_rows=NUM_ROWS_TO_PROCESS)

    # Save results to JSON
    with open(f'no_feedback_classification_results_{str(HEADER_LOC)}.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Create summary DataFrame
    df_results = pd.DataFrame(results)
    df_results.to_csv(f'no_feedback_classification_results_{str(HEADER_LOC)}.csv'+str(HEADER_LOC), index=False)

    print(f"\nProcessed {len(results)} queries")
    print("Results saved to 'no_feedback_classification_results.json' and 'no_feedback_classification_results.csv'")

    # Print summary
    if results:
        query_types = [r['query_type'] for r in results]
        print("\nQuery type distribution:")
        for qt in set(query_types):
            count = query_types.count(qt)
            print(f"  {qt}: {count}")

if __name__ == "__main__":
    main()