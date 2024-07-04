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


def extract_text_from_image(file_path):
    text = pytesseract.image_to_string(Image.open(file_path))
    return text

def extract_name(text: str) -> str:
    lines = text.split('\n')
    for line in lines:
        # Match lines with uppercase letters and spaces (at least one word)
        if re.match(r'^[A-Z]+(?:\s[A-Z]+)*$', line.strip()):
            return line.strip()
    return "Name not found"

def extract_dob(text):
    date_pattern = r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b'
    match = re.search(date_pattern, text)
    if match:
        date_str = match.group(1)
        try:
            date_obj = datetime.strptime(date_str.replace('-', '/'), '%d/%m/%Y')
            return date_obj.strftime('%d-%m-%Y')
        except ValueError:
            pass
    return "DOB not found"

def extract_gender(text):
    gender_match = re.search(r'\b(MALE|FEMALE)\b', text, re.IGNORECASE)
    if gender_match:
        return gender_match.group(1).capitalize()
    return "Gender not found"

def extract_aadhar_number(text):
    aadhar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    match = re.search(aadhar_pattern, text)
    if match:
        aadhar = match.group(0).replace(' ', '')
        return f"{aadhar[:4]} {aadhar[4:8]} {aadhar[8:]}"
    return "Aadhaar number not found"