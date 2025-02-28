from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import pandas as pd
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

app = FastAPI()
load_dotenv()

origins = [
    "https://localhost:3000",
    "http://localhost:3000",
    "https://elevaite-creative-insight.iopex.ai",
    "http://elevaite-creative-insight.iopex.ai",
]


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
)

# Directory where the CSV files are stored
CSV_DIR = os.getenv("CSV_DIR_PATH")
CREATIVE_CSV_FILE = os.getenv("CREATIVE_CSV_FILE")
CAMPAIGN_CSV_FILE = os.getenv("CAMPAIGN_CSV_FILE")

# print(CSV_DIR,CREATIVE_CSV_FILE,CAMPAIGN_CSV_FILE)

# Load the CSVs
try:
    creative_df = pd.read_csv(os.path.join(CSV_DIR, CREATIVE_CSV_FILE))
    creative_df = creative_df.fillna('')
except FileNotFoundError as e:
    print(f"Error loading creative CSV file: {e}")
    creative_df = pd.DataFrame()  # empty dataframe as fallback
except pd.errors.EmptyDataError as e:
    print(f"Error: CSV file is empty: {e}")
    creative_df = pd.DataFrame()  # empty dataframe as fallback
except Exception as e:
    print(f"Unexpected error loading creative CSV: {e}")
    creative_df = pd.DataFrame()  # empty dataframe as fallback

try:
    campaign_df = pd.read_csv(os.path.join(CSV_DIR, CAMPAIGN_CSV_FILE))
except FileNotFoundError as e:
    print(f"Error loading campaign CSV file: {e}")
    campaign_df = pd.DataFrame()  # empty dataframe as fallback
except pd.errors.EmptyDataError as e:
    print(f"Error: CSV file is empty: {e}")
    campaign_df = pd.DataFrame()  # empty dataframe as fallback
except Exception as e:
    print(f"Unexpected error loading campaign CSV: {e}")
    campaign_df = pd.DataFrame()  # empty dataframe as fallback
    
@app.get("api/hc")
async def hc():
    return {"status":"LIVE"}

@app.get("/api/adsurface_brand_pairs")
async def get_adsurface_brand_pairs():
    try:
        pairs = creative_df[['Ad_Surface', 'Brand']].drop_duplicates().to_dict('records')
        print("Sent Pairs:", pairs)
        return {"adsurface_brand_pairs": pairs}
    except KeyError as e:
        print(f"Error in get_adsurface_brand_pairs: Missing expected column - {e}")
        return {"error": f"Missing expected column in the data: {e}"}
    except Exception as e:
        print(f"Unexpected error in get_adsurface_brand_pairs: {e}")
        return {"error": f"Unexpected error: {e}"}

@app.get("/api/campaign_data")
async def get_campaign_data(ad_surface: str, brand: str):
    try:
        print(f"Request received for ad_surface: {ad_surface}, brand: {brand}")
        
        # Filter the creative and campaign data
        filtered_creative_df = creative_df[(creative_df['Ad_Surface'] == ad_surface) & (creative_df['Brand'] == brand)]
        filtered_campaign_df = campaign_df[(campaign_df['Ad_Surface'] == ad_surface) & (campaign_df['Brand'] == brand)]
        
        if filtered_creative_df.empty or filtered_campaign_df.empty:
            print(f"No data found for ad_surface: {ad_surface}, brand: {brand}")
            return {"error": f"No data found for ad_surface: {ad_surface}, brand: {brand}"}
        
        # Extract unique campaigns
        campaigns = filtered_creative_df['Campaign_Name'].unique().tolist()
        creative_data = filtered_creative_df.to_dict('records')
        campaign_data = filtered_campaign_df.to_dict('records')

        print(f"Campaigns found: {campaigns}, Sent Data: {campaign_data}")
        return {
            "campaigns": campaigns,
            "creative_data": creative_data,
            "campaign_data": campaign_data,
        }
    except KeyError as e:
        print(f"Error in get_campaign_data: Missing expected column - {e}")
        return {"error": f"Missing expected column in the data: {e}"}
    except ValueError as e:
        print(f"Error in get_campaign_data: Invalid value encountered - {e}")
        return {"error": f"Invalid value encountered: {e}"}
    except Exception as e:
        print(f"Unexpected error in get_campaign_data: {e}")
        return {"error": f"Unexpected error: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
