# AI CONTEXT - Pytegrator

## 1) Visao geral tecnica

Pytegrator e uma aplicacao desktop Python orientada a integracao com Mega ERP, com interface em CustomTkinter/Tkinter e tres capacidades principais:

- Geracao de XML para o servico 207 (cadastro/parametrizacao de agentes).
- Envio SOAP em lote para endpoint MegaIntegradorService.
- Interpretacao de traces JSON com foco em SQL (analise de desempenho e erro).

Stack principal:

- UI: customtkinter + tkinter + ttk.
- HTTP/API: requests.
- XML: xml.etree.ElementTree, minidom, xml.sax.saxutils.escape.
- Build distribuicao: PyInstaller (onefile/windowed) via script BAT.
- Logging: RotatingFileHandler em logs/Pytegrator.log.

Dependencias declaradas em requirements.txt:

- customtkinter
- Pillow
- requests
- zeep (presente mas nao utilizado diretamente no codigo atual)

---

## 2) Estrutura funcional (modulos e responsabilidades)

### Entry point

- main.py
  - Configura ambiente e logging.
  - Carrega mapeamento CSV para memoria.
  - Inicializa janela principal e roteamento entre frames.
  - Mantem estado compartilhado via self.shared_data (ex.: current_xml).

### Configuracao transversal

- core/logger_config.py
  - Inicializa root logger.
  - Log em arquivo rotativo (5MB x 5 backups) + console.
  - Captura excecoes nao tratadas via sys.excepthook.

### Servico 207

- app/services/servico_207/form_207.py (pasta real: servico com acento no nome da pasta do workspace)
  - Formulario grande com validacoes de negocio.
  - Integracoes com APIs IBGE/ViaCEP.
  - Gera blocos XML (Pessoa, Fiscal, AgenteId, Inscricoes etc.).
  - Entrega XML final para tela Resultado via controller.shared_data.

### Resultado XML

- app/views/xmlResultado.py
  - Exibe XML gerado.
  - Copia para clipboard.
  - Aciona integracao com SOAP preenchendo payload automaticamente.

### SOAP

- app/services/soap/form_ferramentasoap.py
  - Monta envelope SOAP e faz requests.post em loop.
  - Executa envio em thread para nao travar UI.
  - Exibe logs/progresso e detalha resposta XML.
  - Exponibiliza metodo preencher_payload(xml_string, cod_servico).

### Trace Interpreter

- app/services/trace_interpreter/trace_interpreter.py
  - Carrega trace JSON (lista de eventos).
  - Aplica filtros dinamicos por campos e status de erro.
  - Renderiza lista de eventos em drawer.
  - Mostra detalhes e SQL com substituicao de parametros + formatacao.
  - Identifica pico de execucao e permite navegacao direta.

### Bibliotecas de apoio

- app/lib/mappers/codigoMapper.py
  - Resolve caminho de recurso em modo dev e PyInstaller.
  - Carrega app/assets/codigo.csv em cache (MAPA_CODIGOS).
  - Faz lookup IBGE -> codigo interno Mega.
- app/lib/api/ibgeAPI.py
  - Busca municipios por UF e retorna codigo IBGE do municipio.
- app/lib/api/viaCepAPI.py
  - Busca endereco aproximado por municipio/UF e retorna cep/logradouro/bairro/numero.
- app/lib/formatters/formatters.py
  - Sanitiza e escapa campos XML.
- app/lib/generators/\*.py
  - Gera CPF/CNPJ/inscricoes e nomes/fantasias sinteticos.

### Artefato auxiliar

- app/lib/tipoPessoaRural.py
  - Exemplo demonstrativo de UI (nao integrado no fluxo principal).

---

## 3) Fluxos ponta-a-ponta

### Fluxo A - Inicializacao

1. main.py chama setup_environment().
2. setup_logging() e aplicado (ou fallback basicConfig se falhar import).
3. codigoMapper.carregar_mapa_codigos() deve ocorrer antes de gerar XML com municipio.
4. AppController instancia frames e exibe MenuPrincipal.

### Fluxo B - Geracao XML 207

1. Usuario preenche formulario em Gerador207Frame.
2. on_gerar_xml valida campos obrigatorios e consistencia de selecoes.
3. Busca codigo IBGE e endereco (IBGE/ViaCEP).
4. Resolve codigo interno via MAPA_CODIGOS.
5. Monta XML final (Agente + Parametros + AgenteId + Fiscal + blocos condicionais).
6. Salva em shared_data[current_xml] e navega para Resultado.

### Fluxo C - Resultado -> SOAP

1. ResultadoFrame recebe XML via set_xml().
2. Usuario aciona "Copiar XML e ir para Integracao".
3. ResultadoFrame localiza FerramentaSOAP e chama preencher_payload(xml, "207").
4. AppController troca para frame SOAP.

### Fluxo D - Envio SOAP em lote

1. Usuario define endpoint/porta/campos e opcionalmente XML payload.
2. Validacoes impedem combinacoes invalidas (transacao x payload).
3. \_iniciar_processo() envia N vezes em thread (requests.post, timeout 30s).
4. UI recebe atualizacoes com after() (thread-safe).
5. Resposta e parseada para Result/Mensagem/CodTransacao e logada.

### Fluxo E - Interpretacao de trace

1. Carrega JSON via file dialog.
2. Valida formato (lista nao vazia de dicts).
3. Calcula evento mais lento.
4. Popular campos de filtro dinamicamente por uniao de chaves.
5. Renderiza drawer com cards + detalhes + SQL formatado.

---

## 4) Contratos de dados importantes

### shared_data

