from fastapi import APIRouter
from src.apis.station import router as stationRouter
from src.apis.datapoint import router as datapointRouter

apis = APIRouter()
apis.include_router(stationRouter)
apis.include_router(datapointRouter)

__all__ = ["apis"]
