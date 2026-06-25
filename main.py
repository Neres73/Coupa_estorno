"""
Coupa - Estorno de Recebimentos
Lê números de PO da planilha Excel e estorna os recibos no Coupa.

  Primeiro uso (login manual):   python coupa_estorno.py --login
  Uso normal (já logado):        python coupa_estorno.py

Configure as variáveis no arquivo .env (veja .env.example)
"""

import os
import re
import sys
from pathlib import Path

import openpyxl
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

load_dotenv()

COUPA_URL       = os.getenv("COUPA_URL", "https://gpabr.coupahost.com/user/home")
RECEBIMENTO_URL = os.getenv("RECEBIMENTO_URL", "https://gpabr.coupahost.com/receipts/history")
EXCEL_PATH      = Path(os.getenv("EXCEL_PATH", ""))
COLUNA_REQ      = int(os.getenv("COLUNA_REQ", "7"))
USER_DATA_DIR   = Path(os.getenv("USER_DATA_DIR", "./perfil_recebimento")).resolve()
USER_DATA_DIR.mkdir(exist_ok=True, parents=True)


# ============================================================================
# LEITURA DA PLANILHA
# ============================================================================
def ler_pedidos_excel() -> list[str]:
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    pedidos = []
    vistas  = set()
    for row in ws.iter_rows(min_row=2):
        celula = row[COLUNA_REQ - 1]
        if celula.value:
            num = str(celula.value).strip()
            if num not in vistas:
                vistas.add(num)
                pedidos.append(num)
    print(f"{len(pedidos)} número(s) de pedido lido(s) da planilha.")
    return pedidos


# ============================================================================
# FILTRO AVANÇADO
# ============================================================================
def pesquisar_po(page: Page, numero_po: str) -> None:
    painel_visivel = page.locator("[data-cond-col-select='true']").first.is_visible()
    if not painel_visivel:
        print("  Abrindo painel Avançado...")
        try:
            page.locator("a:has(span:text-is('Avançado'))").first.click(timeout=5_000)
        except PlaywrightTimeoutError:
            page.locator("span:text-is('Avançado')").first.click(force=True)
        page.wait_for_timeout(1_500)

    page.locator("[data-cond-col-select='true']").first.select_option(
        value="order_line.order_header.po_number", force=True
    )
    page.wait_for_timeout(1_500)

    page.locator("select.cond_comparator").first.select_option(value="con", force=True)
    page.wait_for_timeout(300)

    page.locator("input[aria-label='Filtrar texto']").first.fill(numero_po, force=True)
    page.wait_for_timeout(200)

    page.locator("button[type='submit'] span:text-is('Pesquisar')").first.click()
    page.wait_for_load_state("load")
    page.wait_for_timeout(800)


