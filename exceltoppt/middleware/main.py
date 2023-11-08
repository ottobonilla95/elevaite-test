from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
import logging
import openpyxl
import yaml
import os

from utils import generate_manifest
from utils import generate_summary
from utils import generate_cisco_presentation

current_woring_dir = os.path.dirname(os.path.realpath(__file__))

app = FastAPI()
origins = [
    
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Ensure the "data/Excel" folder exists
        os.makedirs("data/Excel", exist_ok=True)

        # Save the uploaded file to the "data/Excel" folder
        with open(f"data/Excel/{file.filename}", "wb") as f:
            f.write(file.file.read())

        # Open the uploaded Excel file using openpyxl
        excel_file = openpyxl.load_workbook(f"data/Excel/{file.filename}")
        file_path = "data/Excel/{file.filename}"

        # Get the list of sheet names in the Excel file
        sheet_names = excel_file.sheetnames

        return JSONResponse(content={"message": "File uploaded successfully", "sheet_names": sheet_names, "file_path" : file_path}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.post("/generateManifest/")
async def generateManifest(request: Request):
    try:
        data = await request.json()
        file_name = data.get('file_name')
        file_path = data.get('file_path')
        save_dir = data.get('save_dir')

        result = await generate_manifest(file_name, file_path, save_dir)
        if(result["status"] == 200):
            return JSONResponse(content=result, status_code=200)
        
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/getYamlContent/")
async def getYamlContent(file_name: str, yaml_file: str):
    try:
    
        if yaml_file:
            yaml_file_path = os.path.join(current_woring_dir, "data", "Manifest",file_name, yaml_file)
            with open(yaml_file_path, 'r') as file:
                yaml_content = file.read()
                return JSONResponse(content=yaml_content, status_code=200)
        else:
            return JSONResponse(content={"error": "yaml_file_path is not provided."}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

@app.get('/generatePPT/')
async def generate_powerpoint(excel_file: str ,manifest_file: str, folder_name: str):
    try:
        
        excel_file_path = os.path.join("data", "Excel", excel_file)
        manifest_file_path = os.path.join("data", "Manifest", folder_name, manifest_file)
        selected_sheet = manifest_file.split(".")[0]

        summary = await generate_summary(excel_file_path, selected_sheet)
        if(summary["status"] == 200):

            result = generate_cisco_presentation(excel_file_path, manifest_file_path, summary["summary"], selected_sheet)
            return JSONResponse(content = result, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
