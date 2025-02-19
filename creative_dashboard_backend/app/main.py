from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import pandas as pd
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory where your CSV files are stored
CSV_DIR = "app/csv_files"
CREATIVE_CSV_FILE = "Creative_Data.csv"  # Replace with your actual CSV filename
CAMPAIGN_CSV_FILE = "Campaign_Data.csv"

# Load the CSV file once when the app starts
creative_df = pd.read_csv(os.path.join(CSV_DIR, CREATIVE_CSV_FILE))
campaign_df = pd.read_csv(os.path.join(CSV_DIR, CAMPAIGN_CSV_FILE))

target_directory = "C:/Users/vishnu.krishnan/Iopex/Ingestion Pipeline/static"

app.mount("/static", StaticFiles(directory=target_directory), name="static")

@app.get("/api/adsurface_brand_pairs")
async def get_adsurface_brand_pairs():
    try:
        pairs = creative_df[['Ad_Surface', 'Brand']].drop_duplicates().to_dict('records')
        print("Sent Pairs:",pairs)
        return {"adsurface_brand_pairs": pairs}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/campaign_data")
async def get_campaign_data(ad_surface: str, brand: str):
    try:
        print(f"Request received for ad_surface: {ad_surface}, brand: {brand}")
        filtered_creative_df = creative_df[(creative_df['Ad_Surface'] == ad_surface) & (creative_df['Brand'] == brand)]


        filtered_campaign_df = campaign_df[(campaign_df['Ad_Surface'] == ad_surface) & (campaign_df['Brand'] == brand)]
        if filtered_creative_df.empty or filtered_campaign_df.empty:
            print(f"No data found for ad_surface: {ad_surface}, brand: {brand}")

        campaigns = filtered_creative_df['Campaign_Name'].unique().tolist()
        creative_data = filtered_creative_df.to_dict('records')
        campaign_data = filtered_campaign_df.to_dict('records')

        print(f"Campaigns found: {campaigns}, Sent Data :{campaign_data}")
        return {
            "campaigns": campaigns,
            "creative_data": creative_data,
            "campaign_data": campaign_data,
        }
    except Exception as e:
        print(f"Error in get_campaign_data: {str(e)}")
        return {"error": str(e)}

        
    except Exception as e:
        print(f"Error in get_campaign_data: {str(e)}")
        return {"error": str(e)}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
