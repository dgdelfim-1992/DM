import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import flet as ft
import os
import shutil
import json

from logo_dm import LOGO_DM_BASE64

from database.banco import (
    CAMINHO_BANCO,
    criar_backup_automatico,
    listar_precificacoes,
    listar_historico_precificacao_v2,
    obter_precificacao_v2,
    listar_ingredientes,
    listar_alertas_aumento_ingredientes,
    listar_historico_precos_ingrediente,
    obter_ingrediente,
    salvar_precificacao_v2,
    excluir_precificacao_v2,
    obter_taxa_cartao,
    obter_taxas_pagamento,
    salvar_taxas_pagamento,
    obter_margem_minima,
    salvar_margem_minima,
    obter_markup_ideal,
    salvar_markup_ideal,
    calcular_simulacao_precificacao,
    criar_tabelas,
    salvar_tempos_receita,
    salvar_horas_produtivas_mensais,
    obter_horas_produtivas_mensais,
    obter_custo_fixo_por_hora,
    calcular_custo_fixo_proporcional,
    salvar_precificacao_completa,
    calcular_precificacao_completa,
    salvar_precificacao_produto,
    obter_precificacao_produto,
    calcular_precificacao_produto,
    excluir_ingrediente,
    cadastrar_ingrediente,
    listar_ingredientes,
    obter_ingrediente,
    atualizar_ingrediente,
    cadastrar_receita,
    obter_receita,
    atualizar_receita,
    excluir_receita,
    calcular_custo_receita,
    cadastrar_custo_fixo,
    atualizar_custo_fixo,
    excluir_custo_fixo,
    obter_fator_custo_fixo,
    obter_conexao,
    salvar_orcamento,
    excluir_orcamentos,
    atualizar_orcamento as atualizar_orcamento_salvo,
    listar_versoes_orcamento,
    listar_orcamentos,
    obter_orcamento,
    atualizar_status_orcamento,
    obter_dados_painel,
    listar_agenda_producao,
    atualizar_status_producao,
)


