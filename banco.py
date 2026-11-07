
import sqlite3
from pathlib import Path
from datetime import datetime


PASTA_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = PASTA_PROJETO / "database" / "dm_gulositos.db"


# =========================================================
# CONEXÃO COM O BANCO
# =========================================================

def obter_conexao():
    CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


# =========================================================
# CRIAÇÃO E ATUALIZAÇÃO DAS TABELAS
# =========================================================

def criar_tabelas():
    conexao = obter_conexao()

    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS custos_fixos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor_centavos INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ingredientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT,
                fornecedor TEXT,
                quantidade_compra REAL NOT NULL,
                unidade_compra TEXT NOT NULL,
                preco_pago_centavos INTEGER NOT NULL,
                quantidade_base REAL NOT NULL,
                unidade_base TEXT NOT NULL,
                custo_por_unidade_base REAL NOT NULL,
                observacoes TEXT,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'PRODUTO',
                rendimento_unidades REAL NOT NULL DEFAULT 1,
                custo_embalagem_centavos INTEGER DEFAULT 0,
                margem_lucro_pct REAL NOT NULL DEFAULT 100.0,
                taxa_cartao_pct REAL DEFAULT 0.0,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                tempo_preparo_min REAL NOT NULL DEFAULT 0,
                tempo_batedeira_min REAL NOT NULL DEFAULT 0,
                tempo_forno_min REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS receita_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_pai_id INTEGER NOT NULL,
                ingrediente_id INTEGER,
                sub_receita_id INTEGER,
                quantidade_usada REAL NOT NULL,

                FOREIGN KEY (receita_pai_id)
                    REFERENCES receitas(id) ON DELETE CASCADE,

                FOREIGN KEY (ingrediente_id)
                    REFERENCES ingredientes(id),

                FOREIGN KEY (sub_receita_id)
                    REFERENCES receitas(id)
            );

            CREATE TABLE IF NOT EXISTS precificacao_produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_id INTEGER NOT NULL UNIQUE,
                custo_embalagem_centavos INTEGER NOT NULL DEFAULT 0,
                margem_lucro_pct REAL NOT NULL DEFAULT 100,
                taxa_cartao_pct REAL NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL,

                FOREIGN KEY (receita_id)
                    REFERENCES receitas(id)
            );
        """)

                # MIGRAÇÃO DA PRECIFICAÇÃO
        colunas = {
            linha["name"]
            for linha in con.execute(
                "PRAGMA table_info(precificacoes)"
            ).fetchall()
        }

        if "embalagem_id" not in colunas:
            con.execute(
                "ALTER TABLE precificacoes ADD COLUMN embalagem_id INTEGER"
            )

        if "quantidade_embalagem_insumo" not in colunas:
            con.execute(
                """
                ALTER TABLE precificacoes
                ADD COLUMN quantidade_embalagem_insumo REAL NOT NULL DEFAULT 1
                """
            )

        if "sacola_id" not in colunas:
            con.execute(
                "ALTER TABLE precificacoes ADD COLUMN sacola_id INTEGER"
            )

        if "quantidade_sacola" not in colunas:
            con.execute(
                """
                ALTER TABLE precificacoes
                ADD COLUMN quantidade_sacola REAL NOT NULL DEFAULT 0
                """
            )

        con.execute("""
            INSERT OR IGNORE INTO configuracoes(chave, valor)
            VALUES ('horas_produtivas_mensais', '220')
        """)

        # MIGRAÇÃO SEGURA:
        # Acrescenta os campos de tempo caso o banco já exista.

        colunas_receitas = [
            coluna["name"]
            for coluna in conexao.execute(
                "PRAGMA table_info(receitas)"
            ).fetchall()
        ]

        novas_colunas = {
            "tempo_preparo_min": "REAL NOT NULL DEFAULT 0",
            "tempo_batedeira_min": "REAL NOT NULL DEFAULT 0",
            "tempo_forno_min": "REAL NOT NULL DEFAULT 0",
            "unidade_rendimento": "TEXT NOT NULL DEFAULT 'un'"
        }

        for nome_coluna, tipo_coluna in novas_colunas.items():
            if nome_coluna not in colunas_receitas:
                conexao.execute(
                    f"ALTER TABLE receitas ADD COLUMN {nome_coluna} {tipo_coluna}"
                )

        conexao.execute("""
            INSERT OR IGNORE INTO configuracoes (chave, valor)
            VALUES ('faturamento_mensal', '2000.00')
        """)

        conexao.commit()

        colunas_receitas = {
            linha["name"]
            for linha in con.execute(
                "PRAGMA table_info(receitas)"
            ).fetchall()
        }

        for coluna in (
            "tempo_preparo_min",
            "tempo_batedeira_min",
            "tempo_forno_min"
        ):
            if coluna not in colunas_receitas:
                con.execute(
                    f"ALTER TABLE receitas ADD COLUMN {coluna} REAL NOT NULL DEFAULT 0"
                )

    finally:
        conexao.close()


# =========================================================
# CONVERSÃO DE UNIDADES
# =========================================================

def converter_para_base(quantidade, unidade):
    unidade = unidade.strip().lower()

    conversoes = {
        "kg": (1000, "g"),
        "g": (1, "g"),
        "l": (1000, "ml"),
        "litro": (1000, "ml"),
        "litros": (1000, "ml"),
        "ml": (1, "ml"),
        "un": (1, "un"),
        "unidade": (1, "un"),
        "unidades": (1, "un")
    }

    if unidade not in conversoes:
        raise ValueError(f"Unidade não reconhecida: {unidade}")

    if quantidade <= 0:
        raise ValueError("A quantidade precisa ser maior que zero.")

    fator, unidade_base = conversoes[unidade]

    return quantidade * fator, unidade_base


def calcular_custo_unitario(preco_pago_centavos, quantidade_base):
    if preco_pago_centavos < 0 or quantidade_base <= 0:
        raise ValueError("Valores inválidos para cálculo.")

    return (preco_pago_centavos / 100) / quantidade_base


# =========================================================
# INGREDIENTES
# =========================================================

def cadastrar_ingrediente(
    nome,
    marca,
    fornecedor,
    quantidade_compra,
    unidade_compra,
    preco_pago_centavos,
    observacoes=""
):
    nome = nome.strip()

    if not nome:
        raise ValueError("Informe o nome do ingrediente.")

    quantidade_base, unidade_base = converter_para_base(
        quantidade_compra,
        unidade_compra
    )

    custo_unitario = calcular_custo_unitario(
        preco_pago_centavos,
        quantidade_base
    )

    agora = datetime.now().isoformat(timespec="seconds")
    unidade_normalizada = unidade_compra.strip().lower()

    conexao = obter_conexao()

    try:
        cursor = conexao.execute("""
            INSERT INTO ingredientes (
                nome,
                marca,
                fornecedor,
                quantidade_compra,
                unidade_compra,
                preco_pago_centavos,
                quantidade_base,
                unidade_base,
                custo_por_unidade_base,
                observacoes,
                ativo,
                criado_em,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            nome,
            marca.strip() if marca else None,
            fornecedor.strip() if fornecedor else None,
            quantidade_compra,
            unidade_normalizada,
            preco_pago_centavos,
            quantidade_base,
            unidade_base,
            custo_unitario,
            observacoes.strip() if observacoes else None,
            agora,
            agora
        ))

        ingrediente_id = cursor.lastrowid

        conexao.commit()

        return ingrediente_id

    finally:
        conexao.close()


