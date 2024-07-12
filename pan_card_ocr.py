import cv2
import numpy as np
import easyocr
import re
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

def extract_text_from_image(file_path: str) -> Optional[str]:
    """Extract text from an image using EasyOCR."""
    try:
        results = reader.readtext(file_path, paragraph=False)
        if results:
            return "\n".join([result[1] for result in results if len(result) > 1])
        else:
            logger.warning(f"No text extracted from {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return None

def extract_pan_name(text: Optional[str]) -> str:
    """Extract name from PAN card text."""
    if not text:
        return "Name not found"
    name_patterns = [
        r'\b([A-Z]+\s[A-Z]+(?:\s[A-Z]+)?)\b',
        r'Name\s*:\s*([A-Z\s]+)',
        r'([A-Z]+\s[A-Z]+(?:\s[A-Z]+)?)\s*$'
    ]
    for pattern in name_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return max(matches, key=len).strip()
    return "Name not found"

def extract_pan_dob(text: Optional[str]) -> str:
    """Extract Date of Birth from PAN card text."""
    if not text:
        return "DOB not found"
    dob_patterns = [
        r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b',
        r'DOB\s*:\s*(\d{2}[-/]\d{2}[-/]\d{4})',
        r'Date of Birth\s*:\s*(\d{2}[-/]\d{2}[-/]\d{4})'
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return "DOB not found"

def extract_pan_number(text: Optional[str]) -> str:
    """Extract PAN number from text."""
    if not text:
        return "PAN number not found"
    pan_patterns = [
        r'\b([A-Z]{5}[0-9]{4}[A-Z])\b',
        r'PAN\s*:\s*([A-Z0-9]{10})',
        r'Permanent Account Number\s*:\s*([A-Z0-9]{10})'
    ]
    for pattern in pan_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return "PAN number not found"

def process_pan_image(image_path: str) -> Dict[str, str]:
    """Process PAN card image and extract details."""
    text = extract_text_from_image(image_path)
    if text:
        logger.info(f"Extracted Text from {image_path}:\n{text}")
    else:
        logger.warning(f"No text extracted from {image_path}")
    
    result = {
        "name": extract_pan_name(text),
        "dob": extract_pan_dob(text),
        "number": extract_pan_number(text)
    }
    return result