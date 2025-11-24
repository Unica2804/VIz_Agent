import pdfplumber
import json
import pandas as pd
import os
import requests
from pathlib import Path
from typing import Dict, Union
from urllib.parse import urlparse
import tempfile
import mimetypes


def _detect_file_type(file_path: str) -> str:
    """
    Detect file type from extension or mime type.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type extension (csv, xlsx, pdf, xml, json, etc.)
    """
    ext = Path(file_path).suffix.lower().lstrip('.')
    if ext:
        return ext
    
    # Try mime type detection
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_to_ext = {
        'application/pdf': 'pdf',
        'text/csv': 'csv',
        'application/vnd.ms-excel': 'xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/xml': 'xml',
        'text/xml': 'xml',
        'application/json': 'json',
    }
    return mime_to_ext.get(mime_type, 'unknown')


def _download_from_url(url: str) -> str:
    """
    Download file from URL to temporary location.
    
    Args:
        url: URL to download from
        
    Returns:
        Path to downloaded file
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    # Get filename from URL or content-disposition
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    
    if not filename or '.' not in filename:
        content_type = response.headers.get('content-type', '')
        ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.dat'
        filename = f"download{ext}"
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix)
    temp_file.write(response.content)
    temp_file.close()
    
    return temp_file.name


def _parse_csv(file_path: str) -> Dict:
    """Parse CSV file."""
    df = pd.read_csv(file_path)
    return {
        'data': df.to_dict(orient='records'),
        'pages': 1,
        'rows': len(df),
        'columns': len(df.columns)
    }


def _parse_excel(file_path: str) -> Dict:
    """Parse Excel file (supports .xls, .xlsx)."""
    excel_file = pd.ExcelFile(file_path)
    all_data = []
    total_rows = 0
    total_columns = 0
    
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        sheet_data = {
            'sheet_name': sheet_name,
            'data': df.to_dict(orient='records'),
            'rows': len(df),
            'columns': len(df.columns)
        }
        all_data.append(sheet_data)
        total_rows += len(df)
        total_columns = max(total_columns, len(df.columns))
    
    return {
        'data': all_data,
        'pages': len(excel_file.sheet_names),
        'rows': total_rows,
        'columns': total_columns
    }


def _parse_pdf(file_path: str) -> Dict:
    """Parse PDF file with tables."""
    all_tables = []
    total_rows = 0
    total_columns = 0
    
    with pdfplumber.open(file_path) as pdf:
        num_pages = len(pdf.pages)
        
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            
            for table_num, table in enumerate(tables, 1):
                if table and len(table) > 0:
                    # Convert table to DataFrame
                    df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                    
                    table_data = {
                        'page': page_num,
                        'table': table_num,
                        'data': df.to_dict(orient='records'),
                        'rows': len(df),
                        'columns': len(df.columns)
                    }
                    all_tables.append(table_data)
                    total_rows += len(df)
                    total_columns = max(total_columns, len(df.columns))
        
        return {
            'data': all_tables,
            'pages': num_pages,
            'rows': total_rows,
            'columns': total_columns
        }


def _parse_xml(file_path: str) -> Dict:
    """Parse XML file."""
    import xml.etree.ElementTree as ET
    
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Convert XML to list of dictionaries
    def xml_to_dict(element):
        result = {}
        if element.text and element.text.strip():
            result['_text'] = element.text.strip()
        for child in element:
            child_data = xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        result.update({f"@{k}": v for k, v in element.attrib.items()})
        return result
    
    data = xml_to_dict(root)
    
    # Try to flatten if it looks like tabular data
    rows_data = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                rows_data = value
                break
    
    rows = len(rows_data) if rows_data else 1
    columns = len(rows_data[0]) if rows_data and isinstance(rows_data[0], dict) else len(data)
    
    return {
        'data': rows_data if rows_data else data,
        'pages': 1,
        'rows': rows,
        'columns': columns
    }


def _parse_json(file_path: str) -> Dict:
    """Parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Determine structure
    if isinstance(data, list):
        rows = len(data)
        columns = len(data[0]) if data and isinstance(data[0], dict) else 0
    elif isinstance(data, dict):
        rows = 1
        columns = len(data)
    else:
        rows = 1
        columns = 1
    
    return {
        'data': data,
        'pages': 1,
        'rows': rows,
        'columns': columns
    }


def data_parser(file_path_or_url: str, file_type: str = None) -> Dict:
    """
    Parses data from a file path or URL, detects file type, and converts to JSON format.

    Args:
        file_path_or_url (str): The file path or URL to the data file.
        file_type (str, optional): The type of the file. If None, will be auto-detected.

    Returns:
        dict: Dictionary containing:
            - status: 'success' or 'failure'
            - error: Error message if failure
            - json_path: Path to saved JSON file
            - pages: Number of pages/sheets
            - rows: Total number of rows
            - columns: Maximum number of columns
    """
    temp_file_to_cleanup = None
    
    try:
        # Check if input is URL
        is_url = file_path_or_url.startswith(('http://', 'https://'))
        
        if is_url:
            # Download from URL
            file_path = _download_from_url(file_path_or_url)
            temp_file_to_cleanup = file_path
        else:
            file_path = file_path_or_url
            
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                'status': 'failure',
                'error': f'File not found: {file_path}',
                'json_path': None,
                'pages': 0,
                'rows': 0,
                'columns': 0
            }
        
        # Detect file type if not provided
        if not file_type:
            file_type = _detect_file_type(file_path)
        
        # Parse based on file type
        parser_map = {
            'csv': _parse_csv,
            'xlsx': _parse_excel,
            'xls': _parse_excel,
            'pdf': _parse_pdf,
            'xml': _parse_xml,
            'json': _parse_json,
        }
        
        parser = parser_map.get(file_type.lower())
        if not parser:
            return {
                'status': 'failure',
                'error': f'Unsupported file type: {file_type}',
                'json_path': None,
                'pages': 0,
                'rows': 0,
                'columns': 0
            }
        
        # Parse the file
        parsed_data = parser(file_path)
        
        # Save to JSON file
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        base_name = Path(file_path_or_url if not is_url else 'downloaded_file').stem
        json_output_path = output_dir / f"{base_name}_parsed.json"
        
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data['data'], f, ensure_ascii=False, indent=2, default=str)
        
        return {
            'status': 'success',
            'error': None,
            'json_path': str(json_output_path),
            'pages': parsed_data['pages'],
            'rows': parsed_data['rows'],
            'columns': parsed_data['columns']
        }
        
    except Exception as e:
        return {
            'status': 'failure',
            'error': str(e),
            'json_path': None,
            'pages': 0,
            'rows': 0,
            'columns': 0
        }
    
    finally:
        # Clean up temporary file if downloaded
        if temp_file_to_cleanup and os.path.exists(temp_file_to_cleanup):
            try:
                os.unlink(temp_file_to_cleanup)
            except:
                pass
    