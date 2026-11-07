import flet as ft
from database import banco

def parse_float(val, default=0.0):
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return default

def criar_tela_precificacao(page: ft.Page):
    
    # -- Componentes Visuais (Inputs) --
    dd_produto = ft.Dropdown(label="Produto Final", expand=True)
    txt_qtd_venda = ft.TextField(label="Quantidade de Venda (ex: 150)", value="1", expand=True)
    
    dd_embalagem = ft.Dropdown(label="Selecione a Embalagem", expand=True)
    txt_qtd_embalagem = ft.TextField(label="Qtd", value="1", width=80)
    
    dd_sacola = ft.Dropdown(label="Selecione a Sacola", expand=True)
    txt_qtd_sacola = ft.TextField(label="Qtd", value="1", width=80)
    
    txt_markup = ft.TextField(label="Markup Ideal (%)", value="100", expand=True)
    txt_preco_praticado = ft.TextField(label="Preço Praticado (R$)", value="0.00", expand=True)
    
    # -- Componentes Visuais (Resumo e Outputs) --
    lbl_custo_insumos = ft.Text("R$ 0,00", weight=ft.FontWeight.W_500)
    lbl_custo_fixo = ft.Text("R$ 0,00", weight=ft.FontWeight.W_500)
    lbl_custo_emb = ft.Text("R$ 0,00", weight=ft.FontWeight.W_500)
    lbl_custo_total = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, size=16)
    
    lbl_preco_sugerido = ft.Text("R$ 0,00", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700, size=18)
    lbl_markup_praticado = ft.Text("0.00%", weight=ft.FontWeight.BOLD)
    lbl_status = ft.Text("-", weight=ft.FontWeight.BOLD)

    def carregar_dados():
        con = banco.obter_conexao()
        try:
            receitas = con.execute("SELECT id, nome FROM receitas WHERE ativo=1 AND tipo IN ('PRODUTO', 'FINAL') ORDER BY nome").fetchall()
            ingredientes = banco.listar_ingredientes()
        finally:
            con.close()
            
        dd_produto.options = [ft.dropdown.Option(str(r["id"]), r["nome"]) for r in receitas]
        
        opcoes_insumos = [ft.dropdown.Option(str(i["id"]), i["nome"]) for i in ingredientes]
        dd_embalagem.options = [ft.dropdown.Option("", "Nenhuma")] + opcoes_insumos
        dd_sacola.options = [ft.dropdown.Option("", "Nenhuma")] + opcoes_insumos
        page.update()

    def calcular(e=None):
        if not dd_produto.value:
            return

        receita_id = int(dd_produto.value)
        qtd_venda = parse_float(txt_qtd_venda.value)
        
        emb_id = int(dd_embalagem.value) if dd_embalagem.value else None
        qtd_emb = parse_float(txt_qtd_embalagem.value)
        
        sac_id = int(dd_sacola.value) if dd_sacola.value else None
        qtd_sac = parse_float(txt_qtd_sacola.value)
        
        markup = parse_float(txt_markup.value) / 100.0
        
        try:
            resultado = banco.calcular_precificacao_completa(
                receita_id=receita_id,
                quantidade_venda=qtd_venda,
                embalagem_id=emb_id,
                quantidade_embalagem=qtd_emb,
                sacola_id=sac_id,
                quantidade_sacola=qtd_sac,
                markup=markup
            )
            
            lbl_custo_insumos.value = f"R$ {resultado['custo_insumos']:.2f}"
            lbl_custo_fixo.value = f"R$ {resultado['custo_fixo']:.2f}"
            custo_emb_sac = resultado['custo_embalagem'] + resultado['custo_sacola']
            lbl_custo_emb.value = f"R$ {custo_emb_sac:.2f}"
            lbl_custo_total.value = f"R$ {resultado['custo_total']:.2f}"
            lbl_preco_sugerido.value = f"R$ {resultado['preco_sugerido']:.2f}"
            
            preco_praticado = parse_float(txt_preco_praticado.value)
            
            if preco_praticado > 0 and resultado['custo_total'] > 0:
                markup_praticado = (preco_praticado / resultado['custo_total']) - 1
                lbl_markup_praticado.value = f"{markup_praticado * 100:.2f}%"
                
                if markup_praticado >= markup:
                    lbl_status.value = "Dentro / Acima do Ideal"
                    lbl_status.color = ft.colors.GREEN_600
                else:
                    lbl_status.value = "Abaixo do Ideal"
                    lbl_status.color = ft.colors.RED_600
            else:
                lbl_markup_praticado.value = "0.00%"
                lbl_status.value = "Informe o preço praticado"
                lbl_status.color = ft.colors.GREY_500
                
            page.update()
        except Exception as ex:
            print(f"Erro no cálculo: {ex}")

    def salvar(e):
        if not dd_produto.value:
            return
            
        receita_id = int(dd_produto.value)
        qtd_venda = parse_float(txt_qtd_venda.value)
        emb_id = int(dd_embalagem.value) if dd_embalagem.value else None
        qtd_emb = parse_float(txt_qtd_embalagem.value)
        sac_id = int(dd_sacola.value) if dd_sacola.value else None
        qtd_sac = parse_float(txt_qtd_sacola.value)
        markup = parse_float(txt_markup.value) / 100.0
        preco_prat = parse_float(txt_preco_praticado.value)
        
        try:
            banco.salvar_precificacao_completa(
                receita_id, qtd_venda, emb_id, qtd_emb, sac_id, qtd_sac, markup, int(preco_prat * 100)
            )
            page.snack_bar = ft.SnackBar(ft.Text("Precificação salva com sucesso!"), bgcolor=ft.colors.GREEN_800)
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar: {ex}"), bgcolor=ft.colors.RED_800)
            page.snack_bar.open = True
            page.update()

    dd_produto.on_change = calcular
    txt_qtd_venda.on_change = calcular
    dd_embalagem.on_change = calcular
    txt_qtd_embalagem.on_change = calcular
    dd_sacola.on_change = calcular
    txt_qtd_sacola.on_change = calcular
    txt_markup.on_change = calcular
    txt_preco_praticado.on_change = calcular

    secao_inputs = ft.Column([
        ft.Text("1. Produto e Quantidade", style=ft.TextThemeStyle.TITLE_MEDIUM, color=ft.colors.BLUE_700),
        ft.Row([dd_produto, txt_qtd_venda]),
        
        ft.Divider(height=30),
        ft.Text("2. Embalagens e Sacolas (Insumos)", style=ft.TextThemeStyle.TITLE_MEDIUM, color=ft.colors.BLUE_700),
        ft.Row([dd_embalagem, txt_qtd_embalagem]),
        ft.Row([dd_sacola, txt_qtd_sacola]),
        
        ft.Divider(height=30),
        ft.Text("3. Margem e Venda", style=ft.TextThemeStyle.TITLE_MEDIUM, color=ft.colors.BLUE_700),
        ft.Row([txt_markup, txt_preco_praticado]),
    ], spacing=10)

    secao_resumo = ft.Card(
        elevation=4,
        content=ft.Container(
            padding=20,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=10,
            content=ft.Column([
                ft.Text("Resumo da Precificação", style=ft.TextThemeStyle.TITLE_LARGE),
                ft.Divider(),
                ft.Row([ft.Text("Custo dos Insumos:"), lbl_custo_insumos], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Custo Fixo (Tempo):"), lbl_custo_fixo], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Embalagem e Sacola:"), lbl_custo_emb], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Row([ft.Text("Custo Total:", weight=ft.FontWeight.BOLD), lbl_custo_total], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=30),
                ft.Row([ft.Text("Preço Sugerido (Ideal):", weight=ft.FontWeight.BOLD), lbl_preco_sugerido], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Markup Praticado:"), lbl_markup_praticado], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Status do Preço:"), lbl_status], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=20),
                ft.ElevatedButton("Salvar Precificação", on_click=salvar, icon=ft.icons.SAVE, width=float("inf"), style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE))
            ])
        )
    )

    carregar_dados()

    return ft.ResponsiveRow([
        ft.Column([secao_inputs], col={"sm": 12, "md": 6}),
        ft.Column([secao_resumo], col={"sm": 12, "md": 6}),
    ])
