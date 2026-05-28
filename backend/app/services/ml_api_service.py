"""
Integração com a API do Mercado Livre.

Fluxo OAuth:
1. Usuário clica "Conectar" → redireciona pra ML com CLIENT_ID.
2. ML autentica e redireciona de volta pra /ml/callback?code=...
3. Backend troca o código por access_token + refresh_token.
4. Tokens ficam salvos na empresa. Access token expira em 6h — renovação automática.

Fluxo de sync:
1. Usuário escolhe período e clica "Sincronizar".
2. Backend busca pedidos na API do ML (paginado).
3. Normaliza para PedidoNormalizado e calcula o lucro.
4. Devolve o mesmo formato {resumo, pedidos} que o upload de relatório.
"""

import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from fastapi import HTTPException, status

from app.database import SessionLocal, criar_tabelas
from app.models.company_model import EmpresaModel

ML_AUTH = "https://auth.mercadolivre.com.br/authorization"
ML_API = "https://api.mercadolivre.com"


def _client_id():
    v = os.getenv("ML_CLIENT_ID", "")
    if not v:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integração com Mercado Livre não configurada no servidor.",
        )
    return v


def _client_secret():
    return os.getenv("ML_CLIENT_SECRET", "")


def _redirect_uri():
    return os.getenv(
        "ML_REDIRECT_URI",
        "https://profit-hub-api.onrender.com/ml/callback",
    )


# ── OAuth ──────────────────────────────────────────────────────────────────────


def gerar_url_oauth(empresa_id: int) -> str:
    """Gera a URL de autorização do Mercado Livre."""
    params = {
        "response_type": "code",
        "client_id": _client_id(),
        "redirect_uri": _redirect_uri(),
        "state": str(empresa_id),
    }
    return f"{ML_AUTH}?{urlencode(params)}"


def _salvar_tokens(
    empresa_id: int,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    seller_id: str,
):
    criar_tabelas()
    db = SessionLocal()
    try:
        emp = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if emp:
            emp.ml_access_token = access_token
            emp.ml_refresh_token = refresh_token
            emp.ml_token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            if seller_id:
                emp.ml_seller_id = seller_id
            db.commit()
    finally:
        db.close()


def trocar_codigo_por_token(code: str, empresa_id: int):
    """Troca o código de autorização por tokens de acesso."""
    resp = requests.post(
        f"{ML_API}/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "code": code,
            "redirect_uri": _redirect_uri(),
        },
        timeout=15,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao autenticar com o Mercado Livre: {resp.text[:200]}",
        )
    dados = resp.json()
    _salvar_tokens(
        empresa_id=empresa_id,
        access_token=dados["access_token"],
        refresh_token=dados["refresh_token"],
        expires_in=dados.get("expires_in", 21600),
        seller_id=str(dados.get("user_id", "")),
    )
    return dados


def _obter_token_valido(empresa: EmpresaModel) -> str:
    """Retorna um access token válido, renovando automaticamente se necessário."""
    if not empresa.ml_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mercado Livre não conectado. Conecte sua conta em Minha Conta.",
        )

    # Renovar se expira nos próximos 5 minutos
    if (
        empresa.ml_token_expiry is None
        or datetime.utcnow() >= empresa.ml_token_expiry - timedelta(minutes=5)
    ):
        resp = requests.post(
            f"{ML_API}/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": _client_id(),
                "client_secret": _client_secret(),
                "refresh_token": empresa.ml_refresh_token,
            },
            timeout=15,
        )
        if not resp.ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessão do Mercado Livre expirada. Reconecte sua conta.",
            )
        dados = resp.json()
        _salvar_tokens(
            empresa_id=empresa.id,
            access_token=dados["access_token"],
            refresh_token=dados.get("refresh_token", empresa.ml_refresh_token),
            expires_in=dados.get("expires_in", 21600),
            seller_id=empresa.ml_seller_id or str(dados.get("user_id", "")),
        )
        return dados["access_token"]

    return empresa.ml_access_token


def desconectar_ml(empresa_id: int):
    """Remove os tokens de ML da empresa."""
    criar_tabelas()
    db = SessionLocal()
    try:
        emp = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if emp:
            emp.ml_access_token = ""
            emp.ml_refresh_token = ""
            emp.ml_token_expiry = None
            emp.ml_seller_id = ""
            emp.ml_ultimo_sync = None
            db.commit()
    finally:
        db.close()


