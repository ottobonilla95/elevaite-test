from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from model import HealthCheckResponse,ErrorResponse,AdSurfaceBrandPairsResponse,CampaignDataResponse,ReloadResponse,InferencePayload,InferenceResponse
import pandas as pd
from dotenv import load_dotenv
import os
from db_connector import db_connector
from sql_agent_inference import sql_inference
import json
from fastapi.responses import StreamingResponse, JSONResponse


app = FastAPI(    
    title="Creative Insight API",
    description="API for retrieving campaign and creative data for analysis",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
    )

load_dotenv()

origins = [
    "https://localhost:3000",
    "http://localhost:3000",
    "https://elevaite-creative-insight.iopex.ai",
    "http://elevaite-creative-insight.iopex.ai",
    "https://elevaite-assist.iopex.ai"
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
)

CSV_DIR = os.getenv("CSV_DIR_PATH")
if CSV_DIR is None:
    print("WARNING: CSV_DIR_PATH environment variable is not set!")
    CSV_DIR = "/app/csv_files"  # Fallback to a default value

CREATIVE_CSV_FILE = os.getenv("CREATIVE_CSV_FILE")
if CREATIVE_CSV_FILE is None:
    print("WARNING: CREATIVE_CSV_FILE environment variable is not set!")
    CREATIVE_CSV_FILE = "CSV1"  # Fallback to a default value

CAMPAIGN_CSV_FILE = os.getenv("CAMPAIGN_CSV_FILE")
if CAMPAIGN_CSV_FILE is None:
    print("WARNING: CAMPAIGN_CSV_FILE environment variable is not set!")
    CAMPAIGN_CSV_FILE = "CSV2"  # Fallback to a default value

print(f"Using CSV_DIR: {CSV_DIR}")
print(f"Using CREATIVE_CSV_FILE: {CREATIVE_CSV_FILE}")
print(f"Using CAMPAIGN_CSV_FILE: {CAMPAIGN_CSV_FILE}")

# Create directory if it doesn't exist
os.makedirs(CSV_DIR, exist_ok=True)

# Print paths for debugging
print(f"CSV Directory: {CSV_DIR}")
print(f"Creative CSV path: {os.path.join(CSV_DIR, CREATIVE_CSV_FILE)}")
print(f"Campaign CSV path: {os.path.join(CSV_DIR, CAMPAIGN_CSV_FILE)}")

# Load the CSVs
creative_df = pd.DataFrame()  # Initialize with empty dataframe
campaign_df = pd.DataFrame()  # Initialize with empty dataframe

def load_csv_files():
    global creative_df, campaign_df
    
    try:
        creative_path = os.path.join(CSV_DIR, CREATIVE_CSV_FILE)
        if os.path.exists(creative_path):
            creative_df = pd.read_csv(creative_path)
            creative_df = creative_df.fillna('')
            print(f"Successfully loaded creative CSV with {len(creative_df)} rows")
        else:
            print(f"Creative CSV file not found at: {creative_path}")
    except Exception as e:
        print(f"Error loading creative CSV: {e}")
    
    try:
        campaign_path = os.path.join(CSV_DIR, CAMPAIGN_CSV_FILE)
        if os.path.exists(campaign_path):
            campaign_df = pd.read_csv(campaign_path)
            campaign_df = campaign_df.fillna('')
            print(f"Successfully loaded campaign CSV with {len(campaign_df)} rows")
        else:
            print(f"Campaign CSV file not found at: {campaign_path}")
    except Exception as e:
        print(f"Error loading campaign CSV: {e}")

# Load CSV files on startup
load_csv_files()

# Add a reload endpoint to reload CSV files after they've been updated
@app.post("/api/reload_csv",
        response_model=ReloadResponse,
        description="Reloads CSV files from disk to update data")
async def reload_csv_files():
    load_csv_files()
    return {"status": "CSV files reloaded"}

# Rest of your API endpoints...
@app.get("/api/hc", response_model=HealthCheckResponse, 
         description="Health check endpoint to verify API is running")
async def hc():
    return {"status": "LIVE"}

@app.get("/api/adsurface_brand_pairs",response_model=AdSurfaceBrandPairsResponse,
         responses={500: {"model": ErrorResponse}},
         description="Returns all unique Ad Surface and Brand combinations available in the dataset")
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

@app.get("/api/campaign_data", 
         response_model=CampaignDataResponse,
         responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
         description="Returns campaign and creative data filtered by Ad Surface and Brand")
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
        
        print(f"Creative Data Sent:{creative_data}")
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

@app.options("/api/sqlagent")
async def options_sqlagent():
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

@app.post("/api/sqlagent",
          responses={500: {"model": ErrorResponse} ,200: {"model": InferenceResponse},},
          description="Accepts a natural language query and returns a stream of data from the SQL Agent."
          )
async def post_message(inference_payload: InferencePayload):
    try:
        async def event_generator():
            async for chunk in sql_inference(inference_payload):
                yield f"data: {json.dumps(chunk)}\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
