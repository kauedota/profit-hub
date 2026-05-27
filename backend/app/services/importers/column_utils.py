"""
Utilitários compartilhados de leitura de Excel e normalização de colunas.

Reaproveita a mesma filosofia que já existia em excel_import_service.py
(localizar coluna por variações de nome, converter valores monetários),
mas isolada aqui para ser usada por todos os importadores novos.
"""

import unicodedata

import pandas as pd


def limpar_nome_coluna(texto):
    """Normaliza um nome de coluna: minúsculo, sem acento, sem espaços extras."""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace("\n", " ").replace("\r", " ")
    texto = " ".join(texto.split())
    return texto


def localizar_coluna(df, opcoes):
    """
    Procura no DataFrame uma coluna que case com alguma das `opcoes`.

    Primeiro tenta correspondência exata (normalizada), depois correspondência
    parcial (a opção aparece dentro do nome da coluna). Devolve o nome ORIGINAL
    da coluna no df, ou None.
    """
    colunas_normalizadas = {limpar_nome_coluna(c): c for c in df.columns}

    for opcao in opcoes:
        opcao_limpa = limpar_nome_coluna(opcao)
        if opcao_limpa in colunas_normalizadas:
            return colunas_normalizadas[opcao_limpa]

    for nome_limpo, nome_original in colunas_normalizadas.items():
        for opcao in opcoes:
            if limpar_nome_coluna(opcao) in nome_limpo:
                return nome_original

    return None


def valor_numero(valor):
    """
    Converte qualquer célula em float de forma robusta.

    Aceita números, strings com R$, ponto ou vírgula decimal, e trata
    '-', '' e NaN como 0. Os relatórios diretos vêm com ponto decimal,
    mas mantemos suporte a vírgula para não quebrar com variações.
    """
    if valor is None:
        return 0.0

    if isinstance(valor, (int, float)):
        try:
            if pd.isna(valor):
                return 0.0
        except (TypeError, ValueError):
            pass
        return float(valor)

    texto = str(valor).strip()

    if texto in ("", "-", "--", "nan", "NaN", "None"):
        return 0.0

    texto = texto.replace("R$", "").replace(" ", "")

    if "," in texto and "." in texto:
        # formato brasileiro 1.234,56
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0.0


def valor_texto(valor):
    """Devolve a célula como texto limpo, '' quando vazia/NaN."""
    if valor is None:
        return ""
    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass
    texto = str(valor).strip()
    if texto in ("nan", "NaN", "None", "-"):
        return ""
    return texto


def ler_excel_detectando_cabecalho(
    caminho_arquivo,
    aba=None,
    marcadores_cabecalho=None,
    max_linhas_busca=10,
):
    """
    Lê um Excel cujo cabeçalho real não está na primeira linha.

    Vários relatórios de marketplace começam com linhas de título/banner antes
    da linha de cabeçalho de verdade (ML começa na linha 6, Shopee/Renda na 3).
    Esta função varre as primeiras `max_linhas_busca` linhas e escolhe como
    cabeçalho a primeira que contenha algum dos `marcadores_cabecalho`. Se nada
    casar, usa a linha com mais células preenchidas.

    Retorna um DataFrame já com o cabeçalho correto.
    """
    if aba is None:
        aba = 0
    bruto = pd.read_excel(caminho_arquivo, sheet_name=aba, header=None, dtype=object)

    marcadores = [limpar_nome_coluna(m) for m in (marcadores_cabecalho or [])]

    linha_cabecalho = None
    melhor_preenchidas = -1
    linha_mais_preenchida = 0

    limite = min(max_linhas_busca, len(bruto))

    for i in range(limite):
        valores = [limpar_nome_coluna(v) for v in bruto.iloc[i].tolist() if v not in (None, "")]
        preenchidas = len(valores)

        if preenchidas > melhor_preenchidas:
            melhor_preenchidas = preenchidas
            linha_mais_preenchida = i

        if marcadores:
            linha_texto = " | ".join(valores)
            if any(m in linha_texto for m in marcadores):
                linha_cabecalho = i
                break

    if linha_cabecalho is None:
        linha_cabecalho = linha_mais_preenchida

    cabecalho = [str(c).strip() if c is not None else "" for c in bruto.iloc[linha_cabecalho].tolist()]
    dados = bruto.iloc[linha_cabecalho + 1:].copy()
    dados.columns = cabecalho

    # remove colunas totalmente vazias e linhas totalmente vazias
    dados = dados.loc[:, [c for c in dados.columns if str(c).strip() != ""]]
    dados = dados.dropna(how="all")

    dados.reset_index(drop=True, inplace=True)
    return dados


def listar_abas(caminho_arquivo):
    """Devolve os nomes das abas de um arquivo Excel."""
    try:
        return pd.ExcelFile(caminho_arquivo).sheet_names
    except Exception:
        return []
