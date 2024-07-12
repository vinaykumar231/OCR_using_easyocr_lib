from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from ..models.adhar import save_upload_file
from pan_card_ocr import extract_text_from_image,extract_pan_name, extract_pan_dob,extract_pan_number
import os
import uuid
import shutil
from ..models.pancard import PanCard


router = APIRouter()


@router.post("/upload_pan/")
def upload_pan_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Save uploaded image
        file_path = save_upload_file(file)

        # Perform OCR to extract details
        extracted_text = extract_text_from_image(file_path)

        # Parse extracted details
        name = extract_pan_name(extracted_text)
        dob = extract_pan_dob(extracted_text)
        pan_number = extract_pan_number(extracted_text)
        existing_pan_number = db.query(PanCard).filter(PanCard.pan_number == pan_number).first()
        if existing_pan_number:
            raise HTTPException(status_code=400, detail=f"{pan_number} pan card number already submitted")

        # Save details to database
        db_pan = PanCard(
            pan_card_images=file_path,
            name=name,
            dob=dob,
            pan_number=pan_number
        )
        db.add(db_pan)
        db.commit()
        db.refresh(db_pan)

        return db_pan

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PAN card: {str(e)}")
    


@router.get("/pan_cards/{pan_number}", response_model=None)
def get_pan_card(pan_number: str, db: Session = Depends(get_db)):
    pan_card = db.query(PanCard).filter(PanCard.pan_number == pan_number).first()
    if pan_card is None:
        raise HTTPException(status_code=404, detail="PAN card not found")
    return pan_card

@router.get("/pan_cards/", response_model=None)
async def read_all_pan_cards(db: Session = Depends(get_db)):
    try:
        pan_cards = db.query(PanCard).all()
        return pan_cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.delete("/pan_cards/{pan_number}")
def delete_pan_card(pan_number: str, db: Session = Depends(get_db)):
    pan_card = db.query(PanCard).filter(PanCard.pan_number == pan_number).first()
    if pan_card is None:
        raise HTTPException(status_code=404, detail="PAN card not found")
    db.delete(pan_card)
    db.commit()
    return {"message": f"PAN card with number {pan_number} has been deleted"}