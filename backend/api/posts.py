from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import shutil
import os
import json
from typing import List

from core.database import get_db
from core import models, schemas
from ai.generator import generate_caption_and_tags
from automation.poster import post_to_facebook

router = APIRouter()

@router.post("/generate-content")
async def generate_post_content(
    files: List[UploadFile] = File(...),
    departments: str = Form("[]"),
    specific_faculty: str = Form("[]"),
    db: Session = Depends(get_db)
):
    """
    Takes uploaded files, saves them, and asks Gemini to generate a caption and tags.
    """
    valid_extensions = ('.png', '.jpg', '.jpeg', '.mp4', '.mov', '.avi', '.webm')
    file_paths = []
    
    for file in files:
        if not file.filename.lower().endswith(valid_extensions):
            raise HTTPException(status_code=400, detail=f"Invalid format for {file.filename}")
            
        file_path = f"uploads/flyers/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_path)
        
    try:
        dept_list = json.loads(departments)
    except:
        dept_list = []
        
    try:
        specific_list = json.loads(specific_faculty)
    except:
        specific_list = []
        
    faculty_usernames = set()
    
    # Handle departments
    if dept_list:
        if "ALL" in dept_list:
            faculty_records = db.query(models.Faculty).filter(models.Faculty.is_active == True).all()
        else:
            faculty_records = db.query(models.Faculty).filter(
                models.Faculty.is_active == True,
                models.Faculty.department.in_(dept_list)
            ).all()
            
        for f in faculty_records:
            if f.fb_username:
                faculty_usernames.add(f.fb_username)
                
    # Add specific faculty
    for username in specific_list:
        faculty_usernames.add(username)
        
    faculty_usernames_list = list(faculty_usernames)
    
    caption, _ = generate_caption_and_tags(file_paths, faculty_usernames_list)
    
    # Use selected usernames as suggested tags
    suggested_tags = faculty_usernames_list
    
    # Save to history as pending
    db_history = models.PostHistory(
        flyer_filename=",".join([f.filename for f in files]),
        caption=caption,
        status="pending"
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    
    return {
        "history_id": db_history.id,
        "image_path": file_path,
        "caption": caption,
        "suggested_tags": suggested_tags
    }

@router.post("/publish")
async def publish_post(
    history_id: int = Form(...),
    final_caption: str = Form(...),
    tags_json: str = Form("[]"), # JSON array of tags to actually use
    db: Session = Depends(get_db)
):
    """
    Takes the approved caption and tags, and triggers the Playwright poster.
    """
    history_record = db.query(models.PostHistory).filter(models.PostHistory.id == history_id).first()
    if not history_record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    history_record.caption = final_caption
    db.commit()
    
    tags = json.loads(tags_json)
    filenames = history_record.flyer_filename.split(',')
    file_paths = [f"uploads/flyers/{name}" for name in filenames]
    
    import sys
    import asyncio
    from starlette.concurrency import run_in_threadpool

    def run_pw_isolated():
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(post_to_facebook(file_paths, final_caption, tags))
        finally:
            loop.close()
            
    success, msg = await run_in_threadpool(run_pw_isolated)
    
    from datetime import datetime
    
    if success:
        history_record.status = "posted"
        history_record.posted_at = datetime.now()
    else:
        history_record.status = "failed"
        history_record.error_message = msg
        
    db.commit()
    
    return {"status": "success" if success else "failed", "message": msg}
