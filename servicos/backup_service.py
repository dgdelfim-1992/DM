"""Rotinas seguras de backup, exportação e restauração do banco SQLite."""
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO_PADRAO = PASTA_PROJETO / "database" / "dm_gulositos.db"
TABELAS_OBRIGATORIAS = {"ingredientes", "receitas", "configuracoes"}


def _resolver_caminho(caminho_banco=None):
    return Path(caminho_banco or CAMINHO_BANCO_PADRAO)


def criar_copia_sqlite(origem, destino):
    """Cria uma cópia consistente usando a API de backup do SQLite."""
    origem, destino = Path(origem), Path(destino)
    if not origem.is_file() or origem.stat().st_size == 0:
        raise FileNotFoundError("Banco de dados de origem não encontrado ou vazio.")
    if origem.resolve() == destino.resolve():
        raise ValueError("A origem e o destino do backup devem ser diferentes.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    conexao_origem = sqlite3.connect(str(origem), timeout=30)
    conexao_destino = sqlite3.connect(str(destino), timeout=30)
    try:
        conexao_origem.backup(conexao_destino)
        conexao_destino.commit()
    except Exception:
        conexao_destino.close()
        conexao_origem.close()
        destino.unlink(missing_ok=True)
        raise
    else:
        conexao_destino.close()
        conexao_origem.close()
    return destino


def validar_banco(caminho):
    """Confere integridade SQLite e presença das tabelas essenciais."""
    caminho = Path(caminho)
    if not caminho.is_file() or caminho.stat().st_size == 0:
        raise ValueError("O arquivo de banco está vazio ou não existe.")
    conexao = sqlite3.connect(f"{caminho.resolve().as_uri()}?mode=ro", uri=True)
    try:
        resultado = conexao.execute("PRAGMA integrity_check").fetchone()
        if not resultado or resultado[0] != "ok":
            raise ValueError("O banco está corrompido.")
        tabelas = {
            linha[0] for linha in conexao.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if not TABELAS_OBRIGATORIAS.issubset(tabelas):
            raise ValueError("O arquivo selecionado não pertence à DM Gulositos.")
    except sqlite3.DatabaseError as erro:
        raise ValueError("O arquivo selecionado não é um banco SQLite válido.") from erro
    finally:
        conexao.close()
    return True


def criar_backup_automatico(limite=15, caminho_banco=None):
    """Cria no máximo um backup válido por dia e aplica retenção."""
    if not isinstance(limite, int) or limite < 1:
        raise ValueError("O limite de backups deve ser um número inteiro maior que zero.")
    banco = _resolver_caminho(caminho_banco)
    if not banco.is_file() or banco.stat().st_size == 0:
        return None
    pasta_backups = banco.parent / "backups"
    pasta_backups.mkdir(parents=True, exist_ok=True)
    hoje = datetime.now().strftime("%Y%m%d")
    backups_hoje = sorted(pasta_backups.glob(f"automatico_{hoje}_*.db"))
    for existente in reversed(backups_hoje):
        try:
            validar_banco(existente)
            return existente
        except (ValueError, sqlite3.DatabaseError):
            continue
    destino = pasta_backups / datetime.now().strftime(
        "automatico_%Y%m%d_%H%M%S_%f.db"
    )
    criar_copia_sqlite(banco, destino)
    try:
        validar_banco(destino)
    except Exception:
        destino.unlink(missing_ok=True)
        raise
    backups = sorted(
        pasta_backups.glob("automatico_*.db"),
        key=lambda arquivo: arquivo.stat().st_mtime,
        reverse=True,
    )
    for antigo in backups[limite:]:
        antigo.unlink()
    return destino


def gerar_backup_bytes(caminho_banco=None):
    """Gera em memória uma cópia consistente pronta para exportação."""
    banco = _resolver_caminho(caminho_banco)
    if not banco.is_file():
        raise FileNotFoundError("Banco de dados não encontrado.")
    with tempfile.TemporaryDirectory() as pasta:
        temporario = Path(pasta) / "backup_gulositos.db"
        criar_copia_sqlite(banco, temporario)
        validar_banco(temporario)
        return temporario.read_bytes()


def restaurar_banco_bytes(conteudo, caminho_banco=None):
    """Valida o arquivo, protege o banco atual e só então faz a substituição."""
    if not isinstance(conteudo, (bytes, bytearray, memoryview)) or not conteudo:
        raise ValueError("O arquivo selecionado está vazio ou não contém dados válidos.")
    banco = _resolver_caminho(caminho_banco)
    banco.parent.mkdir(parents=True, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".db", prefix="restauracao_",
            dir=banco.parent, delete=False,
        ) as arquivo:
            arquivo.write(bytes(conteudo))
            temporario = Path(arquivo.name)
        validar_banco(temporario)
        if banco.exists():
            conexao = sqlite3.connect(str(banco), timeout=30)
            try:
                checkpoint = conexao.execute(
                    "PRAGMA wal_checkpoint(TRUNCATE)"
                ).fetchone()
                if checkpoint and checkpoint[0] != 0:
                    raise RuntimeError(
                        "Não foi possível finalizar as gravações pendentes do banco atual. "
                        "Feche outras telas ou tente novamente."
                    )
            finally:
                conexao.close()
            pasta_backups = banco.parent / "backups"
            pasta_backups.mkdir(parents=True, exist_ok=True)
            nome = datetime.now().strftime("antes_restauracao_%Y%m%d_%H%M%S_%f.db")
            backup_atual = pasta_backups / nome
            criar_copia_sqlite(banco, backup_atual)
            validar_banco(backup_atual)
        for sufixo in ("-wal", "-shm"):
            auxiliar = Path(f"{banco}{sufixo}")
            if auxiliar.exists():
                auxiliar.unlink()
        os.replace(temporario, banco)
        temporario = None
        validar_banco(banco)
        return banco
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()
