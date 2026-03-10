# Pytegrator

Aplicacao desktop em Python para apoiar integracoes com Mega ERP, com foco em:

- Geracao de XML para servico 207.
- Envio SOAP em lote para integrador.
- Interpretacao de traces JSON com analise de SQL.

## Funcionalidades

- Interface desktop com CustomTkinter/Tkinter.
- Gerador de XML com validacoes de campos e regras fiscais.
- Tela de resultado para copiar XML e enviar diretamente para o modulo SOAP.
- Ferramenta SOAP com execucao em thread, logs e visualizacao de retorno XML.
- Interpretador de trace com filtros dinamicos, destaque de erros e pico de execucao.

## Estrutura do projeto

- main.py: ponto de entrada da aplicacao.
- gerenciar_aplicação.bat: menu de operacoes (venv, run, build e git).
- app/services/serviço_207/form_207.py: tela de geracao de XML 207.
- app/services/soap/form_ferramentasoap.py: tela de integracao SOAP.
- app/services/trace_interpreter/trace_interpreter.py: tela de interpretacao de trace.
- app/views/xmlResultado.py: tela de exibicao e copia do XML.
- app/lib/mappers/codigoMapper.py: mapeamento IBGE para codigo interno via CSV.
- app/assets/codigo.csv: base de mapeamento usada em runtime.
- core/logger_config.py: configuracao de logs.

## Requisitos

- Windows com Python 3.10+.
- Dependencias em requirements.txt.

## Como executar

Opcao recomendada (Windows):

1. Execute gerenciar_aplicação.bat.
2. Selecione a opcao 1 para recriar o ambiente e instalar dependencias.
3. Selecione a opcao 3 para rodar a aplicacao.

Opcao manual:

1. Criar ambiente virtual:
   - py -m venv .venv
2. Instalar dependencias:
   - .venv\\Scripts\\pip install -r requirements.txt
3. Executar app:
   - .venv\\Scripts\\python -m main

## Build do executavel

Pelo script:

1. Execute gerenciar_aplicação.bat.
2. Selecione a opcao 4 (build).

Isso gera o executavel na pasta dist.

## Logs

- Arquivo principal: logs/Pytegrator.log

## Observacoes tecnicas

- O mapeamento IBGE -> codigo interno depende de app/assets/codigo.csv.
- Para distribuicao com PyInstaller, os assets sao empacotados via --add-data no script BAT.
- Se houver erro de API externa (IBGE/ViaCEP), o fluxo de geracao usa tratamento com mensagens para o usuario.

## Licenca

Este projeto esta licenciado sob a Licenca MIT. Consulte o arquivo LICENSE para detalhes.
