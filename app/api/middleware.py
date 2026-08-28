import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = str(uuid4())
        start_time = time.perf_counter()

        request.state.request_id = request_id

        client_ip = (
            request.client.host
            if request.client
            else None
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            raise

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "client_ip": client_ip,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return response