- Chave usada: current_xml (str).
- Produtor: Gerador207Frame.
- Consumidor: ResultadoFrame (via AppController.show_frame("Resultado")).

### MAPA_CODIGOS (codigoMapper)

- Tipo: dict[str, str].
- Chave: codigo IBGE (MUN_IN_CODIGOIBGE).
- Valor: codigo interno Mega (MUN_IN_CODIGO).
- Origem: app/assets/codigo.csv.

### Estrutura de evento esperada no trace

Campos usados de forma direta:

- objectName, eventId, eventType, execution, rowsAffected
- userId, userComputerName, userIp
- sql, parameters, errorText

### Retorno SOAP esperado

- XML com no {http://tempuri.org/}Result contendo XML interno com tags:
  - Erro
  - Mensagem
  - CodTransacao

---

## 5) Regras de negocio relevantes

- Em servico 207:
  - Campo Nome, Estado, Municipio e Filial sao obrigatorios.
  - UF deve existir em lista fechada UF_LIST.
  - Tipo Rural exige subescolha F/J.
  - ISENTO desabilita inscricoes estadual/municipal.
- Em SOAP:
  - Cód. Servico nao pode ser 0000.
  - Se XML Envio estiver preenchido, transacao deve ser 0.

---

## 6) Acoplamentos e pontos criticos

### Acoplamentos fortes

- ResultadoFrame depende de nome de frame FerramentaSOAP e metodo preencher_payload.
- Gerador207 depende de carga previa do mapper (carregar_mapa_codigos).
- SOAP depende de contrato XML especifico do endpoint MegaIntegradorService.

### Recursos criticos para operacao

- app/assets/codigo.csv (sem ele o lookup IBGE->interno falha).
- app/assets/icon.ico e icones auxiliares (impacto visual, nao funcional principal).

### Build com PyInstaller

- Script usa --add-data "app/assets;app/assets".
- codigoMapper contem logica correta para resolver recurso em modo frozen (sys.\_MEIPASS).

---

## 7) Riscos tecnicos e debt atual

1. Nome de pasta com acento: app/services/servico_207 usando caractere especial em caminho (servico com acento no workspace atual) pode causar friccao em scripts/ferramentas cross-platform.
2. URLs em ibgeAPI/viaCepAPI possuem espacos extras em chamadas upper()/quote() (ex.: uf.upper( )) que nao quebram Python, mas indicam sujeira de estilo.
3. Uso de print em modulos de biblioteca (API/mapper) em vez de logging centralizado.
4. zeep esta declarado, mas o cliente SOAP usa requests manualmente; dependencia possivelmente ociosa.
5. Arquivo duplicado de codigo.csv em app/lib/mappers/codigo.csv e app/assets/codigo.csv; o runtime usa app/assets/codigo.csv, gerando risco de divergencia silenciosa.
6. tipoPessoaRural.py aparenta ser exemplo isolado nao utilizado e pode confundir manutencao.
7. Falta camada de testes automatizados (unitarios/integracao) para geracao XML, parse SOAP e parser de trace.

---

## 8) Como rodar e operar (referencia rapida)

### Ambiente

- Windows + Python.
- Script recomendado: gerenciar_aplicacao.bat

### Execucao

- Opcao 1: refaz venv e instala deps.
- Opcao 3: executa app (python -m main).

### Build

- Opcao 4 do BAT (PyInstaller onefile windowed).

### Logs

- Arquivo principal: logs/Pytegrator.log

---

## 9) Checklist para IA antes de editar codigo

1. Confirmar se alteracao impacta fluxo 207, SOAP ou Trace.
2. Se mexer em geracao XML, validar:
   - escape XML via campo_xml
   - regras de obrigatoriedade e combinacao de campos
   - compatibilidade com ResultadoFrame e SOAP preencher_payload
3. Se mexer em mapper/API, preservar compatibilidade com PyInstaller.
4. Se mexer em SOAP threading, manter atualizacao de UI via after().
5. Evitar quebrar nomes de frames esperados por AppController.show_frame().

---

## 10) Sugestoes de melhorias priorizadas

P0 (confiabilidade)

- Trocar prints por logging nos modulos de API/mapper.
- Eliminar duplicidade de codigo.csv ou definir fonte unica com validacao de checksum/data.
- Adicionar tratamento padrao de erro/retry para chamadas HTTP (IBGE/ViaCEP/SOAP).

P1 (manutenibilidade)

- Extrair geracao de XML 207 para servico separado (fora da classe UI).
- Criar dataclasses para payload de 207 e evento de trace.
- Adicionar testes para:
  - \_format_sql_with_params
  - \_gerar_bloco_fiscal / \_gerar_bloco_agente_id
  - buscar_codigo_municipio / buscar_endereco_por_municipio (mock HTTP)

P2 (produto)

- Exportacao de resultados (trace) para arquivo.
- Templates de payload SOAP por servico.
- Validacao visual mais guiada no formulario 207.

---

## 11) Prompt base para uso por IA neste repositorio

Use este contexto como base e siga as regras:

- Nao quebrar navegacao entre frames: MenuPrincipal, Gerador207, FerramentaSOAP, Resultado, TraceInterpreter.
- Preservar compatibilidade de build PyInstaller e caminho de assets.
- Em alteracoes de 207, manter contrato de XML aceito pelo integrador e uso de campo_xml.
- Em alteracoes SOAP, manter processo em thread + atualizacao thread-safe da UI.
- Em alteracoes do Trace, manter capacidade de ler listas JSON heterogeneas e filtros dinamicos.
- Sempre avaliar impacto em app/assets/codigo.csv e lookup IBGE->codigo interno.

Fim do contexto.
