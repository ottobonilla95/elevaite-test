from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import logging
import openpyxl
import yaml
import uvicorn
import io 
import os

from utils import generate_manifest
from utils import generate_summary
from utils import generate_cisco_presentation
from utils import generate_presentation
from utils import ask_csv_agent
from utils import Excel_to_dataframe
from utils import Excel_to_Dataframe_auto
from utils import ask_questions
from utils import convert_bytes_to_human_readable


from langchain.document_loaders import CSVLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings

current_woring_dir = os.path.dirname(os.path.realpath(__file__))
csv_file_path = os.path.join(current_woring_dir, "data/Output", "output.csv")

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
        clean_file_name = file.filename.replace(" ", "");
        # Save the uploaded file to the "data/Excel" folder
        with open(f"data/Excel/{file.filename}", "wb") as f:
            f.write(file.file.read())
        file.file.seek(0, 2)  
        size = file.file.tell()  
        file.file.seek(0) 
        size = convert_bytes_to_human_readable(size)
        
        # Open the uploaded Excel file using openpyxl
        excel_file = openpyxl.load_workbook(f"data/Excel/{file.filename}")
        file_path = "data/Excel/{file.filename}"

        # Get the list of sheet names in the Excel file
        sheet_names = excel_file.sheetnames

        return JSONResponse(content={"message": "File uploaded successfully", "sheet_names": sheet_names, "file_path" : file_path, "file_size" : size}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/generateManifest/")
async def generateManifest(file_name: str, file_path: str, save_dir: str):
    try:
        '''data = await request.json()
        file_name = data.get('file_name')
        file_path = data.get('file_path')
        save_dir = data.get('save_dir')'''

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
    
 
@app.get('/askcsvagent/')
async def askCsvAgent(excel_file: str, manifest_file: str, question: str):
    try:
        excel_file_path = os.path.join("data", "Excel", excel_file)
        manifest_file_path = os.path.join("data", "Manifest", excel_file.split(".")[0], manifest_file)
        selected_sheet = manifest_file.split(".")[0]
        if excel_file == "cisco.xlsx":
            df = Excel_to_dataframe(excel_file_path, manifest_file_path, selected_sheet)
            df.to_csv(csv_file_path, index = True)
            loader = CSVLoader(file_path=csv_file_path)
            document = loader.load()
            embeddings = OpenAIEmbeddings()
            index_creator = VectorstoreIndexCreator()
            docsearch = index_creator.from_loaders([loader])
            chain = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=docsearch.vectorstore.as_retriever(), input_key="question")
            response = chain({"question": question})
            return JSONResponse(content = response, status_code=200)
        else:
            df = Excel_to_Dataframe_auto(excel_file_path, selected_sheet, csv_file_path)
            df.to_csv(csv_file_path, index = True)
            loader = CSVLoader(file_path=csv_file_path)
            document = loader.load()
            embeddings = OpenAIEmbeddings()
            index_creator = VectorstoreIndexCreator()
            docsearch = index_creator.from_loaders([loader])
            chain = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=docsearch.vectorstore.as_retriever(), input_key="question")
            response = chain({"question": question})
            return JSONResponse(content = response, status_code=200)
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/downloadppt")
async def download_ppt(ppt_path: str):
    try:
        with open(ppt_path, 'rb') as file:
            content = file.read()
        filename = ppt_path.split("/")[-1]
        
        return StreamingResponse(io.BytesIO(content), media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation', headers={"Content-Disposition": f"attachment; filename={filename}"})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/getppturl")
async def getppturl(ppt_path: str):
    try:
        ppt_name = ppt_path.split('/')[-1]
        url = f"http://localhost:6000/{ppt_name}"

        #os.chdir(ppt_path)
        handler = SimpleHTTPRequestHandler
        with TCPServer(("", 6000), handler) as httpd:
            httpd.serve_forever()
        return url
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
            if folder_name == "cisco":
                sumy = summary["summary"]
                print("calling generate ppt function")
                result = generate_cisco_presentation(excel_file_path, manifest_file_path, sumy, selected_sheet)
                return JSONResponse(content = result, status_code=200)
            else:
                print("inside else")
                sumy = summary["summary"]
                result = generate_presentation(excel_file_path, manifest_file_path, sumy, selected_sheet)
                return JSONResponse(content = result, status_code=200)  
        return JSONResponse(content = summary, status_code=200)
    except Exception as e:
        print("Error from generate ppt: " + str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)
    


