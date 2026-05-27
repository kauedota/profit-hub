# Subir o Profit Hub para a internet

Guia passo a passo. Stack: **Render** (backend FastAPI + banco Postgres) +
**Vercel** (frontend React/Vite). Tudo grátis no início; quando os planos pagos
começarem, sobe pra ~US$ 7-15/mês cada.

Pré-requisito: ter o projeto num **repositório do GitHub**. Se ainda não tem, o
caminho mais simples é instalar o GitHub Desktop, criar um repositório novo
chamado `profit-hub`, e dar "publish" pasta inteira.

> Coloque o `backend/data/profit_hub.db` no `.gitignore` antes de subir — não
> queremos o banco local no repositório.

---

## Parte 1 — Backend e banco no Render

1. Crie uma conta em https://render.com (pode logar com a conta do GitHub).
2. No painel: **New +** → **PostgreSQL**.
   - Name: `profit-hub-db`
   - Region: **Oregon** (US-West) ou **Frankfurt** — o que tiver melhor latência aí
   - Plan: **Free** (válido por 90 dias; depois ~US$ 7/mês)
   - **Create Database**
3. Quando estiver pronto, copie o campo **Internal Database URL** (vamos colar
   no backend daqui a pouco).
4. De volta ao painel: **New +** → **Web Service** → conecte sua conta GitHub e
   selecione o repositório `profit-hub`.
   - Name: `profit-hub-api`
   - Region: a mesma do banco
   - Branch: `main`
   - **Root Directory**: `backend`  (importante, porque o repositório tem
     `backend/` e `frontend/`)
   - Runtime: **Python**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Plan: **Free** (boa para teste)
5. Antes de criar, em **Environment Variables**, adicione:
   - `DATABASE_URL` = cole o Internal Database URL do Postgres
   - `SECRET_KEY` = uma string longa aleatória (no terminal: `openssl rand -hex 32`)
   - `ALGORITHM` = `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES` = `10080`
   - `CORS_ORIGINS` = `https://profit-hub.vercel.app` (vamos confirmar o domínio
     na Parte 2; pode deixar `*` por enquanto e ajustar depois)
6. **Create Web Service**. O Render vai instalar tudo e subir. Vai levar uns
   3-5 minutos na primeira vez. Quando aparecer "Live", o backend está no ar
   em algo como `https://profit-hub-api.onrender.com`.
7. Teste abrindo `https://<sua-url>/docs` no navegador — tem que aparecer a
   documentação da API.

---

## Parte 2 — Frontend no Vercel

1. Crie uma conta em https://vercel.com (logue com GitHub).
2. **Add New** → **Project** → importe o mesmo repositório `profit-hub`.
3. Em **Configure Project**:
   - **Root Directory**: `frontend`
   - Framework Preset: **Vite** (deve detectar sozinho)
   - Build Command: `npm run build` (padrão)
   - Output Directory: `dist` (padrão)
4. Em **Environment Variables**:
   - `VITE_API_URL` = a URL do backend no Render (do passo 1.6)
5. **Deploy**. Em 1-2 minutos o site fica no ar em
   `https://profit-hub.vercel.app` (ou nome parecido).
6. Volte no Render, em Environment Variables, atualize `CORS_ORIGINS` para a
   URL exata do Vercel. O serviço reinicia sozinho.

Pronto — o site está no ar. Pode criar conta nele do mesmo jeito que fez local.

---

## Domínio próprio (opcional, quando quiser)

- Compre no Registro.br (`profithub.com.br` ~R$ 40/ano) ou Cloudflare/Hostinger.
- **Vercel** → Settings → Domains → adicione o domínio e siga as instruções
  de DNS (normalmente um CNAME).
- **Render** → opcional, se quiser uma URL bonita pro backend também
  (`api.profithub.com.br`).

## O que muda quando você atualiza o código

- Faz commit + push no GitHub na branch `main` →
- Render redeploya o backend sozinho. Vercel redeploya o frontend sozinho.
- Nenhuma migração manual: o `criar_tabelas()` roda automaticamente no startup
  e atualiza o esquema.

## Custos esperados (real, depois do free)

- Render Web Service: US$ 7/mês (Starter)
- Render Postgres: US$ 7/mês (Basic)
- Vercel: grátis (Hobby), suficiente até muito tráfego
- Domínio: R$ 40/ano
- **Total: ~US$ 14-15/mês** + domínio

Quando subir e tiver a URL pública, me avisa que partimos pra integração do
Mercado Livre via API (que é o próximo grande passo).
