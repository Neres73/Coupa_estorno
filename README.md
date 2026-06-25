# Coupa — Estorno de Recebimentos

Automação com Python e Playwright que lê números de PO de uma planilha Excel e realiza o estorno dos recibos correspondentes no histórico de recebimentos do Coupa.

---

## O que faz

1. Lê os números de PO da coluna **G** da planilha Excel (deduplica repetidos)
2. Abre o histórico de recebimentos do Coupa
3. Para cada número de PO:
   - Aplica o filtro avançado por "Número da PO" contém o número informado
   - Se não encontrar recibos, pula para o próximo
   - Para cada recibo encontrado:
     - Clica no botão de anular
     - Preenche a quantidade `1`
     - Marca o checkbox "Anular totalmente esta transação"
     - Clica em "Anular recibo"
     - Confirma o popup "Tem certeza?" automaticamente
4. Exibe relatório final com estornos realizados e erros

---

## Pré-requisitos

- Python 3.10+
- Microsoft Edge instalado
- PyCharm (recomendado)

### Instalação das dependências

```bash
pip install playwright openpyxl
playwright install msedge
```

---

## Configuração

Abra o arquivo `coupa_estorno.py` e ajuste as variáveis no topo:

```python
EXCEL_PATH    = Path(r"C:\Users\SEU_USUARIO\...\Pasta1.xlsx")  # caminho da planilha
COLUNA_REQ    = 7                                               # coluna G = 7
USER_DATA_DIR = Path("./perfil_recebimento")                   # pasta do perfil Edge
```

| Coluna | Letra | Valor |
|--------|-------|-------|
| F | 6 | — |
| G | **7** | Números de PO ✅ |
| H | 8 | — |

---

## Como usar

### Primeiro uso — salvar o login

```bash
python coupa_estorno.py --login
```

Faça o login na janela do Edge que abrir e pressione **Enter** no terminal. A sessão fica salva em `perfil_recebimento/`.

### Uso normal

```bash
python coupa_estorno.py
```

---

## Relatório final

```
====================================================
📋  RELATÓRIO FINAL — ESTORNO
====================================================
  POs processadas           : 3
  ✅ Recibos estornados      : 4
  ❌ Erros                  : 0

  Detalhe por PO:
    • 4200369785  →  ✅ 2 estornado(s)
    • 4200369796  →  ✅ 1 estornado(s)
    • 4200369819  →  ✅ 1 estornado(s)
====================================================
```

---

## Observações

- Usa o mesmo perfil em `perfil_recebimento/` da automação de recebimento — **não apague essa pasta**
- Se a sessão expirar, rode novamente com `--login`
- O popup "Tem certeza?" é confirmado automaticamente pelo script
- POs não encontradas no histórico são puladas sem erro
- POs duplicadas na planilha são processadas apenas uma vez
