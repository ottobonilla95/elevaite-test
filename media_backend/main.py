from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from model import InferencePayload, MarkdownRequest
from llm_rag_inference import perform_inference
from fastapi.responses import StreamingResponse
import json
import re
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import httpx

app = FastAPI()

origins = [
    "http://localhost:3004",  # Your frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def download_image(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            return BytesIO(response.content)  # Return a BytesIO object
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None
async def parse_markdown_table(lines):
    table_data = []
    
    for line in lines:
        if line.strip() and not all(char in '-|' for char in line.strip()):
            row = [cell.strip() for cell in line.split('|') if cell.strip()]
            processed_row = []
            for cell in row:
                cleaned_cell = cell.replace('**', '').strip()
                
                # Regex to capture image URL correctly
                img_match = re.search(r'!\[(.*?)\]\((http[^\s)]+)(?:\s+"[^"]*")?\)', cleaned_cell)
                if img_match:
                    _, img_url = img_match.groups()
                    img_url = img_url.strip()  # Clean up the URL
                    print(f"Processing image URL: {img_url}")  # Debug output
                    try:
                        img_data = await download_image(img_url)
                        if img_data:
                            processed_row.append(img_data)
                        else:
                            processed_row.append(Paragraph("Image not available", getSampleStyleSheet()['Normal']))
                    except Exception as e:
                        print(f"Error downloading image: {e}")  # Log the error
                        processed_row.append(Paragraph("Error loading image", getSampleStyleSheet()['Normal']))
                else:
                    processed_row.append(Paragraph(cleaned_cell, getSampleStyleSheet()['Normal']))
            if processed_row:
                table_data.append(processed_row)
    return table_data


@app.post("/generate-pdf")
async def generate_pdf(request: MarkdownRequest):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        heading_style = styles['Heading1']
        subheading_style = styles['Heading2']
        bold_style = styles['Normal'].clone('Bold')  # Clone for bold style

        table_width = doc.width * 0.9
        lines = request.markdown.splitlines()
        table_lines = []
        in_table = False

        for line in lines:
            if line.strip() == '---':
                story.append(Spacer(1, 12))
                continue
            if '|' in line:
                in_table = True
                table_lines.append(line)
            else:
                if in_table:
                    if table_lines:
                        story.append(Spacer(1, 12))
                        table_data = await parse_markdown_table(table_lines)
                        num_columns = len(table_data[0])
                        col_widths = [table_width / num_columns] * num_columns
                        wrapped_table_data = []
                        
                        for row in table_data:
                            wrapped_row = []
                            for cell in row:
                                if isinstance(cell, BytesIO):  # Check if it's image data
                                    img = Image(cell, width=100, height=75)  # Use BytesIO directly
                                    wrapped_row.append(img)
                                elif isinstance(cell, Paragraph):
                                    wrapped_row.append(cell)
                                else:
                                    wrapped_row.append(Paragraph(str(cell), normal_style))
                            wrapped_table_data.append(wrapped_row)

                        table = Table(wrapped_table_data, colWidths=col_widths)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), "#F5F5F5"),
                            ('TEXTCOLOR', (0, 0), (-1, 0), "#FFFFFF"),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), 
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), "#FFFFFF"),
                            ('GRID', (0, 0), (-1, -1), 1, "#EEEEEE"),
                            ('LEFTPADDING', (0, 0), (-1, -1), 5),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                            ('BORDER', (0, 0), (-1, -1), 1, "#D9D9D9"),
                        ]))
                        story.append(table)
                        table_lines = []
                    in_table = False
                else:
                    # Process headings and bold text outside the table
                    formatted_line = line.strip()
                    
                    if formatted_line.startswith('### '):
                        story.append(Paragraph(formatted_line[4:], subheading_style))
                    elif formatted_line.startswith('## '):
                        story.append(Paragraph(formatted_line[3:], heading_style))
                    elif formatted_line.startswith('# '):
                        story.append(Paragraph(formatted_line[2:], heading_style))
                    else:
                        # Handle bold text with ** if present
                        if '**' in formatted_line:
                            parts = formatted_line.split('**')
                            paragraphs = []
                            for i, part in enumerate(parts):
                                if i % 2 == 1:  # Bold part
                                    paragraphs.append(Paragraph(part.strip(), bold_style))
                                else:  # Normal part
                                    paragraphs.append(Paragraph(part.strip(), normal_style))
                            story.extend(paragraphs)
                        else:
                            story.append(Paragraph(formatted_line, normal_style))

        if table_lines:
            table_data = await parse_markdown_table(table_lines)
            max_column_width = (doc.width / len(table_data[0]) * 0.9) - 20
            col_widths = [max_column_width] * len(table_data[0])
            wrapped_table_data = []
            for row in table_data:
                wrapped_row = []
                for cell in row:
                    if isinstance(cell, BytesIO):  # Check if it's image data
                        img = Image(cell, width=100, height=75)  # Use BytesIO directly
                        wrapped_row.append(img)
                    else:
                        wrapped_row.append(cell)
                wrapped_table_data.append(wrapped_row)

            table = Table(wrapped_table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), "#F5F5F5"),
                ('TEXTCOLOR', (0, 0), (-1, 0), "#FFFFFF"),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'), 
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), "#FFFFFF"),
                ('GRID', (0, 0), (-1, -1), 1, "#EEEEEE"),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BORDER', (0, 0), (-1, -1), 1, "#D9D9D9"),
            ]))
            story.append(table)

        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=chat_session.pdf"})

    except Exception as e:
        print("Error generating PDF: %s" % str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
# Serves the static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/")
async def post_message(inference_payload: InferencePayload):
    try:
        async def event_generator():
            async for chunk in perform_inference(inference_payload):
                yield f"data: {json.dumps(chunk)}\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
