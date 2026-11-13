import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import flet as ft
import os
import shutil
import json

from logo_dm import LOGO_DM_BASE64
from telas.menu import criar_tela_menu
from telas.agenda import criar_abrir_agenda_producao
from telas.orcamentos import criar_abrir_orcamentos
from telas.ingredientes import criar_abrir_ingredientes
from telas.receitas import criar_abrir_receitas
from telas.custos_fixos import criar_abrir_custos_fixos
from telas.relatorios import criar_telas_relatorios
from componentes.ui import criar_componentes_padrao

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
    obter_remuneracao_mensal_desejada,
    salvar_remuneracao_mensal_desejada,
    obter_impostos_pct,
    salvar_impostos_pct,
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
    componentes = criar_componentes_padrao(
        ft,
        {
            "marrom": MARROM,
            "rosa": ROSA,
            "rosa_claro": ROSA_CLARO,
            "branco": BRANCO,
            "texto_secundario": TEXTO_SECUNDARIO,
        },
    )
    criar_campo_padrao = componentes["campo"]
    criar_dropdown_padrao = componentes["dropdown"]
    criar_dialogo_padrao = componentes["dialogo"]
    criar_cabecalho_padrao = componentes["cabecalho"]
    criar_botao_primario = componentes["botao_primario"]

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
    # Referência compartilhada: a barra é criada depois das fábricas de tela.
    navegacao_ref = {"controle": None}

    abrir_agenda_producao = criar_abrir_agenda_producao({
        "ft": ft,
        "datetime": datetime,
        "timedelta": timedelta,
        "json": json,
        "listar_agenda_producao": listar_agenda_producao,
        "atualizar_status_producao": atualizar_status_producao,
        "mostrar_aviso": mostrar_aviso,
        "BRANCO": BRANCO,
        "ROSA": ROSA,
        "ROSA_CLARO": ROSA_CLARO,
        "MARROM": MARROM,
        "TEXTO_SECUNDARIO": TEXTO_SECUNDARIO,
        "page": page,
        "abrir_menu_opcoes": lambda ev=None: abrir_menu_opcoes(ev),
        "indice_atual": indice_atual,
        "navegacao_ref": navegacao_ref,
    })

    def abrir_menu_opcoes(e=None):
        tela = criar_tela_menu(
            ft,
            acoes={
                "ingredientes": abrir_ingredientes,
                "receitas": abrir_receitas,
                "custos_fixos": abrir_custos_fixos,
                "orcamentos": abrir_orcamentos,
                "agenda": abrir_agenda_producao,
                "relatorios": abrir_relatorios,
                "backup": abrir_tela_backup,
            },
            cores={
                "marrom": MARROM,
                "rosa": ROSA,
                "rosa_claro": ROSA_CLARO,
                "branco": BRANCO,
                "texto_secundario": TEXTO_SECUNDARIO,
            },
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

        # Usa a maior taxa configurada para precificações ainda sem preço praticado.
        taxas_lista = obter_taxas_pagamento()
        taxa_cartao = max([float(v) for v in taxas_lista.values()] or [0.0])

        for prec in precificacoes:
            preco_praticado = prec['preco_praticado_centavos'] / 100
            
            # Recalcular os dados para descobrir o status da margem
            # Passando os argumentos na ordem correta (posicional) sem os nomes
            res = calcular_simulacao_precificacao(
                prec['receita_id'], prec['quantidade_embalagem'],
                prec['custo_embalagem_centavos'], prec['markup_ideal_pct'],
                prec['preco_praticado_centavos'], taxa_cartao,
                embalagem_id=prec["embalagem_id"],
                quantidade_embalagem_insumo=prec["quantidade_embalagem_insumo"],
                sacola_id=prec["sacola_id"],
                quantidade_sacola=prec["quantidade_sacola"],
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
    abrir_orcamentos = criar_abrir_orcamentos({
        "ft": ft,
        "datetime": datetime,
        "json": json,
        "page": page,
        "BRANCO": BRANCO,
        "MARROM": MARROM,
        "ROSA": ROSA,
        "ROSA_CLARO": ROSA_CLARO,
        "TEXTO_SECUNDARIO": TEXTO_SECUNDARIO,
        "ids_orcamentos_selecionados": ids_orcamentos_selecionados,
        "obter_orcamento": obter_orcamento,
        "listar_precificacoes": listar_precificacoes,
        "obter_taxas_pagamento": obter_taxas_pagamento,
        "obter_margem_minima": obter_margem_minima,
        "calcular_simulacao_precificacao": calcular_simulacao_precificacao,
        "criar_dialogo_padrao": criar_dialogo_padrao,
        "mostrar_aviso": mostrar_aviso,
        "excluir_orcamentos": excluir_orcamentos,
        "listar_orcamentos": listar_orcamentos,
        "atualizar_status_orcamento": atualizar_status_orcamento,
        "listar_versoes_orcamento": listar_versoes_orcamento,
        "criar_campo_padrao": criar_campo_padrao,
        "criar_dropdown_padrao": criar_dropdown_padrao,
        "abrir_menu_opcoes": lambda ev=None: abrir_menu_opcoes(ev),
        "indice_atual": indice_atual,
        "navegacao_ref": navegacao_ref,
        "atualizar_orcamento_salvo": atualizar_orcamento_salvo,
        "salvar_orcamento": salvar_orcamento,
    })
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
        insumos_embalagem = listar_ingredientes()
        opcoes_insumos = [ft.dropdown.Option("", "Não utilizar")] + [
            ft.dropdown.Option(str(item["id"]), item["nome"])
            for item in insumos_embalagem
        ]

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
            label="Outros custos de embalagem (R$)",
            value=(
                f"{dados_atuais['custo_embalagem_centavos'] / 100:.2f}".replace(".", ",")
                if em_edicao else "0,00"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        dd_embalagem = criar_dropdown_padrao(
            label="Embalagem cadastrada como insumo",
            options=opcoes_insumos,
            value=str(dados_atuais["embalagem_id"] or "") if em_edicao else "",
            border_radius=12,
            expand=True,
        )
        tf_qtd_embalagem_insumo = criar_campo_padrao(
            label="Quantidade de embalagens",
            value=str(dados_atuais["quantidade_embalagem_insumo"] or 0) if em_edicao else "0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )
        dd_sacola = criar_dropdown_padrao(
            label="Sacola cadastrada como insumo",
            options=opcoes_insumos,
            value=str(dados_atuais["sacola_id"] or "") if em_edicao else "",
            border_radius=12,
            expand=True,
        )
        tf_qtd_sacola = criar_campo_padrao(
            label="Quantidade de sacolas",
            value=str(dados_atuais["quantidade_sacola"] or 0) if em_edicao else "0",
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
        lbl_mao_obra = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=MARROM)
        lbl_embalagens = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=MARROM)
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
                                    ft.Text("Resultado após rateio", size=12, color=TEXTO_SECUNDARIO),
                                    lbl_lucro,
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Margem de contribuição", size=12, color=TEXTO_SECUNDARIO),
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
                embalagem_id = int(dd_embalagem.value) if dd_embalagem.value else None
                qtd_embalagem_insumo = float((tf_qtd_embalagem_insumo.value or "0").replace(",", "."))
                sacola_id = int(dd_sacola.value) if dd_sacola.value else None
                qtd_sacola = float((tf_qtd_sacola.value or "0").replace(",", "."))
                if embalagem_id and qtd_embalagem_insumo <= 0:
                    raise ValueError("Informe a quantidade de embalagens utilizada.")
                if sacola_id and qtd_sacola <= 0:
                    raise ValueError("Informe a quantidade de sacolas utilizada.")
                preco_praticado = float(
                    (tf_preco_praticado.value or "0").replace(",", ".")
                )

                # Usa a maior taxa cadastrada para que o preço sugerido cubra
                # todas as formas de pagamento configuradas.
                taxa_referencia = max([float(v) for v in taxas_pagamento.values()] or [0.0])
                resultado = calcular_simulacao_precificacao(
                    rec_id, qtd_emb, custo_emb, markup_ideal, 0,
                    taxa_referencia, margem_minima,
                    embalagem_id=embalagem_id,
                    quantidade_embalagem_insumo=qtd_embalagem_insumo,
                    sacola_id=sacola_id,
                    quantidade_sacola=qtd_sacola,
                )

                if not resultado:
                    raise ValueError("Não foi possível calcular os custos do produto.")

                custo_total = resultado["custo_total"]
                preco_sugerido = resultado["preco_sugerido"]
                usar_preco_praticado = preco_praticado > 0
                preco_referencia = preco_praticado if usar_preco_praticado else preco_sugerido

                lbl_insumo.value = formatar_reais(resultado["custo_insumo"])
                lbl_mao_obra.value = formatar_reais(resultado["custo_mao_obra"])
                lbl_embalagens.value = formatar_reais(resultado["custo_embalagem"])
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
                    valor_impostos = preco_referencia * resultado["impostos_pct"] / 100
                    valor_liquido = preco_referencia - valor_taxa - valor_impostos
                    lucro = valor_liquido - custo_total
                    custos_variaveis = resultado["custo_insumo"] + resultado["custo_mao_obra"] + resultado["custo_embalagem"]
                    contribuicao = valor_liquido - custos_variaveis
                    margem = (contribuicao / preco_referencia * 100) if preco_referencia > 0 else 0

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
                    valor_impostos = preco_com_desconto * resultado["impostos_pct"] / 100
                    valor_liquido = preco_com_desconto - valor_taxa - valor_impostos
                    lucro = valor_liquido - custo_total
                    custos_variaveis = resultado["custo_insumo"] + resultado["custo_mao_obra"] + resultado["custo_embalagem"]
                    contribuicao = valor_liquido - custos_variaveis
                    margem = (contribuicao / preco_com_desconto * 100) if preco_com_desconto > 0 else -100
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
        dd_embalagem.on_change = atualizar_calculos
        tf_qtd_embalagem_insumo.on_change = atualizar_calculos
        dd_sacola.on_change = atualizar_calculos
        tf_qtd_sacola.on_change = atualizar_calculos
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
                embalagem_id = int(dd_embalagem.value) if dd_embalagem.value else None
                qtd_embalagem_insumo = float((tf_qtd_embalagem_insumo.value or "0").replace(",", "."))
                sacola_id = int(dd_sacola.value) if dd_sacola.value else None
                qtd_sacola = float((tf_qtd_sacola.value or "0").replace(",", "."))
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
                    embalagem_id,
                    qtd_embalagem_insumo,
                    sacola_id,
                    qtd_sacola,
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
                    row_resumo("Mão de obra direta:", lbl_mao_obra),
                    row_resumo("Embalagens e sacolas:", lbl_embalagens),
                    row_resumo("Despesas fixas rateadas:", lbl_custo_fixo),
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
                                    row_resumo("Resultado após rateio:", linha["lucro"]),
                                    row_resumo("Margem de contribuição:", linha["margem"]),
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
                            ft.Row(controls=[dd_embalagem, tf_qtd_embalagem_insumo]),
                            ft.Row(controls=[dd_sacola, tf_qtd_sacola]),
                            ft.Text(
                                "Os custos selecionados acima são buscados nos Insumos. "
                                "Use 'Outros custos' apenas para valores adicionais, evitando duplicar embalagem ou sacola.",
                                size=11,
                                color=TEXTO_SECUNDARIO,
                            ),
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

    abrir_ingredientes = criar_abrir_ingredientes({
        "ft": ft,
        "page": page,
        "BRANCO": BRANCO,
        "MARROM": MARROM,
        "ROSA": ROSA,
        "ROSA_CLARO": ROSA_CLARO,
        "TEXTO_SECUNDARIO": TEXTO_SECUNDARIO,
        "indice_atual": indice_atual,
        "navegacao_ref": navegacao_ref,
        "voltar_inicio": voltar_inicio,
        "listar_ingredientes": listar_ingredientes,
        "listar_alertas_aumento_ingredientes": listar_alertas_aumento_ingredientes,
        "excluir_ingrediente": excluir_ingrediente,
        "obter_ingrediente": obter_ingrediente,
        "atualizar_ingrediente": atualizar_ingrediente,
        "cadastrar_ingrediente": cadastrar_ingrediente,
        "criar_dialogo_padrao": criar_dialogo_padrao,
        "criar_cabecalho_padrao": criar_cabecalho_padrao,
        "criar_botao_primario": criar_botao_primario,
        "criar_campo_padrao": criar_campo_padrao,
        "criar_dropdown_padrao": criar_dropdown_padrao,
        "abrir_historico_precos_ingrediente": abrir_historico_precos_ingrediente,
        "abrir_menu_opcoes": lambda ev=None: abrir_menu_opcoes(ev),
    })
    filtro_receita = {"tipo": "TODOS"}

    abrir_receitas = criar_abrir_receitas({
        "ft": ft,
        "page": page,
        "BRANCO": BRANCO,
        "MARROM": MARROM,
        "ROSA": ROSA,
        "ROSA_CLARO": ROSA_CLARO,
        "TEXTO_SECUNDARIO": TEXTO_SECUNDARIO,
        "indice_atual": indice_atual,
        "navegacao_ref": navegacao_ref,
        "voltar_inicio": voltar_inicio,
        "filtro_receita": filtro_receita,
        "obter_conexao": obter_conexao,
        "excluir_receita": excluir_receita,
        "mostrar_aviso": mostrar_aviso,
        "criar_dialogo_padrao": criar_dialogo_padrao,
        "calcular_custo_receita": calcular_custo_receita,
        "criar_cabecalho_padrao": criar_cabecalho_padrao,
        "criar_botao_primario": criar_botao_primario,
        "listar_ingredientes": listar_ingredientes,
        "obter_receita": obter_receita,
        "criar_dropdown_padrao": criar_dropdown_padrao,
        "criar_campo_padrao": criar_campo_padrao,
        "atualizar_receita": atualizar_receita,
        "cadastrar_receita": cadastrar_receita,
    })
    abrir_custos_fixos = criar_abrir_custos_fixos({
        "ft": ft,
        "page": page,
        "BRANCO": BRANCO,
        "MARROM": MARROM,
        "ROSA": ROSA,
        "ROSA_CLARO": ROSA_CLARO,
        "TEXTO_SECUNDARIO": TEXTO_SECUNDARIO,
        "indice_atual": indice_atual,
        "navegacao_ref": navegacao_ref,
        "obter_conexao": obter_conexao,
        "obter_remuneracao_mensal_desejada": obter_remuneracao_mensal_desejada,
        "obter_horas_produtivas_mensais": obter_horas_produtivas_mensais,
        "obter_impostos_pct": obter_impostos_pct,
        "obter_taxas_pagamento": obter_taxas_pagamento,
        "obter_markup_ideal": obter_markup_ideal,
        "obter_margem_minima": obter_margem_minima,
        "criar_campo_padrao": criar_campo_padrao,
        "salvar_remuneracao_mensal_desejada": salvar_remuneracao_mensal_desejada,
        "salvar_horas_produtivas_mensais": salvar_horas_produtivas_mensais,
        "salvar_impostos_pct": salvar_impostos_pct,
        "salvar_taxas_pagamento": salvar_taxas_pagamento,
        "salvar_markup_ideal": salvar_markup_ideal,
        "salvar_margem_minima": salvar_margem_minima,
        "atualizar_custo_fixo": atualizar_custo_fixo,
        "cadastrar_custo_fixo": cadastrar_custo_fixo,
        "excluir_custo_fixo": excluir_custo_fixo,
    })
    abrir_relatorios, montar_painel_inicial = criar_telas_relatorios({
        "ft": ft,
        "page": page,
        "datetime": datetime,
        "LOGO_DM_BASE64": LOGO_DM_BASE64,
        "BRANCO": BRANCO,
        "MARROM": MARROM,
        "ROSA": ROSA,
        "ROSA_CLARO": ROSA_CLARO,
        "TEXTO_SECUNDARIO": TEXTO_SECUNDARIO,
        "indice_atual": indice_atual,
        "navegacao_ref": navegacao_ref,
        "obter_conexao": obter_conexao,
        "calcular_custo_receita": calcular_custo_receita,
        "calcular_precificacao_produto": calcular_precificacao_produto,
        "calcular_custo_fixo_proporcional": calcular_custo_fixo_proporcional,
        "obter_dados_painel": obter_dados_painel,
        "criar_indicador": criar_indicador,
        "criar_atalho": criar_atalho,
        "abrir_orcamentos": abrir_orcamentos,
        "abrir_precificacao": abrir_precificacao,
        "abrir_receitas": abrir_receitas,
        "abrir_ingredientes": abrir_ingredientes,
    })
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

    navegacao_ref["controle"] = navegacao

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