def listar_ingredientes():
    conexao = obter_conexao()

    try:
        return conexao.execute("""
            SELECT *
            FROM ingredientes
            WHERE ativo = 1
            ORDER BY nome COLLATE NOCASE
        """).fetchall()

    finally:
        conexao.close()


def obter_ingrediente(ingrediente_id):
    conexao = obter_conexao()

    try:
        return conexao.execute("""
            SELECT *
            FROM ingredientes
            WHERE id = ? AND ativo = 1
        """, (ingrediente_id,)).fetchone()

    finally:
        conexao.close()


def atualizar_ingrediente(
    ingrediente_id,
    nome,
    marca,
    fornecedor,
    quantidade_compra,
    unidade_compra,
    preco_pago_centavos,
    observacoes=""
):
    nome = (nome or "").strip()

    if not nome:
        raise ValueError("Informe o nome do ingrediente.")

    unidade_normalizada = (unidade_compra or "").strip().lower()

    quantidade_base, unidade_base = converter_para_base(
        quantidade_compra,
        unidade_normalizada
    )

    custo_unitario = calcular_custo_unitario(
        preco_pago_centavos,
        quantidade_base
    )

    agora = datetime.now().isoformat(timespec="seconds")

    conexao = obter_conexao()

    try:
        conexao.execute("""
            UPDATE ingredientes SET
                nome = ?,
                marca = ?,
                fornecedor = ?,
                quantidade_compra = ?,
                unidade_compra = ?,
                preco_pago_centavos = ?,
                quantidade_base = ?,
                unidade_base = ?,
                custo_por_unidade_base = ?,
                observacoes = ?,
                atualizado_em = ?
            WHERE id = ?
        """, (
            nome,
            marca.strip() if marca else None,
            fornecedor.strip() if fornecedor else None,
            quantidade_compra,
            unidade_normalizada,
            preco_pago_centavos,
            quantidade_base,
            unidade_base,
            custo_unitario,
            observacoes.strip() if observacoes else None,
            agora,
            ingrediente_id
        ))

        conexao.commit()

        return True

    finally:
        conexao.close()


