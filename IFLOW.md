# iFlow CLI - Project Context

## Project Overview
This is a WeChat Article Style Converter web application that allows users to convert any HTML content to a WeChat article style. The application features a dual-pane interface where users can view the original content on the left (read-only) and edit the content on the right while preserving the original structure and style.

## Architecture
```
stylemover/
├── main.py              # Backend server (FastAPI)
├── project.toml         # Python dependencies (replaces requirements.txt)
├── start.sh             # Startup script
├── README.md            # Project documentation
├── IFLOW.md             # iFlow CLI context file
├── cue.md               # Additional documentation
├── test_api.py          # API testing script
├── test_article.html    # Test HTML file
├── static/
│   └── index.html       # Frontend interface
└── .venv/               # Virtual environment (created on first run)
```

## Key Components

### Backend (main.py)
- Built with FastAPI framework
- Implements CORS middleware for frontend-backend communication
- Provides three main endpoints:
  1. `GET /` - Health check endpoint
  2. `POST /fetch-content` - Fetch and parse HTML content from a URL
  3. `POST /process-content` - Process edited content
- Uses BeautifulSoup4 for HTML parsing and manipulation
- Handles both remote URLs and local file URLs for testing

### Frontend (static/index.html)
- Dual-pane interface design
- Left pane: Read-only view of original content
- Right pane: Editable view for content modification
- Responsive design with mobile support
- WeChat-like styling for content display
- Action buttons for Reset, Save Changes, and Export HTML
- JavaScript implementation for API communication

## Dependencies
- fastapi==0.104.1
- uvicorn==0.24.0
- requests==2.31.0
- beautifulsoup4==4.12.2
- python-multipart==0.0.6

## Development Setup

### Prerequisites
- Python 3.11+
- `uv` package manager

### Installation and Running
Option 1: Using the startup script
```bash
./start.sh
```

With auto-restart (for development):
```bash
./start.sh --auto-restart
# or
./start.sh -r
```

Option 2: Manual setup
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .  # Install from project.toml
python main.py
```

With auto-restart (for development):
```bash
AUTO_RESTART=1 python main.py
```

### Accessing the Application
After starting the server:
- Open your browser and navigate to `http://localhost:5003/static/index.html`

## Usage Workflow
1. Enter a WeChat article URL (or any HTML URL) in the input field
2. Click "Load Article" to fetch and display the content
3. View the original content in the left pane (read-only)
4. Edit the content in the right pane as needed
5. Click "Save Changes" to process your edits
6. Click "Export HTML" to download the edited content as an HTML file

## Testing
For local testing, you can use a file URL in the format:
`file:///path/to/your/file.html`

A test article is included at `test_article.html` that can be used for testing with the URL:
`file:///Users/yourusername/path/to/stylemover/test_article.html`

## API Endpoints
- `GET /` - Health check endpoint returning a simple message
- `POST /fetch-content` - Fetches and parses HTML content from a provided URL
- `POST /process-content` - Processes edited content (placeholder for future enhancements)

## Key Features
- Dual-pane interface for comparison and editing
- Preservation of original HTML structure and styling
- WeChat article styling compatibility
- Content editing capabilities
- Export functionality to save edited content as HTML
- Responsive design for both desktop and mobile devices
- Support for local file URLs for development and testing
- Auto-restart support for development