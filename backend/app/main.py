import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    account_routes,
    auth_routes,
    billing_routes,
    config_routes,
    ml_routes,
    product_routes,
    report_routes,
    upload_routes,
)

load_dotenv()

app = FastAPI(
    title="Profit Hub Marketplaces",
    description="Plataforma de cálculo de lucro real para lojistas de marketplaces.",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    """Roda migrações no startup. Se o banco demorar, loga e continua."""
    try:
        from app.database import criar_tabelas

        criar_tabelas()
        print("[startup] Banco atualizado com sucesso.")
    except Exception as e:
        print(f"[startup] Aviso: migração falhou ({e}). Continuando...")


# Origens liberadas no CORS, configuráveis pelo .env (CORS_ORIGINS, separadas por vírgula).
origens_env = os.getenv("CORS_ORIGINS", "*").strip()
if origens_env == "*" or not origens_env:
    origens = ["*"]
else:
    origens = [o.strip() for o in origens_env.split(",") if o.strip()]

# O frontend autentica por token no cabeçalho (não usa cookies), então não
# precisamos de allow_credentials — o que permite manter allow_origins flexível.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(product_routes.router)
app.include_router(report_routes.router)
app.include_router(upload_routes.router)
app.include_router(config_routes.router)
app.include_router(account_routes.router)
app.include_router(billing_routes.router)
app.include_router(ml_routes.router)


@app.get("/")
def home():
    return {
        "message": "API do Profit Hub Marketplaces funcionando!",
        "status": "online",
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Profit Hub Marketplaces"}