def main(page: ft.Page):

    erro_backup_automatico = None

    try:
        criar_backup_automatico()
    except Exception as erro:
        erro_backup_automatico = str(erro)

    criar_tabelas()

    # ==================================================
    # CONFIGURAÇÕES
    # ==================================================

    page.title = "DM Gulositos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F8F1EF"
    page.padding = 0
    page.window.width = 420
    page.window.height = 850

    MARROM = "#603D3B"
    ROSA = "#A65F72"
    ROSA_CLARO = "#F8EDEB"
    TEXTO_SECUNDARIO = "#876A65"
    BRANCO = "#FFFFFF"

    indice_atual = {"valor": 0}
    ids_orcamentos_selecionados = set()

    # ==================================================
    # UTILITÁRIO SEGURO DE SNACKBAR
    # ==================================================
    def mostrar_aviso(mensagem, cor="#2E7D32"):
        snack = ft.SnackBar(content=ft.Text(mensagem, color=BRANCO), bgcolor=cor)
        try:
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except Exception:
            try:
                page.snack_bar = snack
                page.snack_bar.open = True
                page.update()
            except Exception:
                pass

    if erro_backup_automatico:
        mostrar_aviso(
            f"Não foi possível criar o backup automático: {erro_backup_automatico}",
            "#C62828"
        )


    # ==================================================
    # COMPONENTES VISUAIS PADRONIZADOS
    # ==================================================
    def criar_campo_padrao(**kwargs):
        kwargs.setdefault(
            "border",
            {
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=1, color=ROSA_CLARO),
                ),
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=2, color=ROSA),
                ),
            },
        )
        kwargs.setdefault("cursor_color", ROSA)
        kwargs.setdefault("label_style", ft.TextStyle(color=TEXTO_SECUNDARIO))
        return ft.TextField(**kwargs)

    def criar_dropdown_padrao(**kwargs):
        kwargs.setdefault(
            "border",
            {
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=1, color=ROSA_CLARO),
                ),
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=2, color=ROSA),
                ),
            },
        )
        kwargs.setdefault("label_style", ft.TextStyle(color=TEXTO_SECUNDARIO))
        return ft.Dropdown(**kwargs)

    def criar_dialogo_padrao(*args, **kwargs):
        kwargs.setdefault("bgcolor", BRANCO)
        kwargs.setdefault("shape", ft.RoundedRectangleBorder(radius=18))
        return ft.AlertDialog(*args, **kwargs)


    def criar_cabecalho_padrao(titulo, subtitulo, acao_voltar):
        return ft.Container(
            padding=ft.Padding.only(left=18, right=18, top=20, bottom=4),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        bgcolor=ROSA_CLARO,
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        on_click=acao_voltar,
                        content=ft.Icon(
                            ft.Icons.ARROW_BACK_ROUNDED,
                            color=MARROM,
                            size=22,
                        ),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Text(
                                titulo,
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                            ft.Text(
                                subtitulo,
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                        ],
                    ),
                ],
            ),
        )

    def criar_botao_primario(texto, acao, icone=ft.Icons.ADD):
        return ft.Container(
            height=52,
            padding=ft.Padding.symmetric(horizontal=16),
            bgcolor=ROSA,
            border_radius=14,
            on_click=acao,
            alignment=ft.Alignment(0, 0),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=9,
                controls=[
                    ft.Icon(icone, color=BRANCO, size=21),
                    ft.Text(
                        texto,
                        color=BRANCO,
                        weight=ft.FontWeight.BOLD,
                        size=14,
                    ),
                ],
            ),
        )

    # ==================================================
    # BACKUP E RESTAURAÇÃO SEGURA DO BANCO
    # ==================================================

    def criar_copia_sqlite(origem, destino):
        """Cria uma cópia consistente usando o próprio SQLite."""

        origem = Path(origem)
        destino = Path(destino)

        destino.parent.mkdir(parents=True, exist_ok=True)

        conexao_origem = sqlite3.connect(str(origem))
        conexao_destino = sqlite3.connect(str(destino))

        try:
            conexao_origem.backup(conexao_destino)
            conexao_destino.commit()
        finally:
            conexao_destino.close()
            conexao_origem.close()

    def gerar_backup_bytes():
        """Gera o arquivo de backup para exportação."""

        if not CAMINHO_BANCO.exists():
            raise FileNotFoundError("Banco de dados não encontrado.")

        with tempfile.TemporaryDirectory() as pasta:
            arquivo_temp = Path(pasta) / "backup_gulositos.db"

            criar_copia_sqlite(CAMINHO_BANCO, arquivo_temp)

            return arquivo_temp.read_bytes()

    def validar_banco(caminho):
        """Verifica se o arquivo é um banco SQLite íntegro."""

        conexao = sqlite3.connect(
            f"file:{Path(caminho).resolve().as_posix()}?mode=ro",
            uri=True
        )

        try:
            resultado = conexao.execute(
                "PRAGMA integrity_check"
            ).fetchone()

            if not resultado or resultado[0] != "ok":
                raise ValueError("O banco está corrompido.")

            tabelas = {
                linha[0]
                for linha in conexao.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }

            obrigatorias = {
                "ingredientes",
                "receitas",
                "configuracoes"
            }

            if not obrigatorias.issubset(tabelas):
                raise ValueError(
                    "O arquivo selecionado não pertence à DM Gulositos."
                )

        finally:
            conexao.close()

    def restaurar_banco_bytes(conteudo):
        """Valida, protege o banco atual e restaura o selecionado."""

        if not conteudo:
            raise ValueError("O arquivo selecionado está vazio.")

        CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)

        arquivo_temp = None

        try:
            # 1. Salva o arquivo selecionado temporariamente
            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".db",
                prefix="restauracao_",
                dir=CAMINHO_BANCO.parent,
                delete=False
            ) as arquivo:

                arquivo.write(conteudo)
                arquivo_temp = Path(arquivo.name)

            # 2. Valida o backup antes de mexer no banco atual
            validar_banco(arquivo_temp)

            # 3. Finaliza eventuais operações pendentes do banco atual
            if CAMINHO_BANCO.exists():

                conexao = sqlite3.connect(str(CAMINHO_BANCO))

                try:
                    conexao.execute(
                        "PRAGMA wal_checkpoint(TRUNCATE)"
                    )
                finally:
                    conexao.close()

                # 4. Cria uma cópia automática de segurança
                pasta_backups = CAMINHO_BANCO.parent / "backups"
                pasta_backups.mkdir(parents=True, exist_ok=True)

                data = datetime.now().strftime("%Y%m%d_%H%M%S")

                backup_atual = (
                    pasta_backups /
                    f"antes_restauracao_{data}.db"
                )

                criar_copia_sqlite(
                    CAMINHO_BANCO,
                    backup_atual
                )

                # 5. Remove arquivos auxiliares do banco anterior
                for sufixo in ("-wal", "-shm"):
                    auxiliar = Path(str(CAMINHO_BANCO) + sufixo)

                    if auxiliar.exists():
                        auxiliar.unlink()

            # 6. Substitui o banco somente depois de validar
            os.replace(arquivo_temp, CAMINHO_BANCO)
            arquivo_temp = None

        finally:
            if arquivo_temp and arquivo_temp.exists():
                arquivo_temp.unlink()

    # ==================================================
    # FILE PICKER - COMPATÍVEL COM FLET 1.0+
    # ==================================================

    picker_salvar = ft.FilePicker()
    picker_restaurar = ft.FilePicker()

    page.services.append(picker_salvar)
    page.services.append(picker_restaurar)

    async def acionar_exportar(e):
        try:
            # Gera uma cópia consistente do banco
            dados_backup = gerar_backup_bytes()

            # Abre o salvamento nativo
            caminho = await picker_salvar.save_file(
                dialog_title="Salvar Backup DM Gulositos",
                file_name="backup_gulositos.db",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["db"],
                src_bytes=dados_backup
            )

            if caminho is not None or page.web:
                mostrar_aviso(
                    "Backup exportado com sucesso!",
                    "#2E7D32"
                )

        except Exception as erro:
            mostrar_aviso(
                f"Erro ao exportar backup: {erro}",
                "#C62828"
            )

    async def acionar_importar(e):
        try:
            arquivos = await picker_restaurar.pick_files(
                dialog_title="Selecionar Backup DM Gulositos",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["db"],
                allow_multiple=False,
                with_data=True
            )

            if not arquivos:
                return

            arquivo = arquivos[0]

            if not arquivo.bytes:
                raise ValueError(
                    "Não foi possível ler o conteúdo do arquivo."
                )

            restaurar_banco_bytes(arquivo.bytes)

            mostrar_aviso(
                "Backup restaurado! Feche e abra novamente o aplicativo.",
                "#2E7D32"
            )

        except Exception as erro:
            mostrar_aviso(
                f"Erro ao restaurar backup: {erro}",
                "#C62828"
            )

    # ==================================================
    # NAVEGAÇÃO
    # ==================================================

    def voltar_inicio(e=None):
        nonlocal conteudo
        indice_atual["valor"] = 0
        navegacao.selected_index = 0
        conteudo = montar_painel_inicial()
        page.controls.clear()
        page.add(conteudo)
        page.update()

    def navegar(e):
        indice = e.control.selected_index

        if indice == 0:
            voltar_inicio()
        elif indice == 1:
            abrir_precificacao()
        elif indice == 2:
            abrir_menu_opcoes()
        else:
            navegacao.selected_index = indice_atual["valor"]
            page.update()

    # ==================================================
    # MENU DE OPÇÕES (SUBSTITUI A BARRA INFERIOR ANTIGA)
    # ==================================================

    # ==================================================
    # AGENDA DE PRODUÇÃO
    # ==================================================
    def abrir_agenda_producao(e=None):
        filtro = {"valor": "Todos"}
        filtro_data = {"valor": "Todas"}

        def formatar_reais(valor):
            return ("R$ {:,.2f}".format(valor)).replace(",", "X").replace(".", ",").replace("X", ".")

        def obter_data_entrega(valor):
            try:
                return datetime.strptime(valor[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        def formatar_data(valor):
            data = obter_data_entrega(valor)
            return data.strftime("%d/%m/%Y") if data else (valor or "Sem data")

        conteudo = ft.Column(spacing=10)

        def aplicar_filtro(valor):
            filtro["valor"] = valor
            montar_agenda()

        def aplicar_filtro_data(valor):
            filtro_data["valor"] = valor
            montar_agenda()

        def montar_agenda():
            registros = listar_agenda_producao()
            hoje = datetime.now().date()
            limite_proximos_dias = hoje + timedelta(days=7)

            if filtro["valor"] != "Todos":
                registros = [
                    registro for registro in registros
                    if (registro["status_producao"] or "Pendente") == filtro["valor"]
                ]

            if filtro_data["valor"] == "Hoje":
                registros = [
                    registro for registro in registros
                    if obter_data_entrega(registro["data_entrega"]) == hoje
                ]
            elif filtro_data["valor"] == "Próximos 7 dias":
                registros = [
                    registro for registro in registros
                    if (obter_data_entrega(registro["data_entrega"]) is not None
                        and hoje < obter_data_entrega(registro["data_entrega"]) <= limite_proximos_dias)
                ]
            elif filtro_data["valor"] == "Atrasadas":
                registros = [
                    registro for registro in registros
                    if (obter_data_entrega(registro["data_entrega"]) is not None
                        and obter_data_entrega(registro["data_entrega"]) < hoje
                        and (registro["status_producao"] or "Pendente") != "Concluída")
                ]

            # Entregas mais próximas aparecem primeiro; registros sem data ficam no final.
            registros.sort(
                key=lambda registro: (
                    obter_data_entrega(registro["data_entrega"]) is None,
                    obter_data_entrega(registro["data_entrega"]) or hoje,
                )
            )

            cartoes = []
            for registro in registros:
                data_texto = formatar_data(registro["data_entrega"])
                data_entrega_obj = obter_data_entrega(registro["data_entrega"])
                status_atual = registro["status_producao"] or "Pendente"
                atrasada = (
                    data_entrega_obj is not None
                    and data_entrega_obj < hoje
                    and status_atual != "Concluída"
                )
                entrega_hoje = (
                    data_entrega_obj == hoje
                    and status_atual != "Concluída"
                )
                cor_cartao = "#FDECEC" if atrasada else ("#FFF4E5" if entrega_hoje else BRANCO)
                texto_data = "ATRASADA" if atrasada else ("ENTREGA HOJE" if entrega_hoje else data_texto)
                cor_data = "#C62828" if atrasada else ( "#A65F00" if entrega_hoje else ROSA)

                try:
                    itens = json.loads(registro["itens_json"] or "[]")
                    nomes_itens = [
                        f'{item.get("quantidade", 1):g} {item.get("unidade", "un")} - {item.get("nome", "Produto")}'
                        for item in itens
                    ]
                except (ValueError, TypeError):
                    nomes_itens = []

                def alterar_status(ev, oid=registro["id"]):
                    try:
                        atualizar_status_producao(oid, ev.control.value)
                        montar_agenda()
                        mostrar_aviso("Status da produção atualizado.")
                    except Exception as erro:
                        mostrar_aviso(f"Não foi possível atualizar: {erro}", "#C62828")

                cartoes.append(
                    ft.Container(
                        bgcolor=cor_cartao,
                        padding=15,
                        border_radius=16,
                        content=ft.Column(spacing=8, controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f'Encomenda {registro["numero"]}', weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(
                                        texto_data,
                                        color=cor_data,
                                        weight=ft.FontWeight.BOLD,
                                        size=12,
                                    ),
                                ],
                            ),
                            ft.Text(registro["cliente"] or "Cliente não informado", color=TEXTO_SECUNDARIO, size=12),
                            ft.Text("Produtos: " + (", ".join(nomes_itens) if nomes_itens else "Consulte os detalhes do orçamento"), color=MARROM, size=12),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Total: " + formatar_reais(registro["total_final_centavos"] / 100),
                                        color=MARROM,
                                        weight=ft.FontWeight.BOLD,
                                        size=12,
                                    ),
                                    ft.Dropdown(
                                        width=155,
                                        dense=True,
                                        value=registro["status_producao"] or "Pendente",
                                        options=[
                                            ft.dropdown.Option("Pendente"),
                                            ft.dropdown.Option("Em produção"),
                                            ft.dropdown.Option("Concluída"),
                                        ],
                                        on_select=alterar_status,
                                    ),
                                ],
                            ),
                        ]),
                    )
                )

            if not cartoes:
                cartoes.append(
                    ft.Container(
                        bgcolor=BRANCO,
                        padding=22,
                        border_radius=16,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=38, color=ROSA),
                                ft.Text("Nenhuma encomenda encontrada.", color=MARROM, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    "A agenda mostra orçamentos aprovados que tenham data de entrega.",
                                    color=TEXTO_SECUNDARIO,
                                    size=12,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                        ),
                    )
                )

            conteudo.controls = [
                ft.Text("Filtrar por status", color=MARROM, weight=ft.FontWeight.BOLD, size=13),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(
                            nome,
                            on_click=lambda ev, valor=nome: aplicar_filtro(valor),
                            bgcolor=ROSA if filtro["valor"] == nome else ROSA_CLARO,
                            color=BRANCO if filtro["valor"] == nome else MARROM,
                        )
                        for nome in ["Todos", "Pendente", "Em produção", "Concluída"]
                    ],
                ),
                ft.Text("Filtrar por data de entrega", color=MARROM, weight=ft.FontWeight.BOLD, size=13),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(
                            nome,
                            on_click=lambda ev, valor=nome: aplicar_filtro_data(valor),
                            bgcolor=ROSA if filtro_data["valor"] == nome else ROSA_CLARO,
                            color=BRANCO if filtro_data["valor"] == nome else MARROM,
                        )
                        for nome in ["Todas", "Hoje", "Próximos 7 dias", "Atrasadas"]
                    ],
                ),
                *cartoes,
            ]
            page.update()

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=18, top=18, bottom=6),
                    content=ft.Row(controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MARROM, on_click=abrir_menu_opcoes),
                        ft.Text("Agenda de Produção", size=22, weight=ft.FontWeight.BOLD, color=MARROM),
                    ]),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=conteudo,
                ),
            ],
        )
        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        montar_agenda()

    def abrir_menu_opcoes(e=None):
        def criar_card_menu(icone, titulo, descricao, acao):
            return ft.Container(
                expand=True,
                height=142,
                padding=14,
                bgcolor=BRANCO,
                border_radius=18,
                on_click=acao,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=9,
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            border_radius=12,
                            bgcolor=ROSA_CLARO,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(icone, color=ROSA, size=23),
                        ),
                        ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color=MARROM),
                        ft.Text(descricao, size=10, color=TEXTO_SECUNDARIO),
                    ],
                ),
            )

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=18, right=18, top=22, bottom=2),
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("Menu Principal", size=24, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text("Acesse as ferramentas da sua doceria.", size=12, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Row(
                                spacing=12,
                                controls=[
                                    criar_card_menu(ft.Icons.INVENTORY_2_OUTLINED, "Insumos", "Gerenciar estoque e preços", abrir_ingredientes),
                                    criar_card_menu(ft.Icons.MENU_BOOK_OUTLINED, "Receitas", "Fichas técnicas e tempos", abrir_receitas),
                                ],
                            ),
                            ft.Row(
                                spacing=12,
                                controls=[
                                    criar_card_menu(ft.Icons.CALCULATE_OUTLINED, "Custos Fixos", "Despesas, rateio e taxas", abrir_custos_fixos),
                                    criar_card_menu(ft.Icons.DESCRIPTION_OUTLINED, "Orçamentos", "Montar e enviar propostas", abrir_orcamentos),
                                ],
                            ),
                            ft.Row(
                                spacing=12,
                                controls=[
                                    criar_card_menu(ft.Icons.CALENDAR_MONTH_OUTLINED, "Agenda de Produção", "Organizar encomendas e entregas", abrir_agenda_producao),
                                    criar_card_menu(ft.Icons.BAR_CHART_OUTLINED, "Relatórios", "Análise de lucratividade", abrir_relatorios),
                                ],
                            ),
                            ft.Row(
                                spacing=12,
                                controls=[
                                    criar_card_menu(ft.Icons.SAVE_OUTLINED, "Backup / Exportar", "Salvar e restaurar dados", abrir_tela_backup),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        )
        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # TELA DE BACKUP
    # ==================================================

    def abrir_tela_backup(e=None):
        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=10),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=abrir_menu_opcoes,
                                content=ft.Icon(ft.Icons.ARROW_BACK, color=MARROM, size=24),
                            ),
                            ft.Text("Backup e Restauração", size=22, weight=ft.FontWeight.BOLD, color=MARROM),
                        ]
                    )
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            ft.Text(
                                "Mantenha seus dados seguros. Faça cópias regulares e guarde na nuvem (Google Drive, OneDrive).",
                                color=TEXTO_SECUNDARIO,
                                size=13
                            ),
                            # Botão de Exportar
                            ft.Container(
                                bgcolor=BRANCO,
                                padding=20,
                                border_radius=16,
                                on_click=acionar_exportar,
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.DOWNLOAD_FOR_OFFLINE, color=ROSA, size=40),
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text("Fazer Backup (Exportar)", weight=ft.FontWeight.BOLD, color=MARROM, size=16),
                                                ft.Text("Salva uma cópia dos dados no PC", color=TEXTO_SECUNDARIO, size=12)
                                            ]
                                        )
                                    ]
                                )
                            ),
                            # Botão de Importar
                            ft.Container(
                                bgcolor=BRANCO,
                                padding=20,
                                border_radius=16,
                                on_click=acionar_importar,
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.UPLOAD_FILE, color="#C62828", size=40),
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text("Restaurar Dados (Importar)", weight=ft.FontWeight.BOLD, color=MARROM, size=16),
                                                ft.Text("Substitui tudo pelo backup selecionado", color=TEXTO_SECUNDARIO, size=12)
                                            ]
                                        )
                                    ]
                                )
                            ),
                        ]
                    )
                )
            ]
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # PRECIFICAÇÃO (ESTILO LISTA + FORMULÁRIO DETALHADO)
    # ==================================================

    
    def abrir_historico_precificacao(prec_id, nome):
        historico = listar_historico_precificacao_v2(prec_id)

        controles = []

        if not historico:
            controles.append(
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "Ainda não existem registros de histórico.",
                        color=TEXTO_SECUNDARIO,
                        text_align=ft.TextAlign.CENTER,
                    )
                )
            )

        for item in historico:
            data = item["registrado_em"].replace("T", " ")

            controles.append(
                ft.Container(
                    bgcolor=ROSA_CLARO,
                    padding=14,
                    border_radius=12,
                    content=ft.Column(
                        spacing=7,
                        controls=[
                            ft.Text(
                                data,
                                size=11,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Divider(color=ROSA),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Custo dos insumos", size=12),
                                    ft.Text(
                                        f"R$ {item['custo_insumo_centavos']/100:.2f}",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Custo fixo", size=12),
                                    ft.Text(
                                        f"R$ {item['custo_fixo_centavos']/100:.2f}",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Custo total", size=12),
                                    ft.Text(
                                        f"R$ {item['custo_total_centavos']/100:.2f}",
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                ],
                            ),
                            ft.Divider(color=ROSA),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Preço sugerido", size=12),
                                    ft.Text(
                                        f"R$ {item['preco_sugerido_centavos']/100:.2f}",
                                        weight=ft.FontWeight.BOLD,
                                        color=ROSA,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Preço praticado", size=12),
                                    ft.Text(
                                        f"R$ {item['preco_praticado_centavos']/100:.2f}",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Markup aplicado", size=12),
                                    ft.Text(
                                        f"{item['markup_aplicado_pct']:.1f}%",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Margem de contribuição", size=12),
                                    ft.Text(
                                        f"R$ {item['margem_contribuicao_centavos']/100:.2f}",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"Status: {item['status']}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color="#2E7D32" if item["status"] == "Dentro da Margem" else "#C62828",
                            ),
                        ],
                    ),
                )
            )

        def fechar_dialogo(e):
            dialogo.open = False
            page.update()

        dialogo = criar_dialogo_padrao(
            modal=True,
            title=ft.Text(
                f"Histórico — {nome}",
                color=MARROM,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    controls=controles,
                    spacing=12,
                    height=450,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Fechar", on_click=fechar_dialogo),
            ],
        )

        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()


    def abrir_precificacao(e=None):
        precificacoes = listar_precificacoes()
        cartoes = []

        def solicitar_exclusao_prec(prec_id, nome):
            def confirmar_exclusao(e):
                dialogo.open = False
                page.update()
                excluir_precificacao_v2(prec_id)
                abrir_precificacao()

            def cancelar(e):
                dialogo.open = False
                page.update()

            dialogo = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Excluir Precificação"),
                content=ft.Text(f"Deseja excluir a precificação de {nome}?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar),
                    ft.TextButton("Excluir", on_click=confirmar_exclusao, style=ft.ButtonStyle(color="#B00020")),
                ],
            )
            page.overlay.append(dialogo)
            dialogo.open = True
            page.update()

        # Obter taxa do cartão uma única vez para usar nos cálculos da lista
        taxa_cartao = obter_taxa_cartao()

        for prec in precificacoes:
            preco_praticado = prec['preco_praticado_centavos'] / 100
            
            # Recalcular os dados para descobrir o status da margem
            # Passando os argumentos na ordem correta (posicional) sem os nomes
            res = calcular_simulacao_precificacao(
                prec['receita_id'],
                prec['quantidade_embalagem'],
                prec['custo_embalagem_centavos'],
                prec['markup_ideal_pct'],
                prec['preco_praticado_centavos'],
                taxa_cartao
            )

            # Definir cores baseadas no status
            if res:
                status_txt = res['status']
                cor_status = "#2E7D32" if status_txt == "Dentro da Margem" else "#C62828"
                fundo_status = "#E8F5E9" if status_txt == "Dentro da Margem" else "#FFEBEE"
            else:
                status_txt = "Erro"
                cor_status = TEXTO_SECUNDARIO
                fundo_status = ROSA_CLARO

            cartoes.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=16,
                    border_radius=16,
                    on_click=lambda e, pid=prec['id']: abrir_edicao_precificacao(pid),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        prec["nome_receita"],
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.HISTORY,
                                                icon_color=MARROM,
                                                tooltip="Ver histórico",
                                                on_click=lambda e, pid=prec["id"], n=prec["nome_receita"]: abrir_historico_precificacao(pid, n),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.EDIT_OUTLINED,
                                                icon_color=ROSA,
                                                on_click=lambda e, pid=prec["id"]: abrir_edicao_precificacao(pid),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Divider(color=ROSA_CLARO, height=1),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text("Preço Praticado:", size=11, color=TEXTO_SECUNDARIO),
                                            ft.Text(f"R$ {preco_praticado:.2f}", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                                        ]
                                    ),
                                    # "Etiqueta" visual para o status
                                    ft.Container(
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                        bgcolor=fundo_status,
                                        border_radius=8,
                                        content=ft.Text(status_txt, size=11, weight=ft.FontWeight.BOLD, color=cor_status)
                                    )
                                ]
                            ),
                        ]
                    )
                ),
            )

        if not cartoes:
            cartoes.append(
                ft.Container(
                    padding=25, bgcolor=BRANCO, border_radius=16,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.PRICE_CHANGE_OUTLINED, size=40, color=ROSA),
                            ft.Text("Nenhuma precificação salva.", color=MARROM),
                        ]
                    )
                )
            )

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=10),
                    content=ft.Row(
                        controls=[
                            ft.Container(padding=8, border_radius=10, on_click=voltar_inicio, content=ft.Icon(ft.Icons.ARROW_BACK, color=MARROM, size=24)),
                            ft.Text("Precificação", size=23, weight=ft.FontWeight.BOLD, color=MARROM),
                        ]
                    )
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        width=380, padding=14, bgcolor=ROSA, border_radius=12,
                        on_click=lambda e: abrir_edicao_precificacao(),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ADD, color=BRANCO),
                                ft.Text("Nova Precificação", color=BRANCO, weight=ft.FontWeight.BOLD),
                            ]
                        )
                    )
                ),
                ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Column(spacing=12, controls=cartoes))
            ]
        )
        indice_atual["valor"] = 1
        navegacao.selected_index = 1
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # ORÇAMENTOS
    # ==================================================
    def abrir_orcamentos(e=None, orcamento_id=None, filtro_status=None):
        filtro_status_atual = {"valor": filtro_status or "Todos"}
        registro_edicao = obter_orcamento(orcamento_id) if orcamento_id else None
        precificacoes = listar_precificacoes()
        taxas = obter_taxas_pagamento()
        margem_minima = obter_margem_minima()
        modalidades = [
            ("Dinheiro", "dinheiro"),
            ("Pix", "pix"),
            ("Cartão de débito", "debito"),
            ("Crédito à vista", "credito_avista"),
            ("Crédito parcelado", "credito_parcelado"),
        ]
        produtos = {}
        for prec in precificacoes:
            resultado = calcular_simulacao_precificacao(
                prec["receita_id"],
                prec["quantidade_embalagem"],
                prec["custo_embalagem_centavos"],
                prec["markup_ideal_pct"],
                prec["preco_praticado_centavos"],
                taxas.get("credito_avista", 0),
                margem_minima,
            )
            if resultado:
                preco_base = (
                    resultado["preco_praticado"]
                    if resultado["preco_praticado"] > 0
                    else resultado["preco_sugerido"]
                )
                produtos[str(prec["id"])] = {
                    "precificacao_id": prec["id"],
                    "receita_id": prec["receita_id"],
                    "nome": prec["nome_receita"],
                    "unidade": prec["unidade_rendimento"] or "un",
                    "quantidade_embalagem": float(prec["quantidade_embalagem"]),
                    "custo": float(resultado["custo_total"]),
                    "preco_base": float(preco_base),
                }

        def formatar_reais(valor):
            return ("R$ {:,.2f}".format(valor)).replace(",", "X").replace(".", ",").replace("X", ".")

        def alternar_selecao_orcamento(orcamento_id, selecionado):
            if selecionado:
                ids_orcamentos_selecionados.add(orcamento_id)
            else:
                ids_orcamentos_selecionados.discard(orcamento_id)

        def executar_exclusao(dialogo, ids):
            fechar_dialogo(dialogo)
            try:
                quantidade = excluir_orcamentos(ids)
                ids_orcamentos_selecionados.difference_update(ids)
                mostrar_aviso(f"{quantidade} orçamento(s) excluído(s) com sucesso.")
                montar_tela_historico(filtro_status_atual["valor"])
            except Exception as erro:
                mostrar_aviso(f"Não foi possível excluir os orçamentos: {erro}", "#C62828")

        def confirmar_exclusao_orcamentos(orcamento_ids):
            ids = list(dict.fromkeys(int(valor) for valor in orcamento_ids))
            if not ids:
                mostrar_aviso("Selecione pelo menos um orçamento para excluir.", "#C62828")
                return
            quantidade = len(ids)
            def abrir_confirmacao_final(e=None):
                fechar_dialogo(dlg_primeira_confirmacao)
                dlg_final = criar_dialogo_padrao(
                    modal=True,
                    title=ft.Text("Confirmação final"),
                    content=ft.Text(
                        f"Esta ação é permanente. Deseja realmente excluir {quantidade} "
                        f"orçamento(s), incluindo seus itens e histórico de alterações?"
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda ev: fechar_dialogo(dlg_final)),
                        ft.Button("Excluir definitivamente", icon=ft.Icons.DELETE_FOREVER, bgcolor="#A52D35", color=BRANCO, on_click=lambda ev: executar_exclusao(dlg_final, ids)),
                    ],
                )
                page.overlay.append(dlg_final)
                dlg_final.open = True
                page.update()
            dlg_primeira_confirmacao = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Excluir orçamento(s)?"),
                content=ft.Text(f"Você selecionou {quantidade} orçamento(s). Deseja continuar para a confirmação final?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda ev: fechar_dialogo(dlg_primeira_confirmacao)),
                    ft.Button("Continuar", on_click=abrir_confirmacao_final),
                ],
            )
            page.overlay.append(dlg_primeira_confirmacao)
            dlg_primeira_confirmacao.open = True
            page.update()
        def montar_tela_historico(filtro_status=None):
            if filtro_status is not None:
                filtro_status_atual["valor"] = filtro_status
            status_selecionado = filtro_status_atual["valor"]
            registros = listar_orcamentos()
            if status_selecionado != "Todos":
                registros = [r for r in registros if r["status"] == status_selecionado]
            cards = []
            for registro in registros:
                total = registro["total_final_centavos"] / 100
                cores_status = {
                    "Aprovado": ("#D1F0D5", "#1B5E20"),
                    "Recusado": ("#FCE8E8", "#A52D35"),
                    "Enviado": ("#E8F1FA", "#285A83"),
                    "Em elaboração": ("#FFF3E0", "#8A5A16"),
                }
                cor_fundo, cor_texto = cores_status.get(registro["status"], (BRANCO, MARROM))
                cards.append(
                    ft.Container(
                        bgcolor=cor_fundo, padding=14, border_radius=14,
                        content=ft.Column(spacing=7, controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                                ft.Text(f'Orçamento {registro["numero"]}', weight=ft.FontWeight.BOLD, color=MARROM),
                                ft.Row(spacing=4, controls=[
                                    ft.Text(registro["status"], size=11, weight=ft.FontWeight.BOLD, color=cor_texto),
                                    ft.Checkbox(value=registro["id"] in ids_orcamentos_selecionados, tooltip="Selecionar para exclusão em lote", on_change=lambda ev, oid=registro["id"]: alternar_selecao_orcamento(oid, ev.control.value)),
                                ]),
                            ]),
                            ft.Text(registro["cliente"] or "Cliente não informado", color=TEXTO_SECUNDARIO, size=12),
                            ft.Text(f"Total do orçamento (Pix): {formatar_reais(total)}", weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Row(wrap=True, spacing=4, controls=[
                                ft.IconButton(
                                    icon=ft.Icons.VISIBILITY,
                                    tooltip="Abrir / copiar orçamento",
                                    icon_color=MARROM,
                                    on_click=lambda ev, oid=registro["id"]: abrir_detalhe_orcamento(oid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar orçamento",
                                    icon_color=MARROM,
                                    on_click=lambda ev, oid=registro["id"]: abrir_orcamentos(orcamento_id=oid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.HISTORY,
                                    tooltip="Histórico de alterações",
                                    icon_color=MARROM,
                                    on_click=lambda ev, oid=registro["id"]: abrir_historico_versoes(oid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.SEND,
                                    tooltip="Marcar como enviado",
                                    icon_color="#285A83",
                                    on_click=lambda ev, oid=registro["id"]: mudar_status_orcamento(oid, "Enviado"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CHECK_CIRCLE,
                                    tooltip="Aprovar orçamento",
                                    icon_color="#1B5E20",
                                    on_click=lambda ev, oid=registro["id"]: mudar_status_orcamento(oid, "Aprovado"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CANCEL,
                                    tooltip="Recusar orçamento",
                                    icon_color="#A52D35",
                                    on_click=lambda ev, oid=registro["id"]: mudar_status_orcamento(oid, "Recusado"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="Excluir orçamento",
                                    icon_color="#A52D35",
                                    on_click=lambda ev, oid=registro["id"]: confirmar_exclusao_orcamentos([oid]),
                                ),
                            ]),
                        ])
                    )
                )
            if not cards:
                mensagem_vazia = (
                    "Nenhum orçamento encontrado com este status."
                    if status_selecionado != "Todos"
                    else "Nenhum orçamento salvo ainda."
                )
                cards.append(ft.Text(mensagem_vazia, color=TEXTO_SECUNDARIO))

            opcoes_filtro = ["Todos", "Aprovado", "Em elaboração", "Recusado", "Enviado"]
            botoes_filtro = ft.Row(
                wrap=True,
                spacing=6,
                controls=[
                    ft.Button(
                        texto,
                        on_click=lambda ev, status=texto: montar_tela_historico(status),
                        bgcolor=ROSA if texto == status_selecionado else ROSA_CLARO,
                        color=BRANCO if texto == status_selecionado else MARROM,
                    )
                    for texto in opcoes_filtro
                ],
            )
            tela = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
                cabecalho_orcamentos("Histórico de orçamentos", abrir_orcamentos),
                ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Column(spacing=8, controls=[
                    ft.Text("Filtrar por status", size=12, weight=ft.FontWeight.BOLD, color=MARROM),
                    botoes_filtro,
                ])),
                ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("Selecione para excluir em lote", size=11, color=TEXTO_SECUNDARIO),
                    ft.TextButton("Excluir selecionados", icon=ft.Icons.DELETE, on_click=lambda ev: confirmar_exclusao_orcamentos(sorted(ids_orcamentos_selecionados))),
                ])),
                ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Column(spacing=12, controls=cards)),
            ])
            page.controls.clear()
            page.add(tela)
            page.update()

        def mudar_status_orcamento(orcamento_id, status):
            atualizar_status_orcamento(orcamento_id, status)
            mostrar_aviso(f"Orçamento atualizado: {status}.")
            montar_tela_historico(filtro_status_atual["valor"])

        def abrir_historico_versoes(orcamento_id):
            versoes = listar_versoes_orcamento(orcamento_id)

            def visualizar_versao(mensagem, numero_versao):
                dlg = criar_dialogo_padrao(
                    modal=True,
                    title=ft.Text(f"Versão anterior — {numero_versao}"),
                    content=ft.Container(
                        width=380,
                        content=criar_campo_padrao(value=mensagem, multiline=True, min_lines=10, max_lines=18, read_only=True)
                    ),
                    actions=[ft.TextButton("Fechar", on_click=lambda ev: fechar_dialogo(dlg))]
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

            controles = []
            for versao in versoes:
                dados_anteriores = json.loads(versao["snapshot_json"])
                data_versao = versao["registrado_em"].replace("T", " ")
                controles.append(
                    ft.Container(
                        bgcolor=ROSA_CLARO, padding=10, border_radius=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(expand=True, spacing=2, controls=[
                                    ft.Text(data_versao, size=11, color=MARROM),
                                    ft.Text(f'Total Pix: {formatar_reais(dados_anteriores["total_final_centavos"] / 100)}', size=12, weight=ft.FontWeight.BOLD, color=MARROM),
                                ]),
                                ft.TextButton("Ver versão", on_click=lambda ev, msg=dados_anteriores["mensagem"], num=versao["numero"]: visualizar_versao(msg, num)),
                            ]
                        )
                    )
                )
            if not controles:
                controles.append(ft.Text("Este orçamento ainda não possui versões anteriores.", color=TEXTO_SECUNDARIO))
            dlg_historico = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Histórico de alterações"),
                content=ft.Container(width=400, content=ft.Column(controls=controles, spacing=8, scroll=ft.ScrollMode.AUTO)),
                actions=[ft.TextButton("Fechar", on_click=lambda ev: fechar_dialogo(dlg_historico))]
            )
            page.overlay.append(dlg_historico)
            dlg_historico.open = True
            page.update()

        def abrir_detalhe_orcamento(orcamento_id):
            registro = obter_orcamento(orcamento_id)
            if not registro:
                mostrar_aviso("Orçamento não encontrado.", "#C62828")
                return
            mensagem = registro["mensagem"]
            texto = criar_campo_padrao(value=mensagem, multiline=True, min_lines=12, max_lines=22, read_only=True)
            dialogo = criar_dialogo_padrao(
                modal=True,
                title=ft.Text(f'Orçamento {registro["numero"]}'),
                content=ft.Container(width=380, content=texto),
                actions=[
                    ft.TextButton("Editar orçamento", on_click=lambda ev: (fechar_dialogo(dialogo), abrir_orcamentos(orcamento_id=orcamento_id))),
                    ft.TextButton("Histórico de alterações", on_click=lambda ev: abrir_historico_versoes(orcamento_id)),
                    ft.TextButton("Fechar", on_click=lambda ev: fechar_dialogo(dialogo)),
                    ft.Button(
                        "Copiar mensagem",
                        icon=ft.Icons.CONTENT_COPY,
                        action=ft.CopyToClipboard(mensagem),
                        on_click=lambda ev: mostrar_aviso("Texto do orçamento copiado. Pode colar no WhatsApp."),
                    ),
                ],
            )
            page.overlay.append(dialogo)
            dialogo.open = True
            page.update()

        def fechar_dialogo(dialogo):
            dialogo.open = False
            page.update()

        def cabecalho_orcamentos(titulo, voltar):
            return ft.Container(
                padding=ft.Padding.only(left=15, right=18, top=18, bottom=8),
                content=ft.Row(controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MARROM, on_click=voltar),
                    ft.Text(titulo, size=21, weight=ft.FontWeight.BOLD, color=MARROM),
                ])
            )

        if not produtos and not registro_edicao:
            mostrar_aviso("Cadastre e salve a precificação de pelo menos um Produto Final.", "#C62828")
            return

        cliente = criar_campo_padrao(label="Nome do cliente (opcional)", value=(registro_edicao["cliente"] or "") if registro_edicao else "", border_radius=10)
        validade = criar_campo_padrao(label="Validade do orçamento (ex.: 7 dias)", value=(registro_edicao["validade"] or "7 dias") if registro_edicao else "7 dias", border_radius=10)

        data_entrega_salva = (registro_edicao["data_entrega"] or "") if registro_edicao else ""
        if data_entrega_salva:
            try:
                data_entrega_salva = datetime.strptime(
                    data_entrega_salva[:10], "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
            except ValueError:
                pass

        data_entrega = criar_campo_padrao(
            label="Data de entrega (opcional)",
            hint_text="DD/MM/AAAA",
            value=data_entrega_salva,
            border_radius=10,
        )

        def obter_data_entrega_iso():
            valor = (data_entrega.value or "").strip()
            if not valor:
                return None
            try:
                return datetime.strptime(valor, "%d/%m/%Y").date().isoformat()
            except ValueError:
                raise ValueError(
                    "Informe a data de entrega no formato DD/MM/AAAA."
                )
        dd_produto = criar_dropdown_padrao(
            label="Produto precificado",
            options=[ft.dropdown.Option(k, v["nome"]) for k, v in produtos.items()],
            value=next(iter(produtos)),
            border_radius=10,
        )
        quantidade = criar_campo_padrao(label="Quantidade", value="1", keyboard_type=ft.KeyboardType.NUMBER, width=115, border_radius=10)
        resumo_edicao = json.loads(registro_edicao["resumo_json"] or "{}") if registro_edicao else {}
        dd_tipo_desconto = criar_dropdown_padrao(
            label="Tipo de desconto",
            value=registro_edicao["desconto_tipo"] if registro_edicao else "percentual",
            options=[
                ft.dropdown.Option("percentual", "Percentual (%)"),
                ft.dropdown.Option("valor", "Valor (R$)"),
                ft.dropdown.Option("nenhum", "Sem desconto"),
            ],
            border_radius=10,
            expand=True,
        )
        desconto = criar_campo_padrao(label="Desconto", value=str(registro_edicao["desconto_valor"]) if registro_edicao else "0", keyboard_type=ft.KeyboardType.NUMBER, width=115, border_radius=10)
        sinal_50 = ft.Checkbox(label="Solicitar sinal de 50% para confirmar a encomenda", value=bool(resumo_edicao.get("sinal_50", False)))
        lista_itens = []
        if registro_edicao:
            for item_salvo in json.loads(registro_edicao["itens_json"] or "[]"):
                snapshot = json.loads(item_salvo.get("snapshot_json") or "{}")
                lista_itens.append({
                    "precificacao_id": snapshot.get("precificacao_id"),
                    "receita_id": item_salvo.get("receita_id"),
                    "nome": item_salvo["nome"],
                    "unidade": item_salvo["unidade"],
                    "quantidade_embalagem": float(snapshot.get("quantidade_embalagem", 1) or 1),
                    "custo": float(item_salvo["custo_unitario_centavos"]) / 100,
                    "preco_base": float(item_salvo["preco_base_centavos"]) / 100,
                    "quantidade": float(item_salvo["quantidade"]),
                })
        lista_controle = ft.Column(spacing=8)
        resumo_controle = ft.Column(spacing=8)
        mensagem_preview = criar_campo_padrao(label="Prévia da mensagem para o cliente", multiline=True, min_lines=10, max_lines=18, read_only=True)
        aviso_margem = ft.Text("", size=12, weight=ft.FontWeight.BOLD)

        def adicionar_item(ev=None):
            try:
                produto = produtos[dd_produto.value]
                qtd = float((quantidade.value or "0").replace(",", "."))
                if qtd <= 0:
                    raise ValueError("A quantidade deve ser maior que zero.")
                lista_itens.append({**produto, "quantidade": qtd})
                atualizar_orcamento()
                mostrar_aviso(f'{produto["nome"]} adicionado ao orçamento.')
            except Exception as erro:
                mostrar_aviso(str(erro), "#C62828")

        def remover_item(indice):
            if 0 <= indice < len(lista_itens):
                lista_itens.pop(indice)
                atualizar_orcamento()

        def calcular_totais():
            total_base = sum(item["preco_base"] * item["quantidade"] for item in lista_itens)
            total_custo = sum(item["custo"] * item["quantidade"] for item in lista_itens)
            valor_desconto = float((desconto.value or "0").replace(",", "."))
            if valor_desconto < 0:
                raise ValueError("O desconto não pode ser negativo.")
            if dd_tipo_desconto.value == "percentual":
                if valor_desconto >= 100:
                    raise ValueError("O desconto percentual deve ser menor que 100%.")
                desconto_reais = total_base * valor_desconto / 100
            elif dd_tipo_desconto.value == "valor":
                desconto_reais = valor_desconto
            else:
                desconto_reais = 0
            if desconto_reais > total_base:
                raise ValueError("O desconto não pode superar o valor dos produtos.")
            fator = ((total_base - desconto_reais) / total_base) if total_base > 0 else 1
            totais = {}
            for nome, chave in modalidades:
                taxa = float(taxas.get(chave, 0)) / 100
                if taxa < 0 or taxa >= 1:
                    raise ValueError(f"Taxa inválida para {nome}.")
                totais[chave] = (total_base * fator / (1 - taxa)) if lista_itens else 0
            return total_base, total_custo, desconto_reais, fator, totais

        def gerar_mensagem(totais, desconto_reais):
            linhas = [
                "✨ *DM GULOSITOS*",
                "*ORÇAMENTO*",
                "",
                f"Olá, {cliente.value.strip() or 'tudo bem'}! Segue nossa proposta:",
                "",
            ]
            for item in lista_itens:
                linhas.append(f'• {item["nome"]} — {item["quantidade"]:g} {item["unidade"]}(s)')
            linhas += ["", "*Valores por forma de pagamento:*"]
            for nome, chave in modalidades:
                linhas.append(f"• {nome}: {formatar_reais(totais[chave])}")
            if desconto_reais > 0:
                linhas += ["", f"Desconto aplicado: {formatar_reais(desconto_reais)}"]
            linhas.append(f"Validade: {validade.value.strip() or 'a combinar'}")
            data_entrega_iso = obter_data_entrega_iso()
            if data_entrega_iso:
                data_entrega_texto = datetime.strptime(
                    data_entrega_iso, "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
                linhas.append(f"Data de entrega: {data_entrega_texto}")
            if sinal_50.value:
                linhas += ["", "*Condição para encomenda:* solicitamos 50% de sinal para confirmar a reserva."]
                for nome, chave in modalidades:
                    sinal = totais[chave] * 0.5
                    saldo = totais[chave] - sinal
                    linhas.append(f"• {nome}: sinal de {formatar_reais(sinal)} | saldo restante de {formatar_reais(saldo)}")
            linhas += ["", "Será um prazer preparar seu pedido! 💗", "DM Gulositos"]
            return "\n".join(linhas)

        def atualizar_orcamento(ev=None):
            try:
                total_base, total_custo, desconto_reais, fator, totais = calcular_totais()
                lista_controle.controls.clear()
                for indice, item in enumerate(lista_itens):
                    lista_controle.controls.append(
                        ft.Container(bgcolor=BRANCO, padding=10, border_radius=10, content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(expand=True, spacing=2, controls=[
                                    ft.Text(item["nome"], weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(f'{item["quantidade"]:g} × {formatar_reais(item["preco_base"])}', size=11, color=TEXTO_SECUNDARIO),
                                ]),
                                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#C62828", on_click=lambda ev, i=indice: remover_item(i)),
                            ]
                        ))
                    )
                resumo_controle.controls.clear()
                for nome, chave in modalidades:
                    taxa = float(taxas.get(chave, 0))
                    total = totais[chave]
                    liquido = total * (1 - taxa / 100)
                    lucro = liquido - total_custo
                    margem = (lucro / total * 100) if total > 0 else 0
                    dentro = margem >= margem_minima
                    resumo_controle.controls.append(
                        ft.Container(bgcolor=ROSA_CLARO, padding=10, border_radius=10, content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(expand=True, spacing=2, controls=[
                                    ft.Text(nome, weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(f"Taxa: {taxa:.2f}%  •  Margem: {margem:.1f}%", size=11, color=TEXTO_SECUNDARIO),
                                    ft.Text("Dentro da margem mínima" if dentro else "Abaixo da margem mínima", size=10, color="#2E7D32" if dentro else "#C62828"),
                                ]),
                                ft.Text(formatar_reais(total), weight=ft.FontWeight.BOLD, color=MARROM),
                            ]
                        ))
                    )
                aviso_margem.value = (
                    "Atenção: uma ou mais formas de pagamento ficam abaixo da margem mínima."
                    if any(
                        ((totais[chave] * (1 - float(taxas.get(chave, 0)) / 100) - total_custo) / totais[chave] * 100 < margem_minima)
                        for _, chave in modalidades if totais[chave] > 0
                    ) else "Todas as formas de pagamento respeitam a margem mínima."
                )
                aviso_margem.color = "#C62828" if aviso_margem.value.startswith("Atenção") else "#2E7D32"
                mensagem_preview.value = gerar_mensagem(totais, desconto_reais) if lista_itens else "Adicione produtos para montar a mensagem."
                botao_salvar_orcamento.action = ft.CopyToClipboard(mensagem_preview.value)
                page.update()
            except Exception as erro:
                aviso_margem.value = str(erro)
                aviso_margem.color = "#C62828"
                page.update()

        def salvar_e_copiar(ev=None):
            try:
                if not lista_itens:
                    raise ValueError("Adicione pelo menos um produto ao orçamento.")
                total_base, total_custo, desconto_reais, fator, totais = calcular_totais()
                mensagem = gerar_mensagem(totais, desconto_reais)
                total_final = totais["pix"]
                itens_snapshot = []
                for item in lista_itens:
                    preco_final_base = item["preco_base"] * fator
                    itens_snapshot.append({
                        "receita_id": item["receita_id"],
                        "nome": item["nome"],
                        "quantidade": item["quantidade"],
                        "unidade": item["unidade"],
                        "custo_unitario_centavos": round(item["custo"] * 100),
                        "preco_base_centavos": round(item["preco_base"] * 100),
                        "preco_final_unitario_centavos": round(preco_final_base * 100),
                        "subtotal_centavos": round(preco_final_base * item["quantidade"] * 100),
                        "snapshot_json": json.dumps({
                            "custo_original": item["custo"],
                            "preco_base_original": item["preco_base"],
                            "quantidade_embalagem": item["quantidade_embalagem"],
                            "precificacao_id": item.get("precificacao_id"),
                            "taxas": taxas,
                            "margem_minima": margem_minima,
                        }, ensure_ascii=False),
                    })
                resumo = {
                    "totais_por_modalidade": totais,
                    "taxas": taxas,
                    "margem_minima": margem_minima,
                    "custo_total": total_custo,
                    "desconto_reais": desconto_reais,
                    "desconto_tipo": dd_tipo_desconto.value,
                    "desconto_valor": float((desconto.value or "0").replace(",", ".")),
                    "sinal_50": bool(sinal_50.value),
                }
                numero_orcamento = registro_edicao["numero"] if registro_edicao else f"ORC-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
                dados = {
                    "numero": numero_orcamento,
                    "cliente": cliente.value.strip(),
                    "status": "Em elaboração",
                    "validade": validade.value.strip(),
                    "data_entrega": obter_data_entrega_iso(),
                    "desconto_tipo": dd_tipo_desconto.value,
                    "desconto_valor": resumo["desconto_valor"],
                    "modalidade": "pix",
                    "total_referencia_centavos": round(total_base * 100),
                    "total_final_centavos": round(total_final * 100),
                    "itens_json": json.dumps(itens_snapshot, ensure_ascii=False),
                    "resumo_json": json.dumps(resumo, ensure_ascii=False),
                    "mensagem": mensagem,
                    "itens": itens_snapshot,
                }
                if registro_edicao:
                    atualizar_orcamento_salvo(orcamento_id, dados)
                    mostrar_aviso("Orçamento atualizado com sucesso.")
                else:
                    salvar_orcamento(dados)
                    mostrar_aviso("Orçamento salvo com sucesso.")
                montar_tela_historico()
            except Exception as erro:
                mostrar_aviso(str(erro), "#C62828")

        for controle in (dd_tipo_desconto, desconto, sinal_50, data_entrega):
            controle.on_change = atualizar_orcamento

        botao_salvar_orcamento = ft.Button(
            "Salvar alterações e copiar mensagem" if registro_edicao else "Salvar orçamento e copiar mensagem",
            icon=ft.Icons.CONTENT_COPY,
            action=ft.CopyToClipboard(mensagem_preview.value),
            on_click=salvar_e_copiar,
            bgcolor=ROSA,
            color=BRANCO,
            expand=True,
        )

        tela = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
            cabecalho_orcamentos("Editar orçamento" if registro_edicao else "Novo orçamento", abrir_menu_opcoes),
            ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Column(spacing=12, controls=[
                ft.Text("Editar orçamento" if registro_edicao else "Dados do cliente", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                cliente, validade, data_entrega,
                ft.Divider(color=ROSA_CLARO),
                ft.Text("Adicionar produtos", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                dd_produto,
                ft.Row(controls=[quantidade, ft.Button("Adicionar", icon=ft.Icons.ADD, on_click=adicionar_item, bgcolor=ROSA, color=BRANCO)]),
                lista_controle,
                ft.Divider(color=ROSA_CLARO),
                ft.Text("Desconto no orçamento", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                ft.Row(controls=[dd_tipo_desconto, desconto]),
                ft.Divider(color=ROSA_CLARO),
                ft.Text("Condição de pagamento da encomenda", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                sinal_50,
                ft.Text("Preços calculados por modalidade", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                ft.Text(f"Margem mínima configurada: {margem_minima:.1f}%", size=11, color=TEXTO_SECUNDARIO),
                resumo_controle,
                aviso_margem,
                ft.Text("Mensagem pronta para compartilhar", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                mensagem_preview,
                botao_salvar_orcamento,
                ft.Button("Ver histórico de orçamentos", icon=ft.Icons.HISTORY, on_click=lambda ev: montar_tela_historico(), bgcolor=ROSA_CLARO, color=MARROM),
            ])),
        ])
        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        if filtro_status is not None:
            montar_tela_historico(filtro_status)
            return
        page.add(tela)
        atualizar_orcamento()
        page.update()

    def abrir_edicao_precificacao(precificacao_id=None):
        em_edicao = precificacao_id is not None
        dados_atuais = obter_precificacao_v2(precificacao_id) if em_edicao else None

        conexao = obter_conexao()
        try:
            receitas = conexao.execute(
                "SELECT * FROM receitas WHERE ativo = 1 AND tipo = 'PRODUTO' ORDER BY nome"
            ).fetchall()
        finally:
            conexao.close()

        if not receitas:
            mostrar_aviso("Cadastre um Produto Final primeiro.")
            return

        taxas_pagamento = obter_taxas_pagamento()
        margem_minima = obter_margem_minima()
        markup_ideal = obter_markup_ideal()

        modalidades = [
            ("Dinheiro", "dinheiro"),
            ("Pix", "pix"),
            ("Débito", "debito"),
            ("Crédito à vista", "credito_avista"),
            ("Crédito parcelado", "credito_parcelado"),
        ]

        def formatar_reais(valor):
            return (
                f"R$ {valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        dd_receita = criar_dropdown_padrao(
            label="Produto Final",
            options=[ft.dropdown.Option(str(r["id"]), r["nome"]) for r in receitas],
            value=str(dados_atuais["receita_id"]) if em_edicao else str(receitas[0]["id"]),
            border_radius=12,
        )

        tf_qtd_emb = criar_campo_padrao(
            label="Qtd. de Produto na Embalagem",
            value=str(dados_atuais["quantidade_embalagem"]) if em_edicao else "1",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        tf_custo_emb = criar_campo_padrao(
            label="Embalagem + Sacola (R$)",
            value=(
                f"{dados_atuais['custo_embalagem_centavos'] / 100:.2f}".replace(".", ",")
                if em_edicao else "0,00"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        tf_preco_praticado = criar_campo_padrao(
            label="Preço de Venda Praticado (R$)",
            value=(
                f"{dados_atuais['preco_praticado_centavos'] / 100:.2f}".replace(".", ",")
                if em_edicao else "0,00"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        info_markup_ideal = ft.Text(
            f"Markup ideal configurado: {markup_ideal:.2f}%".replace(".", ","),
            color=MARROM,
            size=13,
            weight=ft.FontWeight.BOLD,
        )
        info_margem_minima = ft.Text(
            f"Margem mínima exigida: {margem_minima:.2f}%".replace(".", ","),
            color=MARROM,
            size=13,
            weight=ft.FontWeight.BOLD,
        )

        lbl_insumo = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=MARROM)
        lbl_custo_fixo = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=MARROM)
        lbl_custo_total = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, size=16, color=ROSA)
        lbl_preco_sugerido = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, size=16, color=MARROM)
        lbl_preco_comparacao = ft.Text(
            "Aguardando cálculo...",
            color=TEXTO_SECUNDARIO,
            size=12,
        )
        lbl_markup_aplicado = ft.Text("0,0%", weight=ft.FontWeight.BOLD, color=MARROM)

        dd_tipo_desconto = criar_dropdown_padrao(
            label="Tipo de desconto",
            value="percentual",
            options=[
                ft.dropdown.Option("percentual", "Porcentagem (%)"),
                ft.dropdown.Option("valor", "Valor em reais (R$)"),
            ],
            border_radius=12,
            expand=True,
        )
        tf_desconto = criar_campo_padrao(
            label="Desconto",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )
        lbl_preco_original_desconto = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=MARROM)
        lbl_valor_desconto = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=ROSA)
        lbl_preco_com_desconto = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=MARROM)
        lbl_alerta_desconto = ft.Text(
            "Informe um desconto para simular o resultado.",
            size=12,
            color=TEXTO_SECUNDARIO,
        )
        linhas_desconto = []

        linhas_comparativo = []
        controles_comparativo = []

        for nome, chave in modalidades:
            lbl_taxa = ft.Text("0,00%", size=12, color=TEXTO_SECUNDARIO)
            lbl_liquido = ft.Text("R$ 0,00", size=13, weight=ft.FontWeight.BOLD, color=MARROM)
            lbl_lucro = ft.Text("R$ 0,00", size=12, color=MARROM)
            lbl_margem_modalidade = ft.Text("0,0%", size=13, weight=ft.FontWeight.BOLD, color=MARROM)
            lbl_status_modalidade = ft.Text("—", size=11, color=TEXTO_SECUNDARIO)

            linhas_comparativo.append({
                "chave": chave,
                "taxa": lbl_taxa,
                "liquido": lbl_liquido,
                "lucro": lbl_lucro,
                "margem": lbl_margem_modalidade,
                "status": lbl_status_modalidade,
            })

            lbl_liquido_desconto = ft.Text("R$ 0,00", size=12, weight=ft.FontWeight.BOLD, color=MARROM)
            lbl_lucro_desconto = ft.Text("R$ 0,00", size=12, color=MARROM)
            lbl_margem_desconto = ft.Text("0,0%", size=12, weight=ft.FontWeight.BOLD, color=MARROM)
            lbl_status_desconto = ft.Text("Aguardando simulação", size=11, color=TEXTO_SECUNDARIO)
            linhas_desconto.append({
                "chave": chave,
                "liquido": lbl_liquido_desconto,
                "lucro": lbl_lucro_desconto,
                "margem": lbl_margem_desconto,
                "status": lbl_status_desconto,
            })

            controles_comparativo.append(
                ft.Container(
                    padding=12,
                    bgcolor=BRANCO,
                    border_radius=10,
                    content=ft.Column(
                        spacing=5,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(nome, weight=ft.FontWeight.BOLD, color=MARROM),
                                    lbl_taxa,
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Valor líquido", size=12, color=TEXTO_SECUNDARIO),
                                    lbl_liquido,
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Lucro estimado", size=12, color=TEXTO_SECUNDARIO),
                                    lbl_lucro,
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Margem", size=12, color=TEXTO_SECUNDARIO),
                                    lbl_margem_modalidade,
                                ],
                            ),
                            lbl_status_modalidade,
                        ],
                    ),
                )
            )

        def atualizar_calculos(e=None):
            try:
                rec_id = int(dd_receita.value) if dd_receita.value else 0
                qtd_emb = float((tf_qtd_emb.value or "0").replace(",", "."))
                custo_emb = float((tf_custo_emb.value or "0").replace(",", ".")) * 100
                preco_praticado = float(
                    (tf_preco_praticado.value or "0").replace(",", ".")
                )

                # O cálculo-base não inclui taxa: as taxas são comparadas separadamente abaixo.
                resultado = calcular_simulacao_precificacao(
                    rec_id,
                    qtd_emb,
                    custo_emb,
                    markup_ideal,
                    0,
                    0,
                    margem_minima,
                )

                if not resultado:
                    raise ValueError("Não foi possível calcular os custos do produto.")

                custo_total = resultado["custo_total"]
                preco_sugerido = resultado["preco_sugerido"]
                usar_preco_praticado = preco_praticado > 0
                preco_referencia = preco_praticado if usar_preco_praticado else preco_sugerido

                lbl_insumo.value = formatar_reais(resultado["custo_insumo"])
                lbl_custo_fixo.value = formatar_reais(resultado["custo_fixo"])
                lbl_custo_total.value = formatar_reais(custo_total)
                lbl_preco_sugerido.value = formatar_reais(preco_sugerido)

                origem_preco = "preço praticado" if usar_preco_praticado else "preço sugerido"
                lbl_preco_comparacao.value = (
                    f"Comparação calculada sobre o {origem_preco}: "
                    f"{formatar_reais(preco_referencia)}"
                )

                markup_aplicado = (
                    ((preco_referencia - custo_total) / custo_total) * 100
                    if custo_total > 0 else 0
                )
                lbl_markup_aplicado.value = f"{markup_aplicado:.1f}%".replace(".", ",")

                for linha in linhas_comparativo:
                    taxa = float(taxas_pagamento.get(linha["chave"], 0))
                    valor_taxa = preco_referencia * taxa / 100
                    valor_liquido = preco_referencia - valor_taxa
                    lucro = valor_liquido - custo_total
                    margem = (lucro / preco_referencia * 100) if preco_referencia > 0 else 0

                    dentro_margem = margem >= margem_minima
                    linha["taxa"].value = f"Taxa: {taxa:.2f}%".replace(".", ",")
                    linha["liquido"].value = formatar_reais(valor_liquido)
                    linha["lucro"].value = formatar_reais(lucro)
                    linha["margem"].value = f"{margem:.1f}%".replace(".", ",")
                    linha["margem"].color = "#2E7D32" if dentro_margem else "#C62828"
                    linha["status"].value = (
                        "Dentro da margem mínima"
                        if dentro_margem else "Abaixo da margem mínima"
                    )
                    linha["status"].color = "#2E7D32" if dentro_margem else "#C62828"

                # Simulação de desconto sobre o preço de referência.
                desconto_informado = float((tf_desconto.value or "0").replace(",", "."))
                if desconto_informado < 0:
                    raise ValueError("O desconto não pode ser negativo.")

                if dd_tipo_desconto.value == "percentual":
                    if desconto_informado >= 100:
                        raise ValueError("O desconto percentual deve ser menor que 100%.")
                    valor_desconto = preco_referencia * desconto_informado / 100
                else:
                    valor_desconto = desconto_informado

                if valor_desconto > preco_referencia:
                    raise ValueError("O desconto não pode ser maior que o preço do produto.")

                preco_com_desconto = preco_referencia - valor_desconto
                lbl_preco_original_desconto.value = formatar_reais(preco_referencia)
                lbl_valor_desconto.value = formatar_reais(valor_desconto)
                lbl_preco_com_desconto.value = formatar_reais(preco_com_desconto)

                margens_desconto = []
                for linha in linhas_desconto:
                    taxa = float(taxas_pagamento.get(linha["chave"], 0))
                    valor_taxa = preco_com_desconto * taxa / 100
                    valor_liquido = preco_com_desconto - valor_taxa
                    lucro = valor_liquido - custo_total
                    margem = (lucro / preco_com_desconto * 100) if preco_com_desconto > 0 else -100
                    dentro_margem = margem >= margem_minima

                    linha["liquido"].value = formatar_reais(valor_liquido)
                    linha["lucro"].value = formatar_reais(lucro)
                    linha["margem"].value = f"{margem:.1f}%".replace(".", ",")
                    linha["margem"].color = "#2E7D32" if dentro_margem else "#C62828"
                    linha["status"].value = (
                        "Dentro da margem mínima"
                        if dentro_margem else "Abaixo da margem mínima"
                    )
                    linha["status"].color = "#2E7D32" if dentro_margem else "#C62828"
                    margens_desconto.append(dentro_margem)

                if valor_desconto <= 0:
                    lbl_alerta_desconto.value = "Sem desconto aplicado. Informe um valor para simular uma promoção."
                    lbl_alerta_desconto.color = TEXTO_SECUNDARIO
                elif all(margens_desconto):
                    lbl_alerta_desconto.value = "Desconto viável: todas as formas de pagamento permanecem dentro da margem mínima."
                    lbl_alerta_desconto.color = "#2E7D32"
                elif any(margens_desconto):
                    lbl_alerta_desconto.value = "Atenção: o desconto deixa algumas formas de pagamento abaixo da margem mínima."
                    lbl_alerta_desconto.color = "#C77700"
                else:
                    lbl_alerta_desconto.value = "Não recomendado: todas as formas de pagamento ficam abaixo da margem mínima."
                    lbl_alerta_desconto.color = "#C62828"

            except Exception as err:
                lbl_preco_comparacao.value = f"Não foi possível atualizar: {err}"

            page.update()

        dd_receita.on_change = atualizar_calculos
        tf_qtd_emb.on_change = atualizar_calculos
        tf_custo_emb.on_change = atualizar_calculos
        tf_preco_praticado.on_change = atualizar_calculos
        dd_tipo_desconto.on_change = atualizar_calculos
        tf_desconto.on_change = atualizar_calculos

        def salvar_form(e):
            try:
                rec_id = int(dd_receita.value)
                qtd_emb = float((tf_qtd_emb.value or "0").replace(",", "."))
                custo_emb = int(
                    float((tf_custo_emb.value or "0").replace(",", ".")) * 100
                )
                preco_prat = int(
                    float((tf_preco_praticado.value or "0").replace(",", ".")) * 100
                )

                if margem_minima < 0 or margem_minima >= 100:
                    raise ValueError("A margem mínima deve estar entre 0% e 99,99%.")

                # Mantém o crédito à vista como taxa de referência do histórico legado
                # e como critério atual de validação do salvamento.
                salvar_precificacao_v2(
                    precificacao_id,
                    rec_id,
                    qtd_emb,
                    custo_emb,
                    markup_ideal,
                    preco_prat,
                    margem_minima,
                    taxas_pagamento["credito_avista"],
                )
                abrir_precificacao()
            except Exception as err:
                mostrar_aviso(f"Erro ao salvar: {err}")

        def row_resumo(label, control):
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(label, color=TEXTO_SECUNDARIO, size=13),
                    control,
                ],
            )

        painel_resultados = ft.Container(
            bgcolor=ROSA_CLARO,
            padding=16,
            border_radius=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(
                        "COMPOSIÇÃO DO CUSTO",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=MARROM,
                    ),
                    row_resumo("Custo dos insumos:", lbl_insumo),
                    row_resumo("Custo fixo (tempo):", lbl_custo_fixo),
                    ft.Divider(color=ROSA),
                    row_resumo("CUSTO TOTAL:", lbl_custo_total),
                    row_resumo("Preço sugerido:", lbl_preco_sugerido),
                    row_resumo("Markup sobre o preço de comparação:", lbl_markup_aplicado),
                    ft.Divider(color=ROSA),
                    lbl_preco_comparacao,
                ],
            ),
        )

        painel_desconto = ft.Container(
            bgcolor=ROSA_CLARO,
            padding=14,
            border_radius=12,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(
                        "SIMULAÇÃO DE DESCONTOS",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=MARROM,
                    ),
                    ft.Text(
                        "Simule uma promoção em percentual ou em reais. "
                        "O cálculo considera novamente as taxas de cada forma de pagamento.",
                        size=12,
                        color=TEXTO_SECUNDARIO,
                    ),
                    ft.Row(controls=[dd_tipo_desconto, tf_desconto]),
                    row_resumo("Preço original:", lbl_preco_original_desconto),
                    row_resumo("Valor do desconto:", lbl_valor_desconto),
                    row_resumo("Preço com desconto:", lbl_preco_com_desconto),
                    ft.Divider(color=ROSA),
                    ft.Text("Resultado por forma de pagamento", weight=ft.FontWeight.BOLD, color=MARROM, size=12),
                    *[
                        ft.Container(
                            bgcolor=BRANCO,
                            padding=10,
                            border_radius=10,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(nome, weight=ft.FontWeight.BOLD, color=MARROM),
                                    row_resumo("Valor líquido:", linha["liquido"]),
                                    row_resumo("Lucro estimado:", linha["lucro"]),
                                    row_resumo("Margem:", linha["margem"]),
                                    linha["status"],
                                ],
                            ),
                        )
                        for nome, linha in [
                            (nome, linha)
                            for nome, chave in modalidades
                            for linha in linhas_desconto
                            if linha["chave"] == chave
                        ]
                    ],
                    lbl_alerta_desconto,
                ],
            ),
        )

        painel_comparativo = ft.Container(
            bgcolor=ROSA_CLARO,
            padding=14,
            border_radius=12,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(
                        "SIMULAÇÃO POR FORMA DE PAGAMENTO",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=MARROM,
                    ),
                    ft.Text(
                        "Compare quanto sobra em cada modalidade. "
                        "As taxas são configuradas em Custos Fixos.",
                        size=12,
                        color=TEXTO_SECUNDARIO,
                    ),
                    *controles_comparativo,
                ],
            ),
        )

        tela_form = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=5),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=abrir_precificacao,
                                content=ft.Icon(ft.Icons.ARROW_BACK, color=MARROM, size=24),
                            ),
                            ft.Text(
                                "Editar Preço" if em_edicao else "Nova Precificação",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            dd_receita,
                            ft.Row(controls=[tf_qtd_emb, tf_custo_emb]),
                            ft.Container(
                                bgcolor=ROSA_CLARO,
                                padding=12,
                                border_radius=10,
                                content=ft.Column(
                                    spacing=5,
                                    controls=[info_markup_ideal, info_margem_minima],
                                ),
                            ),
                            tf_preco_praticado,
                            painel_resultados,
                            painel_comparativo,
                            ft.Container(
                                width=380,
                                padding=14,
                                bgcolor=ROSA,
                                border_radius=12,
                                on_click=salvar_form,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.SAVE_OUTLINED, color=BRANCO),
                                        ft.Text(
                                            "Salvar Precificação",
                                            color=BRANCO,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        )

        atualizar_calculos()
        page.controls.clear()
        page.add(tela_form)
        page.update()

    # ==================================================
    # INGREDIENTES
    # ==================================================

    def abrir_historico_precos_ingrediente(ingrediente_id, nome):
        historico = listar_historico_precos_ingrediente(ingrediente_id)
        cartoes_historico = []

        for indice, item in enumerate(historico):
            data = item["registrado_em"].replace("T", " ")
            preco = item["preco_pago_centavos"] / 100
            custo_unitario = item["custo_por_unidade_base"]

            detalhes = [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Preço da embalagem", size=12, color=TEXTO_SECUNDARIO),
                        ft.Text(f"R$ {preco:.2f}", weight=ft.FontWeight.BOLD, color=MARROM),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Quantidade", size=12, color=TEXTO_SECUNDARIO),
                        ft.Text(
                            f'{item["quantidade_compra"]:g} {item["unidade_compra"]}',
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f'Custo por {item["unidade_base"]}', size=12, color=TEXTO_SECUNDARIO),
                        ft.Text(f"R$ {custo_unitario:.5f}", weight=ft.FontWeight.BOLD, color=ROSA),
                    ],
                ),
            ]

            if indice + 1 < len(historico):
                anterior = historico[indice + 1]
                custo_anterior = float(anterior["custo_por_unidade_base"])
                if anterior["unidade_base"] == item["unidade_base"] and custo_anterior > 0:
                    variacao = ((float(custo_unitario) - custo_anterior) / custo_anterior) * 100
                    if variacao > 0:
                        texto_variacao = f"Aumento de {variacao:.1f}% em relação ao registro anterior"
                        cor_variacao = "#C62828"
                    elif variacao < 0:
                        texto_variacao = f"Redução de {abs(variacao):.1f}% em relação ao registro anterior"
                        cor_variacao = "#2E7D32"
                    else:
                        texto_variacao = "Sem alteração em relação ao registro anterior"
                        cor_variacao = TEXTO_SECUNDARIO
                    detalhes.append(
                        ft.Text(texto_variacao, size=11, color=cor_variacao, weight=ft.FontWeight.BOLD)
                    )

            cartoes_historico.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=15,
                    border_radius=14,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text(data, size=11, color=TEXTO_SECUNDARIO),
                            ft.Divider(color=ROSA_CLARO),
                            *detalhes,
                        ],
                    ),
                )
            )

        if not cartoes_historico:
            cartoes_historico.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=18,
                    border_radius=14,
                    content=ft.Text(
                        "Ainda não existem registros de preço para este insumo.",
                        color=TEXTO_SECUNDARIO,
                    ),
                )
            )

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=5),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=abrir_ingredientes,
                                content=ft.Icon(ft.Icons.ARROW_BACK, color=MARROM, size=24),
                            ),
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Text("Histórico de preços", size=21, weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(nome, size=12, color=TEXTO_SECUNDARIO),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text(
                                f"{len(historico)} registro(s) encontrado(s)",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                            *cartoes_historico,
                        ],
                    ),
                ),
            ],
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    def abrir_ingredientes(e=None):

        ingredientes = listar_ingredientes()
        alertas = listar_alertas_aumento_ingredientes()
        cartoes = []
        painel_alertas = []

        if alertas:
            itens_alerta = []

            for alerta in alertas:
                itens_alerta.append(
                    ft.Container(
                        padding=12,
                        bgcolor="#FFFFFF",
                        border_radius=10,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    alerta["nome"],
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                    size=14,
                                ),
                                ft.Text(
                                    f"Aumento de "
                                    f"{alerta['aumento_percentual']:.1f}%",
                                    color="#C62828",
                                    weight=ft.FontWeight.BOLD,
                                    size=13,
                                ),
                                ft.Text(
                                    f"Custo por {alerta['unidade_base']}: "
                                    f"R$ {alerta['custo_anterior']:.5f} "
                                    f"→ R$ {alerta['custo_atual']:.5f}",
                                    color=TEXTO_SECUNDARIO,
                                    size=12,
                                ),
                                ft.Text(
                                    f"Embalagem: R$ "
                                    f"{alerta['preco_anterior']:.2f} "
                                    f"→ R$ {alerta['preco_atual']:.2f}",
                                    color=TEXTO_SECUNDARIO,
                                    size=12,
                                ),
                            ],
                        ),
                    )
                )

            painel_alertas.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        padding=14,
                        bgcolor="#FCE8E6",
                        border_radius=14,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.WARNING_AMBER_ROUNDED,
                                            color="#C62828",
                                            size=22,
                                        ),
                                        ft.Text(
                                            "ALERTA DE AUMENTO DE PREÇOS",
                                            color="#C62828",
                                            weight=ft.FontWeight.BOLD,
                                            size=13,
                                        ),
                                    ],
                                ),
                                ft.Text(
                                    "O custo destes ingredientes aumentou "
                                    "em relação ao registro anterior.",
                                    color=MARROM,
                                    size=12,
                                ),
                                *itens_alerta,
                            ],
                        ),
                    ),
                )
            )


        # --------------------------------------------------
        # EXCLUSÃO COM DUPLA CONFIRMAÇÃO
        # --------------------------------------------------

        def solicitar_exclusao(ingrediente_id, nome):

            def fechar_primeiro(e):
                dialogo_primeiro.open = False
                page.update()

            def confirmar_segunda_etapa(e):
                dialogo_primeiro.open = False
                dialogo_segundo.open = True
                page.update()

            def voltar_primeira_etapa(e):
                dialogo_segundo.open = False
                dialogo_primeiro.open = True
                page.update()

            def executar_exclusao(e):

                dialogo_segundo.open = False
                page.update()

                try:
                    excluir_ingrediente(ingrediente_id)
                    abrir_ingredientes()

                except ValueError as erro:

                    def fechar_erro(e):
                        dialogo_erro.open = False
                        page.update()

                    dialogo_erro = criar_dialogo_padrao(
                        modal=True,
                        title=ft.Text("Não foi possível excluir"),
                        content=ft.Text(str(erro)),
                        actions=[
                            ft.TextButton(
                                "Entendi",
                                on_click=fechar_erro,
                            )
                        ],
                    )

                    page.overlay.append(dialogo_erro)
                    dialogo_erro.open = True
                    page.update()

                except Exception as erro:

                    def fechar_erro(e):
                        dialogo_erro.open = False
                        page.update()

                    dialogo_erro = criar_dialogo_padrao(
                        modal=True,
                        title=ft.Text("Erro ao excluir"),
                        content=ft.Text(
                            f"Ocorreu um erro inesperado:\n{erro}"
                        ),
                        actions=[
                            ft.TextButton(
                                "Entendi",
                                on_click=fechar_erro,
                            )
                        ],
                    )

                    page.overlay.append(dialogo_erro)
                    dialogo_erro.open = True
                    page.update()

            dialogo_primeiro = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Excluir ingrediente?"),
                content=ft.Text(
                    f"Deseja realmente excluir o ingrediente '{nome}'?"
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=fechar_primeiro,
                    ),
                    ft.Button(
                        "Continuar",
                        on_click=confirmar_segunda_etapa,
                        bgcolor=ROSA,
                        color=BRANCO,
                    ),
                ],
            )

            dialogo_segundo = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Confirmação definitiva"),
                content=ft.Text(
                    f"Esta ação não poderá ser desfeita.\n\n"
                    f"Confirma a exclusão de '{nome}'?"
                ),
                actions=[
                    ft.TextButton(
                        "Voltar",
                        on_click=voltar_primeira_etapa,
                    ),
                    ft.Button(
                        "Excluir definitivamente",
                        on_click=executar_exclusao,
                        bgcolor="#C62828",
                        color=BRANCO,
                    ),
                ],
            )

            page.overlay.append(dialogo_primeiro)
            page.overlay.append(dialogo_segundo)

            dialogo_primeiro.open = True
            page.update()

        # --------------------------------------------------
        # CARTÕES
        # --------------------------------------------------

        for ingrediente in ingredientes:

            preco = ingrediente["preco_pago_centavos"] / 100
            marca = ingrediente["marca"] or "Sem marca informada"
            ingrediente_id = ingrediente["id"]
            nome_ingrediente = ingrediente["nome"]

            cartoes.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=18,
                    border_radius=18,
                    on_click=lambda e, item_id=ingrediente_id:
                        abrir_edicao_ingrediente(item_id),
                    content=ft.Column(
                        spacing=9,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Container(
                                        expand=True,
                                        content=ft.Text(
                                            nome_ingrediente,
                                            size=17,
                                            weight=ft.FontWeight.BOLD,
                                            color=MARROM,
                                        ),
                                    ),
                                    ft.Row(
                                        spacing=2,
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.EDIT_OUTLINED,
                                                icon_color=ROSA,
                                                tooltip="Editar ingrediente",
                                                on_click=lambda e, item_id=ingrediente_id:
                                                    abrir_edicao_ingrediente(item_id),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.HISTORY,
                                                icon_color=MARROM,
                                                tooltip="Ver histórico de preços",
                                                on_click=lambda e, item_id=ingrediente_id, nome=nome_ingrediente:
                                                    abrir_historico_precos_ingrediente(item_id, nome),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE_OUTLINE,
                                                icon_color="#C62828",
                                                tooltip="Excluir ingrediente",
                                                on_click=lambda e, item_id=ingrediente_id, nome=nome_ingrediente:
                                                    solicitar_exclusao(
                                                        item_id,
                                                        nome,
                                                    ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"Marca: {marca}",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"{ingrediente['quantidade_compra']:g} "
                                        f"{ingrediente['unidade_compra']}",
                                        color=MARROM,
                                        size=13,
                                    ),
                                    ft.Text(
                                        f"R$ {preco:.2f}",
                                        color=MARROM,
                                        weight=ft.FontWeight.BOLD,
                                        size=16,
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"Custo por {ingrediente['unidade_base']}: "
                                f"R$ {ingrediente['custo_por_unidade_base']:.5f}",
                                size=12,
                                color=ROSA,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Toque para editar",
                                size=10,
                                color=TEXTO_SECUNDARIO,
                            ),
                        ],
                    ),
                )
            )

        if not cartoes:
            cartoes.append(
                ft.Container(
                    padding=25,
                    bgcolor=BRANCO,
                    border_radius=16,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.INVENTORY_2_OUTLINED,
                                size=40,
                                color=ROSA,
                            ),
                            ft.Text(
                                "Nenhum ingrediente cadastrado.",
                                color=MARROM,
                            ),
                        ],
                    ),
                )
            )

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                criar_cabecalho_padrao(
                    "Ingredientes",
                    f"{len(ingredientes)} ingrediente(s) cadastrado(s)",
                    voltar_inicio,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=criar_botao_primario(
                        "Adicionar ingrediente",
                        abrir_cadastro_ingrediente,
                    ),
                ),

                *painel_alertas,

                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=cartoes,
                    ),
                ),
            ],
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # FORMULÁRIO DE INGREDIENTES
    # ==================================================

    def abrir_cadastro_ingrediente(e=None):
        abrir_formulario_ingrediente()

    def abrir_edicao_ingrediente(ingrediente_id):

        ingrediente = obter_ingrediente(ingrediente_id)

        if ingrediente is None:
            abrir_ingredientes()
            return

        abrir_formulario_ingrediente(ingrediente)

    def abrir_formulario_ingrediente(ingrediente=None):

        em_edicao = ingrediente is not None

        unidades_antigas = {
            "litro": "l",
            "litros": "l",
            "unidade": "un",
            "unidades": "un",
        }

        unidade_atual = (
            ingrediente["unidade_compra"].strip().lower()
            if em_edicao else "g"
        )

        unidade_atual = unidades_antigas.get(
            unidade_atual,
            unidade_atual,
        )

        if unidade_atual not in ["g", "kg", "ml", "l", "un"]:
            unidade_atual = "g"

        campo_nome = criar_campo_padrao(
            label="Nome do ingrediente *",
            hint_text="Ex.: Farinha de trigo",
            value=ingrediente["nome"] if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_marca = criar_campo_padrao(
            label="Marca",
            hint_text="Ex.: Qualy",
            value=(ingrediente["marca"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_fornecedor = criar_campo_padrao(
            label="Fornecedor ou estabelecimento",
            hint_text="Onde foi comprado?",
            value=(ingrediente["fornecedor"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_quantidade = criar_campo_padrao(
            label="Quantidade da embalagem *",
            hint_text="Ex.: 500",
            value=str(ingrediente["quantidade_compra"]) if em_edicao else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_unidade = criar_dropdown_padrao(
            label="Unidade de compra *",
            value=unidade_atual,
            border_radius=12,
            border_color=ROSA_CLARO,
            options=[
                ft.dropdown.Option("g", "Gramas (g)"),
                ft.dropdown.Option("kg", "Quilogramas (kg)"),
                ft.dropdown.Option("ml", "Mililitros (ml)"),
                ft.dropdown.Option("l", "Litros (L)"),
                ft.dropdown.Option("un", "Unidade (un)"),
            ],
        )

        campo_preco = criar_campo_padrao(
            label="Preço pago (R$) *",
            hint_text="Ex.: 6,99",
            value=(
                f"{ingrediente['preco_pago_centavos'] / 100:.2f}".replace(".", ",")
                if em_edicao else ""
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_observacoes = criar_campo_padrao(
            label="Observações",
            hint_text="Informações adicionais...",
            value=(ingrediente["observacoes"] or "") if em_edicao else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        previa_custo = ft.Text(
            "Informe quantidade, unidade e preço para calcular.",
            size=13,
            color=TEXTO_SECUNDARIO,
        )

        mensagem = ft.Text(
            "",
            size=12,
            color="#B00020",
        )

        unidades = {
            "kg": (1000, "g"),
            "g": (1, "g"),
            "l": (1000, "ml"),
            "ml": (1, "ml"),
            "un": (1, "un"),
        }

        def atualizar_previa(e=None):

            try:
                quantidade = float(
                    (campo_quantidade.value or "").replace(",", ".")
                )

                preco = float(
                    (campo_preco.value or "").replace(",", ".")
                )

                unidade = campo_unidade.value

                if quantidade <= 0 or preco < 0:
                    raise ValueError

                if unidade not in unidades:
                    raise ValueError

                fator, unidade_base = unidades[unidade]
                custo = preco / (quantidade * fator)

                previa_custo.value = (
                    f"Custo por {unidade_base}: R$ {custo:.5f}"
                )

                previa_custo.color = ROSA

            except (ValueError, AttributeError):
                previa_custo.value = (
                    "Informe quantidade, unidade e preço para calcular."
                )
                previa_custo.color = TEXTO_SECUNDARIO

            page.update()

        campo_quantidade.on_change = atualizar_previa
        campo_unidade.on_change = atualizar_previa
        campo_preco.on_change = atualizar_previa

        if em_edicao:
            atualizar_previa()

        # --------------------------------------------------
        # SALVAR INGREDIENTE
        # --------------------------------------------------

        def salvar_ingrediente(e=None):

            try:
                nome = (campo_nome.value or "").strip()
                marca = (campo_marca.value or "").strip()
                fornecedor = (campo_fornecedor.value or "").strip()
                observacoes = (campo_observacoes.value or "").strip()

                if not nome:
                    mensagem.value = "Informe o nome do ingrediente."
                    page.update()
                    return

                quantidade = float(
                    (campo_quantidade.value or "").replace(",", ".")
                )

                preco = float(
                    (campo_preco.value or "").replace(",", ".")
                )

                unidade = campo_unidade.value

                if quantidade <= 0:
                    mensagem.value = "A quantidade deve ser maior que zero."
                    page.update()
                    return

                if preco < 0:
                    mensagem.value = "O preço não pode ser negativo."
                    page.update()
                    return

                if unidade not in unidades:
                    mensagem.value = "Selecione uma unidade válida."
                    page.update()
                    return

                preco_centavos = round(preco * 100)

                if em_edicao:
                    atualizar_ingrediente(
                        ingrediente_id=ingrediente["id"],
                        nome=nome,
                        marca=marca,
                        fornecedor=fornecedor,
                        quantidade_compra=quantidade,
                        unidade_compra=unidade,
                        preco_pago_centavos=preco_centavos,
                        observacoes=observacoes,
                    )
                else:
                    cadastrar_ingrediente(
                        nome=nome,
                        marca=marca,
                        fornecedor=fornecedor,
                        quantidade_compra=quantidade,
                        unidade_compra=unidade,
                        preco_pago_centavos=preco_centavos,
                        observacoes=observacoes,
                    )

                abrir_ingredientes()

            except ValueError as erro:
                mensagem.value = f"Verifique os dados: {erro}"
                page.update()

            except Exception as erro:
                mensagem.value = f"Não foi possível salvar: {erro}"
                page.update()

        titulo_formulario = (
            "Editar ingrediente" if em_edicao else "Novo ingrediente"
        )

        texto_botao = (
            "Salvar alterações" if em_edicao else "Salvar ingrediente"
        )

        controles_formulario = [
            campo_nome,
            campo_marca,
            campo_fornecedor,
            ft.Row(
                controls=[
                    ft.Container(
                        expand=2,
                        content=campo_quantidade,
                    ),
                    ft.Container(
                        expand=1,
                        content=campo_unidade,
                    ),
                ],
            ),
            campo_preco,
            ft.Container(
                bgcolor=ROSA_CLARO,
                padding=15,
                border_radius=12,
                content=ft.Column(
                    spacing=7,
                    controls=[
                        ft.Text(
                            "CÁLCULO DO CUSTO UNITÁRIO",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                        ),
                        previa_custo,
                    ],
                ),
            ),
            campo_observacoes,
            mensagem,
            ft.Container(
                width=380,
                padding=14,
                bgcolor=ROSA,
                border_radius=12,
                on_click=salvar_ingrediente,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(
                            ft.Icons.SAVE_OUTLINED,
                            color=BRANCO,
                        ),
                        ft.Text(
                            texto_botao,
                            color=BRANCO,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            ),
        ]

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(
                        left=15,
                        right=20,
                        top=20,
                        bottom=5,
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=abrir_ingredientes,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
                            ),
                            ft.Text(
                                titulo_formulario,
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=13,
                        controls=controles_formulario,
                    ),
                ),
            ],
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # RECEITAS
    # ==================================================

    filtro_receita = {"tipo": "TODOS"}

    def abrir_receitas(e=None):

        conexao = obter_conexao()

        try:
            receitas_todas = conexao.execute(
                """
                SELECT *
                FROM receitas
                WHERE ativo = 1
                ORDER BY nome
                """
            ).fetchall()
        finally:
            conexao.close()

        receitas_filtradas = [
            r for r in receitas_todas
            if filtro_receita["tipo"] == "TODOS"
            or r["tipo"] == filtro_receita["tipo"]
        ]

        # --------------------------------------------------
        # EXCLUSÃO COM DUPLA CONFIRMAÇÃO
        # --------------------------------------------------

        def confirmar_exclusao_receita(receita_id, nome_receita):

            def cancelar_primeira(e=None):
                dialogo_primeiro.open = False
                page.update()

            def continuar_exclusao(e=None):
                dialogo_primeiro.open = False
                dialogo_segundo.open = True
                page.update()

            def cancelar_segunda(e=None):
                dialogo_segundo.open = False
                page.update()

            def executar_exclusao(e=None):

                try:
                    excluir_receita(receita_id)

                    dialogo_segundo.open = False
                    page.update()

                    abrir_receitas()

                except Exception as erro:

                    dialogo_segundo.open = False

                    mostrar_aviso(f"Erro ao excluir receita: {erro}", "#C62828")

            dialogo_primeiro = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Confirmar exclusão"),
                content=ft.Text(
                    f"Deseja realmente excluir a receita '{nome_receita}'?"
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=cancelar_primeira,
                    ),
                    ft.TextButton(
                        "Continuar",
                        on_click=continuar_exclusao,
                    ),
                ],
            )

            dialogo_segundo = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Segunda confirmação"),
                content=ft.Text(
                    f"Confirma definitivamente a exclusão lógica "
                    f"de '{nome_receita}'?\n\n"
                    f"A receita deixará de aparecer na listagem."
                ),
                actions=[
                    ft.TextButton(
                        "Voltar",
                        on_click=cancelar_segunda,
                    ),
                    ft.TextButton(
                        "Sim, excluir",
                        on_click=executar_exclusao,
                    ),
                ],
            )

            page.overlay.append(dialogo_primeiro)
            page.overlay.append(dialogo_segundo)

            dialogo_primeiro.open = True
            page.update()

        # --------------------------------------------------
        # CARTÕES DAS RECEITAS
        # --------------------------------------------------

        cartoes = []

        for rec in receitas_filtradas:

            calculo = calcular_custo_receita(rec["id"])

            if not calculo:
                continue

            rec_id = rec["id"]
            nome_receita = rec["nome"]

            tipo_tag = (
                "SUB-RECEITA"
                if rec["tipo"] == "SUB_RECEITA"
                else "PRODUTO FINAL"
            )

            custo_insumos = calculo["custo_insumos"]
            rendimento = rec["rendimento_unidades"] or 0

            unidade_rendimento = rec["unidade_rendimento"] or "un"

            if unidade_rendimento not in ("un", "g"):
                unidade_rendimento = "un"

            custo_por_rendimento = (
                custo_insumos / rendimento
                if rendimento > 0
                else 0
            )

            texto_unidade = (
                "grama"
                if unidade_rendimento == "g"
                else "unidade"
            )

            tempo_preparo = rec["tempo_preparo_min"] or 0
            tempo_batedeira = rec["tempo_batedeira_min"] or 0
            tempo_forno = rec["tempo_forno_min"] or 0

            cartoes.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=18,
                    border_radius=18,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Container(
                                        expand=True,
                                        content=ft.Text(
                                            nome_receita,
                                            size=17,
                                            weight=ft.FontWeight.BOLD,
                                            color=MARROM,
                                        ),
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            tipo_tag,
                                            size=9,
                                            color=BRANCO,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        bgcolor=(
                                            ROSA
                                            if rec["tipo"] == "PRODUTO"
                                            else MARROM
                                        ),
                                        padding=ft.Padding.symmetric(
                                            horizontal=8,
                                            vertical=4,
                                        ),
                                        border_radius=8,
                                    ),
                                    ft.Container(
                                        padding=6,
                                        border_radius=8,
                                        on_click=lambda e, item_id=rec_id:
                                            abrir_cadastro_receita(
                                                receita_id=item_id
                                            ),
                                        content=ft.Icon(
                                            ft.Icons.EDIT_OUTLINED,
                                            color=ROSA,
                                            size=21,
                                        ),
                                    ),
                                    ft.Container(
                                        padding=6,
                                        border_radius=8,
                                        on_click=lambda e, item_id=rec_id, nome=nome_receita:
                                            confirmar_exclusao_receita(
                                                item_id,
                                                nome,
                                            ),
                                        content=ft.Icon(
                                            ft.Icons.DELETE_OUTLINED,
                                            color="#B00020",
                                            size=21,
                                        ),
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"Rendimento: {rendimento:g} "
                                f"{unidade_rendimento}",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Custo total dos insumos:",
                                        color=MARROM,
                                        size=12,
                                    ),
                                    ft.Text(
                                        f"R$ {custo_insumos:.2f}",
                                        color=MARROM,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"Custo por {texto_unidade}:",
                                        color=MARROM,
                                        size=12,
                                    ),
                                    ft.Text(
                                        (
                                            f"R$ {custo_por_rendimento:.5f}"
                                            if rendimento > 0
                                            else "Rendimento não informado"
                                        ),
                                        color=ROSA,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Text(
                                "TEMPOS DE PRODUÇÃO",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"Preparo: {tempo_preparo:g} min",
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                    ft.Text(
                                        f"Batedeira: {tempo_batedeira:g} min",
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                    ft.Text(
                                        f"Forno: {tempo_forno:g} min",
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                            ft.Text(
                                "Use o lápis para editar ou a lixeira para excluir.",
                                size=10,
                                color=TEXTO_SECUNDARIO,
                            ),
                        ],
                    ),
                )
            )

        if not cartoes:
            cartoes.append(
                ft.Container(
                    padding=25,
                    bgcolor=BRANCO,
                    border_radius=16,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.MENU_BOOK_OUTLINED,
                                size=40,
                                color=ROSA,
                            ),
                            ft.Text(
                                "Nenhuma receita encontrada para este filtro.",
                                color=MARROM,
                            ),
                        ],
                    ),
                )
            )

        # --------------------------------------------------
        # FILTROS
        # --------------------------------------------------

        def alterar_filtro(novo_tipo):
            filtro_receita["tipo"] = novo_tipo
            abrir_receitas()

        botoes_filtro = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Button(
                    "Todos",
                    bgcolor=(
                        ROSA
                        if filtro_receita["tipo"] == "TODOS"
                        else ROSA_CLARO
                    ),
                    color=(
                        BRANCO
                        if filtro_receita["tipo"] == "TODOS"
                        else MARROM
                    ),
                    on_click=lambda e: alterar_filtro("TODOS"),
                ),
                ft.Button(
                    "Produtos",
                    bgcolor=(
                        ROSA
                        if filtro_receita["tipo"] == "PRODUTO"
                        else ROSA_CLARO
                    ),
                    color=(
                        BRANCO
                        if filtro_receita["tipo"] == "PRODUTO"
                        else MARROM
                    ),
                    on_click=lambda e: alterar_filtro("PRODUTO"),
                ),
                ft.Button(
                    "Sub-receitas",
                    bgcolor=(
                        ROSA
                        if filtro_receita["tipo"] == "SUB_RECEITA"
                        else ROSA_CLARO
                    ),
                    color=(
                        BRANCO
                        if filtro_receita["tipo"] == "SUB_RECEITA"
                        else MARROM
                    ),
                    on_click=lambda e: alterar_filtro("SUB_RECEITA"),
                ),
            ],
        )

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                criar_cabecalho_padrao(
                    "Receitas / Fichas Técnicas",
                    f"{len(receitas_filtradas)} receita(s) exibida(s)",
                    voltar_inicio,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=botoes_filtro,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=criar_botao_primario(
                        "Nova Receita / Ficha Técnica",
                        lambda e: abrir_cadastro_receita(),
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=cartoes,
                    ),
                ),
            ],
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # CADASTRO E EDIÇÃO DE RECEITA
    # ==================================================

    def abrir_cadastro_receita(e=None, receita_id=None):

        ingredientes_disponiveis = listar_ingredientes()

        conexao = obter_conexao()

        try:
            sub_receitas_disponiveis = conexao.execute(
                """
                SELECT *
                FROM receitas
                WHERE ativo = 1
                AND tipo = 'SUB_RECEITA'
                ORDER BY nome
                """
            ).fetchall()
        finally:
            conexao.close()

        dados_edicao = None
        em_edicao = receita_id is not None

        if em_edicao:

            dados_edicao = obter_receita(receita_id)

            if not dados_edicao or not dados_edicao["receita"]:
                abrir_receitas()
                return

        rec = dados_edicao["receita"] if em_edicao else None

        # --------------------------------------------------
        # TIPO DE RECEITA
        # --------------------------------------------------

        dropdown_tipo = criar_dropdown_padrao(
            label="Tipo de Receita",
            value=rec["tipo"] if em_edicao else "PRODUTO",
            options=[
                ft.dropdown.Option(
                    "PRODUTO",
                    "Produto Final (Venda)",
                ),
                ft.dropdown.Option(
                    "SUB_RECEITA",
                    "Sub-receita (Massa / Recheio Base)",
                ),
            ],
            border_radius=12,
        )

        # --------------------------------------------------
        # NOME
        # --------------------------------------------------

        campo_nome_rec = criar_campo_padrao(
            label="Nome da Receita *",
            hint_text="Ex.: BiscoNut / Massa Base",
            value=rec["nome"] if em_edicao else "",
            border_radius=12,
        )

        # --------------------------------------------------
        # RENDIMENTO E UNIDADE
        # --------------------------------------------------

        campo_rendimento = criar_campo_padrao(
            label="Quantidade do rendimento *",
            value=(
                str(rec["rendimento_unidades"])
                if em_edicao else "1"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        dropdown_unidade_rendimento = criar_dropdown_padrao(
            label="Unidade",
            value=(
                rec["unidade_rendimento"]
                if em_edicao else "un"
            ),
            options=[
                ft.dropdown.Option("un", "Unidades (un)"),
                ft.dropdown.Option("g", "Gramas (g)"),
            ],
            border_radius=12,
            expand=True,
        )

        linha_rendimento = ft.Row(
            controls=[
                campo_rendimento,
                dropdown_unidade_rendimento,
            ],
        )

        # --------------------------------------------------
        # TEMPOS DE PRODUÇÃO
        # --------------------------------------------------

        campo_tempo_preparo = criar_campo_padrao(
            label="Tempo de preparo (min)",
            value=(
                str(rec["tempo_preparo_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_tempo_batedeira = criar_campo_padrao(
            label="Tempo de batedeira (min)",
            value=(
                str(rec["tempo_batedeira_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_tempo_forno = criar_campo_padrao(
            label="Tempo de forno (min)",
            value=(
                str(rec["tempo_forno_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        mensagem_rec = ft.Text(
            "",
            size=12,
            color="#B00020",
        )

        # --------------------------------------------------
        # INGREDIENTES E SUB-RECEITAS
        # --------------------------------------------------

        ingredientes_selecionados = []
        lista_insumos_ui = ft.Column(spacing=8)

        opcoes_combo = []

        for ing in ingredientes_disponiveis:
            opcoes_combo.append(
                ft.dropdown.Option(
                    f"ING_{ing['id']}",
                    f"[Insumo] {ing['nome']} ({ing['unidade_base']})",
                )
            )

        for sub in sub_receitas_disponiveis:

            if em_edicao and sub["id"] == receita_id:
                continue

            unidade_sub = sub["unidade_rendimento"] or "un"

            opcoes_combo.append(
                ft.dropdown.Option(
                    f"SUB_{sub['id']}",
                    f"[Sub-Receita] {sub['nome']} ({unidade_sub})",
                )
            )

        def adicionar_insumo_ui(opcao_val=None, qtd_val=""):

            dropdown_combo = criar_dropdown_padrao(
                label="Selecione o Insumo ou Sub-receita",
                value=opcao_val,
                expand=2,
                options=opcoes_combo,
            )

            campo_qtd_usada = criar_campo_padrao(
                label="Qtd usada",
                value=qtd_val,
                expand=1,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            linha = ft.Row(
                controls=[
                    dropdown_combo,
                    campo_qtd_usada,
                ]
            )

            ingredientes_selecionados.append(
                (dropdown_combo, campo_qtd_usada)
            )

            lista_insumos_ui.controls.append(linha)
            page.update()

        if em_edicao and dados_edicao["itens"]:

            for item in dados_edicao["itens"]:

                if item["ingrediente_id"]:
                    adicionar_insumo_ui(
                        f"ING_{item['ingrediente_id']}",
                        str(item["quantidade_usada"]),
                    )

                elif item["sub_receita_id"]:
                    adicionar_insumo_ui(
                        f"SUB_{item['sub_receita_id']}",
                        str(item["quantidade_usada"]),
                    )

        else:
            adicionar_insumo_ui()

        # --------------------------------------------------
        # SALVAR RECEITA
        # --------------------------------------------------

        def salvar_nova_receita(e=None):

            try:
                nome = (campo_nome_rec.value or "").strip()

                if not nome:
                    mensagem_rec.value = "Preencha o nome da receita."
                    page.update()
                    return

                rendimento = float(
                    (campo_rendimento.value or "").replace(",", ".")
                )

                unidade_rendimento = dropdown_unidade_rendimento.value

                if unidade_rendimento not in ("un", "g"):
                    mensagem_rec.value = (
                        "Selecione a unidade do rendimento."
                    )
                    page.update()
                    return

                tempo_preparo = int(
                    float(
                        (campo_tempo_preparo.value or "0").replace(",", ".")
                    )
                )

                tempo_batedeira = int(
                    float(
                        (campo_tempo_batedeira.value or "0").replace(",", ".")
                    )
                )

                tempo_forno = int(
                    float(
                        (campo_tempo_forno.value or "0").replace(",", ".")
                    )
                )

                if rendimento <= 0:
                    mensagem_rec.value = (
                        "O rendimento deve ser maior que zero."
                    )
                    page.update()
                    return

                if min(
                    tempo_preparo,
                    tempo_batedeira,
                    tempo_forno,
                ) < 0:
                    mensagem_rec.value = (
                        "Os tempos não podem ser negativos."
                    )
                    page.update()
                    return

                if not dropdown_tipo.value:
                    mensagem_rec.value = "Selecione o tipo de receita."
                    page.update()
                    return

                lista_ing_salvar = []

                for drop, campo_q in ingredientes_selecionados:

                    valor_selecionado = drop.value
                    quantidade_texto = (
                        campo_q.value or ""
                    ).strip()

                    if not valor_selecionado and not quantidade_texto:
                        continue

                    if not valor_selecionado or not quantidade_texto:
                        mensagem_rec.value = (
                            "Complete o insumo e a quantidade em cada linha."
                        )
                        page.update()
                        return

                    quantidade = float(
                        quantidade_texto.replace(",", ".")
                    )

                    if quantidade <= 0:
                        mensagem_rec.value = (
                            "A quantidade utilizada deve ser maior que zero."
                        )
                        page.update()
                        return

                    if valor_selecionado.startswith("ING_"):

                        lista_ing_salvar.append(
                            {
                                "ingrediente_id": int(
                                    valor_selecionado.replace("ING_", "")
                                ),
                                "quantidade_usada": quantidade,
                            }
                        )

                    elif valor_selecionado.startswith("SUB_"):

                        lista_ing_salvar.append(
                            {
                                "sub_receita_id": int(
                                    valor_selecionado.replace("SUB_", "")
                                ),
                                "quantidade_usada": quantidade,
                            }
                        )

                if not lista_ing_salvar:
                    mensagem_rec.value = (
                        "Adicione ao menos um ingrediente ou sub-receita "
                        "com quantidade."
                    )
                    page.update()
                    return

                parametros = {
                    "nome": nome,
                    "tipo": dropdown_tipo.value,
                    "rendimento_unidades": rendimento,
                    "custo_embalagem_centavos": 0,
                    "margem_lucro_pct": 0,
                    "taxa_cartao_pct": 0,
                    "lista_itens": lista_ing_salvar,
                    "tempo_preparo_min": tempo_preparo,
                    "tempo_batedeira_min": tempo_batedeira,
                    "tempo_forno_min": tempo_forno,
                    "unidade_rendimento": unidade_rendimento,
                }

                if em_edicao:
                    atualizar_receita(
                        receita_id=receita_id,
                        **parametros,
                    )
                else:
                    cadastrar_receita(**parametros)

                abrir_receitas()

            except ValueError as erro:
                mensagem_rec.value = (
                    f"Verifique os dados informados: {erro}"
                )
                page.update()

            except Exception as erro:
                mensagem_rec.value = (
                    f"Erro ao salvar receita: {erro}"
                )
                page.update()

        titulo_form = (
            "Editar Receita / Ficha Técnica"
            if em_edicao
            else "Nova Receita / Ficha Técnica"
        )

        texto_btn_salvar = (
            "Salvar Alterações"
            if em_edicao
            else "Salvar Ficha Técnica"
        )

        controles_form = [
            dropdown_tipo,
            campo_nome_rec,
            ft.Text(
                "RENDIMENTO DA RECEITA",
                weight=ft.FontWeight.BOLD,
                color=MARROM,
                size=13,
            ),
            linha_rendimento,
            ft.Divider(color=ROSA_CLARO),
            ft.Text(
                "TEMPOS DE PRODUÇÃO",
                weight=ft.FontWeight.BOLD,
                color=MARROM,
                size=13,
            ),
            campo_tempo_preparo,
            campo_tempo_batedeira,
            campo_tempo_forno,
            ft.Divider(color=ROSA_CLARO),
            ft.Text(
                "Ingredientes / Sub-receitas Utilizadas",
                weight=ft.FontWeight.BOLD,
                color=MARROM,
            ),
            lista_insumos_ui,
            ft.TextButton(
                "  Mais um ingrediente",
                icon=ft.Icons.ADD,
                on_click=lambda e: adicionar_insumo_ui(),
            ),
            mensagem_rec,
            ft.Container(
                width=380,
                padding=14,
                bgcolor=ROSA,
                border_radius=12,
                on_click=salvar_nova_receita,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(
                            ft.Icons.SAVE_OUTLINED,
                            color=BRANCO,
                        ),
                        ft.Text(
                            texto_btn_salvar,
                            color=BRANCO,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            ),
        ]

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(
                        left=15,
                        right=20,
                        top=20,
                        bottom=5,
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=abrir_receitas,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
                            ),
                            ft.Text(
                                titulo_form,
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=controles_form,
                    ),
                ),
            ],
        )

        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # CUSTOS FIXOS E RATEIO
    # ==================================================

    def abrir_custos_fixos(e=None):

        conexao = obter_conexao()

        try:
            custos = conexao.execute(
                "SELECT * FROM custos_fixos ORDER BY descricao"
            ).fetchall()

            faturamento_row = conexao.execute("SELECT valor FROM configuracoes WHERE chave = 'faturamento_mensal'").fetchone()
            faturamento_atual = faturamento_row["valor"] if faturamento_row else "2000.00"

            taxas_atuais = obter_taxas_pagamento()
            markup_ideal_atual = obter_markup_ideal()
            margem_minima_atual = obter_margem_minima()

        finally:
            conexao.close()

        total_custos = sum(
            c["valor_centavos"] for c in custos
        ) / 100

        faturamento_numero = float(
            str(faturamento_atual).replace(",", ".")
        )

        fator_percentual = (
            (total_custos / faturamento_numero) * 100
            if faturamento_numero > 0 else 0
        )

        campo_faturamento = criar_campo_padrao(
            label="Faturamento Médio Mensal Alvo (R$)",
            value=str(faturamento_atual),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        
        campo_markup_ideal = criar_campo_padrao(
            label="Markup Ideal Padrão (%)",
            value=str(markup_ideal_atual).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_margem_minima = criar_campo_padrao(
            label="Margem Mínima (%)",
            value=str(margem_minima_atual).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )

        campo_taxa_pix = criar_campo_padrao(
            label="Taxa Pix (%)",
            value=str(taxas_atuais["pix"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_dinheiro = criar_campo_padrao(
            label="Taxa Dinheiro (%)",
            value=str(taxas_atuais["dinheiro"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_debito = criar_campo_padrao(
            label="Taxa Débito (%)",
            value=str(taxas_atuais["debito"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_credito = criar_campo_padrao(
            label="Crédito à vista (%)",
            value=str(taxas_atuais["credito_avista"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_parcelado = criar_campo_padrao(
            label="Crédito parcelado (%)",
            value=str(taxas_atuais["credito_parcelado"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )

        mensagem_custos = ft.Text("", size=12, color=ROSA)

        def salvar_configuracoes_acao(e):
            try:
                val_fat = (campo_faturamento.value or "0").replace(",", ".").strip()
                markup_ideal_valor = (campo_markup_ideal.value or "0").replace(",", ".").strip()
                margem_minima_valor = (campo_margem_minima.value or "0").replace(",", ".").strip()
                taxas = {
                    "pix": (campo_taxa_pix.value or "0").replace(",", ".").strip(),
                    "dinheiro": (campo_taxa_dinheiro.value or "0").replace(",", ".").strip(),
                    "debito": (campo_taxa_debito.value or "0").replace(",", ".").strip(),
                    "credito_avista": (campo_taxa_credito.value or "0").replace(",", ".").strip(),
                    "credito_parcelado": (campo_taxa_parcelado.value or "0").replace(",", ".").strip(),
                }

                if float(val_fat) <= 0:
                    mensagem_custos.value = "Informe um faturamento maior que zero."
                    page.update()
                    return

                if float(markup_ideal_valor) < 0 or float(markup_ideal_valor) >= 10000:
                    raise ValueError("O markup ideal deve estar entre 0% e 9999,99%.")
                if float(margem_minima_valor) < 0 or float(margem_minima_valor) >= 100:
                    raise ValueError("A margem mínima deve estar entre 0% e 99,99%.")

                conexao = obter_conexao()
                try:
                    conexao.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES ('faturamento_mensal', ?)", (val_fat,))
                    conexao.commit()
                finally:
                    conexao.close()

                salvar_taxas_pagamento(taxas)
                salvar_markup_ideal(float(markup_ideal_valor))
                salvar_margem_minima(float(margem_minima_valor))
                abrir_custos_fixos()
            except Exception as err:
                mensagem_custos.value = f"Erro ao atualizar: {err}"
                page.update()

        # --------------------------------------------------
        # FORMULÁRIO DE CUSTO FIXO
        # --------------------------------------------------

        def abrir_form_custo_fixo(custo=None):

            em_ed = custo is not None

            c_desc = criar_campo_padrao(
                label="Descrição do Custo Fixo *",
                value=custo["descricao"] if em_ed else "",
                border_radius=12,
            )

            c_val = criar_campo_padrao(
                label="Valor (R$) *",
                value=(
                    f"{custo['valor_centavos'] / 100:.2f}".replace(".", ",")
                    if em_ed else ""
                ),
                keyboard_type=ft.KeyboardType.NUMBER,
                border_radius=12,
            )

            c_msg = ft.Text(
                "",
                size=12,
                color="#B00020",
            )

            def salvar_cf(e):

                try:
                    desc = (c_desc.value or "").strip()

                    v = float(
                        (c_val.value or "").replace(",", ".")
                    )

                    if not desc or v < 0:
                        c_msg.value = (
                            "Preencha a descrição e valor válido."
                        )
                        page.update()
                        return

                    val_centavos = round(v * 100)

                    if em_ed:
                        atualizar_custo_fixo(
                            custo["id"],
                            desc,
                            val_centavos,
                        )
                    else:
                        cadastrar_custo_fixo(
                            desc,
                            val_centavos,
                        )

                    abrir_custos_fixos()

                except Exception as err:
                    c_msg.value = f"Erro: {err}"
                    page.update()

            def deletar_cf(e):

                if em_ed:
                    excluir_custo_fixo(custo["id"])
                    abrir_custos_fixos()

            ctrls = [
                c_desc,
                c_val,
                c_msg,
                ft.Container(
                    width=380,
                    padding=12,
                    bgcolor=ROSA,
                    border_radius=12,
                    on_click=salvar_cf,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Salvar Custo Fixo",
                                color=BRANCO,
                                weight=ft.FontWeight.BOLD,
                            )
                        ],
                    ),
                ),
            ]

            if em_ed:
                ctrls.append(
                    ft.Container(
                        width=380,
                        padding=12,
                        bgcolor="#B00020",
                        border_radius=12,
                        on_click=deletar_cf,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "Excluir Despesa",
                                    color=BRANCO,
                                    weight=ft.FontWeight.BOLD,
                                )
                            ],
                        ),
                    )
                )

            tela_modal = ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=14,
                controls=[
                    ft.Container(
                        padding=ft.Padding.only(
                            left=15,
                            right=20,
                            top=20,
                            bottom=5,
                        ),
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    padding=8,
                                    border_radius=10,
                                    on_click=abrir_custos_fixos,
                                    content=ft.Icon(
                                        ft.Icons.ARROW_BACK,
                                        color=MARROM,
                                        size=24,
                                    ),
                                ),
                                ft.Text(
                                    "Editar Custo Fixo"
                                    if em_ed else "Novo Custo Fixo",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                ),
                            ]
                        ),
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=18),
                        content=ft.Column(
                            spacing=12,
                            controls=ctrls,
                        ),
                    ),
                ],
            )

            page.controls.clear()
            page.add(tela_modal)
            page.update()

        # --------------------------------------------------
        # LISTA DE CUSTOS
        # --------------------------------------------------

        lista_custos = ft.Column(spacing=10)

        for c in custos:

            c_item = c

            lista_custos.controls.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=14,
                    border_radius=12,
                    on_click=lambda e, item=c_item:
                        abrir_form_custo_fixo(item),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        c["descricao"],
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                        size=15,
                                    ),
                                    ft.Text(
                                        "Toque para editar ou excluir",
                                        size=10,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"R$ {c['valor_centavos'] / 100:.2f}",
                                color=ROSA,
                                weight=ft.FontWeight.BOLD,
                                size=16,
                            ),
                        ],
                    ),
                )
            )

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(
                        left=15,
                        right=20,
                        top=20,
                        bottom=10,
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=voltar_inicio,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
                            ),
                            ft.Text(
                                "Custos Fixos & Rateio",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Container(
                                bgcolor=ROSA_CLARO,
                                padding=16,
                                border_radius=14,
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            "RESUMO DO RATEIO DE CUSTO FIXO",
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXTO_SECUNDARIO,
                                        ),
                                        ft.Text(
                                            f"Total Despesas: R$ {total_custos:.2f}",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                            color=MARROM,
                                        ),
                                        ft.Text(
                                            f"Taxa de Rateio: {fator_percentual:.1f}% "
                                            "sobre o custo de insumos",
                                            size=13,
                                            color=ROSA,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ]
                                ),
                            ),
                            campo_faturamento,
                            ft.Text("PARÂMETROS GERAIS DE PRECIFICAÇÃO", weight=ft.FontWeight.BOLD, color=MARROM, size=13),
                            ft.Row(controls=[campo_markup_ideal, campo_margem_minima]),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Text("TAXAS POR FORMA DE PAGAMENTO", weight=ft.FontWeight.BOLD, color=MARROM, size=13),
                            ft.Row(controls=[campo_taxa_pix, campo_taxa_dinheiro]),
                            ft.Row(controls=[campo_taxa_debito, campo_taxa_credito]),
                            campo_taxa_parcelado,
                            mensagem_custos,
                            ft.Container(
                                width=380, padding=12, bgcolor=ROSA, border_radius=12, on_click=salvar_configuracoes_acao,
                                content=ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Text("Atualizar Configurações", color=BRANCO, weight=ft.FontWeight.BOLD)])
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Despesas Fixas Cadastradas:",
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.IconButton(
                                        ft.Icons.ADD_CIRCLE,
                                        icon_color=ROSA,
                                        on_click=lambda e:
                                            abrir_form_custo_fixo(),
                                    ),
                                ],
                            ),
                            lista_custos,
                        ],
                    ),
                ),
            ],
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # RELATÓRIOS
    # ==================================================

    def abrir_relatorios(e=None):

        conexao = obter_conexao()

        try:
            receitas = conexao.execute(
                """
                SELECT *
                FROM receitas
                WHERE ativo = 1
                ORDER BY tipo DESC, nome
                """
            ).fetchall()

            custos = conexao.execute(
                """
                SELECT *
                FROM custos_fixos
                """
            ).fetchall()

            ingredientes = conexao.execute(
                """
                SELECT *
                FROM ingredientes
                WHERE ativo = 1
                """
            ).fetchall()

            fat_row = conexao.execute(
                """
                SELECT valor
                FROM configuracoes
                WHERE chave = 'faturamento_mensal'
                """
            ).fetchone()

            faturamento_alvo = (
                float(fat_row["valor"])
                if fat_row else 2000.0
            )

        finally:
            conexao.close()

        total_despesas_fixas = (
            sum(c["valor_centavos"] for c in custos) / 100
        )

        produtos_relatorio = []

        for receita in receitas:

            calculo = calcular_custo_receita(receita["id"])

            if not calculo:
                continue

            if receita["tipo"] == "PRODUTO":

                precificacao = calcular_precificacao_produto(
                    receita["id"]
                )

                if precificacao:

                    preco_venda = precificacao["preco_venda_sugerido"]
                    lucro = precificacao["lucro_unitario"]

                    margem_real = (
                        lucro / preco_venda * 100
                        if preco_venda > 0 else 0
                    )

                    produtos_relatorio.append(
                        {
                            "nome": receita["nome"],
                            "tipo": "Produto final",
                            "custo_unitario": precificacao["custo_unitario"],
                            "preco_sugerido": preco_venda,
                            "lucro": lucro,
                            "margem_real": margem_real,
                        }
                    )

                else:

                    rendimento = receita["rendimento_unidades"] or 0

                    custo_fixo_receita = calcular_custo_fixo_proporcional(
                        receita["id"]
                    )
                    custo_total_receita = (
                        calculo["custo_insumos"] + custo_fixo_receita
                    )
                    custo_unitario = (
                        custo_total_receita / rendimento
                        if rendimento > 0 else 0
                    )

                    produtos_relatorio.append(
                        {
                            "nome": receita["nome"],
                            "tipo": "Produto final",
                            "custo_unitario": custo_unitario,
                            "preco_sugerido": None,
                            "lucro": None,
                            "margem_real": None,
                        }
                    )

            else:

                rendimento = receita["rendimento_unidades"] or 0

                custo_unitario = (
                    calculo["custo_insumos"] / rendimento
                    if rendimento > 0 else 0
                )

                produtos_relatorio.append(
                    {
                        "nome": receita["nome"],
                        "tipo": "Sub-receita",
                        "custo_unitario": custo_unitario,
                        "preco_sugerido": None,
                        "lucro": None,
                        "margem_real": None,
                    }
                )

        # --------------------------------------------------
        # CARTÕES DO RELATÓRIO
        # --------------------------------------------------

        cartoes_relatorio = []

        for item in produtos_relatorio:

            if item["tipo"] == "Sub-receita":

                conteudo = ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            item["nome"],
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                            size=15,
                        ),
                        ft.Text(
                            "Sub-receita — custo de produção",
                            size=11,
                            color=TEXTO_SECUNDARIO,
                        ),
                        ft.Text(
                            f"Custo por unidade de rendimento: "
                            f"R$ {item['custo_unitario']:.4f}",
                            color=ROSA,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                )

            elif item["preco_sugerido"] is None:

                conteudo = ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            item["nome"],
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                            size=15,
                        ),
                        ft.Text(
                            "Produto final — ainda não precificado",
                            size=11,
                            color=TEXTO_SECUNDARIO,
                        ),
                        ft.Text(
                            f"Custo por unidade de rendimento: "
                            f"R$ {item['custo_unitario']:.4f}",
                            color=ROSA,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                )

            else:

                conteudo = ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    item["nome"],
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                    size=15,
                                ),
                                ft.Text(
                                    f"Lucro: R$ {item['lucro']:.2f}",
                                    color=ROSA,
                                    weight=ft.FontWeight.BOLD,
                                    size=14,
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    f"Custo: R$ {item['custo_unitario']:.4f}",
                                    size=12,
                                    color=TEXTO_SECUNDARIO,
                                ),
                                ft.Text(
                                    f"Preço: R$ {item['preco_sugerido']:.2f}",
                                    size=12,
                                    color=MARROM,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
                        ft.Text(
                            f"Margem efetiva: {item['margem_real']:.1f}%",
                            size=11,
                            color=ROSA,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                )

            cartoes_relatorio.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=14,
                    border_radius=12,
                    content=conteudo,
                )
            )

        if not cartoes_relatorio:
            cartoes_relatorio.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=16,
                    border_radius=12,
                    content=ft.Text(
                        "Ainda não existem dados para exibir.",
                        color=TEXTO_SECUNDARIO,
                    ),
                )
            )

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(
                        left=15,
                        right=20,
                        top=20,
                        bottom=10,
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=voltar_inicio,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
                            ),
                            ft.Text(
                                "Relatórios & Lucratividade",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Container(
                                bgcolor=ROSA_CLARO,
                                padding=16,
                                border_radius=14,
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            "INDICADORES GERAIS",
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXTO_SECUNDARIO,
                                        ),
                                        ft.Row(
                                            controls=[
                                                criar_indicador(
                                                    str(len(receitas)),
                                                    "Receitas cadastradas",
                                                    MARROM,
                                                ),
                                                criar_indicador(
                                                    str(len(ingredientes)),
                                                    "Insumos cadastrados",
                                                    MARROM,
                                                ),
                                            ],
                                        ),
                                        ft.Divider(color=ROSA),
                                        ft.Row(
                                            controls=[
                                                criar_indicador(
                                                    f"R$ {total_despesas_fixas:.2f}",
                                                    "Despesas fixas",
                                                    MARROM,
                                                ),
                                                criar_indicador(
                                                    f"R$ {faturamento_alvo:.2f}",
                                                    "Faturamento alvo",
                                                    ROSA,
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ),
                            ft.Text(
                                "Custos e lucratividade",
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                            ft.Column(
                                spacing=10,
                                controls=cartoes_relatorio,
                            ),
                        ],
                    ),
                ),
            ],
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # PAINEL INICIAL - DM GULOSITOS
    # ==================================================

    def criar_card_painel(icone, valor, titulo, descricao, cor, acao):
        return ft.Container(
            expand=True,
            bgcolor=BRANCO,
            padding=14,
            border_radius=16,
            on_click=acao,
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        bgcolor=ROSA_CLARO,
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icone, color=cor, size=22),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(str(valor), size=22, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(titulo, size=12, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(descricao, size=10, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                ],
            ),
        )

    def montar_painel_inicial():
        painel = obter_dados_painel()
        agora = datetime.now()
        hora = agora.hour
        saudacao = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")

        cabecalho = ft.Container(
            margin=ft.Margin.only(left=18, right=18, top=18),
            padding=16,
            bgcolor=BRANCO,
            border_radius=20,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    ft.Container(
                        width=82,
                        height=82,
                        padding=4,
                        bgcolor=ROSA_CLARO,
                        border_radius=16,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Image(
                            src=LOGO_DM_BASE64,
                            width=74,
                            height=74,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(f"{saudacao}!", size=21, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text("Painel de gestão da doceria", size=12, color=TEXTO_SECUNDARIO),
                            ft.Text(agora.strftime("%d/%m/%Y"), size=11, color=ROSA, weight=ft.FontWeight.BOLD),
                        ],
                    ),
                ],
            ),
        )

        indicadores = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_card_painel(
                            ft.Icons.SEND,
                            painel["aguardando_retorno"],
                            "Enviados",
                            "Orçamentos aguardando retorno",
                            ROSA,
                            lambda ev: abrir_orcamentos(filtro_status="Enviado"),
                        ),
                        criar_card_painel(
                            ft.Icons.CHECK_CIRCLE,
                            painel["aprovados"],
                            "Aprovados",
                            "Encomendas confirmadas",
                            "#2E7D32",
                            lambda ev: abrir_orcamentos(filtro_status="Aprovado"),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_card_painel(
                            ft.Icons.EDIT,
                            painel["em_elaboracao"],
                            "Em elaboração",
                            "Orçamentos não enviados",
                            "#A66A20",
                            lambda ev: abrir_orcamentos(filtro_status="Em elaboração"),
                        ),
                        criar_card_painel(
                            ft.Icons.CANCEL,
                            painel["recusados"],
                            "Recusados",
                            "Orçamentos não aprovados",
                            "#A52D35",
                            lambda ev: abrir_orcamentos(filtro_status="Recusado"),
                        ),
                    ],
                ),
            ],
        )

        entregas_controles = []
        for entrega in painel["entregas"]:
            try:
                data_entrega_texto = datetime.strptime(
                    str(entrega["data_entrega"])[:10], "%Y-%m-%d"
                ).strftime("%d/%m")
            except (ValueError, TypeError):
                data_entrega_texto = str(entrega["data_entrega"] or "—")

            entregas_controles.append(
                ft.Container(
                    padding=12,
                    bgcolor=ROSA_CLARO,
                    border_radius=12,
                    on_click=lambda ev, oid=entrega["id"]: abrir_orcamentos(orcamento_id=oid),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=48,
                                height=48,
                                bgcolor=BRANCO,
                                border_radius=12,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    spacing=0,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ROSA),
                                        ft.Text(data_entrega_texto, size=11, weight=ft.FontWeight.BOLD, color=MARROM),
                                    ],
                                ),
                            ),
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        entrega["cliente"] or "Cliente não informado",
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                        size=13,
                                    ),
                                    ft.Text(f'Orçamento {entrega["numero"]}', size=10, color=TEXTO_SECUNDARIO),
                                ],
                            ),
                            ft.Text(
                                "R$ " + f'{entrega["total_final_centavos"] / 100:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."),
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                )
            )

        if not entregas_controles:
            entregas_controles.append(
                ft.Container(
                    padding=16,
                    bgcolor=ROSA_CLARO,
                    border_radius=12,
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.CALENDAR_TODAY, color=ROSA, size=24),
                            ft.Text(
                                "Nenhuma entrega aprovada nos próximos 7 dias. "
                                "Cadastre a data de entrega nos novos orçamentos.",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                                expand=True,
                            ),
                        ],
                    ),
                )
            )

        atividades_controles = []
        for atividade in painel["atividades"]:
            icone = {
                "Orçamento": ft.Icons.DESCRIPTION_OUTLINED,
                "Insumo": ft.Icons.INVENTORY_2_OUTLINED,
                "Precificação": ft.Icons.CALCULATE_OUTLINED,
            }.get(atividade["tipo"], ft.Icons.HISTORY)

            data_atividade = str(atividade["data"] or "")
            try:
                data_atividade = datetime.fromisoformat(
                    data_atividade.replace("Z", "+00:00")
                ).strftime("%d/%m %H:%M")
            except (ValueError, TypeError):
                data_atividade = data_atividade[:16].replace("T", " ")

            atividades_controles.append(
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(
                            width=34,
                            height=34,
                            bgcolor=ROSA_CLARO,
                            border_radius=10,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(icone, color=ROSA, size=18),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(atividade["descricao"], size=12, weight=ft.FontWeight.BOLD, color=MARROM),
                                ft.Text(
                                    f'{atividade["tipo"]} • {atividade["detalhe"]}',
                                    size=10,
                                    color=TEXTO_SECUNDARIO,
                                ),
                            ],
                        ),
                        ft.Text(data_atividade, size=9, color=TEXTO_SECUNDARIO),
                    ],
                )
            )

        if not atividades_controles:
            atividades_controles.append(
                ft.Text(
                    "As movimentações recentes aparecerão aqui.",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                )
            )

        atalhos_painel = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_atalho(
                            ft.Icons.ADD_CIRCLE_OUTLINE,
                            "Novo orçamento",
                            "Criar proposta para cliente",
                            ROSA,
                            abrir_orcamentos,
                        ),
                        criar_atalho(
                            ft.Icons.CALCULATE_OUTLINED,
                            "Precificação",
                            "Calcular preço de venda",
                            ROSA,
                            abrir_precificacao,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_atalho(
                            ft.Icons.MENU_BOOK_OUTLINED,
                            "Receitas",
                            "Fichas técnicas",
                            ROSA,
                            abrir_receitas,
                        ),
                        criar_atalho(
                            ft.Icons.INVENTORY_2_OUTLINED,
                            "Insumos",
                            "Cadastro e preços",
                            ROSA,
                            abrir_ingredientes,
                        ),
                    ],
                ),
            ],
        )

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                cabecalho,
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Visão geral", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(
                                "Acompanhe os orçamentos e a rotina da doceria.",
                                size=11,
                                color=TEXTO_SECUNDARIO,
                            ),
                            indicadores,
                            ft.Text("Acessos rápidos", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            atalhos_painel,
                            ft.Text("Próximas encomendas", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(
                                "Entregas aprovadas previstas para os próximos 7 dias.",
                                size=11,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Container(
                                padding=12,
                                bgcolor=BRANCO,
                                border_radius=16,
                                content=ft.Column(spacing=9, controls=entregas_controles),
                            ),
                            ft.Text("Atividades recentes", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Container(
                                padding=14,
                                bgcolor=BRANCO,
                                border_radius=16,
                                content=ft.Column(spacing=12, controls=atividades_controles),
                            ),
                        ],
                    ),
                ),
            ],
        )

    # ==================================================
    # MENU INFERIOR
    # ==================================================

    navegacao = ft.NavigationBar(
        selected_index=0,
        on_change=navegar,
        bgcolor=BRANCO,
        indicator_color=ROSA_CLARO,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="Início",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PRICE_CHANGE_OUTLINED,
                selected_icon=ft.Icons.PRICE_CHANGE,
                label="Precificação",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.MENU,
                label="Menu",
            ),
        ],
    )

    # ==================================================
    # TELA INICIAL
    # ==================================================

    conteudo = montar_painel_inicial()

    page.navigation_bar = navegacao
    page.add(conteudo)


# ==================================================
# COMPONENTES AUXILIARES
# ==================================================

def criar_indicador(valor, descricao, cor):

    return ft.Column(
        expand=True,
        spacing=4,
        controls=[
            ft.Text(
                valor,
                size=22,
                weight=ft.FontWeight.BOLD,
                color=cor,
            ),
            ft.Text(
                descricao,
                size=11,
                color="#876A65",
            ),
        ],
    )


def criar_atalho(icone, titulo, descricao, cor, acao=None):

    return ft.Container(
        expand=True,
        bgcolor="#FFFFFF",
        padding=16,
        border_radius=18,
        on_click=acao,
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Icon(
                    icone,
                    color=cor,
                    size=28,
                ),
                ft.Text(
                    titulo,
                    color="#603D3B",
                    weight=ft.FontWeight.BOLD,
                    size=14,
                ),
                ft.Text(
                    descricao,
                    color="#876A65",
                    size=11,
                ),
            ],
        ),
    )


# ==================================================
# EXECUÇÃO
# ==================================================

if __name__ == "__main__":
    ft.run(main)
