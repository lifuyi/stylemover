from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import re
from bs4 import BeautifulSoup
import uvicorn
import os
import html
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Serve config file
@app.get("/config")
async def get_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = f.read()
        return Response(content=config, media_type="application/json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Config file not found")

class URLRequest(BaseModel):
    url: str

class ContentUpdate(BaseModel):
    original_content: str
    edited_content: str

class WeChatDraftRequest(BaseModel):
    access_token: str
    title: str = "默认标题"
    content: str
    author: str = ""
    digest: str = ""
    content_source_url: str = ""
    thumb_media_id: str = ""
    need_open_comment: int = 1
    only_fans_can_comment: int = 1

class WeChatTokenRequest(BaseModel):
    appid: str
    secret: str

@app.get("/")
async def read_root():
    return {"message": "WeChat Article Style Converter API"}

@app.post("/fetch-content")
async def fetch_content(request: URLRequest):
    # Validate and correct URL format before processing
    corrected_url = request.url
    if not corrected_url.startswith(("http://", "https://", "file://")):
        # If no scheme is provided, default to https:// for URLs that look like domains
        if "://" not in corrected_url and "." in corrected_url:
            corrected_url = "https://" + corrected_url
            logger.info(f"Corrected URL from '{request.url}' to '{corrected_url}'")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid URL '{request.url}': No scheme supplied. Perhaps you meant https://{request.url}?")
    
    # Update the request with the corrected URL
    request.url = corrected_url
    
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
            
            # Remove problematic hardcoded styling that conflicts with frontend JavaScript
            # The frontend JavaScript will handle all blockquote, code, and pre styling consistently
            # This ensures both panes (readonly and editable) have identical styling
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

@app.post("/send-to-wechat-draft")
async def send_to_wechat_draft(request: WeChatDraftRequest):
    """
    发送内容到微信草稿箱
    根据微信官方文档：https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add.html
    """
    logger.info("Sending to WeChat draft")
    access_token = request.access_token
    title = request.title
    content = request.content
    author = request.author
    digest = request.digest
    content_source_url = request.content_source_url
    thumb_media_id = request.thumb_media_id
    need_open_comment = request.need_open_comment
    only_fans_can_comment = request.only_fans_can_comment

    if not access_token:
        raise HTTPException(status_code=400, detail="缺少access_token")
    
    if not content:
        raise HTTPException(status_code=400, detail="缺少内容")
        
    if not thumb_media_id or thumb_media_id.strip() == "":
        raise HTTPException(status_code=400, detail="缺少封面图片media_id")

    # 构造微信API请求
    url = f'https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}'
    
    # 处理Unicode编码问题
    try:
        encoded_title = title.encode('utf-8').decode('latin-1') if isinstance(title, str) else title
        encoded_content = content.encode('utf-8').decode('latin-1') if isinstance(content, str) else content
    except Exception as e:
        logger.warning(f"Unicode encoding warning: {str(e)}")
        encoded_title = title
        encoded_content = content
    
    # 构造文章内容
    article = {
        'title': encoded_title,
        'author': author,
        'digest': digest,
        'content': encoded_content,
        'content_source_url': content_source_url,
        'need_open_comment': need_open_comment,
        'only_fans_can_comment': only_fans_can_comment
    }
    
    # 只有当thumb_media_id不为空时才添加
    if thumb_media_id and thumb_media_id.strip() != '':
        article['thumb_media_id'] = thumb_media_id
        logger.info(f"Adding thumb_media_id: {thumb_media_id}")
    else:
        logger.info("No thumb_media_id provided")
    
    articles = {
        'articles': [article]
    }
    
    logger.info(f"Sending article to WeChat: {articles}")
    
    try:
        logger.info(f"Sending request to WeChat API: {url}")
        logger.info(f"Request data: {articles}")
        response = requests.post(url, json=articles, timeout=10)
        logger.info(f"WeChat API response status: {response.status_code}")
        result = response.json()
        logger.info(f"WeChat API response data: {result}")
        
        if 'errcode' in result and result['errcode'] != 0:
            logger.info(f"WeChat API returned error: {result}")
            return JSONResponse(
                status_code=400,
                content={"errcode": result['errcode'], "errmsg": result['errmsg']}
            )
        
        logger.info("Successfully sent to WeChat draft")
        return {
            "success": True,
            "message": "内容已成功发送到微信草稿箱",
            "data": result
        }
    except requests.RequestException as e:
        error_msg = str(e) if str(e) else "网络请求失败或超时"
        logger.error(f"RequestException occurred: {error_msg}")
        raise HTTPException(status_code=500, detail=f"请求微信API失败: {error_msg}")
    except Exception as e:
        error_msg = str(e) if str(e) else "未知错误"
        logger.error(f"Exception occurred: {error_msg}")
        raise HTTPException(status_code=500, detail=f"请求微信API失败: {error_msg}")

@app.post("/wechat/token")
async def get_wechat_token(request: WeChatTokenRequest):
    """
    Exchange app ID and secret for access token
    """
    appid = request.appid
    secret = request.secret
    
    logger.info(f"Received request with appid: {appid}, secret: {'*' * len(secret) if secret else None}")
    
    if not appid:
        logger.info("Missing appid")
        raise HTTPException(status_code=400, detail="缺少appid")
    
    if not secret:
        logger.info("Missing secret")
        raise HTTPException(status_code=400, detail="缺少secret")

    # Construct WeChat API request
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
    logger.info(f"Requesting WeChat API: {url}")
    
    try:
        logger.info("About to make request to WeChat API")
        response = requests.get(url, timeout=10)
        logger.info(f"WeChat API response status: {response.status_code}")
        logger.info(f"WeChat API response headers: {dict(response.headers)}")
        result = response.json()
        logger.info(f"WeChat API response data: {result}")
        
        # Check if WeChat API returned an error
        if 'errcode' in result and result['errcode'] != 0:
            logger.info(f"WeChat API returned error: {result}")
            return JSONResponse(
                status_code=400,
                content={"errcode": result['errcode'], "errmsg": result['errmsg']}
            )
        
        logger.info("Successfully obtained access_token")
        return result
    except requests.RequestException as e:
        error_msg = str(e) if str(e) else f"网络请求失败或超时 (URL: {url})"
        logger.error(f"RequestException occurred: {error_msg}")
        logger.error(f"RequestException type: {type(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response headers: {dict(e.response.headers)}")
            logger.error(f"Response text: {e.response.text}")
        raise HTTPException(status_code=500, detail=f"请求微信API失败: {error_msg}")
    except Exception as e:
        error_msg = str(e) if str(e) else "未知错误"
        logger.error(f"Exception occurred: {error_msg}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"请求微信API失败: {error_msg}")

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