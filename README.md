# WCAl+Elda · Unificador de Documentos

Aplicação web que unifica múltiplos arquivos PDF, DOCX ou imagens em um único documento Markdown utilizando OCR com a Google Vision API. O projeto inclui uma interface web inspirada no layout solicitado e um servidor HTTP escrito apenas com bibliotecas padrão do Python.

## Requisitos

- Python 3.11 ou superior
- Chave de API do [Google Cloud Vision](https://cloud.google.com/vision)
- Acesso à internet para chamadas à API do Google Vision

## Configuração

1. Clone o repositório e entre na pasta do projeto.
2. Crie um arquivo `.env` baseado em `.env.example` e informe a chave da API:

   ```bash
   cp .env.example .env
   echo "GOOGLE_VISION_API_KEY=\"sua-chave\"" >> .env
   ```

3. Inicie o servidor usando o módulo principal do pacote:

   ```bash
   python -m app.server
   ```

   O servidor ficará disponível em `http://localhost:8000` e serve automaticamente a interface web na rota raiz.

## Uso

1. Acesse `http://localhost:8000` no navegador.
2. Faça upload de um ou mais arquivos PDF, DOCX ou imagens (PNG/JPG).
3. Clique em **Converter para Markdown** para iniciar o processamento.
4. Após a conclusão, visualize o resultado em Markdown e faça o download do arquivo unificado.

> ⚠️ Sem configurar `GOOGLE_VISION_API_KEY` os uploads de PDF e imagens não funcionarão, pois dependem do OCR. O processamento de arquivos DOCX continua disponível.

## Estrutura do projeto

```
app/
├── config.py          # Leitura de variáveis de ambiente
├── converters.py      # Conversão de arquivos e unificação em Markdown
├── google_vision.py   # Cliente REST simples para o Google Vision
├── markdown.py        # Funções utilitárias para Markdown
└── server.py          # Servidor HTTP e endpoint /api/process
public/
├── index.html         # Interface principal
├── script.js          # Lógica do front-end (upload e interações)
└── styles.css         # Estilos inspirados no layout fornecido
tests/
└── test_markdown.py   # Testes unitários para utilitários de Markdown
```

## Testes

Execute os testes unitários com:

```bash
python -m unittest discover -s tests
```

## Fluxo de conversão

1. **DOCX → Markdown**: extrai o texto do `word/document.xml` e normaliza para Markdown simples.
2. **PDF/Imagens → Markdown**: envia o arquivo para o endpoint REST do Google Vision com `DOCUMENT_TEXT_DETECTION` e normaliza o texto retornado.
3. **Unificação**: cada arquivo processado gera uma seção `## Documento N`, resultando em um único arquivo Markdown pronto para download.

## Segurança

- A chave da API do Google Vision nunca é exposta no front-end. Todas as chamadas são feitas pelo servidor.
- Os arquivos enviados são processados em memória e não são persistidos em disco.

## Licença

Este projeto está licenciado sob a licença MIT.
