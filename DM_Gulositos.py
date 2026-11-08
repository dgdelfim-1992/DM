import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
import flet as ft
import os
import shutil

from database.banco import (
    CAMINHO_BANCO,
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
)


def main(page: ft.Page):

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
        indice_atual["valor"] = 0
        navegacao.selected_index = 0
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

    def abrir_menu_opcoes(e=None):
        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=10),
                    content=ft.Text("Menu Principal", size=24, weight=ft.FontWeight.BOLD, color=MARROM),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            criar_atalho(ft.Icons.INVENTORY_2_OUTLINED, "Insumos", "Gerenciar estoque e preços", ROSA, abrir_ingredientes),
                            criar_atalho(ft.Icons.MENU_BOOK_OUTLINED, "Receitas", "Fichas técnicas e tempos", ROSA, abrir_receitas),
                            criar_atalho(ft.Icons.CALCULATE_OUTLINED, "Custos Fixos", "Despesas, rateio e taxas", ROSA, abrir_custos_fixos),
                            criar_atalho(ft.Icons.BAR_CHART_OUTLINED, "Relatórios", "Análise de lucratividade", ROSA, abrir_relatorios),
                            criar_atalho(ft.Icons.SAVE_OUTLINED, "Backup / Exportar", "Salvar e restaurar dados", ROSA, abrir_tela_backup),
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

        dialogo = ft.AlertDialog(
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

            dialogo = ft.AlertDialog(
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

        dd_receita = ft.Dropdown(
            label="Produto Final",
            options=[ft.dropdown.Option(str(r["id"]), r["nome"]) for r in receitas],
            value=str(dados_atuais["receita_id"]) if em_edicao else str(receitas[0]["id"]),
            border_radius=12,
        )

        tf_qtd_emb = ft.TextField(
            label="Qtd. de Produto na Embalagem",
            value=str(dados_atuais["quantidade_embalagem"]) if em_edicao else "1",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        tf_custo_emb = ft.TextField(
            label="Embalagem + Sacola (R$)",
            value=(
                f"{dados_atuais['custo_embalagem_centavos'] / 100:.2f}".replace(".", ",")
                if em_edicao else "0,00"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        tf_preco_praticado = ft.TextField(
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

        dd_tipo_desconto = ft.Dropdown(
            label="Tipo de desconto",
            value="percentual",
            options=[
                ft.dropdown.Option("percentual", "Porcentagem (%)"),
                ft.dropdown.Option("valor", "Valor em reais (R$)"),
            ],
            border_radius=12,
            expand=True,
        )
        tf_desconto = ft.TextField(
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

                if valor_desconto <= 0:
                    lbl_alerta_desconto.value = "Sem desconto aplicado. Informe um valor para simular uma promoção."
                    lbl_alerta_desconto.color = TEXTO_SECUNDARIO
                else:
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

                    if all(margens_desconto):
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
                            painel_desconto,
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

                    dialogo_erro = ft.AlertDialog(
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

                    dialogo_erro = ft.AlertDialog(
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

            dialogo_primeiro = ft.AlertDialog(
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

            dialogo_segundo = ft.AlertDialog(
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
                    padding=16,
                    border_radius=16,
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
                ft.Container(
                    padding=ft.Padding.only(
                        left=15,
                        right=20,
                        top=20,
                        bottom=10,
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.START,
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
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Ingredientes",
                                        size=23,
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.Text(
                                        f"{len(ingredientes)} ingrediente(s) cadastrado(s)",
                                        size=12,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        width=380,
                        padding=14,
                        bgcolor=ROSA,
                        border_radius=12,
                        on_click=abrir_cadastro_ingrediente,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ADD, color=BRANCO),
                                ft.Text(
                                    "Adicionar ingrediente",
                                    color=BRANCO,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
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

        campo_nome = ft.TextField(
            label="Nome do ingrediente *",
            hint_text="Ex.: Farinha de trigo",
            value=ingrediente["nome"] if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_marca = ft.TextField(
            label="Marca",
            hint_text="Ex.: Qualy",
            value=(ingrediente["marca"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_fornecedor = ft.TextField(
            label="Fornecedor ou estabelecimento",
            hint_text="Onde foi comprado?",
            value=(ingrediente["fornecedor"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_quantidade = ft.TextField(
            label="Quantidade da embalagem *",
            hint_text="Ex.: 500",
            value=str(ingrediente["quantidade_compra"]) if em_edicao else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_unidade = ft.Dropdown(
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

        campo_preco = ft.TextField(
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

        campo_observacoes = ft.TextField(
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

            dialogo_primeiro = ft.AlertDialog(
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

            dialogo_segundo = ft.AlertDialog(
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
                    padding=16,
                    border_radius=16,
                    content=ft.Column(
                        spacing=8,
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
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Receitas / Fichas Técnicas",
                                        size=22,
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.Text(
                                        f"{len(receitas_filtradas)} receita(s) exibida(s)",
                                        size=12,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=botoes_filtro,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        width=380,
                        padding=14,
                        bgcolor=ROSA,
                        border_radius=12,
                        on_click=lambda e: abrir_cadastro_receita(),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ADD, color=BRANCO),
                                ft.Text(
                                    "Nova Receita / Ficha Técnica",
                                    color=BRANCO,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
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

        dropdown_tipo = ft.Dropdown(
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

        campo_nome_rec = ft.TextField(
            label="Nome da Receita *",
            hint_text="Ex.: BiscoNut / Massa Base",
            value=rec["nome"] if em_edicao else "",
            border_radius=12,
        )

        # --------------------------------------------------
        # RENDIMENTO E UNIDADE
        # --------------------------------------------------

        campo_rendimento = ft.TextField(
            label="Quantidade do rendimento *",
            value=(
                str(rec["rendimento_unidades"])
                if em_edicao else "1"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        dropdown_unidade_rendimento = ft.Dropdown(
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

        campo_tempo_preparo = ft.TextField(
            label="Tempo de preparo (min)",
            value=(
                str(rec["tempo_preparo_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_tempo_batedeira = ft.TextField(
            label="Tempo de batedeira (min)",
            value=(
                str(rec["tempo_batedeira_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_tempo_forno = ft.TextField(
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

            dropdown_combo = ft.Dropdown(
                label="Selecione o Insumo ou Sub-receita",
                value=opcao_val,
                expand=2,
                options=opcoes_combo,
            )

            campo_qtd_usada = ft.TextField(
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

        campo_faturamento = ft.TextField(
            label="Faturamento Médio Mensal Alvo (R$)",
            value=str(faturamento_atual),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        
        campo_markup_ideal = ft.TextField(
            label="Markup Ideal Padrão (%)",
            value=str(markup_ideal_atual).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_margem_minima = ft.TextField(
            label="Margem Mínima (%)",
            value=str(margem_minima_atual).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )

        campo_taxa_pix = ft.TextField(
            label="Taxa Pix (%)",
            value=str(taxas_atuais["pix"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_dinheiro = ft.TextField(
            label="Taxa Dinheiro (%)",
            value=str(taxas_atuais["dinheiro"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_debito = ft.TextField(
            label="Taxa Débito (%)",
            value=str(taxas_atuais["debito"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_credito = ft.TextField(
            label="Crédito à vista (%)",
            value=str(taxas_atuais["credito_avista"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_parcelado = ft.TextField(
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

            c_desc = ft.TextField(
                label="Descrição do Custo Fixo *",
                value=custo["descricao"] if em_ed else "",
                border_radius=12,
            )

            c_val = ft.TextField(
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

                    custo_unitario = (
                        calculo["custo_insumos"] / rendimento
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
    # CABEÇALHO DA HOME
    # ==================================================

    cabecalho = ft.Container(
        padding=ft.Padding.only(
            left=20,
            right=20,
            top=25,
            bottom=15,
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Text(
                            "DM Gulositos",
                            size=25,
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                        ),
                        ft.Text(
                            "GESTÃO E PRECIFICAÇÃO",
                            size=10,
                            color=TEXTO_SECUNDARIO,
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor=BRANCO,
                    padding=12,
                    border_radius=15,
                    content=ft.Icon(
                        ft.Icons.CAKE_OUTLINED,
                        color=ROSA,
                        size=30,
                    ),
                ),
            ],
        ),
    )

    # ==================================================
    # CARTÃO DE RESUMO
    # ==================================================

    resumo = ft.Container(
        bgcolor=BRANCO,
        padding=20,
        border_radius=18,
        content=ft.Column(
            spacing=15,
            controls=[
                ft.Text(
                    "RESUMO DO NEGÓCIO",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=TEXTO_SECUNDARIO,
                ),
                ft.Row(
                    controls=[
                        criar_indicador(
                            "29",
                            "Insumos no estoque",
                            MARROM,
                        ),
                        criar_indicador(
                            "19.5%",
                            "Taxa Custo Fixo",
                            MARROM,
                        ),
                    ],
                ),
                ft.Divider(color=ROSA_CLARO),
                ft.Row(
                    controls=[
                        criar_indicador(
                            "100%",
                            "Margem padrão",
                            ROSA,
                        ),
                        criar_indicador(
                            "R$ 2.000",
                            "Fat. Mensal Alvo",
                            MARROM,
                        ),
                    ],
                ),
            ],
        ),
    )

    # ==================================================
    # ACESSOS PRINCIPAIS
    # ==================================================

    atalhos = ft.Column(
        spacing=12,
        controls=[
            ft.Text(
                "O que deseja fazer?",
                size=19,
                weight=ft.FontWeight.BOLD,
                color=MARROM,
            ),
            ft.Row(
                controls=[
                    criar_atalho(
                        ft.Icons.INVENTORY_2_OUTLINED,
                        "Ingredientes",
                        "Insumos e preços",
                        ROSA,
                        abrir_ingredientes,
                    ),
                    criar_atalho(
                        ft.Icons.MENU_BOOK_OUTLINED,
                        "Receitas",
                        "Fichas técnicas",
                        ROSA,
                        abrir_receitas,
                    ),
                ],
            ),
            ft.Row(
                controls=[
                    criar_atalho(
                        ft.Icons.CALCULATE_OUTLINED,
                        "Precificação",
                        "Preço de venda dos produtos",
                        ROSA,
                        abrir_precificacao,
                    ),
                    criar_atalho(
                        ft.Icons.BAR_CHART_OUTLINED,
                        "Relatórios",
                        "Custos e lucros",
                        ROSA,
                        abrir_relatorios,
                    ),
                ],
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

    conteudo = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=18,
        controls=[
            cabecalho,
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=18),
                content=ft.Column(
                    spacing=18,
                    controls=[
                        resumo,
                        atalhos,
                    ],
                ),
            ),
        ],
    )

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
        padding=15,
        border_radius=16,
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
