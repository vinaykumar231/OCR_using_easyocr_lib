from sqlalchemy import Column, Integer, String,ForeignKey
from database import Base
from sqlalchemy.orm import Session, relationship
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
import os
import uuid
import shutil
import pytesseract
from PIL import Image
import re
from datetime import datetime


class AadhaarCard(Base):
    __tablename__ = "aadhaar_card"

    id = Column(Integer, primary_key=True, index=True)
    adhar_card_images = Column(String(255))
    name = Column(String(255))
    dob = Column(String(255))
    gender = Column(String(255))
    phone_number= Column(String(255))
    aadhar_number = Column(String(255), unique=True)


def save_upload_file(upload_file: UploadFile) -> str:
    try:
        unique_filename = str(uuid.uuid4()) + "_" + upload_file.filename
        file_path = os.path.join("static", "uploads", unique_filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        # Convert backslashes to forward slashes
        file_path = file_path.replace("\\", "/")
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