# ============================================================================
# ESTORNO
# ============================================================================
def estornar_recibos(page: Page, numero_po: str) -> tuple[int, int]:
    ok   = 0
    erro = 0

    botoes_void = page.locator("img.sprite-arrow_void")
    total = botoes_void.count()

    if total == 0:
        print(f"  ⏭️  Nenhum recibo encontrado para PO {numero_po}.")
        return 0, 0

    print(f"  {total} recibo(s) encontrado(s) para PO {numero_po}.")

    for i in range(total):
        print(f"  → Recibo {i + 1}/{total}")
        try:
            botao = page.locator("img.sprite-arrow_void").first
            if botao.count() == 0:
                botao = page.locator("img[aria-label*='nulo']").first
            botao.wait_for(state="attached", timeout=10_000)
            botao.click(force=True)
            page.wait_for_timeout(1_000)

            campo_qty = page.locator("input#inventory_transaction_voiding_value")
            campo_qty.wait_for(timeout=10_000)
            campo_qty.scroll_into_view_if_needed()
            campo_qty.click()
            campo_qty.fill("1")
            campo_qty.press("Tab")
            page.wait_for_timeout(400)

            checkbox = page.locator("input#inventory_transaction_void_all")
            checkbox.scroll_into_view_if_needed()
            checkbox.click()
            page.wait_for_timeout(400)
            checkbox.click()
            page.wait_for_timeout(400)
            checkbox.click()
            page.wait_for_timeout(400)

            botao_anular = page.locator("span:text-is('Anular recibo')").first
            tentativas = 0
            while tentativas < 3:
                pai = botao_anular.locator("xpath=..")
                desabilitado = (
                    pai.get_attribute("disabled") is not None or
                    "disabled" in (pai.get_attribute("class") or "") or
                    botao_anular.is_disabled()
                )
                if not desabilitado:
                    break
                print(f"     Botão indisponível, repetindo ciclo ({tentativas + 1}/3)...")
                checkbox.click()
                page.wait_for_timeout(400)
                checkbox.click()
                page.wait_for_timeout(400)
                checkbox.click()
                page.wait_for_timeout(400)
                tentativas += 1

            botao_anular.click(force=True)
            page.wait_for_timeout(800)

            try:
                btn_ok = page.locator("button:text-is('OK'), input[value='OK'], a:text-is('OK')").first
                if btn_ok.count() > 0:
                    btn_ok.click()
                    page.wait_for_timeout(500)
            except Exception:
                pass

            page.wait_for_load_state("load")
            page.wait_for_timeout(800)
            print(f"     ✅ Estornado.")
            ok += 1

        except Exception as e:
            print(f"     ❌ Erro: {e}")
            erro += 1
            page.goto(RECEBIMENTO_URL, wait_until="load")
            pesquisar_po(page, numero_po)

    return ok, erro


# ============================================================================
# LOGIN MANUAL
# ============================================================================
def fazer_login_manual(context: BrowserContext) -> None:
    page = context.new_page()
    page.goto(COUPA_URL)
    print("\n>>> Faça login no Coupa nessa janela do Edge.")
    input("\nDepois de logar, volte aqui e aperte Enter para salvar a sessão...")
    print("Sessão salva em:", USER_DATA_DIR)


# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================
def main() -> None:
    modo_login = "--login" in sys.argv

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            channel="msedge",
            headless=False,
        )

        if modo_login:
            fazer_login_manual(context)
            context.close()
            return

        pedidos = ler_pedidos_excel()
        if not pedidos:
            print("Nenhum pedido encontrado na planilha. Encerrando.")
            context.close()
            return

        page = context.pages[0] if context.pages else context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        print("\nAbrindo histórico de recebimentos...")
        page.goto(RECEBIMENTO_URL, wait_until="load")

        total_ok   = 0
        total_erro = 0
        detalhes   = []

        for numero_po in pedidos:
            print(f"\nProcessando PO {numero_po}...")
            try:
                pesquisar_po(page, numero_po)
                ok, erro = estornar_recibos(page, numero_po)
                total_ok   += ok
                total_erro += erro
                detalhes.append((numero_po, ok, erro))
            except Exception as e:
                print(f"  ❌ Erro geral na PO {numero_po}: {e}")
                total_erro += 1
                detalhes.append((numero_po, 0, 1))
                page.goto(RECEBIMENTO_URL, wait_until="load")

        print("\n" + "=" * 52)
        print("📋  RELATÓRIO FINAL — ESTORNO")
        print("=" * 52)
        print(f"  POs processadas           : {len(pedidos)}")
        print(f"  ✅ Recibos estornados      : {total_ok}")
        print(f"  ❌ Erros                  : {total_erro}")
        print("\n  Detalhe por PO:")
        for po, ok, err in detalhes:
            status = f"✅ {ok} estornado(s)" if err == 0 else f"✅ {ok} / ❌ {err} erro(s)"
            print(f"    • {po}  →  {status}")
        print("=" * 52)

        input("\nPressione ENTER para fechar o browser...")
        context.close()


if __name__ == "__main__":
    main()
