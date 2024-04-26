import logging
import json
from fastapi import APIRouter
from src.db.schema import (
    get_stations,
    add_station
)



router = APIRouter()


@router.get("/stations", status_code=200)
async def list():
  stations = get_stations()
  return stations



@router.post("/stations", status_code=200)
async def list(region: str):
  add_station(region)
  return None