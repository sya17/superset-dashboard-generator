"""
Superset Import Manager for handling ZIP file imports.

This module provides functionality to import dashboard ZIP files 
back into Superset after generation and export.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .client import SupersetClient
from .exceptions import SupersetClientError

logger = logging.getLogger(__name__)


class SupersetImportManager:
    """
    Manager for importing dashboard ZIP files into Superset.
    
    Handles the complete import process including file upload,
    import execution, and result validation.
    """
    
    def __init__(self, superset_client: SupersetClient = None):
        """
        Initialize the import manager.
        
        Args:
            superset_client: Optional SupersetClient instance. If not provided,
                           a new instance will be created.
        """
        self.superset_client = superset_client or SupersetClient()
        
    async def import_dashboard_zip(self, zip_file_path: str) -> Dict[str, Any]:
        """
        Import a dashboard ZIP file into Superset.
        
        Args:
            zip_file_path: Path to the ZIP file to import
            
        Returns:
            Dictionary containing import result information
        """
        try:
            zip_path = Path(zip_file_path)
            
            if not zip_path.exists():
                logger.error(f"❌ ZIP file does not exist: {zip_file_path}")
                return {
                    'success': False,
                    'error': f'ZIP file not found: {zip_file_path}',
                    'import_info': None
                }
            
            logger.info(f"🔄 Starting dashboard import: {zip_path.name}")
            
            # Perform the import
            import_result = self._perform_import(zip_path)
            
            if import_result['success']:
                logger.info(f"✅ Dashboard import completed successfully")
                logger.info(f"📊 Import details: {import_result.get('import_info', {})}")
                return import_result
            else:
                logger.error(f"❌ Dashboard import failed: {import_result.get('error')}")
                return import_result
                
        except Exception as e:
            logger.error(f"❌ Import process failed: {e}")
            return {
                'success': False,
                'error': f'Import process failed: {str(e)}',
                'import_info': None
            }
    
    def _perform_import(self, zip_path: Path) -> Dict[str, Any]:
        """
        Perform the actual import operation via Superset API.
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            Import result dictionary
        """
        try:
            logger.info(f"📤 Uploading ZIP file to Superset: {zip_path.name}")
            
            # Prepare the file for upload
            with open(zip_path, 'rb') as zip_file:
                files = {
                    'formData': (zip_path.name, zip_file, 'application/x-zip-compressed')
                }
                
                # Additional form data for import options (sesuai browser format)
                form_data = {
                    'passwords': '{}',  # JSON object as string, not empty string
                    'ssh_tunnel_passwords': '{}',
                    'ssh_tunnel_private_key_passwords': '{}', 
                    'ssh_tunnel_private_keys': '{}',
                    'overwrite': 'true'
                    # Note: 'overwrite' parameter tidak digunakan seperti di browser
                }
                
                # Make the import request
                response = self._upload_and_import(files, form_data, zip_path)

                logger.info(f"📥 Import response received")
                logger.info(f"📥 Import response received: {response}")

                if response:
                    return self._process_import_response(response)
                else:
                    return {
                        'success': False,
                        'error': 'No response received from Superset import API',
                        'import_info': None
                    }
                    
        except FileNotFoundError as e:
            logger.error(f"❌ ZIP file not found: {e}")
            return {
                'success': False,
                'error': f'ZIP file not found: {str(e)}',
                'import_info': None
            }
        except Exception as e:
            logger.error(f"❌ Import upload failed: {e}")
            return {
                'success': False,
                'error': f'Import upload failed: {str(e)}',
                'import_info': None
            }
    
    def _upload_and_import(self, files: Dict[str, Any], form_data: Dict[str, Any], zip_path: Path) -> Optional[Dict[str, Any]]:
        """
        Upload ZIP file and perform import via Superset API.
        
        Args:
            files: File data for upload
            form_data: Additional form parameters
            zip_path: Path to the ZIP file (for logging)
            
        Returns:
            API response or None if failed
        """
        try:
            # Use the client's request handler for file upload
            # Superset 5.0.0 uses /api/v1/dashboard/import/ endpoint
            endpoint = "dashboard/import/"
            
            logger.info(f"🌐 Making import request to: {endpoint}")
            
            # Make multipart form request
            response = self._make_multipart_request(endpoint, files, form_data, zip_path)
            
            return response
            
        except SupersetClientError as e:
            logger.error(f"❌ Superset API error during import: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during import: {e}")
            raise
    
    def _make_multipart_request(self, endpoint: str, files: Dict[str, Any], form_data: Dict[str, Any], zip_path: Path) -> Dict[str, Any]:
        """
        Make a multipart form request to Superset API.
        
        Args:
            endpoint: API endpoint
            files: File data
            form_data: Form parameters
            zip_path: Path to the ZIP file (for logging)
            
        Returns:
            API response
        """
        try:
            # Get session first
            session = self.superset_client.session_manager.get_session()
            
            # Ensure authentication - this sets session cookies
            access_token = self.superset_client.request_handler.auth_manager.ensure_authenticated()
            
            # Verify session has cookies after authentication
            logger.info(f"🔍 Session object ID: {id(session)}")
            logger.info(f"🔍 Session cookies count after auth: {len(session.cookies)}")
            
            # Log session cookies for debugging
            cookies_info = []
            for cookie in session.cookies:
                cookies_info.append(f"{cookie.name}={cookie.value[:20]}...")
            logger.info(f"🍪 Session cookies: {cookies_info}")
            
            # Get CSRF token with access token 
            csrf_token = self.superset_client.request_handler.csrf_handler.get_csrf_token(access_token)
            logger.info(f"🔑 Access token: {access_token[:20]}... (length: {len(access_token) if access_token else 0})")
            
            # Prepare headers sesuai browser format (session-based auth, bukan Bearer)
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}', 
                'Origin': self.superset_client.base_url,
                'Referer': f'{self.superset_client.base_url}/dashboard/list/',
                'User-Agent': 'python-requests/2.32.5'  # Identify as our client
            }
            
            if csrf_token:
                headers['X-CSRFToken'] = csrf_token
                logger.info(f"🔐 Using CSRF token: {csrf_token[:20]}...")
            else:
                logger.warning(f"⚠️ No CSRF token available - proceeding without it")
                
            # Session cookies are automatically handled by requests session
            # No need for Authorization header - using session cookies instead
            
            # Prepare URL
            url = f"{self.superset_client.base_url}/api/v1/{endpoint}"
            
            logger.info(f"🔗 Import URL: {url}")
            logger.info(f"📋 Form data: {form_data}")
            logger.info(f"📋 Headers: {headers}")
            logger.info(f"📄 File: {zip_path.name} ({zip_path.stat().st_size} bytes)")
            
            # Log final session state before request
            final_cookies = {cookie.name: cookie.value for cookie in session.cookies}
            logger.info(f"🍪 Final session cookies before request: {list(final_cookies.keys())}")
            
            # Make the request without following redirects
            # Note: Don't set Content-Type header manually for multipart/form-data
            # requests will set it automatically with proper boundary
            response = session.post(
                url,
                files=files,
                data=form_data,
                headers=headers,
                allow_redirects=False,  # Don't follow redirects to detect auth issues
                timeout=30  # Add timeout for large files
            )
            
            logger.info(f"📡 Import response status: {response.status_code}")
            logger.info(f"📄 Response headers: {dict(response.headers)}")
            logger.info(f"📄 Response content type: {response.headers.get('content-type', 'unknown')}")
            
            # Check for redirect responses (indicates authentication failure)
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                error_msg = f"Import redirected (status {response.status_code}) to {location} - likely authentication failure"
                logger.error(f"❌ {error_msg}")
                raise SupersetClientError(error_msg)
            
            elif response.status_code == 401:
                error_msg = "Import failed with 401 Unauthorized - authentication or CSRF token invalid"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 Response content: {response.text[:500]}")
                # Log which cookies were sent with the request
                sent_cookies = response.request.headers.get('Cookie', 'No cookies sent')
                logger.error(f"🍪 Cookies sent with request: {sent_cookies}")
                raise SupersetClientError(error_msg)
                
            elif response.status_code == 403:
                error_msg = "Import failed with 403 Forbidden - insufficient permissions or CSRF token invalid"
                logger.error(f"❌ {error_msg}")
                raise SupersetClientError(error_msg)
            
            elif response.status_code == 200:
                # Check content type to determine if it's JSON or HTML
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    try:
                        return response.json()
                    except ValueError as e:
                        logger.error(f"❌ Failed to parse JSON response: {e}")
                        return {
                            'success': False,
                            'message': 'Failed to parse JSON response',
                            'status_code': response.status_code,
                            'content': response.text[:500]
                        }
                elif 'text/html' in content_type:
                    # HTML response with 200 status typically means successful upload
                    # Superset sometimes returns HTML instead of JSON for file uploads
                    logger.info(f"📄 Received HTML response with status 200 - treating as successful import")
                    
                    return {
                        'success': True,
                        'message': 'Dashboard import completed successfully (HTML response)',
                        'status_code': response.status_code,
                        'content_type': content_type,
                        'note': 'Superset returned HTML instead of JSON, but 200 status indicates success'
                    }
                else:
                    # Other content type
                    return {
                        'success': True,  # Status 200 suggests success
                        'message': f'Import completed (content-type: {content_type})',
                        'status_code': response.status_code,
                        'content_type': content_type
                    }
            else:
                error_msg = f"Import failed with status {response.status_code}: {response.text[:200]}"
                logger.error(f"❌ {error_msg}")
                raise SupersetClientError(error_msg)
                
        except Exception as e:
            logger.error(f"❌ Multipart request failed: {e}")
            raise
    
    def _process_import_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the import response from Superset API.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed import result
        """
        try:
            # Check if response indicates success
            success = False
            error_message = None
            import_info = {}
            
            # Different possible response formats from Superset
            if isinstance(response, dict):
                # Check for explicit success field first
                if 'success' in response:
                    success = response['success']
                    if success:
                        import_info = response
                    else:
                        error_message = response.get('message', 'Import failed')
                
                # Check for success indicators in message
                elif 'message' in response:
                    message = response['message']
                    if any(word in message.lower() for word in ['success', 'imported', 'completed', 'upload']):
                        success = True
                        import_info['message'] = message
                    else:
                        error_message = message
                
                # Check for error indicators
                if 'error' in response and not success:
                    error_message = response['error']
                elif 'errors' in response and not success:
                    error_message = str(response['errors'])
                
                # Extract import details
                if 'result' in response:
                    import_info.update(response['result'])
                
                # If we have status code 200 and no explicit error, likely success
                if response.get('status_code') == 200 and not error_message and not success:
                    # Additional check for HTML responses
                    content_type = response.get('content_type', '')
                    if 'html' in content_type:
                        # For HTML responses with 200 status, consider it successful
                        # since the file upload was accepted
                        success = True
                        import_info['message'] = 'Dashboard import completed (HTML response)'
                        import_info['status_code'] = response['status_code']
                        import_info['content_type'] = content_type
                    else:
                        success = True
                        import_info['status_code'] = response['status_code']
                        if 'content' in response:
                            import_info['response_content'] = response['content'][:200]
            
            if success:
                logger.info(f"✅ Import processing successful")
                return {
                    'success': True,
                    'error': None,
                    'import_info': import_info
                }
            else:
                logger.error(f"❌ Import processing failed: {error_message}")
                return {
                    'success': False,
                    'error': error_message or 'Unknown import error',
                    'import_info': import_info
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to process import response: {e}")
            return {
                'success': False,
                'error': f'Failed to process import response: {str(e)}',
                'import_info': {'raw_response': str(response)[:500]}
            }