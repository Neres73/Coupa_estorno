# Coupa — Estorno de Recebimentos em Lote

Script em Python + Playwright que lê números de pedido (PO) numa planilha Excel e anula, no histórico de recebimentos do Coupa, todos os recibos de cada pedido.

Uso no meu trabalho, no back-office de Manutenção, quando um lote de recebimentos precisa ser desfeito.

---

## Por que existe

Para estornar um recebimento é preciso achar o pedido no histórico, abrir cada recibo, informar a anulação, confirmar e voltar. Quando o lote tem vários pedidos e cada pedido tem mais de um recibo, isso vira muito clique repetido. O script percorre a lista da planilha e faz esses passos sozinho.

---

## O que o script faz

1. Lê os números de PO da coluna configurada na planilha e **remove os repetidos**
2. Abre o histórico de recebimentos do Coupa (com a sessão já salva)
3. Para cada PO:
   - Filtra o histórico por **Número da PO contém** o número da planilha
   - Se não houver recibo, pula para o próximo
   - Para cada recibo encontrado:
     - Clica em anular
     - Preenche a quantidade e marca **Anular totalmente esta transação**
     - Se o botão **Anular recibo** não habilitar, repete a marcação (até 3 vezes)
     - Clica em **Anular recibo** e confirma o aviso "Tem certeza?"
   - Se um recibo der erro, registra, volta ao histórico, refaz o filtro e segue
4. Mostra no terminal o resumo: recibos estornados e erros por PO

---

## Exemplo de saída

```
====================================================
📋  RELATÓRIO FINAL — ESTORNO
====================================================
  POs processadas           : 3
  ✅ Recibos estornados      : 4
  ❌ Erros                  : 0

  Detalhe por PO:
    • 4200000001  →  ✅ 2 estornado(s)
    • 4200000002  →  ✅ 1 estornado(s)
    • 4200000003  →  ✅ 1 estornado(s)
====================================================
```
*(números fictícios)*

---

## Instalação

Requisitos: Python 3.10+ e Microsoft Edge.

```bash
git clone https://github.com/Neres73/Coupa_estorno.git
cd Coupa_estorno

python -m venv .venv
.venv\Scripts\activate            # Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
playwright install msedge
```

## Configuração

Copie o modelo e preencha com os dados do seu ambiente:

```bash
copy .env.example .env            # Linux/Mac: cp .env.example .env
```

| Variável | O que é | Padrão |
|---|---|---|
| `COUPA_URL` | Página inicial do seu Coupa | obrigatória |
| `RECEBIMENTO_URL` | Página do histórico de recebimentos | montada a partir do `COUPA_URL` |
| `EXCEL_PATH` | Caminho da planilha com os números de PO | obrigatória |
| `COLUNA_REQ` | Número da coluna com os POs (A=1 … G=7) | `7` |
| `USER_DATA_DIR` | Pasta do perfil do navegador com a sessão | `./perfil_recebimento` |

A planilha precisa ter cabeçalho na linha 1; os números são lidos a partir da linha 2 da aba ativa. O perfil padrão é o mesmo do [Coupa_recebimento](https://github.com/Neres73/Coupa_recebimento), então um login serve para os dois.

O `.env`, a pasta do perfil e as planilhas estão no `.gitignore` e nunca vão para o repositório.

## Uso

```bash
python main.py --login    # 1ª vez: abre o Edge para você fazer login; a sessão fica salva
python main.py            # execuções seguintes
```

O script **não lê, guarda nem digita senha**. Se a sessão expirar, é só rodar `--login` de novo.

---

## Limitações

- Anula **todos** os recibos encontrados para o PO; não há como escolher só alguns
- O filtro usa "contém": um número curto pode trazer recibos de outros POs, então use o número completo
- Os seletores são da interface do Coupa em português no ambiente onde o script foi feito; outro ambiente pode exigir ajustes
- O resumo sai só no terminal (não gera arquivo)
- Sem modo de simulação: rodar o script **estorna de verdade**

## Estrutura

```
├── main.py            # leitura da planilha, filtro no histórico, estorno e resumo
├── requirements.txt
├── .env.example       # modelo de configuração
└── .gitignore
```

---

Desenvolvido por [Gustavo Neres](https://github.com/Neres73), com apoio do Claude (IA) para modelar a lógica, escrever e revisar o código. Projeto compartilhado como portfólio: nenhuma URL, credencial ou dado da empresa está no repositório. Licença MIT.
