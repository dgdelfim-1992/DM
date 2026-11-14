# Histórico de versões

## 1.0.0 — Em preparação

### Organização e interface
- Organização modular das telas de Insumos, Receitas, Custos Fixos, Orçamentos, Agenda e Relatórios.
- Menu principal dividido por áreas de trabalho.
- Cabeçalhos compartilhados nas telas de Agenda e Custos Fixos.
- Identidade visual do aplicativo configurada com ícone, tela de abertura e versão.

### Gestão da doceria
- Cadastro de insumos e histórico de preços.
- Receitas e sub-receitas com fichas técnicas e tempos de produção.
- Custos fixos, mão de obra e parâmetros de precificação.
- Precificação de produtos, orçamentos, agenda e relatórios.

### Segurança e persistência
- Serviço dedicado para backup automático, exportação, validação e restauração.
- Dupla confirmação antes de restaurar um backup.
- Cópia de segurança do banco atual antes da restauração.
- Migração para o armazenamento persistente do Flet, mantendo o banco legado original.
- Arquivos SQLite locais e diretórios de dados excluídos do versionamento.

### Validação
- Testes automatizados de backup, restauração, migração e consultas adicionados.
- Execução dos testes, validação manual, execução web e build APK ainda pendentes.
