"""
Chart Exporter Service
Service untuk mengexport chart dari Superset API dan mengekstrak hasil ZIP.
"""

import os
import json
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from app.services.superset.client import SupersetClient
from app.core.config import settings
from .constants import (
    CACHE_DIR_NAME, ZIP_FILE_EXTENSION, EXTRACTED_DIR_SUFFIX,
    ACCEPT_ZIP_HEADER, ACCEPT_OCTET_STREAM_HEADER, EXPORT_REQUEST_TIMEOUT,
    ERROR_MESSAGES, SUCCESS_MESSAGES, LOG_MESSAGES
)

logger = logging.getLogger(__name__)


class ChartExporterError(Exception):
    """Exception untuk Chart Exporter service."""
    pass


class ChartExporter:
    """
    Service untuk mengexport chart dari Superset dan mengekstrak file hasil.
    
    Flow:
    1. Export chart via Superset API menggunakan chart ID
    2. Simpan file ZIP ke cache/chart_export/
    3. Ekstrak file ZIP untuk mendapatkan chart definition
    """
    
    def __init__(self):
        self.superset_client = SupersetClient()
        self.cache_dir = Path(CACHE_DIR_NAME)
        
        # Buat directory cache jika belum ada
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(LOG_MESSAGES["service_initialized"])
    
    async def export_chart(self, chart_id: int) -> Dict[str, Any]:
        """
        Export chart dari Superset dan simpan ke cache directory.
        
        Args:
            chart_id: ID chart yang akan diexport
            
        Returns:
            Dictionary dengan informasi export result
        """
        try:
            logger.info(LOG_MESSAGES["starting_export"].format(chart_id))
            
            # 1. Export chart via Superset API
            export_data = self._export_chart_from_superset(chart_id)
            
            # 2. Simpan file ZIP ke cache
            zip_file_path = self._save_export_to_cache(chart_id, export_data)
            
            # 3. Ekstrak file ZIP
            extracted_files = self._extract_zip_file(zip_file_path, chart_id)
            
            result = {
                "success": True,
                "chart_id": chart_id,
                "zip_file_path": str(zip_file_path),
                "extracted_files": extracted_files,
                "export_timestamp": self._get_current_timestamp()
            }
            
            logger.info(SUCCESS_MESSAGES["export_completed"] + f" for chart ID: {chart_id}")
            return result
            
        except Exception as e:
            logger.error(f"Chart export failed for chart ID {chart_id}: {e}")
            return {
                "success": False,
                "chart_id": chart_id,
                "error": str(e),
                "export_timestamp": self._get_current_timestamp()
            }
    
    def _export_chart_from_superset(self, chart_id: int, retry_with_alternative_format: bool = True) -> bytes:
        """
        Export chart dari Superset API menggunakan /chart/export/ endpoint.
        
        Args:
            chart_id: ID chart yang akan diexport
            
        Returns:
            Binary data dari ZIP file
        """
        try:
            from urllib.parse import urljoin
            import requests
            
            # Get authentication dan CSRF token seperti dashboard export
            access_token = self.superset_client.request_handler.auth_manager.ensure_authenticated()
            csrf_token = self.superset_client.request_handler.csrf_handler.get_csrf_token(access_token)
            
            # Build export URL dengan proper rison encoding
            base_url = self.superset_client.base_url
            export_url = urljoin(base_url, f"api/v1/chart/export/?q=!({chart_id})")
            
            # Format parameter q dengan rison array format
            # rison_param = f"!({chart_id})"
            # params = {"q": rison_param}
            
            logger.info(f"Exporting chart from: {export_url} ")
            
            # Prepare headers seperti dashboard export
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-CSRFToken': csrf_token,  # ← CSRF token di header
                'Accept': ACCEPT_ZIP_HEADER,
                'User-Agent': 'Superset-Dashboard-Generator/1.0'
            }
            logger.info(f"Exporting chart header: {headers}")
            
            # Make request dengan params seperti dashboard export
            session = self.superset_client.request_handler.api_client.session_manager.get_session()
            response = session.get(export_url, headers=headers, params=None, timeout=EXPORT_REQUEST_TIMEOUT)
            
            # Log response details untuk debugging
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check response status dengan error detail yang lebih baik
            if not response.ok:
                error_detail = ""
                try:
                    # Coba parse response sebagai JSON untuk error detail
                    error_data = response.json()
                    error_detail = f" - {error_data}"
                except:
                    # Jika tidak bisa parse JSON, gunakan text
                    error_detail = f" - {response.text[:500]}"
                
                logger.error(f"Export request failed with status {response.status_code}{error_detail}")
                response.raise_for_status()
            
            # Validate response content type
            content_type = response.headers.get('content-type', '')
            if ACCEPT_ZIP_HEADER not in content_type and ACCEPT_OCTET_STREAM_HEADER not in content_type:
                logger.warning(f"Unexpected content type: {content_type}")
            
            # Return binary content
            binary_data = response.content
            
            if len(binary_data) == 0:
                raise ChartExporterError(ERROR_MESSAGES["empty_response"])
            
            logger.info(f"Export successful, received {len(binary_data)} bytes")
            return binary_data
            
        except Exception as e:
            logger.error(f"Error exporting chart from Superset: {e}")
            
            raise ChartExporterError(f"{ERROR_MESSAGES['export_failed']}: {e}")
    
    def _save_export_to_cache(self, chart_id: int, export_data: bytes) -> Path:
        """
        Simpan hasil export ke cache directory.
        
        Args:
            chart_id: ID chart
            export_data: Binary data ZIP file
            
        Returns:
            Path ke file ZIP yang disimpan
        """
        try:
            zip_filename = f"{chart_id}{ZIP_FILE_EXTENSION}"
            zip_file_path = self.cache_dir / zip_filename
            
            logger.info(LOG_MESSAGES["saving_file"].format(zip_file_path))
            
            # Write binary data ke file
            with open(zip_file_path, 'wb') as f:
                f.write(export_data)
            
            logger.info(f"Export file saved successfully: {zip_file_path}")
            return zip_file_path
            
        except Exception as e:
            logger.error(f"Error saving export file: {e}")
            raise ChartExporterError(f"{ERROR_MESSAGES['save_failed']}: {e}")
    
    def _extract_zip_file(self, zip_file_path: Path, chart_id: int) -> Dict[str, Any]:
        """
        Ekstrak file ZIP dan return informasi file yang diekstrak.
        
        Args:
            zip_file_path: Path ke file ZIP
            chart_id: ID chart untuk nama folder ekstraksi
            
        Returns:
            Dictionary dengan informasi file yang diekstrak
        """
        try:
            extract_dir = self.cache_dir / f"{chart_id}{EXTRACTED_DIR_SUFFIX}"
            extract_dir.mkdir(exist_ok=True)
            
            logger.info(LOG_MESSAGES["extracting_zip"].format(extract_dir))
            
            extracted_files = []
            
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                # List semua file dalam ZIP
                zip_files = zip_ref.namelist()
                logger.info(f"Files in ZIP: {zip_files}")
                
                # Extract semua file
                zip_ref.extractall(extract_dir)
                
                # Process setiap file yang diekstrak
                for filename in zip_files:
                    file_path = extract_dir / filename
                    file_info = {
                        "filename": filename,
                        "path": str(file_path),
                        "size": file_path.stat().st_size if file_path.exists() else 0
                    }
                    
                    # Jika file JSON, parse content
                    if filename.endswith('.json') and file_path.exists():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_info["content"] = json.load(f)
                        except Exception as e:
                            logger.warning(f"Failed to parse JSON file {filename}: {e}")
                            file_info["content"] = None
                    
                    extracted_files.append(file_info)
            
            result = {
                "extract_directory": str(extract_dir),
                "files": extracted_files,
                "total_files": len(extracted_files)
            }
            
            logger.info(SUCCESS_MESSAGES["extraction_completed"] + f": {len(extracted_files)} files extracted")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting ZIP file: {e}")
            raise ChartExporterError(f"{ERROR_MESSAGES['extract_failed']}: {e}")
    
    def get_export_info(self, chart_id: int) -> Optional[Dict[str, Any]]:
        """
        Get informasi export yang sudah ada untuk chart ID tertentu.
        
        Args:
            chart_id: ID chart
            
        Returns:
            Dictionary dengan informasi export atau None jika belum ada
        """
        try:
            zip_file_path = self.cache_dir / f"{chart_id}{ZIP_FILE_EXTENSION}"
            extract_dir = self.cache_dir / f"{chart_id}{EXTRACTED_DIR_SUFFIX}"
            
            if not zip_file_path.exists():
                return None
            
            info = {
                "chart_id": chart_id,
                "zip_file_path": str(zip_file_path),
                "zip_file_size": zip_file_path.stat().st_size,
                "zip_file_modified": zip_file_path.stat().st_mtime,
                "extracted_directory": str(extract_dir) if extract_dir.exists() else None,
                "is_extracted": extract_dir.exists()
            }
            
            # Jika sudah diekstrak, tambahkan info file
            if extract_dir.exists():
                extracted_files = []
                for file_path in extract_dir.iterdir():
                    if file_path.is_file():
                        extracted_files.append({
                            "filename": file_path.name,
                            "path": str(file_path),
                            "size": file_path.stat().st_size
                        })
                
                info["extracted_files"] = extracted_files
                info["total_extracted_files"] = len(extracted_files)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting export info for chart {chart_id}: {e}")
            return None
    
    def cleanup_export(self, chart_id: int) -> bool:
        """
        Bersihkan file export untuk chart ID tertentu.
        
        Args:
            chart_id: ID chart
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            zip_file_path = self.cache_dir / f"{chart_id}{ZIP_FILE_EXTENSION}"
            extract_dir = self.cache_dir / f"{chart_id}{EXTRACTED_DIR_SUFFIX}"
            
            cleaned_files = []
            
            # Hapus ZIP file
            if zip_file_path.exists():
                zip_file_path.unlink()
                cleaned_files.append(str(zip_file_path))
            
            # Hapus extracted directory
            if extract_dir.exists():
                import shutil
                shutil.rmtree(extract_dir)
                cleaned_files.append(str(extract_dir))
            
            if cleaned_files:
                logger.info(LOG_MESSAGES["cleanup_files"].format(chart_id, cleaned_files))
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up export for chart {chart_id}: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp dalam format ISO."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'superset_client'):
            self.superset_client.close()
        logger.info(LOG_MESSAGES["service_closed"])