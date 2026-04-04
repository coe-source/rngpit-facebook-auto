from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io

from core.database import get_db
from core import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.Faculty])
def read_faculty(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    faculty = db.query(models.Faculty).offset(skip).limit(limit).all()
    return faculty

@router.delete("/clear")
def clear_faculty(db: Session = Depends(get_db)):
    db.query(models.Faculty).delete()
    db.commit()
    return {"message": "Faculty database cleared successfully."}

@router.post("/", response_model=schemas.Faculty)
def create_faculty(faculty: schemas.FacultyCreate, db: Session = Depends(get_db)):
    db_faculty = models.Faculty(**faculty.model_dump())
    db.add(db_faculty)
    db.commit()
    db.refresh(db_faculty)
    return db_faculty

@router.post("/upload")
async def upload_faculty_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel or CSV file.")
    
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Expecting columns roughly like: 'Name', 'Facebook Profile Link', 'Facebook Username', 'Department'
        # We will map whatever we find that looks close.
        # Simple fuzzy matching for columns
        col_map = {}
        for col in df.columns:
            lower_col = str(col).strip().lower()
            if lower_col in ['faculty name', 'name', 'faculty_name']:
                col_map[col] = 'name'
            elif lower_col in ['facebook link', 'fb link', 'facebook profile link', 'profile link', 'link']:
                col_map[col] = 'fb_profile_link'
            elif lower_col in ['facebook username', 'fb username', 'username', 'facebook_username']:
                col_map[col] = 'fb_username'
            elif lower_col in ['department', 'dept', 'branch']:
                col_map[col] = 'department'
        
        df = df.rename(columns=col_map)
        
        added_count = 0
        for _, row in df.iterrows():
            if 'name' not in row or pd.isna(row['name']):
                continue
                
            username = None
            if 'fb_username' in row and not pd.isna(row['fb_username']):
                username = str(row['fb_username']).strip()
                if username and not username.startswith('@'):
                    username = f"@{username}"
            elif 'fb_profile_link' in row and not pd.isna(row['fb_profile_link']):
                # Simple extraction from URL if username is missing
                link = str(row['fb_profile_link'])
                if 'facebook.com/' in link:
                    parts = link.split('facebook.com/')
                    if len(parts) > 1:
                        potential_username = parts[1].split('/')[0].split('?')[0]
                        if potential_username and potential_username != 'profile.php':
                            username = f"@{potential_username}"
            
            # Check if exists
            existing = db.query(models.Faculty).filter(models.Faculty.name == row['name']).first()
            if not existing:
                db_faculty = models.Faculty(
                    name=row['name'],
                    fb_profile_link=str(row.get('fb_profile_link', '')) if 'fb_profile_link' in row and not pd.isna(row['fb_profile_link']) else None,
                    fb_username=username,
                    department=str(row.get('department', '')) if 'department' in row and not pd.isna(row['department']) else None
                )
                db.add(db_faculty)
                added_count += 1
                
        db.commit()
        return {"message": f"Successfully imported {added_count} faculty records."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing data: {str(e)}")
