from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from ..models.adhar import save_upload_file
from adhar_ocr import extract_text_from_image,extract_name, extract_dob,extract_gender,extract_aadhar_number
import os
import uuid
import shutil
from ..models.adhar import AadhaarCard


router = APIRouter()

@router.post("/upload_aadhaar/")
def upload_aadhaar_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Save uploaded image
        file_path = save_upload_file(file)

        # Perform OCR to extract details
        extracted_text = extract_text_from_image(file_path)

        # Parse extracted details
        name = extract_name(extracted_text)
        dob = extract_dob(extracted_text)
        gender = extract_gender(extracted_text)
        aadhar_number = extract_aadhar_number(extracted_text)
        existing_adhar_number = db.query(AadhaarCard).filter(AadhaarCard.aadhar_number == aadhar_number).first()
        if existing_adhar_number:
            raise HTTPException(status_code=400, detail=f"{aadhar_number} aadhar number already submitted")

        # Save details to database
        db_aadhaar = AadhaarCard(
            adhar_card_images=file_path,
            name=name,
            dob=dob,
            gender=gender,
            aadhar_number=aadhar_number
        )
        db.add(db_aadhaar)
        db.commit()
        db.refresh(db_aadhaar)

        return db_aadhaar

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Aadhaar: {str(e)}")
    


@router.get("/aadhaar_cards/all", response_model=None)
async def read_all_aadhaar_cards(db: Session = Depends(get_db)):
    try:
        aadhaar_cards = db.query(AadhaarCard).all()
        return aadhaar_cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@router.get("/aadhaar_cards/{aadhar_number}", response_model=None)
async def read_aadhaar_card(aadhar_number: str, db: Session = Depends(get_db)):
    try:
        aadhaar_card = db.query(AadhaarCard).filter(AadhaarCard.aadhar_number == aadhar_number).first()
        if aadhaar_card is None:
            raise HTTPException(status_code=404, detail="Aadhaar card not found")
        return aadhaar_card
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


    
@router.delete("/aadhaar_cards/{aadhar_number}")
async def delete_aadhaar_card(aadhar_number: str, db: Session = Depends(get_db)):
    try:
        aadhaar_card = db.query(AadhaarCard).filter(AadhaarCard.aadhar_number == aadhar_number).first()
        if aadhaar_card is None:
            raise HTTPException(status_code=404, detail="Aadhaar card not found")
        db.delete(aadhaar_card)
        db.commit()
        return {"message": f"Aadhaar card with number {aadhar_number} has been deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")