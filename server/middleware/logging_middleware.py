"""
Middleware for logging all HTTP requests and responses
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from logger import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and their responses
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(f"Incoming Request: {method} {url} from {client_host}")
        
        # Log request headers (optional - can be verbose)
        # logger.debug(f"Request Headers: {dict(request.headers)}")
        
        try:
            # Process the request
            response: Response = await call_next(request)
            
            # Calculate processing time
            process_time = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Response: {method} {url} - "
                f"Status: {response.status_code} - "
                f"Duration: {process_time:.2f}ms"
            )
            
            # Add custom header with processing time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log any errors that occur
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request Failed: {method} {url} - "
                f"Error: {str(e)} - "
                f"Duration: {process_time:.2f}ms"
            )
            raise

