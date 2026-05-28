import { useEffect, useState } from "react";
import axios from "axios";
import * as XLSX from "xlsx";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [usuarioLogado, setUsuarioLogado] = useState(null);
  const [token, setToken] = useState(
    localStorage.getItem("profitHubToken") || "",
  );

  const [modoAuth, setModoAuth] = useState("login");
  const [carregandoAuth, setCarregandoAuth] = useState(false);
  const [erroAuth, setErroAuth] = useState("");

  const [loginForm, setLoginForm] = useState({
    email: "",
    senha: "",
  });

  const [cadastroForm, setCadastroForm] = useState({
    nome: "",
    email: "",
    senha: "",
    nomeEmpresa: "",
  });

  const headersAuth = token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};
  const [arquivo, setArquivo] = useState(null);

  const [configuracoes, setConfiguracoes] = useState({
    nomeEmpresa: "",
    impostoPadrao: 10,
    margemMinima: 20,
  });

  const [percentualImposto, setPercentualImposto] = useState(10);
  const [marketplaceSelecionado, setMarketplaceSelecionado] = useState("auto");
  const [marketplacesDisponiveis, setMarketplacesDisponiveis] = useState([
    { valor: "auto", rotulo: "Detectar automaticamente" },
    { valor: "mercado_livre", rotulo: "Mercado Livre" },
    { valor: "shopee", rotulo: "Shopee" },
  ]);
  const [minhaConta, setMinhaConta] = useState(null);
  const [carregandoMinhaConta, setCarregandoMinhaConta] = useState(false);
  const [assinando, setAssinando] = useState(false);
  const [carregandoConfiguracoes, setCarregandoConfiguracoes] = useState(false);

  const [resumo, setResumo] = useState(null);
  const [pedidos, setPedidos] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");

  const [filtroStatus, setFiltroStatus] = useState("todos");
  const [filtroSku, setFiltroSku] = useState("");
  const [filtroPlataforma, setFiltroPlataforma] = useState("todas");
  const [filtroLoja, setFiltroLoja] = useState("todas");
  const [ocultarCancelados, setOcultarCancelados] = useState(false);

  const [pedidosPorPagina, setPedidosPorPagina] = useState(25);
  const [paginaAtual, setPaginaAtual] = useState(1);

  const [abaAtiva, setAbaAtiva] = useState("dashboard");
  const [produtos, setProdutos] = useState([]);

  const [filtroProduto, setFiltroProduto] = useState("");
  const [produtosPorPagina, setProdutosPorPagina] = useState(25);
  const [paginaProdutoAtual, setPaginaProdutoAtual] = useState(1);

  const [arquivoProdutos, setArquivoProdutos] = useState(null);
  const [resultadoImportacao, setResultadoImportacao] = useState(null);
  const [importandoProdutos, setImportandoProdutos] = useState(false);

  const [produtoEditandoId, setProdutoEditandoId] = useState(null);

  const [novoProduto, setNovoProduto] = useState({
    sku: "",
    nome: "",
    custo: "",
    tipo: "unitario",
    codigosExternos: "",
    componentes: [],
  });

  const [novoComponente, setNovoComponente] = useState({
    sku: "",
    quantidade: 1,
  });

  const [cadastroRapido, setCadastroRapido] = useState(null);
  const [salvandoCadastroRapido, setSalvandoCadastroRapido] = useState(false);

  const validarSessao = async () => {
    const tokenSalvo = localStorage.getItem("profitHubToken");

    if (!tokenSalvo) {
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${tokenSalvo}`,
        },
      });

      setUsuarioLogado(response.data);
      setToken(tokenSalvo);
    } catch (error) {
      console.error("Sessão inválida:", error);
      localStorage.removeItem("profitHubToken");
      setUsuarioLogado(null);
      setToken("");
    }
  };

  const fazerLogin = async (event) => {
    event.preventDefault();
    setErroAuth("");

    try {
      setCarregandoAuth(true);

      const response = await axios.post(`${API_URL}/auth/login`, {
        email: loginForm.email,
        senha: loginForm.senha,
      });

      const tokenRecebido = response.data.access_token;

      localStorage.setItem("profitHubToken", tokenRecebido);

      setToken(tokenRecebido);
      setUsuarioLogado(response.data.usuario);

      setLoginForm({
        email: "",
        senha: "",
      });
    } catch (error) {
      console.error(error);
      setErroAuth(
        error.response?.data?.detail ||
          "Erro ao fazer login. Verifique seus dados.",
      );
    } finally {
      setCarregandoAuth(false);
    }
  };

  const fazerCadastro = async (event) => {
    event.preventDefault();
    setErroAuth("");

    try {
      setCarregandoAuth(true);

      const response = await axios.post(`${API_URL}/auth/cadastro`, {
        nome: cadastroForm.nome,
        email: cadastroForm.email,
        senha: cadastroForm.senha,
        nomeEmpresa: cadastroForm.nomeEmpresa,
      });

      const tokenRecebido = response.data.access_token;

      localStorage.setItem("profitHubToken", tokenRecebido);

      setToken(tokenRecebido);
      setUsuarioLogado(response.data.usuario);

      setCadastroForm({
        nome: "",
        email: "",
        senha: "",
        nomeEmpresa: "",
      });
    } catch (error) {
      console.error(error);
      setErroAuth(
        error.response?.data?.detail ||
          "Erro ao criar conta. Verifique os dados.",
      );
    } finally {
      setCarregandoAuth(false);
    }
  };

  const sairDoSistema = () => {
    localStorage.removeItem("profitHubToken");
    setUsuarioLogado(null);
    setToken("");
    setModoAuth("login");
    setResumo(null);
    setPedidos([]);
    setArquivo(null);
  };

  const carregarConfiguracoes = async () => {
    try {
      setCarregandoConfiguracoes(true);

      const response = await axios.get(`${API_URL}/configuracoes`, {
        headers: headersAuth,
      });

      const dados = response.data;

      const configuracoesRecebidas = {
        nomeEmpresa: dados.nomeEmpresa || "",
        impostoPadrao: Number(dados.impostoPadrao || 10),
        margemMinima: Number(dados.margemMinima || 20),
      };

      setConfiguracoes(configuracoesRecebidas);
      setPercentualImposto(configuracoesRecebidas.impostoPadrao);
    } catch (error) {
      console.error("Erro ao carregar configurações:", error);
    } finally {
      setCarregandoConfiguracoes(false);
    }
  };

  const carregarProdutos = async () => {
    try {
      const response = await axios.get(`${API_URL}/produtos`, {
        headers: headersAuth,
      });
      setProdutos(response.data);
    } catch (error) {
      console.error("Erro ao carregar produtos:", error);
    }
  };

  const carregarMinhaConta = async () => {
    try {
      setCarregandoMinhaConta(true);
      const response = await axios.get(`${API_URL}/minha-conta`, {
        headers: headersAuth,
      });
      setMinhaConta(response.data);
    } catch (error) {
      console.error("Erro ao carregar minha conta:", error);
    } finally {
      setCarregandoMinhaConta(false);
    }
  };

  const assinarPlano = async (planoId) => {
    try {
      setAssinando(true);
      const response = await axios.post(
        `${API_URL}/billing/assinar`,
        { plano: planoId },
        { headers: headersAuth },
      );
      const { init_point } = response.data;
      if (init_point) {
        window.location.href = init_point;
      }
    } catch (error) {
      const msg =
        error.response?.data?.detail ||
        "Erro ao iniciar assinatura. Tente novamente.";
      alert(msg);
    } finally {
      setAssinando(false);
    }
  };

  const cancelarAssinatura = async () => {
    if (
      !window.confirm(
        "Tem certeza que deseja cancelar? Você voltará para o plano Free.",
      )
    )
      return;
    try {
      await axios.post(
        `${API_URL}/billing/cancelar`,
        {},
        { headers: headersAuth },
      );
      alert("Assinatura cancelada. Você está no plano Free.");
      carregarMinhaConta();
    } catch (error) {
      alert(error.response?.data?.detail || "Erro ao cancelar assinatura.");
    }
  };

  const carregarMarketplaces = async () => {
    try {
      const response = await axios.get(`${API_URL}/upload/marketplaces`, {
        headers: headersAuth,
      });
      if (response.data?.marketplaces?.length) {
        setMarketplacesDisponiveis(response.data.marketplaces);
      }
    } catch (error) {
      console.error("Erro ao carregar marketplaces:", error);
    }
  };

  useEffect(() => {
    validarSessao();
    // Detecta retorno do checkout do Mercado Pago
    const params = new URLSearchParams(window.location.search);
    if (params.get("assinatura") === "processando") {
      setAbaAtiva("minha-conta");
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  useEffect(() => {
    if (usuarioLogado) {
      carregarProdutos();
      carregarConfiguracoes();
      carregarMarketplaces();
    }
  }, [usuarioLogado]);

  useEffect(() => {
    if (usuarioLogado && abaAtiva === "minha-conta") {
      carregarMinhaConta();
    }
  }, [usuarioLogado, abaAtiva]);

  useEffect(() => {
    setPaginaAtual(1);
  }, [filtroStatus, filtroSku, filtroPlataforma, filtroLoja, pedidosPorPagina]);

  useEffect(() => {
    setPaginaProdutoAtual(1);
  }, [filtroProduto, produtosPorPagina]);

  const salvarConfiguracoes = async () => {
    const novasConfiguracoes = {
      nomeEmpresa: configuracoes.nomeEmpresa || "",
      impostoPadrao: Number(configuracoes.impostoPadrao || 10),
      margemMinima: Number(configuracoes.margemMinima || 20),
    };

    try {
      setCarregandoConfiguracoes(true);

      const response = await axios.put(
        `${API_URL}/configuracoes`,
        novasConfiguracoes,
        {
          headers: headersAuth,
        },
      );

      const dados = response.data;

      const configuracoesSalvas = {
        nomeEmpresa: dados.nomeEmpresa || "",
        impostoPadrao: Number(dados.impostoPadrao || 10),
        margemMinima: Number(dados.margemMinima || 20),
      };

      setConfiguracoes(configuracoesSalvas);
      setPercentualImposto(configuracoesSalvas.impostoPadrao);

      alert("Configurações salvas com sucesso no banco de dados.");
    } catch (error) {
      console.error(error);
      alert("Erro ao salvar configurações.");
    } finally {
      setCarregandoConfiguracoes(false);
    }
  };

  const formatarMoeda = (valor) => {
    return Number(valor || 0).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  };

  const formatarPercentual = (valor) => {
    return `${Number(valor || 0)
      .toFixed(2)
      .replace(".", ",")}%`;
  };

  const copiarTexto = async (texto) => {
    const valor = String(texto || "").trim();

    if (!valor) {
      alert("Nada para copiar.");
      return;
    }

    try {
      await navigator.clipboard.writeText(valor);
      alert(`Copiado: ${valor}`);
    } catch (error) {
      console.error(error);
      alert("Não foi possível copiar.");
    }
  };

  const CampoCopiavel = ({ valor }) => {
    const texto = String(valor || "-");

    return (
      <div className="campo-copiavel">
        <span title={texto}>{texto}</span>

        {texto !== "-" && (
          <button
            type="button"
            className="btn-copiar"
            onClick={() => copiarTexto(texto)}
          >
            Copiar
          </button>
        )}
      </div>
    );
  };

  const formatarPlataforma = (plataforma) => {
    const texto = String(plataforma || "")
      .trim()
      .toLowerCase();

    if (
      texto === "mercado" ||
      texto === "mercado livre" ||
      texto === "mercadolivre" ||
      texto === "ml"
    ) {
      return "Mercado Livre";
    }

    if (texto === "shopee") {
      return "Shopee";
    }

    return plataforma || "-";
  };

  const formatarStatus = (status) => {
    if (status === "lucro") return "Lucro";
    if (status === "prejuizo") return "Prejuízo";
    if (status === "elas_por_elas") return "Neutro";
    if (status === "atencao") return "Atenção";
    return status || "-";
  };

  const obterStatusComercial = (pedido) => {
    const lucroReal = Number(pedido.lucro_real || 0);
    const margemReal = Number(pedido.margem_real || 0);
    const margemMinima = Number(configuracoes.margemMinima || 0);

    if (lucroReal < 0) {
      return "prejuizo";
    }

    if (lucroReal === 0) {
      return "elas_por_elas";
    }

    if (margemReal < margemMinima) {
      return "atencao";
    }

    return "lucro";
  };

  const formatarStatusComercial = (pedido) => {
    const status = obterStatusComercial(pedido);

    if (status === "lucro") return "Lucro saudável";
    if (status === "atencao") return "Atenção";
    if (status === "prejuizo") return "Prejuízo";
    if (status === "elas_por_elas") return "Neutro";

    return "-";
  };

  const classeStatusComercial = (pedido) => {
    const status = obterStatusComercial(pedido);

    if (status === "lucro") return "status lucro";
    if (status === "prejuizo") return "status prejuizo";
    if (status === "atencao") return "status atencao";

    return "status neutro";
  };

  const plataformasDisponiveis = [
    ...new Set(
      pedidos
        .map((pedido) => pedido.plataforma)
        .filter((plataforma) => plataforma && plataforma.trim() !== ""),
    ),
  ].sort();

  const lojasDisponiveis = [
    ...new Set(
      pedidos
        .filter((pedido) => {
          if (filtroPlataforma === "todas") return true;
          return pedido.plataforma === filtroPlataforma;
        })
        .map((pedido) => pedido.loja)
        .filter((loja) => loja && loja.trim() !== ""),
    ),
  ].sort();

  const processarArquivo = async () => {
    if (!arquivo) {
      setErro("Selecione um arquivo Excel primeiro.");
      return;
    }

    try {
      setCarregando(true);
      setErro("");

      const formData = new FormData();
      formData.append("arquivo", arquivo);
      formData.append("percentual_imposto", percentualImposto);
      formData.append("marketplace", marketplaceSelecionado);

      const response = await axios.post(`${API_URL}/upload/pedidos`, formData, {
        headers: {
          ...headersAuth,
          "Content-Type": "multipart/form-data",
        },
      });

      setResumo(response.data.resumo);
      setPedidos(response.data.pedidos);

      setFiltroStatus("todos");
      setFiltroSku("");
      setFiltroPlataforma("todas");
      setFiltroLoja("todas");
      setPaginaAtual(1);
    } catch (error) {
      console.error(error);
      setErro(
        error.response?.data?.detail ||
          "Erro ao processar o arquivo. Verifique se o backend está rodando.",
      );
    } finally {
      setCarregando(false);
    }
  };

  const pedidosFiltrados = pedidos.filter((pedido) => {
    const statusComercial = obterStatusComercial(pedido);

    const statusOk =
      filtroStatus === "todos" ||
      statusComercial === filtroStatus ||
      (filtroStatus === "nao_cadastrado" && !pedido.produto_encontrado);

    const skuOk =
      filtroSku === "" ||
      String(pedido.sku_original || "")
        .toLowerCase()
        .includes(filtroSku.toLowerCase());

    const plataformaOk =
      filtroPlataforma === "todas" || pedido.plataforma === filtroPlataforma;

    const lojaOk = filtroLoja === "todas" || pedido.loja === filtroLoja;

    const canceladoOk = !ocultarCancelados || !pedido.pedido_cancelado;

    return statusOk && skuOk && plataformaOk && lojaOk && canceladoOk;
  });

  const resumoStatusComercial = pedidos.reduce(
    (acc, pedido) => {
      const status = obterStatusComercial(pedido);

      if (status === "lucro") acc.lucro += 1;
      if (status === "atencao") acc.atencao += 1;
      if (status === "prejuizo") acc.prejuizo += 1;
      if (status === "elas_por_elas") acc.neutro += 1;

      return acc;
    },
    {
      lucro: 0,
      atencao: 0,
      prejuizo: 0,
      neutro: 0,
    },
  );

  const totalPaginas = Math.max(
    1,
    Math.ceil(pedidosFiltrados.length / Number(pedidosPorPagina)),
  );

  const paginaSegura = Math.min(paginaAtual, totalPaginas);
  const indiceInicial = (paginaSegura - 1) * Number(pedidosPorPagina);
  const indiceFinal = indiceInicial + Number(pedidosPorPagina);
  const pedidosPaginados = pedidosFiltrados.slice(indiceInicial, indiceFinal);

  const inicioExibicao = pedidosFiltrados.length === 0 ? 0 : indiceInicial + 1;

  const fimExibicao = Math.min(indiceFinal, pedidosFiltrados.length);

  const resumoPorLoja = Object.values(
    pedidos.reduce((acc, pedido) => {
      const plataformaFormatada = formatarPlataforma(pedido.plataforma);
      const chave = `${plataformaFormatada} - ${pedido.loja || "Sem loja"}`;

      if (!acc[chave]) {
        acc[chave] = {
          plataforma: plataformaFormatada,
          loja: pedido.loja || "Sem loja",
          total_pedidos: 0,
          total_vendas: 0,
          total_lucro_upseller: 0,
          total_imposto: 0,
          total_lucro_real: 0,
          total_frete: 0,
          total_atencao: 0,
        };
      }

      acc[chave].total_pedidos += 1;
      acc[chave].total_vendas += Number(pedido.vendas_produtos || 0);
      acc[chave].total_lucro_upseller += Number(pedido.lucro_upseller || 0);
      acc[chave].total_imposto += Number(pedido.imposto_simples || 0);
      acc[chave].total_lucro_real += Number(pedido.lucro_real || 0);
      acc[chave].total_frete += Number(pedido.taxa_frete || pedido.frete || 0);

      if (obterStatusComercial(pedido) === "atencao") {
        acc[chave].total_atencao += 1;
      }

      return acc;
    }, {}),
  ).map((loja) => {
    const margem_real =
      loja.total_vendas > 0
        ? (loja.total_lucro_real / loja.total_vendas) * 100
        : 0;

    return {
      ...loja,
      total_vendas: Number(loja.total_vendas.toFixed(2)),
      total_lucro_upseller: Number(loja.total_lucro_upseller.toFixed(2)),
      total_imposto: Number(loja.total_imposto.toFixed(2)),
      total_lucro_real: Number(loja.total_lucro_real.toFixed(2)),
      total_frete: Number(loja.total_frete.toFixed(2)),
      margem_real: Number(margem_real.toFixed(2)),
    };
  });

  const produtosFiltrados = produtos.filter((produto) => {
    const textoBusca = filtroProduto.toLowerCase();
    const sku = String(produto.sku || "").toLowerCase();
    const nome = String(produto.nome || "").toLowerCase();

    return sku.includes(textoBusca) || nome.includes(textoBusca);
  });

  const totalPaginasProdutos = Math.max(
    1,
    Math.ceil(produtosFiltrados.length / Number(produtosPorPagina)),
  );

  const paginaProdutoSegura = Math.min(
    paginaProdutoAtual,
    totalPaginasProdutos,
  );

  const indiceInicialProdutos =
    (paginaProdutoSegura - 1) * Number(produtosPorPagina);

  const indiceFinalProdutos = indiceInicialProdutos + Number(produtosPorPagina);

  const produtosPaginados = produtosFiltrados.slice(
    indiceInicialProdutos,
    indiceFinalProdutos,
  );

  const inicioExibicaoProdutos =
    produtosFiltrados.length === 0 ? 0 : indiceInicialProdutos + 1;

  const fimExibicaoProdutos = Math.min(
    indiceFinalProdutos,
    produtosFiltrados.length,
  );

  const obterSkuParaCadastro = (pedido) => {
    if (pedido.quantidade_kit > 1 && pedido.sku_base) {
      return pedido.sku_base;
    }

    return pedido.sku_original || "";
  };

  const produtosNaoCadastradosAgrupados = Object.values(
    pedidosFiltrados
      .filter((pedido) => !pedido.produto_encontrado)
      .reduce((acc, pedido) => {
        const skuCadastro = obterSkuParaCadastro(pedido);

        if (!skuCadastro) {
          return acc;
        }

        if (!acc[skuCadastro]) {
          acc[skuCadastro] = {
            sku: skuCadastro,
            idProduto: pedido.id_produto_plataforma || "",
            nomeProduto: pedido.nome_produto || pedido.titulo_anuncio || "",
            exemplosSkuOriginal: new Set(),
            plataformas: new Set(),
            lojas: new Set(),
            total_pedidos: 0,
            total_vendas: 0,
            total_lucro_real: 0,
          };
        }

        if (!acc[skuCadastro].idProduto && pedido.id_produto_plataforma) {
          acc[skuCadastro].idProduto = pedido.id_produto_plataforma;
        }
        if (!acc[skuCadastro].nomeProduto) {
          acc[skuCadastro].nomeProduto =
            pedido.nome_produto || pedido.titulo_anuncio || "";
        }

        acc[skuCadastro].exemplosSkuOriginal.add(
          pedido.sku_original || skuCadastro,
        );
        acc[skuCadastro].plataformas.add(formatarPlataforma(pedido.plataforma));
        acc[skuCadastro].lojas.add(pedido.loja || "Sem loja");
        acc[skuCadastro].total_pedidos += 1;
        acc[skuCadastro].total_vendas += Number(pedido.vendas_produtos || 0);
        acc[skuCadastro].total_lucro_real += Number(pedido.lucro_real || 0);

        return acc;
      }, {}),
  )
    .map((item) => ({
      ...item,
      exemplosSkuOriginal: Array.from(item.exemplosSkuOriginal).slice(0, 3),
      plataformas: Array.from(item.plataformas),
      lojas: Array.from(item.lojas),
      total_vendas: Number(item.total_vendas.toFixed(2)),
      total_lucro_real: Number(item.total_lucro_real.toFixed(2)),
    }))
    .sort((a, b) => {
      if (b.total_pedidos !== a.total_pedidos) {
        return b.total_pedidos - a.total_pedidos;
      }

      return b.total_vendas - a.total_vendas;
    });

  const abrirCadastroRapidoPorSku = (sku) => {
    setCadastroRapido({
      pedido: null,
      sku,
      nome: "",
      custo: "",
      tipo: "unitario",
      origem: "resumo_pendentes",
    });
  };

  const adicionarComponente = () => {
    if (!novoComponente.sku || Number(novoComponente.quantidade) <= 0) {
      alert("Informe o SKU e a quantidade do componente.");
      return;
    }

    const componente = {
      sku: novoComponente.sku.trim().toUpperCase(),
      quantidade: Number(novoComponente.quantidade),
    };

    setNovoProduto({
      ...novoProduto,
      componentes: [...novoProduto.componentes, componente],
    });

    setNovoComponente({
      sku: "",
      quantidade: 1,
    });
  };

  const removerComponente = (index) => {
    const novaLista = novoProduto.componentes.filter((_, i) => i !== index);

    setNovoProduto({
      ...novoProduto,
      componentes: novaLista,
    });
  };

  const limparFormularioProduto = () => {
    setNovoProduto({
      sku: "",
      nome: "",
      custo: "",
      tipo: "unitario",
      codigosExternos: "",
      componentes: [],
    });

    setNovoComponente({
      sku: "",
      quantidade: 1,
    });

    setProdutoEditandoId(null);
  };

  const cadastrarProduto = async () => {
    if (!novoProduto.sku || !novoProduto.nome) {
      alert("Preencha SKU e nome do produto.");
      return;
    }

    if (novoProduto.tipo === "unitario" && !novoProduto.custo) {
      alert("Produto unitário precisa ter custo.");
      return;
    }

    if (
      novoProduto.tipo === "kit_personalizado" &&
      novoProduto.componentes.length === 0
    ) {
      alert("Kit personalizado precisa ter pelo menos um componente.");
      return;
    }

    const dadosProduto = {
      sku: novoProduto.sku,
      nome: novoProduto.nome,
      custo: novoProduto.tipo === "unitario" ? Number(novoProduto.custo) : 0,
      imposto: 10,
      tipo: novoProduto.tipo,
      frete_gratis: 0,
      observacao: "",
      codigosExternos: novoProduto.codigosExternos || "",
      componentes: novoProduto.componentes,
    };

    try {
      if (produtoEditandoId) {
        await axios.put(
          `${API_URL}/produtos/${produtoEditandoId}`,
          dadosProduto,
          {
            headers: headersAuth,
          },
        );
      } else {
        await axios.post(`${API_URL}/produtos`, dadosProduto, {
          headers: headersAuth,
        });
      }

      limparFormularioProduto();
      carregarProdutos();
    } catch (error) {
      console.error(error);

      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Erro ao salvar produto.");
      }
    }
  };

  const excluirProduto = async (id) => {
    try {
      await axios.delete(`${API_URL}/produtos/${id}`, {
        headers: headersAuth,
      });
      carregarProdutos();
    } catch (error) {
      console.error(error);
      alert("Erro ao excluir produto.");
    }
  };

  const editarProduto = (produto) => {
    setProdutoEditandoId(produto.id);

    setNovoProduto({
      sku: produto.sku || "",
      nome: produto.nome || "",
      custo: produto.tipo === "unitario" ? produto.custo : "",
      tipo: produto.tipo || "unitario",
      codigosExternos: produto.codigosExternos || "",
      componentes: produto.componentes || [],
    });

    setNovoComponente({
      sku: "",
      quantidade: 1,
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const cancelarEdicao = () => {
    limparFormularioProduto();
  };

  const baixarModeloProdutos = () => {
    window.open(`${API_URL}/produtos/modelo-importacao`, "_blank");
  };

  const importarProdutosExcel = async () => {
    if (!arquivoProdutos) {
      alert("Selecione uma planilha de produtos primeiro.");
      return;
    }

    try {
      setImportandoProdutos(true);
      setResultadoImportacao(null);

      const formData = new FormData();
      formData.append("arquivo", arquivoProdutos);

      const response = await axios.post(
        `${API_URL}/produtos/importar-excel`,
        formData,
        {
          headers: {
            ...headersAuth,
            "Content-Type": "multipart/form-data",
          },
        },
      );

      setResultadoImportacao(response.data);
      carregarProdutos();
    } catch (error) {
      console.error(error);

      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Erro ao importar produtos.");
      }
    } finally {
      setImportandoProdutos(false);
    }
  };

  const importarMapaShopee = async () => {
    if (!arquivoProdutos) {
      alert(
        "Selecione a planilha da Shopee (mass_update_basic_info) no campo acima primeiro.",
      );
      return;
    }

    try {
      setImportandoProdutos(true);
      setResultadoImportacao(null);

      const formData = new FormData();
      formData.append("arquivo", arquivoProdutos);

      const response = await axios.post(
        `${API_URL}/produtos/importar-mapa-shopee`,
        formData,
        {
          headers: {
            ...headersAuth,
            "Content-Type": "multipart/form-data",
          },
        },
      );

      const dados = response.data;
      alert(
        `Mapa da Shopee importado: ${dados.total_vinculados} produtos vinculados. ` +
          "Lembre de definir o custo dos produtos novos (entraram com custo 0).",
      );
      carregarProdutos();
    } catch (error) {
      console.error(error);

      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Erro ao importar o mapa da Shopee.");
      }
    } finally {
      setImportandoProdutos(false);
    }
  };

  const exportarRelatorioExcel = () => {
    if (!resumo || pedidosFiltrados.length === 0) {
      alert("Não há relatório para exportar.");
      return;
    }

    const dadosResumo = [
      {
        Empresa: configuracoes.nomeEmpresa || "",
        "Imposto usado (%)": percentualImposto,
        "Margem mínima saudável (%)": configuracoes.margemMinima,
        "Total de Pedidos": resumo.total_pedidos,
        "Vendas de Produtos": resumo.total_vendas_produtos,
        "Lucro Marketplace": resumo.total_lucro_upseller,
        "Taxas Marketplace": resumo.total_taxas_marketplace ?? 0,
        "Marketplace Detectado": resumo.marketplace_detectado ?? "",
        "Lucro Corrigido": resumo.total_lucro_corrigido_antes_imposto,
        Imposto: resumo.total_imposto_simples,
        "Frete Vendedor":
          resumo.total_frete_vendedor ?? resumo.total_frete ?? 0,
        "Frete Pago pelo Comprador": resumo.total_frete_pago_comprador ?? 0,
        "Subsídio Marketplace": resumo.total_frete_subsidio_marketplace ?? 0,
        "Frete Original Relatório": resumo.total_frete_relatorio_original ?? 0,
        "Lucro Real": resumo.total_lucro_real,
        "Margem Real (%)": resumo.margem_real_total,
        "Lucro Saudável": resumoStatusComercial.lucro,
        Atenção: resumoStatusComercial.atencao,
        Prejuízo: resumoStatusComercial.prejuizo,
        Neutro: resumoStatusComercial.neutro,
        "Produtos Encontrados": resumo.pedidos_com_produto_cadastrado,
        "Produtos Não Cadastrados": resumo.pedidos_sem_produto_cadastrado,
      },
    ];

    const dadosResumoLoja = resumoPorLoja.map((loja) => ({
      Plataforma: loja.plataforma,
      Loja: loja.loja,
      Pedidos: loja.total_pedidos,
      Vendas: loja.total_vendas,
      "Lucro Real": loja.total_lucro_real,
      "Margem Real (%)": loja.margem_real,
      Atenção: loja.total_atencao,
      "Lucro Marketplace": loja.total_lucro_upseller,
      Frete: loja.total_frete,
      Imposto: loja.total_imposto,
    }));

    const dadosPedidos = pedidosFiltrados.map((pedido) => ({
      Pedido: pedido.pedido_upseller || "",
      "Pedido Plataforma":
        pedido.pedido_plataforma ||
        pedido.pedido_marketplace ||
        pedido.numero_pedido_plataforma ||
        "",
      Plataforma: formatarPlataforma(pedido.plataforma),
      Loja: pedido.loja || "",
      SKU: pedido.sku_original || "",
      "ID do Produto": pedido.id_produto_plataforma || "",
      "SKU Base": pedido.sku_base || "",
      "Quantidade Kit": pedido.quantidade_kit || 1,
      "Produto Encontrado": pedido.produto_encontrado ? "Sim" : "Não",
      "Nome do Produto": pedido.nome_produto || "",
      "SKU de Custo Usado": pedido.sku_custo_usado || "",
      "Custo do Produto": pedido.produto_encontrado
        ? pedido.custo_total_cadastrado
        : "",
      "Taxas Marketplace": pedido.taxas_marketplace ?? 0,
      "Líquido Marketplace": pedido.valor_liquido_plataforma ?? 0,
      "Frete Vendedor":
        pedido.frete_vendedor ?? pedido.taxa_frete ?? pedido.frete ?? 0,
      "Frete Pago pelo Comprador": pedido.frete_pago_comprador ?? 0,
      "Subsídio Marketplace": pedido.frete_subsidio_marketplace ?? 0,
      "Frete Original Relatório": pedido.frete_relatorio_original ?? 0,
      "Regra do Frete": pedido.regra_frete || "",
      Venda: pedido.vendas_produtos,
      "Lucro Real": pedido.lucro_real,
      "Margem Real (%)": pedido.margem_real,
      "Margem Mínima (%)": configuracoes.margemMinima,
      "Status Comercial": formatarStatusComercial(pedido),
      "Status Técnico": formatarStatus(pedido.status),
      "Status no Marketplace": pedido.status_marketplace || "",
      "Cancelado/Devolvido": pedido.pedido_cancelado ? "Sim" : "Não",
      "Lucro Marketplace": pedido.lucro_upseller,
      "Custo Importado": pedido.custo_produto_upseller,
      "Lucro Corrigido": pedido.lucro_corrigido_antes_imposto,
      Imposto: pedido.imposto_simples,
      "Erro Produto": pedido.erro_produto || "",
    }));

    const produtosNaoCadastrados = pedidosFiltrados
      .filter((pedido) => !pedido.produto_encontrado)
      .map((pedido) => ({
        SKU: pedido.sku_original || "",
        "SKU Base": pedido.sku_base || "",
        Plataforma: formatarPlataforma(pedido.plataforma),
        Loja: pedido.loja || "",
        Pedido: pedido.pedido_upseller || "",
        Venda: pedido.vendas_produtos,
        "Lucro Real": pedido.lucro_real,
        "Status Comercial": formatarStatusComercial(pedido),
        Erro: pedido.erro_produto || "Produto não cadastrado",
      }));

    const workbook = XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(
      workbook,
      XLSX.utils.json_to_sheet(dadosResumo),
      "Resumo",
    );

    XLSX.utils.book_append_sheet(
      workbook,
      XLSX.utils.json_to_sheet(dadosResumoLoja),
      "Resumo por Loja",
    );

    XLSX.utils.book_append_sheet(
      workbook,
      XLSX.utils.json_to_sheet(dadosPedidos),
      "Pedidos",
    );

    XLSX.utils.book_append_sheet(
      workbook,
      XLSX.utils.json_to_sheet(produtosNaoCadastrados),
      "Nao Cadastrados",
    );

    const dataAtual = new Date().toISOString().slice(0, 10);

    XLSX.writeFile(workbook, `relatorio_lucro_real_${dataAtual}.xlsx`);
  };

  const cadastrarProdutoPendente = (pedido) => {
    const skuParaCadastrar = obterSkuParaCadastro(pedido);

    setCadastroRapido({
      pedido: pedido.pedido_upseller,
      sku: skuParaCadastrar || "",
      nome: pedido.nome_produto || pedido.titulo_anuncio || "",
      custo: "",
      tipo: "unitario",
      codigosExternos: pedido.id_produto_plataforma || "",
      origem: "linha_pedido",
    });
  };

  const salvarCadastroRapido = async () => {
    if (
      !cadastroRapido?.sku ||
      !cadastroRapido?.nome ||
      !cadastroRapido?.custo
    ) {
      alert("Preencha SKU, nome e custo do produto.");
      return;
    }

    try {
      setSalvandoCadastroRapido(true);

      await axios.post(
        `${API_URL}/produtos`,
        {
          sku: cadastroRapido.sku,
          nome: cadastroRapido.nome,
          custo: Number(cadastroRapido.custo),
          imposto: 10,
          tipo: "unitario",
          frete_gratis: 0,
          observacao: "Cadastrado pelo Dashboard",
          codigosExternos: cadastroRapido.codigosExternos || "",
          componentes: [],
        },
        {
          headers: headersAuth,
        },
      );

      await carregarProdutos();

      if (arquivo) {
        const paginaAnterior = paginaAtual;

        const formData = new FormData();
        formData.append("arquivo", arquivo);
        formData.append("percentual_imposto", percentualImposto);
        formData.append("marketplace", marketplaceSelecionado);

        const response = await axios.post(
          `${API_URL}/upload/pedidos`,
          formData,
          {
            headers: {
              ...headersAuth,
              "Content-Type": "multipart/form-data",
            },
          },
        );

        setResumo(response.data.resumo);
        setPedidos(response.data.pedidos);
        setPaginaAtual(paginaAnterior);
      }

      setCadastroRapido(null);
    } catch (error) {
      console.error(error);

      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert("Erro ao cadastrar produto pelo Dashboard.");
      }
    } finally {
      setSalvandoCadastroRapido(false);
    }
  };

  const cancelarCadastroRapido = () => {
    setCadastroRapido(null);
  };

  if (!usuarioLogado) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <h1>Profit Hub</h1>
            <p>Controle real de lucro para marketplaces</p>
          </div>

          <div className="auth-tabs">
            <button
              type="button"
              className={modoAuth === "login" ? "auth-tab active" : "auth-tab"}
              onClick={() => {
                setModoAuth("login");
                setErroAuth("");
              }}
            >
              Login
            </button>

            <button
              type="button"
              className={
                modoAuth === "cadastro" ? "auth-tab active" : "auth-tab"
              }
              onClick={() => {
                setModoAuth("cadastro");
                setErroAuth("");
              }}
            >
              Criar conta
            </button>
          </div>

          {erroAuth && <div className="auth-error">{erroAuth}</div>}

          {modoAuth === "login" && (
            <form className="auth-form" onSubmit={fazerLogin}>
              <label>
                E-mail
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(event) =>
                    setLoginForm({
                      ...loginForm,
                      email: event.target.value,
                    })
                  }
                  placeholder="seuemail@empresa.com"
                  required
                />
              </label>

              <label>
                Senha
                <input
                  type="password"
                  value={loginForm.senha}
                  onChange={(event) =>
                    setLoginForm({
                      ...loginForm,
                      senha: event.target.value,
                    })
                  }
                  placeholder="Sua senha"
                  required
                />
              </label>

              <button
                type="submit"
                className="auth-button"
                disabled={carregandoAuth}
              >
                {carregandoAuth ? "Entrando..." : "Entrar"}
              </button>
            </form>
          )}

          {modoAuth === "cadastro" && (
            <form className="auth-form" onSubmit={fazerCadastro}>
              <label>
                Nome
                <input
                  type="text"
                  value={cadastroForm.nome}
                  onChange={(event) =>
                    setCadastroForm({
                      ...cadastroForm,
                      nome: event.target.value,
                    })
                  }
                  placeholder="Seu nome"
                  required
                />
              </label>

              <label>
                Nome da empresa
                <input
                  type="text"
                  value={cadastroForm.nomeEmpresa}
                  onChange={(event) =>
                    setCadastroForm({
                      ...cadastroForm,
                      nomeEmpresa: event.target.value,
                    })
                  }
                  placeholder="Nome da sua loja ou empresa"
                  required
                />
              </label>

              <label>
                E-mail
                <input
                  type="email"
                  value={cadastroForm.email}
                  onChange={(event) =>
                    setCadastroForm({
                      ...cadastroForm,
                      email: event.target.value,
                    })
                  }
                  placeholder="seuemail@empresa.com"
                  required
                />
              </label>

              <label>
                Senha
                <input
                  type="password"
                  value={cadastroForm.senha}
                  onChange={(event) =>
                    setCadastroForm({
                      ...cadastroForm,
                      senha: event.target.value,
                    })
                  }
                  placeholder="Mínimo 6 caracteres"
                  required
                />
              </label>

              <button
                type="submit"
                className="auth-button"
                disabled={carregandoAuth}
              >
                {carregandoAuth ? "Criando conta..." : "Criar conta"}
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>Profit Hub</h2>

        <nav>
          <a
            className={abaAtiva === "dashboard" ? "active" : ""}
            onClick={() => setAbaAtiva("dashboard")}
          >
            Dashboard
          </a>

          <a
            className={abaAtiva === "produtos" ? "active" : ""}
            onClick={() => setAbaAtiva("produtos")}
          >
            Produtos
          </a>

          <a
            className={abaAtiva === "configuracoes" ? "active" : ""}
            onClick={() => setAbaAtiva("configuracoes")}
          >
            Configurações
          </a>

          <a
            className={abaAtiva === "minha-conta" ? "active" : ""}
            onClick={() => setAbaAtiva("minha-conta")}
          >
            Minha Conta
          </a>
        </nav>
      </aside>

      <main className="content">
        {abaAtiva === "dashboard" && (
          <>
            <header className="topbar">
              <div>
                <h1>
                  Relatório de Lucro Real
                  {configuracoes.nomeEmpresa && (
                    <span className="empresa-header">
                      {configuracoes.nomeEmpresa}
                    </span>
                  )}
                </h1>
                <p>
                  Importe o relatório do marketplace e veja o lucro após custo
                  cadastrado, imposto informado e margem mínima configurada.
                </p>
              </div>

              <div className="usuario-logado-box">
                <div>
                  <strong>{usuarioLogado?.nome}</strong>
                  <span>{usuarioLogado?.email}</span>
                </div>

                <button
                  type="button"
                  className="btn-sair"
                  onClick={sairDoSistema}
                >
                  Sair
                </button>
              </div>
            </header>

            <section className="upload-card">
              <div>
                <label>Arquivo Excel do relatório</label>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(event) => setArquivo(event.target.files[0])}
                />
              </div>

              <div>
                <label>Marketplace</label>
                <select
                  value={marketplaceSelecionado}
                  onChange={(event) =>
                    setMarketplaceSelecionado(event.target.value)
                  }
                >
                  {marketplacesDisponiveis.map((opcao) => (
                    <option key={opcao.valor} value={opcao.valor}>
                      {opcao.rotulo}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label>Imposto (%)</label>
                <input
                  type="number"
                  value={percentualImposto}
                  onChange={(event) => setPercentualImposto(event.target.value)}
                />
              </div>

              <div>
                <label>Margem mínima</label>
                <input
                  type="number"
                  value={configuracoes.margemMinima}
                  onChange={(event) =>
                    setConfiguracoes({
                      ...configuracoes,
                      margemMinima: event.target.value,
                    })
                  }
                />
              </div>

              <button onClick={processarArquivo} disabled={carregando}>
                {carregando ? "Processando..." : "Processar relatório"}
              </button>
            </section>

            {erro && <div className="erro">{erro}</div>}

            {resumo && (
              <>
                <section className="cards">
                  <div className="card">
                    <span>Pedidos</span>
                    <strong>{resumo.total_pedidos}</strong>
                  </div>

                  <div className="card">
                    <span>Vendas de Produtos</span>
                    <strong>
                      {formatarMoeda(resumo.total_vendas_produtos)}
                    </strong>
                  </div>

                  <div className="card">
                    <span>Lucro Marketplace</span>
                    <strong>
                      {formatarMoeda(resumo.total_lucro_upseller)}
                    </strong>
                  </div>

                  <div className="card">
                    <span>Lucro Corrigido</span>
                    <strong>
                      {formatarMoeda(
                        resumo.total_lucro_corrigido_antes_imposto,
                      )}
                    </strong>
                  </div>

                  <div className="card imposto">
                    <span>Imposto</span>
                    <strong>
                      {formatarMoeda(resumo.total_imposto_simples)}
                    </strong>
                  </div>

                  <div
                    className={
                      resumo.total_lucro_real >= 0
                        ? "card positivo"
                        : "card negativo"
                    }
                  >
                    <span>Lucro Real</span>
                    <strong>{formatarMoeda(resumo.total_lucro_real)}</strong>
                  </div>
                </section>

                <section className="cards second-cards">
                  <div className="card">
                    <span>Margem Real</span>
                    <strong>
                      {formatarPercentual(resumo.margem_real_total)}
                    </strong>
                  </div>

                  <div className="card">
                    <span>Margem mínima</span>
                    <strong>
                      {formatarPercentual(configuracoes.margemMinima)}
                    </strong>
                  </div>

                  <div className="card">
                    <span>Frete Vendedor</span>
                    <strong>
                      {formatarMoeda(
                        resumo.total_frete_vendedor ?? resumo.total_frete ?? 0,
                      )}
                    </strong>
                  </div>

                  <div
                    className="card negativo clicavel"
                    onClick={() => setFiltroStatus("nao_cadastrado")}
                  >
                    <span>Produtos não cadastrados</span>
                    <strong>
                      {resumo.pedidos_sem_produto_cadastrado || 0}
                    </strong>
                  </div>
                </section>

                <section className="status-cards status-cards-4">
                  <div
                    className="mini-card verde clicavel"
                    onClick={() => setFiltroStatus("lucro")}
                  >
                    <span>Lucro saudável</span>
                    <strong>{resumoStatusComercial.lucro}</strong>
                  </div>

                  <div
                    className="mini-card laranja clicavel"
                    onClick={() => setFiltroStatus("atencao")}
                  >
                    <span>Atenção</span>
                    <strong>{resumoStatusComercial.atencao}</strong>
                  </div>

                  <div
                    className="mini-card vermelho clicavel"
                    onClick={() => setFiltroStatus("prejuizo")}
                  >
                    <span>Prejuízo</span>
                    <strong>{resumoStatusComercial.prejuizo}</strong>
                  </div>

                  <div
                    className="mini-card amarelo clicavel"
                    onClick={() => setFiltroStatus("elas_por_elas")}
                  >
                    <span>Neutro</span>
                    <strong>{resumoStatusComercial.neutro}</strong>
                  </div>
                </section>

                <section className="table-card pendentes-card">
                  <div className="table-header">
                    <h2>Produtos não cadastrados</h2>
                    <span>
                      Total de SKUs pendentes:{" "}
                      {produtosNaoCadastradosAgrupados.length}
                    </span>
                  </div>

                  <p className="pendentes-info">
                    Cadastre primeiro os SKUs com mais pedidos ou maior venda
                    total. Após salvar, o relatório será recalculado
                    automaticamente.
                  </p>

                  <div className="table-wrapper">
                    <table className="pendentes-table">
                      <thead>
                        <tr>
                          <th>SKU para cadastrar</th>
                          <th>ID do Produto</th>
                          <th>Nome do produto</th>
                          <th>Exemplos no relatório</th>
                          <th>Pedidos</th>
                          <th>Venda total</th>
                          <th>Lucro atual</th>
                          <th>Plataforma</th>
                          <th>Loja</th>
                          <th>Ação</th>
                        </tr>
                      </thead>

                      <tbody>
                        {produtosNaoCadastradosAgrupados.map((item) => {
                          const cadastroAberto =
                            cadastroRapido &&
                            cadastroRapido.origem === "resumo_pendentes" &&
                            cadastroRapido.sku === item.sku;

                          return (
                            <tr key={item.sku}>
                              <td>
                                <strong>{item.sku}</strong>
                              </td>

                              <td>
                                {item.idProduto ? (
                                  <small>{item.idProduto}</small>
                                ) : (
                                  <small style={{ color: "#999" }}>—</small>
                                )}
                              </td>

                              <td>
                                <small>{item.nomeProduto || "—"}</small>
                              </td>

                              <td>
                                {item.exemplosSkuOriginal.map((sku) => (
                                  <small key={sku}>{sku}</small>
                                ))}
                              </td>

                              <td>{item.total_pedidos}</td>

                              <td>{formatarMoeda(item.total_vendas)}</td>

                              <td
                                className={
                                  item.total_lucro_real >= 0
                                    ? "valor-positivo"
                                    : "valor-negativo"
                                }
                              >
                                {formatarMoeda(item.total_lucro_real)}
                              </td>

                              <td>{item.plataformas.join(", ")}</td>

                              <td>{item.lojas.join(", ")}</td>

                              <td>
                                <button
                                  type="button"
                                  className="btn-cadastrar-pendente"
                                  onClick={() =>
                                    abrirCadastroRapidoPorSku(item.sku)
                                  }
                                >
                                  Cadastrar
                                </button>

                                {cadastroAberto && (
                                  <div className="cadastro-rapido-box cadastro-rapido-box-maior">
                                    <label>SKU</label>
                                    <input
                                      type="text"
                                      value={cadastroRapido.sku}
                                      onChange={(event) =>
                                        setCadastroRapido({
                                          ...cadastroRapido,
                                          sku: event.target.value,
                                        })
                                      }
                                    />

                                    <label>Nome</label>
                                    <input
                                      type="text"
                                      placeholder="Nome do produto"
                                      value={cadastroRapido.nome}
                                      onChange={(event) =>
                                        setCadastroRapido({
                                          ...cadastroRapido,
                                          nome: event.target.value,
                                        })
                                      }
                                    />

                                    <label>Custo</label>
                                    <input
                                      type="number"
                                      placeholder="Ex: 8.50"
                                      value={cadastroRapido.custo}
                                      onChange={(event) =>
                                        setCadastroRapido({
                                          ...cadastroRapido,
                                          custo: event.target.value,
                                        })
                                      }
                                    />

                                    <div className="cadastro-rapido-acoes">
                                      <button
                                        type="button"
                                        className="btn-salvar-rapido"
                                        onClick={salvarCadastroRapido}
                                        disabled={salvandoCadastroRapido}
                                      >
                                        {salvandoCadastroRapido
                                          ? "Salvando..."
                                          : "Salvar"}
                                      </button>

                                      <button
                                        type="button"
                                        className="btn-cancelar-rapido"
                                        onClick={cancelarCadastroRapido}
                                      >
                                        Cancelar
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </td>
                            </tr>
                          );
                        })}

                        {produtosNaoCadastradosAgrupados.length === 0 && (
                          <tr>
                            <td colSpan="10">
                              Nenhum produto pendente. Todos os SKUs foram
                              encontrados.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="table-card lojas-card">
                  <div className="table-header">
                    <h2>Resumo por loja</h2>
                    <span>Total de lojas: {resumoPorLoja.length}</span>
                  </div>

                  <div className="table-wrapper">
                    <table className="lojas-table">
                      <thead>
                        <tr>
                          <th>Plataforma</th>
                          <th>Loja</th>
                          <th>Pedidos</th>
                          <th>Vendas</th>
                          <th>Lucro Real</th>
                          <th>Margem Real</th>
                          <th>Atenção</th>
                          <th>Lucro Marketplace</th>
                          <th>Frete Vendedor</th>
                          <th>Imposto</th>
                        </tr>
                      </thead>

                      <tbody>
                        {resumoPorLoja.map((loja, index) => (
                          <tr key={index}>
                            <td>{loja.plataforma}</td>
                            <td>{loja.loja}</td>
                            <td>{loja.total_pedidos}</td>
                            <td>{formatarMoeda(loja.total_vendas)}</td>
                            <td
                              className={
                                loja.total_lucro_real >= 0
                                  ? "valor-positivo"
                                  : "valor-negativo"
                              }
                            >
                              {formatarMoeda(loja.total_lucro_real)}
                            </td>
                            <td>{formatarPercentual(loja.margem_real)}</td>
                            <td>{loja.total_atencao}</td>
                            <td>{formatarMoeda(loja.total_lucro_upseller)}</td>
                            <td>
                              {formatarMoeda(
                                loja.total_frete_vendedor ??
                                  loja.total_frete ??
                                  0,
                              )}
                            </td>
                            <td>{formatarMoeda(loja.total_imposto)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="table-card">
                  <div className="table-header">
                    <h2>Pedidos importados</h2>

                    <div className="table-header-actions">
                      <button
                        type="button"
                        className="btn-exportar"
                        onClick={exportarRelatorioExcel}
                      >
                        Exportar Excel
                      </button>

                      <span>
                        Mostrando {inicioExibicao}-{fimExibicao} de{" "}
                        {pedidosFiltrados.length}
                      </span>
                    </div>
                  </div>

                  <div className="filters">
                    <div>
                      <label>Plataforma</label>
                      <select
                        value={filtroPlataforma}
                        onChange={(event) => {
                          setFiltroPlataforma(event.target.value);
                          setFiltroLoja("todas");
                        }}
                      >
                        <option value="todas">Todas as plataformas</option>
                        {plataformasDisponiveis.map((plataforma) => (
                          <option key={plataforma} value={plataforma}>
                            {formatarPlataforma(plataforma)}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label>Loja</label>
                      <select
                        value={filtroLoja}
                        onChange={(event) => setFiltroLoja(event.target.value)}
                      >
                        <option value="todas">Todas as lojas</option>
                        {lojasDisponiveis.map((loja) => (
                          <option key={loja} value={loja}>
                            {loja}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label>Status comercial</label>
                      <select
                        value={filtroStatus}
                        onChange={(event) =>
                          setFiltroStatus(event.target.value)
                        }
                      >
                        <option value="todos">Todos</option>
                        <option value="lucro">Lucro saudável</option>
                        <option value="atencao">Atenção</option>
                        <option value="prejuizo">Prejuízo</option>
                        <option value="elas_por_elas">Neutro</option>
                        <option value="nao_cadastrado">
                          Produtos não cadastrados
                        </option>
                      </select>
                    </div>

                    <div>
                      <label>SKU</label>
                      <input
                        type="text"
                        placeholder="Buscar SKU..."
                        value={filtroSku}
                        onChange={(event) => setFiltroSku(event.target.value)}
                      />
                    </div>

                    <div>
                      <label>Ver por página</label>
                      <select
                        value={pedidosPorPagina}
                        onChange={(event) =>
                          setPedidosPorPagina(Number(event.target.value))
                        }
                      >
                        <option value={25}>25 pedidos</option>
                        <option value={50}>50 pedidos</option>
                        <option value={100}>100 pedidos</option>
                        <option value={300}>300 pedidos</option>
                      </select>
                    </div>

                    <div className="filter-button-box">
                      <label>Cancelados/devolvidos</label>
                      <label
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          fontWeight: "normal",
                          whiteSpace: "nowrap",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={ocultarCancelados}
                          onChange={(event) => {
                            setOcultarCancelados(event.target.checked);
                            setPaginaAtual(1);
                          }}
                        />
                        Ocultar{" "}
                        {resumo?.total_cancelados
                          ? `(${resumo.total_cancelados})`
                          : ""}
                      </label>
                    </div>

                    <div className="filter-button-box">
                      <label>&nbsp;</label>
                      <button
                        type="button"
                        className="btn-limpar"
                        onClick={() => {
                          setFiltroStatus("todos");
                          setFiltroSku("");
                          setFiltroPlataforma("todas");
                          setFiltroLoja("todas");
                          setOcultarCancelados(false);
                          setPaginaAtual(1);
                        }}
                      >
                        Limpar filtros
                      </button>
                    </div>
                  </div>

                  <div className="pagination">
                    <button
                      type="button"
                      disabled={paginaSegura <= 1}
                      onClick={() => setPaginaAtual(paginaSegura - 1)}
                    >
                      Anterior
                    </button>

                    <span>
                      Página {paginaSegura} de {totalPaginas}
                    </span>

                    <button
                      type="button"
                      disabled={paginaSegura >= totalPaginas}
                      onClick={() => setPaginaAtual(paginaSegura + 1)}
                    >
                      Próxima
                    </button>
                  </div>

                  <div className="table-wrapper pedidos-wrapper">
                    <table className="pedidos-table">
                      <thead>
                        <tr>
                          <th>Pedido</th>
                          <th>Plataforma</th>
                          <th>SKU</th>
                          <th>ID do Produto</th>
                          <th>Produto</th>
                          <th>Custo do Produto</th>
                          <th>Frete Vendedor</th>
                          <th>Venda</th>
                          <th className="col-lucro-real">Lucro Real</th>
                          <th>Margem</th>
                          <th>Status Comercial</th>
                          <th>Status Técnico</th>
                          <th>Lucro Marketplace</th>
                          <th>Lucro Corrigido</th>
                          <th>Imposto</th>
                        </tr>
                      </thead>

                      <tbody>
                        {pedidosPaginados.map((pedido, index) => {
                          const skuRapido = obterSkuParaCadastro(pedido);

                          const cadastroRapidoAberto =
                            cadastroRapido &&
                            cadastroRapido.origem === "linha_pedido" &&
                            cadastroRapido.pedido === pedido.pedido_upseller &&
                            cadastroRapido.sku === skuRapido;

                          return (
                            <tr key={index}>
                              <td>
                                <CampoCopiavel
                                  valor={pedido.pedido_upseller || "-"}
                                />
                              </td>

                              <td>{formatarPlataforma(pedido.plataforma)}</td>

                              <td>
                                <CampoCopiavel
                                  valor={
                                    pedido.sku_exibicao ||
                                    pedido.sku_original ||
                                    "-"
                                  }
                                />

                                {pedido.quantidade_kit > 1 && (
                                  <small>
                                    Base: {pedido.sku_base} x
                                    {pedido.quantidade_kit}
                                  </small>
                                )}
                              </td>

                              <td>
                                {pedido.id_produto_plataforma ? (
                                  <CampoCopiavel
                                    valor={pedido.id_produto_plataforma}
                                  />
                                ) : (
                                  "-"
                                )}
                              </td>

                              <td className="produto-cell">
                                {pedido.produto_encontrado ? (
                                  <>
                                    <strong className="valor-positivo">
                                      Encontrado
                                    </strong>
                                    <small>{pedido.nome_produto}</small>
                                    <small>
                                      Usado: {pedido.sku_custo_usado}
                                    </small>

                                    {pedido.componentes_kit?.length > 0 && (
                                      <small>
                                        Kit:{" "}
                                        {pedido.componentes_kit
                                          .map(
                                            (item) =>
                                              `${item.sku} x${item.quantidade}`,
                                          )
                                          .join(" + ")}
                                      </small>
                                    )}
                                  </>
                                ) : (
                                  <>
                                    <strong className="valor-negativo">
                                      Não cadastrado
                                    </strong>

                                    {pedido.erro_produto && (
                                      <small>{pedido.erro_produto}</small>
                                    )}

                                    <button
                                      type="button"
                                      className="btn-cadastrar-pendente"
                                      onClick={() =>
                                        cadastrarProdutoPendente(pedido)
                                      }
                                    >
                                      Cadastrar SKU
                                    </button>

                                    {cadastroRapidoAberto && (
                                      <div className="cadastro-rapido-box">
                                        <label>SKU</label>
                                        <input
                                          type="text"
                                          value={cadastroRapido.sku}
                                          onChange={(event) =>
                                            setCadastroRapido({
                                              ...cadastroRapido,
                                              sku: event.target.value,
                                            })
                                          }
                                        />

                                        <label>Nome</label>
                                        <input
                                          type="text"
                                          placeholder="Nome do produto"
                                          value={cadastroRapido.nome}
                                          onChange={(event) =>
                                            setCadastroRapido({
                                              ...cadastroRapido,
                                              nome: event.target.value,
                                            })
                                          }
                                        />

                                        <label>Custo</label>
                                        <input
                                          type="number"
                                          placeholder="Ex: 8.50"
                                          value={cadastroRapido.custo}
                                          onChange={(event) =>
                                            setCadastroRapido({
                                              ...cadastroRapido,
                                              custo: event.target.value,
                                            })
                                          }
                                        />

                                        <div className="cadastro-rapido-acoes">
                                          <button
                                            type="button"
                                            className="btn-salvar-rapido"
                                            onClick={salvarCadastroRapido}
                                            disabled={salvandoCadastroRapido}
                                          >
                                            {salvandoCadastroRapido
                                              ? "Salvando..."
                                              : "Salvar"}
                                          </button>

                                          <button
                                            type="button"
                                            className="btn-cancelar-rapido"
                                            onClick={cancelarCadastroRapido}
                                          >
                                            Cancelar
                                          </button>
                                        </div>
                                      </div>
                                    )}
                                  </>
                                )}
                              </td>

                              <td>
                                {pedido.produto_encontrado
                                  ? formatarMoeda(pedido.custo_total_cadastrado)
                                  : "-"}
                              </td>

                              <td>
                                {formatarMoeda(
                                  pedido.frete_vendedor ??
                                    pedido.taxa_frete ??
                                    pedido.frete ??
                                    0,
                                )}
                              </td>

                              <td>{formatarMoeda(pedido.vendas_produtos)}</td>

                              <td
                                className={
                                  pedido.lucro_real >= 0
                                    ? "valor-positivo destaque-lucro"
                                    : "valor-negativo destaque-lucro"
                                }
                              >
                                {formatarMoeda(pedido.lucro_real)}
                              </td>

                              <td>{formatarPercentual(pedido.margem_real)}</td>

                              <td>
                                <span className={classeStatusComercial(pedido)}>
                                  {formatarStatusComercial(pedido)}
                                </span>
                              </td>

                              <td>
                                <span
                                  className={
                                    pedido.status === "lucro"
                                      ? "status lucro"
                                      : pedido.status === "prejuizo"
                                        ? "status prejuizo"
                                        : "status neutro"
                                  }
                                >
                                  {formatarStatus(pedido.status)}
                                </span>
                              </td>

                              <td>{formatarMoeda(pedido.lucro_upseller)}</td>

                              <td>
                                {formatarMoeda(
                                  pedido.lucro_corrigido_antes_imposto,
                                )}
                              </td>

                              <td>{formatarMoeda(pedido.imposto_simples)}</td>
                            </tr>
                          );
                        })}

                        {pedidosPaginados.length === 0 && (
                          <tr>
                            <td colSpan="15">Nenhum pedido encontrado.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className="pagination pagination-bottom">
                    <button
                      type="button"
                      disabled={paginaSegura <= 1}
                      onClick={() => setPaginaAtual(paginaSegura - 1)}
                    >
                      Anterior
                    </button>

                    <span>
                      Página {paginaSegura} de {totalPaginas}
                    </span>

                    <button
                      type="button"
                      disabled={paginaSegura >= totalPaginas}
                      onClick={() => setPaginaAtual(paginaSegura + 1)}
                    >
                      Próxima
                    </button>
                  </div>
                </section>
              </>
            )}
          </>
        )}

        {abaAtiva === "produtos" && (
          <>
            <header className="topbar">
              <div>
                <h1>Cadastro de Produtos</h1>
                <p>
                  Cadastre produtos unitários e kits personalizados. O imposto é
                  informado apenas no Dashboard.
                </p>
              </div>

              <div className="usuario-logado-box">
                <div>
                  <strong>{usuarioLogado?.nome}</strong>
                  <span>{usuarioLogado?.email}</span>
                </div>

                <button
                  type="button"
                  className="btn-sair"
                  onClick={sairDoSistema}
                >
                  Sair
                </button>
              </div>
            </header>

            <section className="import-card">
              <div className="import-info">
                <h2>Importar produtos por Excel</h2>
                <p>
                  Baixe o modelo, preencha os produtos unitários e kits
                  personalizados, depois importe aqui. Para kit automático,
                  cadastre apenas o SKU base.
                </p>
                <p>
                  <strong>Shopee:</strong> selecione no campo abaixo a planilha
                  exportada da Shopee (mass_update_basic_info, que tem o ID do
                  Produto e o SKU) e clique em "Importar mapa Shopee" para
                  vincular os IDs aos seus SKUs automaticamente. Depois é só
                  ajustar o custo de cada produto.
                </p>
              </div>

              <div className="import-actions">
                <button
                  type="button"
                  className="btn-secundario"
                  onClick={baixarModeloProdutos}
                >
                  Baixar modelo
                </button>

                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(event) =>
                    setArquivoProdutos(event.target.files[0])
                  }
                />

                <button
                  type="button"
                  onClick={importarProdutosExcel}
                  disabled={importandoProdutos}
                >
                  {importandoProdutos ? "Importando..." : "Importar Excel"}
                </button>

                <button
                  type="button"
                  className="btn-secundario"
                  onClick={importarMapaShopee}
                  disabled={importandoProdutos}
                >
                  {importandoProdutos
                    ? "Importando..."
                    : "Importar mapa Shopee"}
                </button>
              </div>

              {resultadoImportacao && (
                <div className="resultado-importacao">
                  <strong>Resultado da importação:</strong>
                  <span>Criados: {resultadoImportacao.total_criados}</span>
                  <span>Erros: {resultadoImportacao.total_erros}</span>

                  {resultadoImportacao.erros?.length > 0 && (
                    <ul>
                      {resultadoImportacao.erros.map((erro, index) => (
                        <li key={index}>
                          Linha {erro.linha_excel} - SKU {erro.sku}: {erro.erro}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </section>

            <section className="product-form-card">
              <div className="campo-sku">
                <label>SKU</label>
                <input
                  type="text"
                  placeholder="Ex: LE885C"
                  value={novoProduto.sku}
                  onChange={(event) =>
                    setNovoProduto({ ...novoProduto, sku: event.target.value })
                  }
                />
              </div>

              <div className="campo-nome">
                <label>Nome do produto</label>
                <input
                  type="text"
                  placeholder="Ex: Kit cabo + fone"
                  value={novoProduto.nome}
                  onChange={(event) =>
                    setNovoProduto({ ...novoProduto, nome: event.target.value })
                  }
                />
              </div>

              <div className="campo-custo">
                <label>Custo unitário</label>
                <input
                  type="number"
                  placeholder="Ex: 12.50"
                  value={novoProduto.custo}
                  disabled={novoProduto.tipo === "kit_personalizado"}
                  onChange={(event) =>
                    setNovoProduto({
                      ...novoProduto,
                      custo: event.target.value,
                    })
                  }
                />
              </div>

              <div className="campo-tipo">
                <label>Tipo</label>
                <select
                  value={novoProduto.tipo}
                  onChange={(event) =>
                    setNovoProduto({
                      ...novoProduto,
                      tipo: event.target.value,
                      custo:
                        event.target.value === "kit_personalizado"
                          ? ""
                          : novoProduto.custo,
                      componentes:
                        event.target.value === "unitario"
                          ? []
                          : novoProduto.componentes,
                    })
                  }
                >
                  <option value="unitario">Unitário</option>
                  <option value="kit_personalizado">Kit personalizado</option>
                </select>
              </div>

              <div className="campo-nome">
                <label>ID do produto no marketplace (opcional)</label>
                <input
                  type="text"
                  placeholder="Ex: ID da Shopee 22693247331 (separe vários por vírgula)"
                  value={novoProduto.codigosExternos}
                  onChange={(event) =>
                    setNovoProduto({
                      ...novoProduto,
                      codigosExternos: event.target.value,
                    })
                  }
                />
              </div>

              <div className="acoes-form-produto">
                <button type="button" onClick={cadastrarProduto}>
                  {produtoEditandoId ? "Salvar edição" : "Cadastrar produto"}
                </button>

                {produtoEditandoId && (
                  <button
                    type="button"
                    className="btn-cancelar"
                    onClick={cancelarEdicao}
                  >
                    Cancelar
                  </button>
                )}
              </div>
            </section>

            {novoProduto.tipo === "kit_personalizado" && (
              <section className="kit-card">
                <div className="table-header">
                  <h2>Componentes do kit</h2>
                  <span>Total: {novoProduto.componentes.length}</span>
                </div>

                <div className="kit-form">
                  <div>
                    <label>SKU do componente</label>
                    <input
                      type="text"
                      placeholder="Ex: LE885C"
                      value={novoComponente.sku}
                      onChange={(event) =>
                        setNovoComponente({
                          ...novoComponente,
                          sku: event.target.value,
                        })
                      }
                    />
                  </div>

                  <div>
                    <label>Quantidade</label>
                    <input
                      type="number"
                      value={novoComponente.quantidade}
                      onChange={(event) =>
                        setNovoComponente({
                          ...novoComponente,
                          quantidade: event.target.value,
                        })
                      }
                    />
                  </div>

                  <button type="button" onClick={adicionarComponente}>
                    Adicionar componente
                  </button>
                </div>

                {novoProduto.componentes.length > 0 && (
                  <div className="componentes-lista">
                    {novoProduto.componentes.map((componente, index) => (
                      <div className="componente-item" key={index}>
                        <strong>{componente.sku}</strong>
                        <span>x{componente.quantidade}</span>
                        <button
                          type="button"
                          onClick={() => removerComponente(index)}
                        >
                          Remover
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            <section className="table-card">
              <div className="table-header">
                <h2>Produtos cadastrados</h2>
                <span>
                  Mostrando {inicioExibicaoProdutos}-{fimExibicaoProdutos} de{" "}
                  {produtosFiltrados.length}
                </span>
              </div>

              <div className="produtos-filtros">
                <div>
                  <label>Buscar produto</label>
                  <input
                    type="text"
                    placeholder="Buscar por SKU ou nome..."
                    value={filtroProduto}
                    onChange={(event) => setFiltroProduto(event.target.value)}
                  />
                </div>

                <div>
                  <label>Ver por página</label>
                  <select
                    value={produtosPorPagina}
                    onChange={(event) =>
                      setProdutosPorPagina(Number(event.target.value))
                    }
                  >
                    <option value={25}>25 produtos</option>
                    <option value={50}>50 produtos</option>
                    <option value={100}>100 produtos</option>
                    <option value={300}>300 produtos</option>
                  </select>
                </div>

                <div className="filter-button-box">
                  <label>&nbsp;</label>
                  <button
                    type="button"
                    className="btn-limpar"
                    onClick={() => {
                      setFiltroProduto("");
                      setPaginaProdutoAtual(1);
                    }}
                  >
                    Limpar busca
                  </button>
                </div>
              </div>

              <div className="pagination">
                <button
                  type="button"
                  disabled={paginaProdutoSegura <= 1}
                  onClick={() => setPaginaProdutoAtual(paginaProdutoSegura - 1)}
                >
                  Anterior
                </button>

                <span>
                  Página {paginaProdutoSegura} de {totalPaginasProdutos}
                </span>

                <button
                  type="button"
                  disabled={paginaProdutoSegura >= totalPaginasProdutos}
                  onClick={() => setPaginaProdutoAtual(paginaProdutoSegura + 1)}
                >
                  Próxima
                </button>
              </div>

              <div className="table-wrapper">
                <table className="produtos-table">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Produto</th>
                      <th>Custo</th>
                      <th>Tipo</th>
                      <th>Componentes</th>
                      <th>Ação</th>
                    </tr>
                  </thead>

                  <tbody>
                    {produtosPaginados.map((produto) => (
                      <tr key={produto.id}>
                        <td>
                          <strong>{produto.sku}</strong>
                        </td>
                        <td>{produto.nome}</td>
                        <td>{formatarMoeda(produto.custo)}</td>
                        <td>{produto.tipo}</td>
                        <td>
                          {produto.componentes?.length > 0
                            ? produto.componentes
                                .map(
                                  (item) => `${item.sku} x${item.quantidade}`,
                                )
                                .join(" + ")
                            : "-"}
                        </td>
                        <td>
                          <div className="acoes-produto">
                            <button
                              type="button"
                              className="btn-editar"
                              onClick={() => editarProduto(produto)}
                            >
                              Editar
                            </button>

                            <button
                              type="button"
                              className="btn-excluir"
                              onClick={() => excluirProduto(produto.id)}
                            >
                              Excluir
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}

                    {produtosPaginados.length === 0 && (
                      <tr>
                        <td colSpan="6">Nenhum produto encontrado.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="pagination pagination-bottom">
                <button
                  type="button"
                  disabled={paginaProdutoSegura <= 1}
                  onClick={() => setPaginaProdutoAtual(paginaProdutoSegura - 1)}
                >
                  Anterior
                </button>

                <span>
                  Página {paginaProdutoSegura} de {totalPaginasProdutos}
                </span>

                <button
                  type="button"
                  disabled={paginaProdutoSegura >= totalPaginasProdutos}
                  onClick={() => setPaginaProdutoAtual(paginaProdutoSegura + 1)}
                >
                  Próxima
                </button>
              </div>
            </section>
          </>
        )}

        {abaAtiva === "configuracoes" && (
          <>
            <header className="topbar">
              <div>
                <h1>Configurações</h1>
                <p>
                  Configure os dados principais da empresa, imposto padrão e
                  margem mínima saudável.
                </p>
              </div>

              <div className="usuario-logado-box">
                <div>
                  <strong>{usuarioLogado?.nome}</strong>
                  <span>{usuarioLogado?.email}</span>
                </div>

                <button
                  type="button"
                  className="btn-sair"
                  onClick={sairDoSistema}
                >
                  Sair
                </button>
              </div>
            </header>

            <section className="config-card">
              <div className="config-grid">
                <div>
                  <label>Nome da empresa ou cliente</label>
                  <input
                    type="text"
                    placeholder="Ex: Smart Mix Casa"
                    value={configuracoes.nomeEmpresa}
                    onChange={(event) =>
                      setConfiguracoes({
                        ...configuracoes,
                        nomeEmpresa: event.target.value,
                      })
                    }
                  />
                </div>

                <div>
                  <label>Imposto padrão (%)</label>
                  <input
                    type="number"
                    value={configuracoes.impostoPadrao}
                    onChange={(event) =>
                      setConfiguracoes({
                        ...configuracoes,
                        impostoPadrao: event.target.value,
                      })
                    }
                  />
                </div>

                <div>
                  <label>Margem mínima saudável (%)</label>
                  <input
                    type="number"
                    value={configuracoes.margemMinima}
                    onChange={(event) =>
                      setConfiguracoes({
                        ...configuracoes,
                        margemMinima: event.target.value,
                      })
                    }
                  />
                </div>
              </div>

              <button
                type="button"
                className="btn-salvar-config"
                onClick={salvarConfiguracoes}
                disabled={carregandoConfiguracoes}
              >
                {carregandoConfiguracoes
                  ? "Salvando..."
                  : "Salvar configurações"}
              </button>
            </section>

            <section className="table-card config-explicacao">
              <h2>Como o status comercial funciona</h2>

              <div className="explicacao-grid">
                <div className="explicacao-item sucesso">
                  <strong>Lucro saudável</strong>
                  <p>Lucro real positivo e margem maior ou igual à mínima.</p>
                </div>

                <div className="explicacao-item alerta">
                  <strong>Atenção</strong>
                  <p>Tem lucro, mas a margem está abaixo da margem mínima.</p>
                </div>

                <div className="explicacao-item perigo">
                  <strong>Prejuízo</strong>
                  <p>Lucro real negativo.</p>
                </div>

                <div className="explicacao-item neutro">
                  <strong>Neutro</strong>
                  <p>Lucro real igual a zero.</p>
                </div>
              </div>
            </section>
          </>
        )}
        {abaAtiva === "minha-conta" && (
          <>
            <header className="topbar">
              <div>
                <h1>Minha Conta</h1>
                <p>Dados da sua conta, empresa e plano atual.</p>
              </div>

              <div className="usuario-logado-box">
                <div>
                  <strong>{usuarioLogado?.nome}</strong>
                  <span>{usuarioLogado?.email}</span>
                </div>

                <button
                  type="button"
                  className="btn-sair"
                  onClick={sairDoSistema}
                >
                  Sair
                </button>
              </div>
            </header>

            {carregandoMinhaConta && (
              <section className="config-card">
                <p>Carregando dados da conta...</p>
              </section>
            )}

            {!carregandoMinhaConta && minhaConta && (
              <>
                <section className="config-card">
                  <h2>Dados da conta</h2>
                  <div className="config-grid">
                    <div>
                      <label>Usuário</label>
                      <p>{minhaConta.usuario?.nome}</p>
                    </div>
                    <div>
                      <label>E-mail</label>
                      <p>{minhaConta.usuario?.email}</p>
                    </div>
                    <div>
                      <label>Empresa</label>
                      <p>{minhaConta.empresa?.nome}</p>
                    </div>
                    <div>
                      <label>Perfil</label>
                      <p>{minhaConta.usuario?.perfil}</p>
                    </div>
                  </div>
                </section>

                <section className="config-card">
                  <h2>Plano atual</h2>
                  <div className="config-grid">
                    <div>
                      <label>Plano</label>
                      <p>{minhaConta.empresa?.plano_nome}</p>
                    </div>
                    <div>
                      <label>Status</label>
                      <p>{minhaConta.empresa?.status}</p>
                    </div>
                    <div>
                      <label>Limite de pedidos por relatório</label>
                      <p>{minhaConta.empresa?.limite_pedidos_mes}</p>
                    </div>
                    <div>
                      <label>Início do teste</label>
                      <p>
                        {minhaConta.empresa?.data_inicio_teste
                          ? new Date(
                              minhaConta.empresa.data_inicio_teste,
                            ).toLocaleDateString("pt-BR")
                          : "-"}
                      </p>
                    </div>
                    <div>
                      <label>Fim do teste</label>
                      <p>
                        {minhaConta.empresa?.data_fim_teste
                          ? new Date(
                              minhaConta.empresa.data_fim_teste,
                            ).toLocaleDateString("pt-BR")
                          : "-"}
                      </p>
                    </div>
                  </div>
                </section>

                <section className="config-card">
                  <h2>Planos</h2>

                  {minhaConta.empresa?.assinatura_status === "pendente" && (
                    <div
                      style={{
                        background: "#fff8e1",
                        border: "1px solid #f0c050",
                        borderRadius: "8px",
                        padding: "12px 16px",
                        marginBottom: "16px",
                      }}
                    >
                      ⏳ Pagamento em processamento. Seu plano será atualizado
                      automaticamente quando o Mercado Pago confirmar.
                    </div>
                  )}

                  {minhaConta.empresa?.assinatura_status === "inadimplente" && (
                    <div
                      style={{
                        background: "#fdecea",
                        border: "1px solid #e57373",
                        borderRadius: "8px",
                        padding: "12px 16px",
                        marginBottom: "16px",
                      }}
                    >
                      ⚠️ Pagamento pendente. Sua assinatura pode ser suspensa.
                      Regularize pelo Mercado Pago.
                    </div>
                  )}

                  <div className="explicacao-grid">
                    {[
                      {
                        id: "free",
                        nome: "Free",
                        limite: "200 pedidos/relatório",
                        preco: "Grátis",
                        destaque: false,
                      },
                      {
                        id: "profissional",
                        nome: "Profissional",
                        limite: "2.000 pedidos/relatório",
                        preco: "R$ 29,90/mês",
                        destaque: true,
                      },
                      {
                        id: "avancado",
                        nome: "Avançado",
                        limite: "10.000 pedidos/relatório",
                        preco: "R$ 59,90/mês",
                        destaque: false,
                      },
                    ].map((plano) => {
                      const planoAtual = minhaConta.empresa?.plano;
                      const ehAtual =
                        planoAtual === plano.id ||
                        (plano.id === "free" &&
                          ["teste", "free"].includes(planoAtual));

                      return (
                        <div
                          key={plano.id}
                          className={
                            ehAtual
                              ? "explicacao-item sucesso"
                              : "explicacao-item"
                          }
                          style={
                            plano.destaque && !ehAtual
                              ? { border: "2px solid #1a73e8" }
                              : {}
                          }
                        >
                          {plano.destaque && !ehAtual && (
                            <small
                              style={{
                                background: "#1a73e8",
                                color: "#fff",
                                borderRadius: "4px",
                                padding: "2px 8px",
                                fontSize: "11px",
                              }}
                            >
                              ★ Mais popular
                            </small>
                          )}
                          <strong>{plano.nome}</strong>
                          <p>{plano.limite}</p>
                          <p>
                            <strong>{plano.preco}</strong>
                          </p>

                          {ehAtual ? (
                            <>
                              <button type="button" disabled>
                                Plano atual ✓
                              </button>
                              {plano.id !== "free" &&
                                minhaConta.empresa?.assinatura_id && (
                                  <button
                                    type="button"
                                    className="btn-secundario"
                                    style={{
                                      marginTop: "6px",
                                      fontSize: "12px",
                                    }}
                                    onClick={cancelarAssinatura}
                                  >
                                    Cancelar assinatura
                                  </button>
                                )}
                            </>
                          ) : plano.id === "free" ? (
                            <button type="button" disabled>
                              Grátis sempre
                            </button>
                          ) : (
                            <button
                              type="button"
                              disabled={assinando}
                              onClick={() => assinarPlano(plano.id)}
                            >
                              {assinando ? "Aguarde..." : "Assinar agora →"}
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  <p
                    style={{
                      fontSize: "12px",
                      color: "#888",
                      marginTop: "12px",
                    }}
                  >
                    Pagamento seguro via Mercado Pago. Cancele quando quiser,
                    sem multa.
                  </p>
                </section>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
