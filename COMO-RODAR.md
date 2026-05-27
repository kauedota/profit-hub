# Profit Hub Marketplaces — Como rodar no seu computador

Projeto completo: backend (FastAPI) + frontend (React/Vite), já com os importadores
diretos de Mercado Livre e Shopee. O UpSeller continua como opção legada.

Seu banco atual (`backend/data/profit_hub.db`) está incluído — seu login e produtos
continuam salvos.

> Pré-requisitos: Python 3.11+ e Node.js 18+ instalados.
> Abra a pasta `profit-hub` no VS Code (File > Open Folder).

---

## 1) Backend (API) — terminal 1

No VS Code: Terminal > New Terminal, e rode:

```bash
cd backend
python -m venv venv
```

Ativar a venv:

- Windows (PowerShell): `venv\Scripts\Activate.ps1`
- Windows (CMD): `venv\Scripts\activate.bat`
- Mac/Linux: `source venv/bin/activate`

Instalar dependências e subir a API:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

A API sobe em **http://127.0.0.1:8000**
Documentação automática (testar rotas): **http://127.0.0.1:8000/docs**

Deixe esse terminal aberto rodando.

---

## 2) Frontend (tela) — terminal 2

Abra OUTRO terminal (o "+" no painel de terminal do VS Code):

```bash
cd frontend
npm install
npm run dev
```

O Vite mostra um endereço, normalmente **http://localhost:5173** — abra no navegador.

> Importante: suba o backend ANTES do frontend. A tela chama a API em
> http://127.0.0.1:8000 (endereço fixo no App.jsx).

---

## 3) Testar

1. Faça login (sua conta já existe no banco incluído).
2. No Dashboard, em "Marketplace", escolha **Detectar automaticamente** (ou force
   Mercado Livre / Shopee / UpSeller).
3. Suba o relatório:
   - Mercado Livre: relatório de **Vendas** exportado para Excel ("Vendas BR").
   - Shopee: relatório de **Renda / Income** (aba "Renda").
4. Veja os cards, pedidos, frete separado, produtos não cadastrados e exporte o Excel.

---

## Estrutura

```
profit-hub/
├─ backend/
│  ├─ app/
│  │  ├─ main.py, database.py, config.py
│  │  ├─ models/        (empresa, produto, usuário, config)
│  │  ├─ routes/        (auth, produtos, upload, config, conta, relatórios)
│  │  ├─ services/
│  │  │  ├─ ... (auth, planos, produtos, excel UpSeller legado, etc.)
│  │  │  └─ importers/  ← NOVO: ML, Shopee, fábrica, motor de cálculo
│  │  ├─ dependencies/  (auth por token)
│  │  └─ schemas/
│  ├─ data/             (profit_hub.db, produtos.json)
│  ├─ requirements.txt
│  └─ .env
└─ frontend/
   ├─ src/ (App.jsx ← atualizado, App.css, index.css, main.jsx)
   ├─ index.html, package.json, vite.config.js
   └─ ...
```

## Observações

- O sistema agora trabalha SÓ com relatórios diretos: Mercado Livre e Shopee.
  Toda referência à "UpSeller" foi removida (nomes agora são genéricos:
  "Lucro Marketplace", "Importar relatório do marketplace", etc.).
- Frete corrigido nos dois marketplaces: agora desconta o que o comprador pagou,
  então o "Frete Vendedor" mostra o custo real (zera na maioria das vendas).
- Pedidos cancelados/devolvidos são sinalizados; há um filtro "Ocultar
  cancelados/devolvidos" no dashboard e uma coluna na exportação.
- O limite do plano é checado ANTES de processar o arquivo.
- Segurança: a SECRET_KEY agora vem do arquivo `.env` (troque o valor em produção);
  o CORS é configurável por `CORS_ORIGINS` no `.env`; a rota de relatórios exige token.
- Pagamento: estrutura preparada (campos de assinatura na empresa + rotas
  `/billing/upgrade` e `/billing/webhook`), ainda SEM cobrança real.
- SHOPEE / SKU: o relatório de Renda traz o ID do anúncio na coluna SKU quando o
  produto não tem SKU mapeado na Shopee. Mapeie o SKU lá, ou cadastre por esse ID.
