from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import io 
import os
from fastapi.responses import FileResponse

from utils import upload_file
from utils import generate_manifest
from utils import generate_summary
#from utils import generate_presentation
from Presentation import generate_presentation
from utils import Excel_to_dataframe
from utils import Excel_to_Dataframe_auto
from utils import ask_your_doc
from utils import generate_csv_for_excel
from utils import ask_csv_agent



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
async def uploadFile(file: UploadFile = File(...)):
    try:
        response = await upload_file(file)
        if response['response'] == 'Success':
            print("File uploaded successfully")
            res = generate_csv_for_excel(response['file_path'])
            if res['response'] == 'Success':
                return JSONResponse(content=response, status_code=200)
    except Exception as e:
        print("File Upload Failed: " + str(e))
    

@app.get("/generateManifest/")
async def generateManifest(file_name: str, file_path: str, save_dir: str):
    try:

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
            print("inside cisco")
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
        print("askCsvAgent error: " +str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/ask")
async def ask(query_and_context: Request):
    try:
        req_info = await query_and_context.json()
        query = req_info["query"]
        context = req_info["context"]
        answer = await ask_your_doc(query, context)
        return JSONResponse(content=answer, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500) 


@app.get("/downloadppt")
async def download_ppt(ppt_path: str):
    try:
        with open(ppt_path, 'rb') as file:
            content = file.read()
        filename = ppt_path.split("/")[-1]
        
        return StreamingResponse(
            io.BytesIO(content), 
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation', 
            headers={"Content-Disposition": f"attachment; filename={filename}"})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/downloadPPT/")
async def download_presentation(ppt_path: str):
    try:
        if ppt_path:
            return FileResponse(ppt_path, media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        else: 
            return JSONResponse(content={"error": str(e)}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

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
            print("Generating Presentation ...")
            sumy = summary["summary"]
            result = generate_presentation(excel_file_path, manifest_file_path, sumy, selected_sheet)
            response = {"export_url" : result, "summary": sumy}
            return JSONResponse(content = response, status_code=200)
        else:
            print('Unable to create presentation ...')
        return JSONResponse(content = "No Summary", status_code=200)
    except Exception as e:
        print("Error from generate ppt: " + str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get('/genPPT/')
async def generatePPT(type: str, excel_file: str, sheet_name: str):
    try:
        
        excel_file_path = os.path.join("data", "Excel", str(excel_file))

        result = await generate_presentation(str(type), excel_file_path, str(sheet_name))
        if result["status"] == 200:
            response = {"export_url": result["ppt_path"], "summary": result["summary"]}
            return JSONResponse(content = response, status_code=200)
    except Exception as e:
        print("Error from generate ppt: " + str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

@app.post("/convert/")
async def convert_pptx_to_pdf(pptx_path: str):
    pdf_bytes = convert_pptx_to_pdf(pptx_path)

    file_name = (pptx_path.split('/')[-1]).split('.')[0]
    pdf_path = os.path.join("data/pdfs", file_name, ".pdf")
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(pdf_bytes.read())
    return "Sucess"

@app.get('/askagent/')
async def chat_with_csv_agent(workbook_name: str, sheet_name: str, question: str):
    print("Request reached")
    csv_folder = os.path.join("data/Output", workbook_name)
    if os.path.exists(csv_folder):
        if ".json" in  sheet_name or ".yaml" in sheet_name:
            csv_sheet_name = sheet_name.split(".")[0] + ".csv"
           
            sheet_path = os.path.join(csv_folder, csv_sheet_name)
            print("csv sheet path: " + sheet_path)
            res = ask_csv_agent(sheet_path, question)
            print(res)
            print(res["response"])
            if res["response"] == "Success":
                return JSONResponse(content = res['answer'], status_code=200)
            else:
                return JSONResponse(content = res['answer'], status_code=400)
    else:
        return JSONResponse(content = "Error while trying to retreive answer. Please contact your admin.", status_code=200)

