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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(255))
    