def excluir_ingrediente(ingrediente_id):
    """
    Exclui logicamente um ingrediente.

    Se ele estiver sendo utilizado em alguma receita,
    a exclusão será impedida para proteger a ficha técnica.
    """

    conexao = obter_conexao()

    try:
        referencia = conexao.execute("""
            SELECT COUNT(*)
            FROM receita_itens
            WHERE ingrediente_id = ?
        """, (ingrediente_id,)).fetchone()[0]

        if referencia > 0:
            raise ValueError(
                "Este ingrediente está vinculado a uma ou mais receitas. "
                "Remova-o das receitas antes de excluí-lo."
            )

        conexao.execute("""
            UPDATE ingredientes
            SET ativo = 0,
                atualizado_em = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(timespec="seconds"),
            ingrediente_id
        ))

        conexao.commit()

        return True

    finally:
        conexao.close()


# =========================================================
# CUSTOS FIXOS
# =========================================================

def cadastrar_custo_fixo(descricao, valor_centavos):
    conexao = obter_conexao()

    try:
        conexao.execute("""
            INSERT INTO custos_fixos (descricao, valor_centavos)
            VALUES (?, ?)
        """, (descricao.strip(), valor_centavos))

        conexao.commit()

    finally:
        conexao.close()


def atualizar_custo_fixo(custo_id, descricao, valor_centavos):
    conexao = obter_conexao()

    try:
        conexao.execute("""
            UPDATE custos_fixos
            SET descricao = ?, valor_centavos = ?
            WHERE id = ?
        """, (descricao.strip(), valor_centavos, custo_id))

        conexao.commit()

    finally:
        conexao.close()


def excluir_custo_fixo(custo_id):
    conexao = obter_conexao()

    try:
        conexao.execute(
            "DELETE FROM custos_fixos WHERE id = ?",
            (custo_id,)
        )

        conexao.commit()

    finally:
        conexao.close()


def obter_fator_custo_fixo():
    conexao = obter_conexao()

    try:
        total_custos = conexao.execute("""
            SELECT SUM(valor_centavos)
            FROM custos_fixos
        """).fetchone()[0] or 0

        fat_row = conexao.execute("""
            SELECT valor
            FROM configuracoes
            WHERE chave = 'faturamento_mensal'
        """).fetchone()

        faturamento = float(fat_row["valor"]) if fat_row else 2000.0

        if faturamento <= 0:
            return 0.0

        return (total_custos / 100) / faturamento

    finally:
        conexao.close()


# =========================================================
# RECEITAS E SUB-RECEITAS
# =========================================================

def cadastrar_receita(
    nome,
    tipo,
    rendimento_unidades,
    custo_embalagem_centavos,
    margem_lucro_pct,
    taxa_cartao_pct,
    lista_itens,
    tempo_preparo_min=0,
    tempo_batedeira_min=0,
    tempo_forno_min=0,
    unidade_rendimento="un"
):
    nome = (nome or "").strip()
    unidade_rendimento = (unidade_rendimento or "un").strip().lower()

    if not nome:
        raise ValueError("Informe o nome da receita.")

    if rendimento_unidades <= 0:
        raise ValueError("O rendimento precisa ser maior que zero.")

    if unidade_rendimento not in ("un", "g"):
        raise ValueError("A unidade de rendimento deve ser un ou g.")

    tempos = [
        tempo_preparo_min,
        tempo_batedeira_min,
        tempo_forno_min
    ]

    if any(tempo < 0 for tempo in tempos):
        raise ValueError("Os tempos não podem ser negativos.")

    agora = datetime.now().isoformat(timespec="seconds")

    conexao = obter_conexao()

    try:
        cursor = conexao.execute("""
            INSERT INTO receitas (
                nome,
                tipo,
                rendimento_unidades,
                custo_embalagem_centavos,
                margem_lucro_pct,
                taxa_cartao_pct,
                ativo,
                criado_em,
                atualizado_em,
                tempo_preparo_min,
                tempo_batedeira_min,
                tempo_forno_min,
                unidade_rendimento
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
        """, (
            nome,
            tipo,
            rendimento_unidades,
            custo_embalagem_centavos,
            margem_lucro_pct,
            taxa_cartao_pct,
            agora,
            agora,
            tempo_preparo_min,
            tempo_batedeira_min,
            tempo_forno_min,
            unidade_rendimento
        ))

        receita_id = cursor.lastrowid

        for item in lista_itens:
            conexao.execute("""
                INSERT INTO receita_itens (
                    receita_pai_id,
                    ingrediente_id,
                    sub_receita_id,
                    quantidade_usada
                )
                VALUES (?, ?, ?, ?)
            """, (
                receita_id,
                item.get("ingrediente_id"),
                item.get("sub_receita_id"),
                item["quantidade_usada"]
            ))

        conexao.commit()

        return receita_id

    finally:
        conexao.close()

def obter_receita(receita_id):
    conexao = obter_conexao()

    try:
        receita = conexao.execute("""
            SELECT *
            FROM receitas
            WHERE id = ? AND ativo = 1
        """, (receita_id,)).fetchone()

        if not receita:
            return None

        itens = conexao.execute("""
            SELECT *
            FROM receita_itens
            WHERE receita_pai_id = ?
        """, (receita_id,)).fetchall()

        return {
            "receita": receita,
            "itens": itens
        }

    finally:
        conexao.close()


def atualizar_receita(
    receita_id,
    nome,
    tipo,
    rendimento_unidades,
    custo_embalagem_centavos,
    margem_lucro_pct,
    taxa_cartao_pct,
    lista_itens,
    tempo_preparo_min=0,
    tempo_batedeira_min=0,
    tempo_forno_min=0,
    unidade_rendimento="un"
):
    nome = (nome or "").strip()
    unidade_rendimento = (unidade_rendimento or "un").strip().lower()

    if not nome:
        raise ValueError("Informe o nome da receita.")

    if rendimento_unidades <= 0:
        raise ValueError("O rendimento precisa ser maior que zero.")

    if unidade_rendimento not in ("un", "g"):
        raise ValueError("A unidade de rendimento deve ser un ou g.")

    tempos = [
        tempo_preparo_min,
        tempo_batedeira_min,
        tempo_forno_min
    ]

    if any(tempo < 0 for tempo in tempos):
        raise ValueError("Os tempos não podem ser negativos.")

    agora = datetime.now().isoformat(timespec="seconds")

    conexao = obter_conexao()

    try:
        conexao.execute("""
            UPDATE receitas SET
                nome = ?,
                tipo = ?,
                rendimento_unidades = ?,
                custo_embalagem_centavos = ?,
                margem_lucro_pct = ?,
                taxa_cartao_pct = ?,
                atualizado_em = ?,
                tempo_preparo_min = ?,
                tempo_batedeira_min = ?,
                tempo_forno_min = ?,
                unidade_rendimento = ?
            WHERE id = ?
        """, (
            nome,
            tipo,
            rendimento_unidades,
            custo_embalagem_centavos,
            margem_lucro_pct,
            taxa_cartao_pct,
            agora,
            tempo_preparo_min,
            tempo_batedeira_min,
            tempo_forno_min,
            unidade_rendimento,
            receita_id
        ))

        conexao.execute("""
            DELETE FROM receita_itens
            WHERE receita_pai_id = ?
        """, (receita_id,))

        for item in lista_itens:
            conexao.execute("""
                INSERT INTO receita_itens (
                    receita_pai_id,
                    ingrediente_id,
                    sub_receita_id,
                    quantidade_usada
                )
                VALUES (?, ?, ?, ?)
            """, (
                receita_id,
                item.get("ingrediente_id"),
                item.get("sub_receita_id"),
                item["quantidade_usada"]
            ))

        conexao.commit()

        return True

    finally:
        conexao.close()

def excluir_receita(receita_id):
    conexao = obter_conexao()

    try:
        conexao.execute("""
            UPDATE receitas
            SET ativo = 0
            WHERE id = ?
        """, (receita_id,))

        conexao.commit()

    finally:
        conexao.close()

# =========================================================
# CÁLCULO DO CUSTO DA RECEITA
# =========================================================

def calcular_custo_receita(receita_id):
    """
    Calcula exclusivamente o custo dos ingredientes e sub-receitas.

    Não considera:
    - Embalagem
    - Custos fixos
    - Taxa de cartão
    - Margem de lucro
    """

    conexao = obter_conexao()

    try:
        receita = conexao.execute("""
            SELECT *
            FROM receitas
            WHERE id = ? AND ativo = 1
        """, (receita_id,)).fetchone()

        if not receita:
            return None

        itens = conexao.execute("""
            SELECT *
            FROM receita_itens
            WHERE receita_pai_id = ?
        """, (receita_id,)).fetchall()

        custo_insumos = 0.0

        for item in itens:

            # Ingrediente direto
            if item["ingrediente_id"] is not None:

                ingrediente = conexao.execute("""
                    SELECT custo_por_unidade_base
                    FROM ingredientes
                    WHERE id = ? AND ativo = 1
                """, (item["ingrediente_id"],)).fetchone()

                if ingrediente:
                    custo_insumos += (
                        item["quantidade_usada"]
                        * ingrediente["custo_por_unidade_base"]
                    )

            # Sub-receita
            elif item["sub_receita_id"] is not None:

                sub_receita = calcular_custo_receita(
                    item["sub_receita_id"]
                )

                if sub_receita:
                    custo_insumos += (
                        item["quantidade_usada"]
                        * sub_receita["custo_unitario"]
                    )

        rendimento = receita["rendimento_unidades"]

        if rendimento <= 0:
            rendimento = 1

        custo_unitario = custo_insumos / rendimento

        return {
            "custo_insumos": custo_insumos,
            "custo_total": custo_insumos,
            "custo_unitario": custo_unitario,
            "rendimento": rendimento,
            "unidade_rendimento": receita["unidade_rendimento"]
        }

    finally:
        conexao.close()

# =========================================================
# PRECIFICAÇÃO INDEPENDENTE
# =========================================================

def salvar_precificacao_produto(
    receita_id,
    custo_embalagem_centavos,
    margem_lucro_pct,
    taxa_cartao_pct
):
    agora = datetime.now().isoformat(timespec="seconds")

    conexao = obter_conexao()

    try:
        conexao.execute("""
            INSERT INTO precificacao_produtos (
                receita_id,
                custo_embalagem_centavos,
                margem_lucro_pct,
                taxa_cartao_pct,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(receita_id)
            DO UPDATE SET
                custo_embalagem_centavos = excluded.custo_embalagem_centavos,
                margem_lucro_pct = excluded.margem_lucro_pct,
                taxa_cartao_pct = excluded.taxa_cartao_pct,
                atualizado_em = excluded.atualizado_em
        """, (
            receita_id,
            custo_embalagem_centavos,
            margem_lucro_pct,
            taxa_cartao_pct,
            agora
        ))

        conexao.commit()

        return True

    finally:
        conexao.close()


def obter_precificacao_produto(receita_id):
    conexao = obter_conexao()

    try:
        return conexao.execute("""
            SELECT *
            FROM precificacao_produtos
            WHERE receita_id = ?
        """, (receita_id,)).fetchone()

    finally:
        conexao.close()


def calcular_precificacao_produto(receita_id):
    """
    Calcula o preço comercial separadamente da ficha técnica.

    Considera:
    - Custo dos ingredientes
    - Embalagem
    - Rateio dos custos fixos
    - Margem de lucro
    - Taxa de cartão
    """

    custo = calcular_custo_receita(receita_id)

    if not custo:
        return None

    precificacao = obter_precificacao_produto(receita_id)

    if not precificacao:
        return None

    rendimento = custo["rendimento"]

    if rendimento <= 0:
        return None

    custo_insumos = custo["custo_insumos"]

    custo_embalagem = (
        precificacao["custo_embalagem_centavos"] / 100
    )

    fator_fixo = obter_fator_custo_fixo()

    custo_fixo = custo_insumos * fator_fixo

    custo_total = (
        custo_insumos
        + custo_embalagem
        + custo_fixo
    )

    custo_unitario = custo_total / rendimento

    margem = precificacao["margem_lucro_pct"] / 100
    taxa = precificacao["taxa_cartao_pct"] / 100

    preco_com_margem = custo_unitario * (1 + margem)

    divisor = 1 - taxa

    if divisor <= 0:
        raise ValueError(
            "A taxa do cartão precisa ser menor que 100%."
        )

    preco_venda = preco_com_margem / divisor

    return {
        "custo_insumos": custo_insumos,
        "custo_embalagem": custo_embalagem,
        "custo_fixo": custo_fixo,
        "custo_total": custo_total,
        "custo_unitario": custo_unitario,
        "preco_venda_sugerido": preco_venda,
        "lucro_unitario": preco_venda - custo_unitario,
        "rendimento": rendimento,
        "unidade_rendimento": custo["unidade_rendimento"]
    }

# =========================================================
# CONFIGURAÇÃO E RATEIO DE CUSTOS FIXOS POR HORA
# =========================================================

def obter_horas_produtivas_mensais():
    con = obter_conexao()
    try:
        resultado = con.execute("""
            SELECT valor FROM configuracoes
            WHERE chave = 'horas_produtivas_mensais'
        """).fetchone()

        return float(resultado["valor"]) if resultado else 220.0
    finally:
        con.close()


def salvar_horas_produtivas_mensais(horas):
    horas = float(horas)

    if horas <= 0:
        raise ValueError("As horas produtivas devem ser maiores que zero.")

    con = obter_conexao()
    try:
        con.execute("""
            INSERT INTO configuracoes(chave, valor)
            VALUES ('horas_produtivas_mensais', ?)
            ON CONFLICT(chave)
            DO UPDATE SET valor = excluded.valor
        """, (str(horas),))
        con.commit()
    finally:
        con.close()


def obter_custo_fixo_por_hora():
    total_centavos = sum(
        int(c["valor_centavos"])
        for c in listar_custos_fixos()
    )

    horas = obter_horas_produtivas_mensais()

    if horas <= 0:
        return 0.0

    return (total_centavos / 100) / horas


# =========================================================
# CUSTO DOS INSUMOS DE EMBALAGEM
# =========================================================

def calcular_custo_embalagem(ingrediente_id, quantidade):
    if not ingrediente_id or float(quantidade) <= 0:
        return 0.0

    ingrediente = obter_ingrediente(ingrediente_id)

    if not ingrediente:
        raise ValueError("Embalagem ou sacola não encontrada.")

    return (
        float(ingrediente["custo_por_unidade_base"])
        * float(quantidade)
    )


# =========================================================
# CÁLCULO COMPLETO DA PRECIFICAÇÃO
# =========================================================

def calcular_precificacao_completa(
    receita_id,
    quantidade_produto,
    embalagem_id,
    quantidade_embalagem,
    sacola_id,
    quantidade_sacola,
    markup
):
    receita = obter_receita(receita_id)

    if not receita:
        raise ValueError("Produto não encontrado.")

    ficha = receita["receita"]

    if ficha["tipo"] != "FINAL":
        raise ValueError("Selecione uma receita do tipo FINAL.")

    calculo_receita = calcular_custo_receita(receita_id)

    rendimento = float(ficha["rendimento"])
    quantidade_produto = float(quantidade_produto)

    if rendimento <= 0 or quantidade_produto <= 0:
        raise ValueError("Confira o rendimento e a quantidade do produto.")

    unidade_rendimento = ficha["unidade_rendimento"].lower()

    if unidade_rendimento not in ("g", "ml", "un"):
        raise ValueError(
            "Para precificar, o rendimento do produto final deve estar em g, ml ou un."
        )

    if unidade_rendimento == "un" and not quantidade_produto.is_integer():
        raise ValueError("Produtos vendidos por unidade precisam usar quantidade inteira.")

    proporcao = quantidade_produto / rendimento

    custo_insumos = calculo_receita["custo_total"] * proporcao

    # Tempo de produção armazenado na receita, quando disponível.
    # Os campos serão adicionados na migração abaixo.
    con = obter_conexao()
    try:
        colunas = {
            linha["name"]
            for linha in con.execute(
                "PRAGMA table_info(receitas)"
            ).fetchall()
        }

        preparo = (
            float(ficha["tempo_preparo_min"])
            if "tempo_preparo_min" in colunas and ficha["tempo_preparo_min"] is not None
            else 0
        )
        batedeira = (
            float(ficha["tempo_batedeira_min"])
            if "tempo_batedeira_min" in colunas and ficha["tempo_batedeira_min"] is not None
            else 0
        )
        forno = (
            float(ficha["tempo_forno_min"])
            if "tempo_forno_min" in colunas and ficha["tempo_forno_min"] is not None
            else 0
        )
    finally:
        con.close()

    tempo_total_minutos = preparo + batedeira + forno
    tempo_proporcional = tempo_total_minutos * proporcao

    custo_fixo_hora = obter_custo_fixo_por_hora()
    custo_fixo = (tempo_proporcional / 60) * custo_fixo_hora

    custo_embalagem = calcular_custo_embalagem(
        embalagem_id, quantidade_embalagem
    )

    custo_sacola = calcular_custo_embalagem(
        sacola_id, quantidade_sacola
    )

    custo_total = (
        custo_insumos
        + custo_fixo
        + custo_embalagem
        + custo_sacola
    )

    markup = float(markup)

    if markup < 0:
        raise ValueError("O markup não pode ser negativo.")

    preco_com_markup = custo_total * (1 + markup / 100)

    return {
        "custo_insumos": custo_insumos,
        "tempo_total_minutos": tempo_proporcional,
        "custo_fixo_hora": custo_fixo_hora,
        "custo_fixo": custo_fixo,
        "custo_embalagem": custo_embalagem,
        "custo_sacola": custo_sacola,
        "custo_total": custo_total,
        "markup_ideal": markup,
        "preco_com_markup": preco_com_markup,
        "preco_sugerido": preco_com_markup,
    }


def calcular_markup_praticado(custo_total, preco_praticado):
    custo_total = float(custo_total)
    preco_praticado = float(preco_praticado)

    if custo_total <= 0:
        return 0.0

    return ((preco_praticado / custo_total) - 1) * 100


def avaliar_status_precificacao(markup_praticado, markup_ideal):
    if markup_praticado < markup_ideal:
        return "ABAIXO DO IDEAL"

    if markup_praticado == markup_ideal:
        return "DENTRO DO IDEAL"

    return "ACIMA DO IDEAL"


# =========================================================
# PRECIFICAÇÃO POR TEMPO DE PRODUÇÃO
# =========================================================

def obter_horas_produtivas_mensais():
    con = obter_conexao()
    try:
        row = con.execute("""
            SELECT valor FROM configuracoes
            WHERE chave = 'horas_produtivas_mensais'
        """).fetchone()
        return float(row["valor"]) if row else 220.0
    finally:
        con.close()


def salvar_horas_produtivas_mensais(horas):
    horas = float(horas)
    if horas <= 0:
        raise ValueError("As horas produtivas precisam ser maiores que zero.")

    con = obter_conexao()
    try:
        con.execute("""
            INSERT INTO configuracoes(chave, valor)
            VALUES('horas_produtivas_mensais', ?)
            ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor
        """, (str(horas),))
        con.commit()
    finally:
        con.close()


def obter_custo_fixo_mensal():
    custos = listar_custos_fixos()
    return sum(float(c["valor_centavos"]) for c in custos) / 100


def obter_custo_fixo_por_hora():
    horas = obter_horas_produtivas_mensais()
    if horas <= 0:
        raise ValueError("Configure as horas produtivas mensais.")
    return obter_custo_fixo_mensal() / horas


def salvar_tempos_receita(receita_id, preparo, batedeira, forno):
    preparo = float(preparo or 0)
    batedeira = float(batedeira or 0)
    forno = float(forno or 0)

    if min(preparo, batedeira, forno) < 0:
        raise ValueError("Os tempos não podem ser negativos.")

    con = obter_conexao()
    try:
        con.execute("""
            UPDATE receitas
            SET tempo_preparo_min=?,
                tempo_batedeira_min=?,
                tempo_forno_min=?
            WHERE id=?
        """, (preparo, batedeira, forno, receita_id))
        con.commit()
    finally:
        con.close()


def calcular_custo_insumo_por_quantidade(ingrediente_id, quantidade):
    quantidade = float(quantidade)
    if quantidade < 0:
        raise ValueError("A quantidade do insumo não pode ser negativa.")

    if quantidade == 0:
        return 0.0

    ingrediente = obter_ingrediente(ingrediente_id)
    if not ingrediente:
        raise ValueError("Embalagem ou sacola não encontrada.")

    return quantidade * float(ingrediente["custo_por_unidade_base"])


def calcular_precificacao_completa(
    receita_id,
    quantidade_venda,
    embalagem_id=None,
    quantidade_embalagem=0,
    sacola_id=None,
    quantidade_sacola=0,
    markup=1.0,
):
    receita_dados = obter_receita(receita_id)
    if not receita_dados:
        raise ValueError("Receita não encontrada.")

    receita = receita_dados["receita"]

    if receita["tipo"] != "FINAL":
        raise ValueError("A precificação aceita somente produtos do tipo FINAL.")

    quantidade_venda = float(quantidade_venda)
    rendimento = float(receita["rendimento"])
    markup = float(markup)

    if quantidade_venda <= 0:
        raise ValueError("Informe uma quantidade de venda maior que zero.")
    if rendimento <= 0:
        raise ValueError("O rendimento da receita precisa ser maior que zero.")
    if markup < 0:
        raise ValueError("O markup não pode ser negativo.")

    custo_receita = calcular_custo_receita(receita_id)

    # Fração da receita utilizada em uma unidade de venda.
    fracao_receita = quantidade_venda / rendimento

    custo_insumos = custo_receita["custo_total"] * fracao_receita

    # Tempo total de produção da receita.
    tempo_preparo = float(receita["tempo_preparo_min"] or 0)
    tempo_batedeira = float(receita["tempo_batedeira_min"] or 0)
    tempo_forno = float(receita["tempo_forno_min"] or 0)

    tempo_total_minutos = (
        tempo_preparo + tempo_batedeira + tempo_forno
    )

    # Rateio proporcional à quantidade vendida.
    tempo_unidade_venda = tempo_total_minutos * fracao_receita
    custo_fixo_hora = obter_custo_fixo_por_hora()
    custo_fixo = (tempo_unidade_venda / 60) * custo_fixo_hora

    custo_embalagem = calcular_custo_insumo_por_quantidade(
        embalagem_id, quantidade_embalagem
    ) if embalagem_id else 0.0

    custo_sacola = calcular_custo_insumo_por_quantidade(
        sacola_id, quantidade_sacola
    ) if sacola_id else 0.0

    custo_total = (
        custo_insumos
        + custo_fixo
        + custo_embalagem
        + custo_sacola
    )

    preco_sugerido = custo_total * (1 + markup)

    return {
        "nome": receita["nome"],
        "rendimento": rendimento,
        "unidade_rendimento": receita["unidade_rendimento"],
        "quantidade_venda": quantidade_venda,
        "custo_insumos": custo_insumos,
        "tempo_total_minutos": tempo_total_minutos,
        "tempo_unidade_venda": tempo_unidade_venda,
        "custo_fixo_hora": custo_fixo_hora,
        "custo_fixo": custo_fixo,
        "custo_embalagem": custo_embalagem,
        "custo_sacola": custo_sacola,
        "custo_total": custo_total,
        "markup": markup,
        "preco_sugerido": preco_sugerido,
    }


def salvar_precificacao_completa(
    receita_id,
    quantidade_venda,
    embalagem_id,
    quantidade_embalagem,
    sacola_id,
    quantidade_sacola,
    markup,
    preco_praticado_centavos=None,
):
    calculo = calcular_precificacao_completa(
        receita_id,
        quantidade_venda,
        embalagem_id,
        quantidade_embalagem,
        sacola_id,
        quantidade_sacola,
        markup,
    )

    stamp = agora()
    con = obter_conexao()
    try:
        con.execute("""
            INSERT INTO precificacoes (
                receita_id,
                quantidade_embalagem,
                embalagem_centavos,
                markup,
                impostos,
                taxa_cartao,
                taxa_delivery,
                preco_praticado_centavos,
                embalagem_id,
                quantidade_embalagem_insumo,
                sacola_id,
                quantidade_sacola,
                ativo,
                criado_em,
                atualizado_em
            )
            VALUES (?, ?, 0, ?, 0, 0, 0, ?, ?, ?, ?, ?, 1, ?, ?)

            ON CONFLICT(receita_id) DO UPDATE SET
                quantidade_embalagem=excluded.quantidade_embalagem,
                embalagem_centavos=0,
                markup=excluded.markup,
                impostos=0,
                taxa_cartao=0,
                taxa_delivery=0,
                preco_praticado_centavos=excluded.preco_praticado_centavos,
                embalagem_id=excluded.embalagem_id,
                quantidade_embalagem_insumo=excluded.quantidade_embalagem_insumo,
                sacola_id=excluded.sacola_id,
                quantidade_sacola=excluded.quantidade_sacola,
                ativo=1,
                atualizado_em=excluded.atualizado_em
        """, (
            receita_id,
            float(quantidade_venda),
            float(markup),
            preco_praticado_centavos,
            embalagem_id,
            float(quantidade_embalagem),
            sacola_id,
            float(quantidade_sacola),
            stamp,
            stamp,
        ))

        row = con.execute("""
            SELECT id FROM precificacoes WHERE receita_id=?
        """, (receita_id,)).fetchone()

        con.execute("""
            INSERT INTO historico_precificacoes (
                precificacao_id,
                preco_sugerido_centavos,
                preco_praticado_centavos,
                custo_total_centavos,
                registrado_em
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            row["id"],
            round(calculo["preco_sugerido"] * 100),
            preco_praticado_centavos,
            round(calculo["custo_total"] * 100),
            stamp,
        ))

        con.commit()
        return row["id"]
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def listar_precificacoes():
    con = obter_conexao()
    try:
        rows = con.execute("""
            SELECT p.*, r.nome AS nome_produto
            FROM precificacoes p
            JOIN receitas r ON r.id=p.receita_id
            WHERE p.ativo=1
              AND r.ativo=1
              AND r.tipo='FINAL'
            ORDER BY r.nome COLLATE NOCASE
        """).fetchall()
    finally:
        con.close()

    resultado = []

    for p in rows:
        calc = calcular_precificacao_completa(
            p["receita_id"],
            p["quantidade_embalagem"],
            p["embalagem_id"],
            p["quantidade_embalagem_insumo"],
            p["sacola_id"],
            p["quantidade_sacola"],
            p["markup"],
        )

        praticado = (
            p["preco_praticado_centavos"] / 100
            if p["preco_praticado_centavos"] is not None
            else None
        )

        markup_praticado = None
        status = "Não informado"

        if praticado is not None and calc["custo_total"] > 0:
            markup_praticado = (
                praticado / calc["custo_total"]
            ) - 1

            if praticado < calc["preco_sugerido"] - 0.01:
                status = "Abaixo do ideal"
            elif praticado > calc["preco_sugerido"] + 0.01:
                status = "Acima do ideal"
            else:
                status = "No ideal"

        resultado.append({
            "id": p["id"],
            "receita_id": p["receita_id"],
            "nome": p["nome_produto"],
            **calc,
            "preco_praticado": praticado,
            "markup_praticado": markup_praticado,
            "status": status,
        })

    return resultado
