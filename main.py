import logging
import os
from dotenv import load_dotenv
from src.apis import apis
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import FastAPI
from src.db.schema import (
    create_schema,
    cleanup
)

logging.basicConfig(
    level = logging.DEBUG,
    format = "%(levelname)-10s%(message)s"
)


app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(apis, prefix="/api")

@app.on_event("startup")
async def startup():
    create_schema()
    



@app.on_event("shutdown")
async def shutdown():
    cleanup()



@app.get("/")
def read_root():
    return {"version": "1.0.0"}

