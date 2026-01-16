from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.database import engine
from app.models import Base
from app.schemas.response import ApiResponse

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    servers=[
        {"url": "https://iot-soil-backend.onrender.com", "description": "Production server"},
        {"url": "http://localhost:8000", "description": "Local development server"},
    ]
)

# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(
            message=str(exc.detail),
            code=exc.status_code
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=ApiResponse.error(
            message="Validation error",
            code=422,
            data=exc.errors()
        ).dict()
    )

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    # Parse the error detail if possible (psycopg2 specific)
    error_detail = "Integrity error"
    if hasattr(exc, 'orig') and hasattr(exc.orig, 'pgerror'):
        error_detail = str(exc.orig.pgerror).split("DETAIL:")[-1].strip()
    
    return JSONResponse(
        status_code=409,
        content=ApiResponse.error(
            message=f"Database integrity error: {error_detail}",
            code=409
        ).dict()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiResponse.error(
            message="Internal server error",
            code=500,
            data={"detail": str(exc)} if settings.DEBUG else None
        ).dict()
    )

@app.middleware("http")
async def wrap_responses(request: Request, call_next):
    # Ignorer les docs et openapi
    if request.url.path.startswith(f"{settings.API_V1_PREFIX}/docs") or \
       request.url.path.startswith(f"{settings.API_V1_PREFIX}/openapi.json") or \
       request.url.path == "/":
        return await call_next(request)

    response = await call_next(request)
    
    # On ne wrap que les réponses JSON réussies (2xx) qui ne sont pas déjà wrappées
    if response.status_code >= 200 and response.status_code < 300:
        if "application/json" in response.headers.get("content-type", ""):
            import json
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                data = json.loads(body)
                # Vérifier si c'est déjà wrappé
                if isinstance(data, dict) and "success" in data and "code" in data:
                    # Déjà wrappé (probablement par un handler d'exception ou une route spécifique)
                    # reconstruct response
                    from fastapi.responses import Response
                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type="application/json"
                    )

                wrapped_data = ApiResponse.ok(
                    data=data,
                    code=response.status_code
                ).dict()
                
                new_headers = dict(response.headers)
                new_headers.pop("content-length", None)
                
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=response.status_code,
                    content=wrapped_data,
                    headers=new_headers
                )
            except Exception:
                # Si erreur de parsing, renvoyer la réponse originale
                from fastapi.responses import Response
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router principal
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "message": "AgroPredict API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}