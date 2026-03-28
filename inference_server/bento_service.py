from __future__ import annotations

import bentoml
from fastapi import FastAPI

from inference_server.main import app as fastapi_app


@bentoml.service(name="agrolidar-inference")
class AgroLidarService:
    def __init__(self) -> None:
        self._app: FastAPI = fastapi_app

    @bentoml.asgi_app(app=fastapi_app, path="/")
    def app(self) -> FastAPI:
        return self._app
