"""Localização persistente do banco de dados em desenvolvimento e no Flet."""
import os
import sqlite3
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO_LEGADO = PASTA_PROJETO / "database" / "dm_gulositos.db"
PASTA_DADOS_FLET = os.environ.get("FLET_APP_STORAGE_DATA")

if PASTA_DADOS_FLET:
    PASTA_DADOS = Path(PASTA_DADOS_FLET).expanduser().resolve()
    CAMINHO_BANCO = PASTA_DADOS / "database" / "dm_gulositos.db"
else:
    PASTA_DADOS = PASTA_PROJETO
    CAMINHO_BANCO = CAMINHO_BANCO_LEGADO


def migrar_banco_legado_se_necessario(caminho_legado=None, caminho_destino=None):
    """Copia o banco antigo para o armazenamento persistente sem apagar a origem."""
    origem = Path(caminho_legado or CAMINHO_BANCO_LEGADO)
    destino = Path(caminho_destino or CAMINHO_BANCO)

    # Migração automática só é necessária quando o Flet definiu outro diretório.
    if caminho_destino is None and CAMINHO_BANCO == CAMINHO_BANCO_LEGADO:
        return None
    if destino.exists():
        return destino
    if not origem.is_file() or origem.stat().st_size == 0:
        return None

    destino.parent.mkdir(parents=True, exist_ok=True)
    conexao_origem = sqlite3.connect(str(origem), timeout=30)
    conexao_destino = sqlite3.connect(str(destino), timeout=30)
    try:
        conexao_origem.backup(conexao_destino)
        conexao_destino.commit()
        integridade = conexao_destino.execute("PRAGMA integrity_check").fetchone()
        if not integridade or integridade[0] != "ok":
            raise RuntimeError("A cópia migrada do banco não passou na verificação de integridade.")
    except Exception:
        conexao_destino.close()
        conexao_origem.close()
        destino.unlink(missing_ok=True)
        raise
    else:
        conexao_destino.close()
        conexao_origem.close()

    return destino
