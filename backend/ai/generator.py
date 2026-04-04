import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure API Key (You'll need a .env file with GEMINI_API_KEY)
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

import time

def generate_caption_and_tags(media_paths: list[str], all_faculty_names: list[str]) -> tuple[str, list[str]]:
    """
    Reads the flyer(s) and generates an engaging Facebook caption.
    Also suggests which faculty members might be relevant to tag based on the content.
    Returns (caption, suggested_faculty_tags)
    """
    if not GENAI_API_KEY:
        # Fallback if no API key is provided
        return "Check out our latest event at RNGPIT! 🎉 #RNGPIT #Engineering #CollegeEvent", all_faculty_names[:5]

    try:
        # Choose a model that supports multimodal input
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        uploaded_files = []
        for path in media_paths:
            sample_file = genai.upload_file(path=path, display_name=os.path.basename(path))
            
            # If it's a video, wait for processing to finish
            if path.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                while sample_file.state.name == 'PROCESSING':
                    time.sleep(2)
                    sample_file = genai.get_file(sample_file.name)
                if sample_file.state.name == 'FAILED':
                    print(f"Video {sample_file.name} failed to process.")
                    
            uploaded_files.append(sample_file)
        
        prompt = f"""
        You are a professional social media manager for an engineering college (RNGPIT).
        Analyze the attached media (promotional flyers, pictures, or videos).
        
        Write a highly engaging, professional, and exciting Facebook caption for this event/post. 
        Include relevant emojis and a few relevant hashtags at the bottom.
        Do not make the caption unnecessarily long. 
        
        Also, I have a list of our faculty members. Based on the topics, try to identify if any specific faculty seem highly relevant (e.g., if it's an Electrical Engineering flyer, maybe standard faculty should be tagged, but here just use your judgement to return a list, or just recommend tagging all).
        For simplicity, just write the caption. I will handle the tagging separately.
        
        RETURN FORMAT:
        Just return the exact text of the Facebook caption you want to post.
        """
        
        # Pass all media files along with the prompt
        response = model.generate_content([*uploaded_files, prompt])
        
        # Clean up files from Google's servers
        for f in uploaded_files:
            genai.delete_file(f.name)
        
        caption = response.text.strip()
        
        # By default, we might just suggest all faculty, or a random sample if too many, to avoid looking like spam.
        # Let's say we suggest linking to the department heads or just all if list is small.
        suggested_faculty = all_faculty_names # Simply returning all for now, as the prompt specifies manual handling
        
        return caption, suggested_faculty
        
    except Exception as e:
        print(f"Error generating caption: {e}")
        return "Check out our latest updates! 🎉 #RNGPIT", all_faculty_names[:5]
