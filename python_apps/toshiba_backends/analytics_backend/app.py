from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import routers from modules
from routers import summary, customer, product, issues, service, query_analytics, user_analytics, technicians

load_dotenv()

app = FastAPI(title="Analytics Dashboard API")

# Enable CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# this endpoint not publicly accessible
@app.get("/")
def root():
    return {"message": "Analytics Dashboard API is running"}

# Include routers for each feature section
app.include_router(summary.router, tags=["Summary"])
app.include_router(customer.router, tags=["Customer Analytics"])
app.include_router(product.router, tags=["Product Analytics"])
app.include_router(issues.router, tags=["Issue Categories"])
app.include_router(service.router, tags=["Service Performance"])
app.include_router(query_analytics.router, tags=["Query Analytics"])
app.include_router(user_analytics.router, tags=["User Analytics"])
app.include_router(technicians.router, tags=["Technicians"])  # NEW: Add this line

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app", 
        host=os.getenv("API_HOST", "0.0.0.0"), 
        port=int(os.getenv("API_PORT", "8000")),
        reload=True
    )