from __future__ import annotations

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("inference_server.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            latency_ms = (time.perf_counter() - started) * 1000.0
            frame_id = getattr(request.state, "frame_id", None)
            logger.info(
                json.dumps(
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "latency_ms": round(latency_ms, 3),
                        "frame_id": frame_id,
                    }
                )
            )
