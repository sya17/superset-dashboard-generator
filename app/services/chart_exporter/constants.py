"""
Constants untuk Chart Exporter Service
"""

# Export API constants
EXPORT_API_ENDPOINT = "chart/export/"
EXPORT_QUERY_PARAM = "q"

# File constants
CACHE_DIR_NAME = "cache/chart_export"
ZIP_FILE_EXTENSION = ".zip"
EXTRACTED_DIR_SUFFIX = "_extracted"

# HTTP headers
ACCEPT_ZIP_HEADER = "application/zip"
ACCEPT_OCTET_STREAM_HEADER = "application/octet-stream"

# Timeout values (in seconds)
EXPORT_REQUEST_TIMEOUT = 30
DEFAULT_TIMEOUT = 30

# File size limits (in bytes)
MAX_ZIP_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_EXTRACTED_FILES = 1000

# Supported file extensions for extraction content parsing
SUPPORTED_JSON_EXTENSIONS = ['.json', '.JSON']
SUPPORTED_TEXT_EXTENSIONS = ['.txt', '.md', '.yaml', '.yml']

# Error messages
ERROR_MESSAGES = {
    "empty_response": "Export response is empty",
    "invalid_chart_id": "Invalid chart ID provided",
    "export_failed": "Failed to export chart from Superset",
    "save_failed": "Failed to save export file",
    "extract_failed": "Failed to extract ZIP file",
    "cleanup_failed": "Failed to cleanup export files",
    "file_too_large": "Export file is too large",
    "too_many_files": "Too many files in ZIP archive"
}

# Success messages
SUCCESS_MESSAGES = {
    "export_completed": "Chart export completed successfully",
    "extraction_completed": "ZIP extraction completed successfully",
    "cleanup_completed": "Export cleanup completed successfully"
}

# Log messages
LOG_MESSAGES = {
    "starting_export": "Starting chart export for chart ID: {}",
    "export_url": "Exporting chart from: {}",
    "saving_file": "Saving export file to: {}",
    "extracting_zip": "Extracting ZIP file to: {}",
    "cleanup_files": "Cleaning up export files for chart {}: {}",
    "service_initialized": "ChartExporter service initialized",
    "service_closed": "ChartExporter service closed"
}