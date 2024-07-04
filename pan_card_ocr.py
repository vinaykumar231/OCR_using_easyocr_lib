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


pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Mukesh\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


def extract_text_from_image(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    return text

def extract_name(text):
    lines = text.split('\n')
    for line in lines:
        if re.match(r'^[A-Z]+\s[A-Z]+(\s[A-Z]+)?$', line.strip()):
            return line.strip()
    return "Name not found"

def extract_dob(text):
    date_pattern = r'\b(\d{2}/\d{2}/\d{4})\b'
    match = re.search(date_pattern, text)
    if match:
        return match.group(1)
    return "DOB not found"

def extract_pan_number(text):
    pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
    match = re.search(pan_pattern, text)
    if match:
        return match.group(0)
    return "PAN number not found"