# ── Busca de pedidos na API ────────────────────────────────────────────────────


def _buscar_pagina(
    seller_id: str, token: str, data_inicio: str, data_fim: str, offset: int
) -> dict:
    resp = requests.get(
        f"{ML_API}/orders/search",
        params={
            "seller": seller_id,
            "order.status": "paid",
            "sort": "date_asc",
            "date_closed.from": data_inicio,
            "date_closed.to": data_fim,
            "offset": offset,
            "limit": 50,
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    if not resp.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao buscar pedidos do ML: {resp.text[:200]}",
        )
    return resp.json()


def buscar_pedidos_api(empresa_id: int, data_inicio: str, data_fim: str) -> list:
    """
    Busca todos os pedidos pagos do período na API do ML.
    data_inicio / data_fim: "YYYY-MM-DD" (convertidos para ISO 8601 com timezone).
    Retorna lista de dicts com o formato da API do ML.
    """
    criar_tabelas()
    db = SessionLocal()
    try:
        emp = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Empresa não encontrada.")
        token = _obter_token_valido(emp)
        seller_id = emp.ml_seller_id
        if not seller_id:
            raise HTTPException(
                status_code=400,
                detail="Seller ID do Mercado Livre não encontrado. Reconecte sua conta.",
            )
    finally:
        db.close()

    # Converte datas para ISO 8601 com timezone Brasil (-03:00)
    dt_ini = f"{data_inicio}T00:00:00.000-03:00"
    dt_fim = f"{data_fim}T23:59:59.999-03:00"

    todos = []
    offset = 0
    while True:
        pagina = _buscar_pagina(seller_id, token, dt_ini, dt_fim, offset)
        resultados = pagina.get("results") or []
        if not resultados:
            break
        todos.extend(resultados)
        total = (pagina.get("paging") or {}).get("total", 0)
        offset += 50
        if offset >= total:
            break

    # Registra data do último sync
    db = SessionLocal()
    try:
        emp = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if emp:
            emp.ml_ultimo_sync = datetime.utcnow()
            db.commit()
    finally:
        db.close()

    return todos


# ── Normalização dos pedidos da API ───────────────────────────────────────────


def normalizar_pedidos_api(orders: list) -> list:
    """
    Converte a lista de pedidos da API do ML para PedidoNormalizado.
    A API já traz o seller_sku diretamente — sem necessidade de mapa externo.
    """
    from app.services.importers.normalized_order import PedidoNormalizado

    pedidos = []
    for order in orders:
        order_id = str(order.get("id", ""))
        data = (order.get("date_closed") or "")[:10]
        status_ml = order.get("status", "")
        cancelado = status_ml in ("cancelled", "invalid")

        paid_amount = float(order.get("paid_amount") or 0)
        total_amount = float(order.get("total_amount") or 0)
        # shipping_cost: negativo = custo do vendedor; positivo = pago pelo comprador
        shipping_signed = float(order.get("shipping_cost") or 0)
        frete_vendedor = abs(min(shipping_signed, 0))

        items = order.get("order_items") or []
        multi = len(items) > 1

        for idx, it in enumerate(items):
            item = it.get("item") or {}
            sku = str(item.get("seller_sku") or item.get("id") or "")
            titulo = item.get("title") or ""
            qtd = int(it.get("quantity") or 1)
            unit_price = float(it.get("unit_price") or 0)
            sale_fee = abs(float(it.get("sale_fee") or 0))

            # Para pedidos multi-item: só o primeiro recebe o valor líquido total
            liq = paid_amount if idx == 0 else 0

            pedidos.append(
                PedidoNormalizado(
                    marketplace="Mercado Livre",
                    loja="Mercado Livre",
                    pedido_plataforma=order_id,
                    numero_pedido=order_id,
                    data=data,
                    sku=sku,
                    id_produto_plataforma="",
                    titulo=titulo,
                    quantidade=qtd,
                    valor_venda=unit_price * qtd,
                    taxas_marketplace=sale_fee,
                    frete_vendedor=frete_vendedor if idx == 0 else 0,
                    frete_pago_comprador=max(shipping_signed, 0) if idx == 0 else 0,
                    frete_subsidio_marketplace=0,
                    valor_liquido=liq,
                    status_marketplace=status_ml,
                    pedido_multi_sku=multi,
                    cancelado=cancelado,
                )
            )

    return pedidos
