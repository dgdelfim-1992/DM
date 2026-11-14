# Checklist de preparação da versão 1.0.0

## Antes dos testes
- [ ] Atualizar a branch local `refatoracao-modular`.
- [ ] Confirmar que o banco real está preservado e fazer uma cópia externa.
- [ ] Conferir se a migração para `FLET_APP_STORAGE_DATA` preserva os registros.
- [ ] Não usar o banco real em testes destrutivos.

## Validação automatizada
- [ ] Executar todos os testes com `python -m unittest discover -s tests -v`.
- [ ] Corrigir falhas e repetir a suíte completa.
- [ ] Conferir os testes de backup, restauração, retenção e migração.

## Validação funcional
- [ ] Abrir todos os sete itens do menu.
- [ ] Conferir Insumos, Receitas, Custos Fixos e Precificação.
- [ ] Criar, editar, enviar e consultar um orçamento.
- [ ] Conferir agenda e relatórios.
- [ ] Exportar backup e validar o arquivo.
- [ ] Restaurar somente um banco temporário e conferir a cópia anterior.
- [ ] Conferir execução web.

## APK
- [ ] Exportar um backup válido do banco real no computador e guardá-lo fora da pasta do projeto.
- [ ] Gerar o APK de release sem incluir bancos SQLite ou backups locais.
- [ ] Instalar em Android e conferir ícone, tela de abertura e nome.
- [ ] Importar o backup exportado no celular e conferir os registros.
- [ ] Conferir persistência dos dados após fechar e reabrir.
- [ ] Conferir atualização sobre uma instalação anterior sem perda de dados.
- [ ] Guardar uma cópia do APK e do backup final em local externo.
