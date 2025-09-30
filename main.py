from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import re
from bs4 import BeautifulSoup
import uvicorn
import os
import html

app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

class URLRequest(BaseModel):
    url: str

class ContentUpdate(BaseModel):
    original_content: str
    edited_content: str

@app.get("/")
async def read_root():
    return {"message": "WeChat Article Style Converter API"}

@app.post("/fetch-content")
async def fetch_content(request: URLRequest):
    try:
        # For local testing, we'll handle file:// URLs differently
        if request.url.startswith("file://"):
            # Extract the file path - handle both file:// and file:/// formats
            if request.url.startswith("file:///"):
                file_path = request.url[7:]  # Remove "file://" prefix, keep the leading /
            else:
                file_path = request.url[7:]  # Remove "file://" prefix
            
            print(f"Attempting to read file: {file_path}")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"Successfully read file: {file_path}")
            else:
                print(f"File not found: {file_path}")
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        else:
            # Validate URL is a WeChat URL (optional in development)
            # if not re.match(r'^https?://mp\.weixin\.qq\.com/', request.url):
            #     # For development, we'll allow any URL, but in production you might want to restrict this
            #     pass
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(request.url, headers=headers, timeout=10)
            response.raise_for_status()
            content = response.text
        
        # Parse the HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract the main content (this might need adjustment based on WeChat's structure)
        # For WeChat articles, content is typically in a div with id 'js_content'
        content_div = soup.find('div', id='js_content')
        
        if not content_div:
            # If we can't find the specific div, return the whole body
            content_div = soup.find('body')
            
        if not content_div:
            # If we can't find body either, return the whole parsed content
            content_div = soup
            
        # For WeChat articles, we want to preserve the content with its styling
        # Convert to string, preserving the structure and styles
        if content_div:
            content_html = str(content_div)
            
            # Fix visibility issues common in WeChat articles
            # Remove problematic inline styles that hide content
            content_html = content_html.replace('visibility: hidden;', 'visibility: visible;')
            content_html = content_html.replace('opacity: 0;', 'opacity: 1;')
            content_html = content_html.replace('display: none;', 'display: block;')
        else:
            content_html = "<p>Content could not be extracted properly.</p>"
            
        # Include basic styling to ensure content is visible
        full_content = content_html
        
        return {
            "success": True,
            "content": full_content,
            "title": soup.title.string if soup.title else "Untitled"
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching URL: {str(e)}")
    except Exception as e:
        import traceback
        error_msg = str(e) if str(e) else "Unknown error occurred"
        print(f"Error in fetch_content: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing content: {error_msg}")

@app.post("/process-content")
async def process_content(update: ContentUpdate):
    try:
        # Here we implement logic to preserve style while allowing text editing
        # We'll compare the original and edited content to preserve structural elements
        original_soup = BeautifulSoup(update.original_content, 'html.parser')
        edited_soup = BeautifulSoup(update.edited_content, 'html.parser')
        
        # Preserve certain attributes and structural elements
        processed_content = preserve_structure(original_soup, edited_soup)
        
        return {
            "success": True,
            "processed_content": str(processed_content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")

def preserve_structure(original, edited):
    """
    Preserve structural elements while allowing text content to be modified.
    This function ensures that tags, classes, and styles are preserved where appropriate.
    """
    # For now, we'll return the edited content as-is
    # In a more sophisticated implementation, we would:
    # 1. Identify structural elements that should be preserved (tags, classes, styles)
    # 2. Identify text content that can be modified
    # 3. Merge the preserved structure with the edited text
    
    return edited

if __name__ == "__main__":
    import os
    # Check if AUTO_RESTART environment variable is set
    if os.environ.get("AUTO_RESTART", "").lower() in ("1", "true", "yes"):
        # Run with auto-restart enabled
        uvicorn.run("main:app", host="0.0.0.0", port=5003, reload=True)
    else:
        # Run without auto-restart
        uvicorn.run(app, host="0.0.0.0", port=5003)