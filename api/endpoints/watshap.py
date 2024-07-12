from fastapi import FastAPI, HTTPException, APIRouter, Request, Depends
from sqlalchemy.orm import Session
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from pydantic import BaseModel
from database import get_db
from ..models.user import User
from ..models.adhar import AadhaarCard
from ..models.pancard import PanCard
from adhar_ocr import  process_aadhaar_image
from pan_card_ocr import process_pan_image
import os
import uuid
import requests
from fastapi.responses import JSONResponse

router = APIRouter()

# Twilio credentials
account_sid = 'ACc882424ebd68dd3f40eb4eda1998fbac'  # Replace with your Twilio Account SID
auth_token = 'f17f8f236f6ed322af3053908ae8f89e'     # Replace with your Twilio Auth Token

client = Client(account_sid, auth_token)
validator = RequestValidator(auth_token)

@router.post("/reply")
async def whatsapp(request: Request, db: Session = Depends(get_db)):
    try:
        form_data = await request.form()
        message = form_data.get("Body", "").strip().lower()
        from_number = form_data.get("From", "").replace('whatsapp:', '')
        
        if not message or not from_number:
            raise ValueError("Missing required fields: Body or From")
        
        aadhaar_user = db.query(AadhaarCard).filter(AadhaarCard.phone_number == from_number).first()
        pan_user = db.query(PanCard).filter(PanCard.phone_number == from_number).first()
        user = db.query(User).filter(User.phone_number == from_number).first()

        # Define the current state based on user data
        if not aadhaar_user:
            state = "START"
        elif not aadhaar_user.aadhar_number:
            state = "AADHAAR"
        elif aadhaar_user.confirmation_status == 'pending':
            state = "AADHAAR_CONFIRM"
        elif aadhaar_user.confirmation_status == 'confirmed' and not pan_user:
            state = "PAN"
        elif pan_user and pan_user.confirmation_status == 'pending':
            state = "PAN_CONFIRM"
        else:
            state = "COMPLETE"

        if message == "hi":
            if state == "START":
                aadhaar_user = AadhaarCard(phone_number=from_number)
                db.add(aadhaar_user)
                db.commit()
                user = User(phone_number=from_number)
                db.add(user)
                db.commit()

                response = "Welcome! Your number has been registered. Please provide your Aadhaar card image for KYC."
            else:
                response = f"Welcome back! Your current status is: {state}. Please proceed accordingly or type 'help' for assistance."

        elif "MediaUrl0" in form_data:
            image_url = form_data.get("MediaUrl0")
            image_response = requests.get(image_url, auth=(account_sid, auth_token))
            
            if image_response.status_code == 200:
                temp_image_path = f"temp_{uuid.uuid4()}.jpg"
                with open(temp_image_path, "wb") as temp_file:
                    temp_file.write(image_response.content)
                
                if state in ["START", "AADHAAR"]:
                    # Process Aadhaar card image
                    extracted_info = process_aadhaar_image(temp_image_path)
                    
                    aadhaar_user.adhar_card_images = image_url
                    aadhaar_user.name = extracted_info["name"]
                    aadhaar_user.dob = extracted_info["dob"]
                    aadhaar_user.gender = extracted_info["gender"]
                    aadhaar_user.aadhar_number = extracted_info["number"]
                    aadhaar_user.confirmation_status = 'pending'
                    db.commit()
                    
                    response = f"""Thank you for providing your Aadhaar card. Here's the information we extracted:

Name: {extracted_info["name"]}
Date of Birth: {extracted_info["dob"]}
Gender: {extracted_info["gender"]}
Aadhaar Number: {extracted_info["number"]}

Please reply with 'CONFIRM' if this information is correct, or 'RETRY' if you need to upload the image again."""
                
                elif state == "PAN":
                    # Process PAN card image
                    extracted_info = process_pan_image(temp_image_path)
                    
                    pan_user = PanCard(
                        pan_card_images=image_url,
                        name=extracted_info["name"],
                        dob=extracted_info["dob"],
                        pan_number=extracted_info["number"],
                        confirmation_status='pending',
                        phone_number=from_number
                    )
                    db.add(pan_user)
                    db.commit()
                    
                    response = f"""Thank you for providing your PAN card. Here's the information we extracted:

Name: {extracted_info["name"]}
Date of Birth: {extracted_info["dob"]}
PAN Number: {extracted_info["number"]}

Please reply with 'CONFIRM PAN' if this information is correct, or 'RETRY PAN' if you need to upload the image again."""
                
                else:
                    response = f"We're not expecting an image at this time. Your current status is: {state}. Please type 'help' for assistance."
                
                os.remove(temp_image_path)
            else:
                response = f"Sorry, we couldn't download the image. Error: {image_response.status_code}"

        elif message == 'confirm':
            if state == "AADHAAR_CONFIRM":
                aadhaar_user.confirmation_status = 'confirmed'
                db.commit()
                response = "Thank you for confirming your Aadhaar information. Now, please provide your PAN card image for further verification."
            else:
                response = f"There's nothing to confirm at this time. Your current status is: {state}. Please type 'help' for assistance."

        elif message == 'confirm pan':
            if state == "PAN_CONFIRM":
                pan_user.confirmation_status = 'confirmed'
                db.commit()
                response = "Thank you for confirming your PAN information. Your KYC process is now complete."
            else:
                response = f"There's nothing to confirm at this time. Your current status is: {state}. Please type 'help' for assistance."

        elif message == 'retry':
            if state == "AADHAAR_CONFIRM":
                aadhaar_user.name = None
                aadhaar_user.dob = None
                aadhaar_user.gender = None
                aadhaar_user.aadhar_number = None
                aadhaar_user.confirmation_status = None
                db.commit()
                response = "Please upload your Aadhaar card image again."
            else:
                response = f"There's nothing to retry at this time. Your current status is: {state}. Please type 'help' for assistance."

        elif message == 'retry pan':
            if state == "PAN_CONFIRM":
                db.delete(pan_user)
                db.commit()
                response = "Please upload your PAN card image again."
            else:
                response = f"There's nothing to retry at this time. Your current status is: {state}. Please type 'help' for assistance."

        elif message == 'help':
            response = f"""Your current status is: {state}. Here's what you can do:

START: Say 'hi' to begin the KYC process.
AADHAAR: Upload your Aadhaar card image.
AADHAAR_CONFIRM: Reply 'confirm' or 'retry' for the Aadhaar information.
PAN: Upload your PAN card image.
PAN_CONFIRM: Reply 'confirm pan' or 'retry pan' for the PAN information.
COMPLETE: Your KYC process is complete."""

        else:
            response = f"I'm sorry, I didn't understand that. Your current status is: {state}. Please type 'help' for assistance."

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