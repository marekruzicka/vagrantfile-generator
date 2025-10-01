"""
Footer API endpoints for configurable footer functionality.

Provides endpoints for discovering footer markdown files and retrieving their content.
"""

import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# Configuration
FOOTER_DATA_DIR = "/app/resources/footer"  # Container path


def get_footer_files() -> Dict[str, List]:
    """
    Discover footer markdown files in the footer directory.
    
    Returns:
        Dictionary with files, excluded, and errors lists
    """
    files = []
    errors = []
    excluded = []
    
    try:
        footer_path = Path(FOOTER_DATA_DIR)
        if not footer_path.exists():
            footer_path.mkdir(parents=True, exist_ok=True)
            
        # Find all .md files, exclude underscore-prefixed files
        md_files = glob.glob(os.path.join(FOOTER_DATA_DIR, "*.md"))
        
        for file_path in md_files:
            filename = os.path.basename(file_path)
            
            # Exclude underscore-prefixed files
            if filename.startswith("_"):
                excluded.append(filename)
                continue
                
            try:
                stat_info = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "path": f"backend/resources/footer/{filename}",
                    "lastModified": datetime.fromtimestamp(stat_info.st_mtime).isoformat() + "Z",
                    "size": stat_info.st_size,
                    "isValid": True
                })
            except OSError as e:
                excluded.append(filename)
                errors.append(f"Unable to read {filename}: {str(e)}")
                
    except Exception as e:
        errors.append(f"Directory access error: {str(e)}")
    
    return {
        "files": files,
        "excluded": excluded,
        "errors": errors
    }


def parse_markdown_heading(content: str) -> Dict[str, Any]:
    """
    Parse markdown content to extract title and external URL if present.
    
    Args:
        content: Raw markdown content
        
    Returns:
        Dict with title, isExternal, externalUrl, and renderedContent
    """
    lines = content.strip().split('\n')
    title = None
    is_external = False
    external_url = None
    
    # Look for first heading (starts with #)
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            # Extract heading text
            heading_text = line.lstrip('#').strip()
            
            # Check for markdown link syntax: [Text](URL)
            if heading_text.startswith('[') and '](http' in heading_text:
                # Parse markdown link
                link_end = heading_text.find('](')
                url_start = link_end + 2
                url_end = heading_text.find(')', url_start)
                
                if link_end > 1 and url_end > url_start:
                    title = heading_text[1:link_end]
                    external_url = heading_text[url_start:url_end]
                    is_external = True
                else:
                    title = heading_text
            else:
                title = heading_text
            break
    
    return {
        "title": title,
        "isExternal": is_external,
        "externalUrl": external_url
    }


@router.get("/footer/files")
async def get_footer_file_list():
    """
    Get list of available footer markdown files.
    
    Returns:
        JSON response with file list, excluded files, and any errors
    """
    try:
        result = get_footer_files()
        return JSONResponse(content={
            "status": "success",
            "files": result["files"],
            "excluded": result["excluded"],
            "errors": result["errors"]
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Footer directory not accessible",
                "code": "DIRECTORY_ERROR",
                "files": [],
                "excluded": [],
                "errors": [str(e)]
            }
        )


@router.get("/footer/content/{filename}")
async def get_footer_content(filename: str):
    """
    Get content of a specific footer markdown file.
    
    Args:
        filename: Name of the file (without .md extension)
        
    Returns:
        JSON response with file content and metadata
    """
    # Sanitize filename - remove .md if present and add it back
    if filename.endswith('.md'):
        filename = filename[:-3]
    
    file_path = os.path.join(FOOTER_DATA_DIR, f"{filename}.md")
    
    # Security check - ensure file is within footer directory
    if not os.path.abspath(file_path).startswith(os.path.abspath(FOOTER_DATA_DIR)):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check if file exists and isn't underscore-prefixed
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if filename.startswith("_"):
        raise HTTPException(status_code=403, detail="Access to hidden files denied")
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get file stats
        stat_info = os.stat(file_path)
        
        # Parse markdown for title and external links
        parsed = parse_markdown_heading(content)
        
        # Fallback to filename if no title found
        if not parsed["title"]:
            parsed["title"] = filename.replace('-', ' ').replace('_', ' ').title()
        
        return JSONResponse(content={
            "status": "success",
            "result": {
                "filename": f"{filename}.md",
                "title": parsed["title"],
                "isExternal": parsed["isExternal"],
                "externalUrl": parsed["externalUrl"],
                "rawContent": content,
                "renderedContent": content,  # For now, return raw - could add markdown parsing later
                "lastModified": datetime.fromtimestamp(stat_info.st_mtime).isoformat() + "Z",
                "size": stat_info.st_size,
                "isValid": True
            },
            "warnings": []
        })
        
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File contains invalid UTF-8 content")