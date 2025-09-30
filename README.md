# WeChat Article Style Converter

This web application allows users to convert any HTML content to a WeChat article style. Users can input a URL (typically a WeChat article URL), view the content in a read-only pane on the left, and edit the content in an editable pane on the right while preserving the original structure and style.

## Features

- Dual-pane interface: read-only view on the left, editable view on the right
- URL input for loading WeChat articles or any HTML content
- Preservation of original structure and style
- Content editing capabilities
- Export functionality to save edited content as HTML

## Setup and Installation

1. Make sure you have Python 3.11+ and `uv` installed
2. Clone or download this repository
3. Run the startup script:
   ```bash
   ./start.sh
   ```
   
   With auto-restart (for development):
   ```bash
   ./start.sh --auto-restart
   # or
   ./start.sh -r
   ```

   Or manually set up:
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

4. Open your browser and navigate to `http://localhost:5003/static/index.html`

## Usage

1. Enter a WeChat article URL in the input field at the top
2. Click "Load Article" to fetch and display the content
3. The original content will appear in the left pane (read-only)
4. The editable version will appear in the right pane
5. Edit the content in the right pane as needed
6. Click "Save Changes" to process your edits
7. Click "Export HTML" to download the edited content as an HTML file

## Testing

For local testing, you can use a file URL in the format:
`file:///path/to/your/file.html`

For example:
`file:///Users/yourusername/path/to/stylemover/test_article.html`

A test article is included at `test_article.html` that you can use for testing.

## Technologies Used

- Backend: Python, FastAPI, BeautifulSoup4
- Frontend: HTML, CSS, JavaScript
- Package Management: uv

## Project Structure

```
stylemover/
├── main.py              # Backend server
├── project.toml         # Python dependencies (replaces requirements.txt)
├── start.sh             # Startup script
├── README.md            # This file
├── test_article.html    # Test HTML file
├── static/
│   └── index.html       # Frontend interface
└── .venv/               # Virtual environment (created on first run)
```

## API Endpoints

- `GET /` - Health check endpoint
- `POST /fetch-content` - Fetch and parse HTML content from a URL
- `POST /process-content` - Process edited content (placeholder for future enhancements)