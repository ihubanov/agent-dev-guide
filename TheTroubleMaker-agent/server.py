import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
# import asyncio # Unused import
from contextlib import asynccontextmanager
from app.configs import settings
from app.apis import api_router
import logging

logging_fmt = "%(asctime)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_fmt)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    logger.info(f"Starting Launchpad Agent server at {settings.host}:{settings.port}")

    try:
        yield

    except Exception as e:
        logger.error(f"Error: {e}")
        raise e

    finally:
        logger.info("Shutting down server")

def main():

    server_app = fastapi.FastAPI(
        lifespan=lifespan
    )

    server_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    server_app.include_router(api_router)

    @server_app.get("/health")
    async def healthcheck():
        return {"status": "ok", "message": "Yo, I am still alive"}

    config = uvicorn.Config(
        server_app,
        host=settings.host,
        port=settings.port,
        log_level="warning",
        timeout_keep_alive=300,
        workers=32,
        ws="none"  # Disable websockets since we don't need them
    )

    server = uvicorn.Server(config)
    server.run()

if __name__ == '__main__':
    main()