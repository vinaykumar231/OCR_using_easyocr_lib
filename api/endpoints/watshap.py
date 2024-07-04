from fastapi import FastAPI, HTTPException, APIRouter, Request, Body, Form, Response
from pydantic import BaseModel
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator

###
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from ..models.adhar import save_upload_file
from adhar_ocr import extract_text_from_image,extract_name, extract_dob,extract_gender,extract_aadhar_number
import os
import uuid
import shutil
from ..models.adhar import AadhaarCard
from ..models.pancard import PanCard
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.user import User
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx
import uuid
from fastapi.responses import JSONResponse
import requests
from io import BytesIO
from dotenv import load_dotenv
import os



router = APIRouter()

# Twilio credentials
load_dotenv()  # This loads the variables from .env

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

client = Client(account_sid, auth_token)
validator = RequestValidator(auth_token)


@router.post("/reply")
async def whatsapp(request: Request, db: Session = Depends(get_db)):
    try:
        form_data = await request.form()
        message = form_data.get("Body")
        from_number = form_data.get("From")
        
        if not message or not from_number:
            raise ValueError("Missing required fields: Body or From")
        
        # Remove 'whatsapp:' prefix if present
        from_number = from_number.replace('whatsapp:', '')
        
        user = db.query(AadhaarCard).filter(AadhaarCard.phone_number == from_number).first()
        
        if message.lower() == "hi":
            if not user:
                # Create new user if not exists
                user = User(phone_number=from_number)
                db.add(user)
                db.commit()
                response = "Welcome! Your number has been registered. Please provide your Aadhar card for KYC."
            else:
                response = "Welcome back! Please provide your Aadhar card for KYC."
        elif "MediaUrl0" in form_data:
            if not user:
                user = User(phone_number=from_number)
                db.add(user)
                db.commit()
            
            # Handle image upload
            image_url = form_data.get("MediaUrl0")
            
            # Download the image
            image_response = requests.get(image_url)
            print("image_url:",image_response)
            if image_response.status_code == 200:
                # Save the image temporarily
                temp_image_path = f"temp_{uuid.uuid4()}.jpg"
                with open(temp_image_path, "wb") as temp_file:
                    temp_file.write(image_response.content)
                print("image_url2:",image_response)
                
                # Extract information from the image
                text = extract_text_from_image(temp_image_path)
                name = extract_name(text)
                dob = extract_dob(text)
                gender = extract_gender(text)
                aadhar_number = extract_aadhar_number(text)
                
                # Update user information
                user.name = name
                user.dob = dob
                user.gender = gender
                user.aadhar_number = aadhar_number
                db.commit()
                
                # Remove temporary image
                os.remove(temp_image_path)
                
                response = f"Thank you for providing your Aadhar card. Here's the information we extracted:\n\nName: {name}\nDOB: {dob}\nGender: {gender}\nAadhar Number: {aadhar_number}\n\nPlease confirm if this information is correct."
            else:
                response = "Sorry, we couldn't download the image. Please try uploading it again."
        else:
            response = "I'm sorry, I didn't understand that. Please say 'hi' to start the KYC process or upload your Aadhar card image."
        
        # Send reply back to user via WhatsApp
        client.messages.create(
            from_='whatsapp:+14155238886',
            to=f'whatsapp:{from_number}',
            body=response
        )
        
        return {"status": "success", "message": "Message processed successfully"}
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }
        )
