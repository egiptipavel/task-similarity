import uvicorn
from fastapi import FastAPI

from web.src.endpoints.endpoints import router

app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=False)
