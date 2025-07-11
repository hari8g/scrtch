from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.formulation import router as formulation_router
from app.routes.conversation import router as conversation_router

app = FastAPI(title="Formulation Engine API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(formulation_router, prefix="/formulation", tags=["formulation"])
app.include_router(conversation_router, prefix="/conversation", tags=["conversation"])


@app.get("/")
async def root():
    return {"message": "Formulation Engine API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 