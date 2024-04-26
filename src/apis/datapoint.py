import logging
import json
from fastapi import APIRouter
from src.models.datapoint import DataPoint
from src.db.schema import (
    log_data_point
)



router = APIRouter()


@router.post("/datapoint", status_code=200)
async def log(data: DataPoint):
  log_data_point(data)
  return None

