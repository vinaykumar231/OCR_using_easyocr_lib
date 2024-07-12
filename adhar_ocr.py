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
from typing import Dict, Optional

###
import spacy
from spacy.matcher import Matcher
import datetime
import spacy
import pytesseract
from PIL import Image
import easyocr
from spacy.matcher import Matcher
##
import easyocr
import spacy
import re
from datetime import datetime
from spacy.matcher import Matcher
from typing import Dict
from spacy.matcher import Matcher

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

nlp = spacy.load("en_core_web_sm")


matcher = Matcher(nlp.vocab)



# Define patterns for name and date extraction
name_pattern = [
    {"POS": "PROPN"},  # Proper noun (name)
    {"POS": "PROPN", "OP": "?"}  # Optional second proper noun
]

# Date patterns include various formats
dob_pattern = [
    {"SHAPE": "dd/dd/dddd"},  # Date format like 01/01/2000
    {"SHAPE": "dd-dd-dddd"},  # Date format like 01-01-2000
    {"SHAPE": "dddd/dd/dd"}   # Date format like 2000/01/01
]

# Add patterns to the Matcher
matcher.add("NAME", [name_pattern])
matcher.add("DOB", [dob_pattern])

def extract_text_from_image(file_path: str) -> str:
    """Extract text from an image using EasyOCR."""
    results = reader.readtext(file_path, paragraph=True)
    text = " ".join([result[1] for result in results])
    return text

def extract_aadhaar_name(text: str) -> str:
    """Extract name from text using spaCy and custom rules."""
    # Remove common headers
    text = re.sub(r'(?i)government of india|भारत सरकार', '', text)
    
    # Split the text into lines
    lines = text.split('\n')
    
    # Look for the name in the first few lines
    for line in lines[:3]:  # Check first 3 lines
        # Remove any numbers or special characters
        cleaned_line = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        
        # Split the line into words
        words = cleaned_line.split()
        
        # Check if we have 2-3 words that could be a name
        if 2 <= len(words) <= 3:
            # Check if words are proper nouns (start with capital letter)
            if all(word[0].isupper() for word in words):
                return ' '.join(words)
    
    # If no name found in the first few lines, use spaCy as a fallback
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    
    return "Name not found"



def extract_aadhaar_dob(text: str) -> str:
    """Extract Date of Birth from text using regex."""
    date_patterns = [
        r'\b\d{2}/\d{2}/\d{4}\b',  # Date format like 01/01/2000
        r'\b\d{2}-\d{2}-\d{4}\b',  # Date format like 01-01-2000
        r'\b\d{4}/\d{2}/\d{2}\b',  # Date format like 2000/01/01
        r'\b\d{4}-\d{2}-\d{2}\b'   # Date format like 2000-01-01
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_string = match.group(0)
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"):
                try:
                    date_obj = datetime.strptime(date_string, fmt)
                    return date_obj.strftime('%d-%m-%Y')
                except ValueError:
                    continue
    return "Date of Birth not found"
def extract_aadhaar_gender(text: str) -> str:
    """Extract gender from Aadhaar card text using spaCy."""
    doc = nlp(text)
    for token in doc:
        if token.text.lower() in ["male", "female"]:
            return token.text.capitalize()
    return "Gender not found"

def extract_aadhaar_number(text: str) -> str:
    """Extract Aadhaar number from text using regex."""
    aadhar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    match = re.search(aadhar_pattern, text)
    if match:
        aadhar = match.group(0).replace(' ', '')
        return f"{aadhar[:4]} {aadhar[4:8]} {aadhar[8:]}"
    return "Aadhaar number not found"

def process_aadhaar_image(image_path: str) -> Dict[str, str]:
    """Process Aadhaar card image and extract details."""
    text = extract_text_from_image(image_path)
    return {
        "name": extract_aadhaar_name(text),
        "dob": extract_aadhaar_dob(text),
        "gender": extract_aadhaar_gender(text),
        "number": extract_aadhaar_number(text)
    }
