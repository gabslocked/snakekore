# Changelog

Todas as mudanças notáveis do PythonKore serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Não Lançado]

### Adicionado
- Sistema de testes completo com pytest
- Test runner com validação de ambiente
- Testes unitários para coordinate system, AI manager, settings manager
- Testes de integração end-to-end
- Performance benchmarks
- Coverage reporting

### Modificado
- Correção de imports relativos para absolutos
- Melhorias na documentação do código
- Otimizações de performance no event bus

## [0.1.0-dev] - 2024-01-XX

### Adicionado
- **Core System**
  - Sistema de configurações compatível com OpenKore
  - Sistema de logging com cores ANSI
  - Event bus assíncrono para comunicação entre módulos
  - CLI interface com argumentos completos

- **AI System**
  - State machine com 29 estados (OFF, AUTO, MANUAL, COMBAT, etc.)
  - Action queue com prioridades e retry automático
  - Context management para dados compartilhados
  - Transições automáticas baseadas em condições

- **Network System**
  - Connection management com reconexão automática
  - Socket manager com SSL/TLS support
  - Async client event-driven
  - Packet system básico com parsing

- **Task System**
  - Task manager com execução concorrente
  - Prioridades, timeouts e retries automáticos
  - Sistema de dependências entre tasks
  - Controle de pausar/resumir/cancelar tasks

- **Plugin System**
  - Plugin manager com descoberta automática
  - Sistema de dependências entre plugins
  - Built-in plugins (auto_response, item_logger)
  - Base para hot-reload de plugins

- **World System**
  - Sistema de coordenadas 8-direções
  - Field system com walkability
  - Cálculos de distância (Euclidiana, Manhattan, Chebyshev)
  - Sistema de áreas e regiões

- **Actor System**
  - Base actor com posição e stats
  - Sistema de propriedades customizáveis
  - Integração com coordinate system

- **Interface System**
  - Console interface interativa
  - Comandos básicos (status, ai, tasks, etc.)
  - Histórico de comandos
  - Integração com AI e Task managers

- **Utils**
  - Math utils com funções RO-específicas
  - String utils para parsing de itens RO
  - Time utils com Timer pausável
  - Extensive validation helpers

### Arquitetura
- **Async/Await**: Arquitetura assíncrona para performance
- **Type Hints**: 100% type safety com mypy
- **Clean Architecture**: Separação clara de responsabilidades
- **Event-driven**: Desacoplamento via event bus
- **Plugin Architecture**: Sistema extensível de plugins

### Compatibilidade
- **Configurações**: 100% compatível com arquivos OpenKore
- **Tabelas**: Suporte aos formatos de dados originais
- **Comandos**: Interface similar ao OpenKore original

### Qualidade
- **Testes**: Suite de testes abrangente
- **Documentation**: Documentação completa em português
- **Code Style**: Formatação consistente com black
- **Linting**: Análise estática com flake8 e mypy

## [0.0.1] - 2024-01-XX

### Adicionado
- Estrutura inicial do projeto
- Análise arquitetural do OpenKore original
- Requirements e dependências
- TODO estruturado com 13 fases de desenvolvimento
- Documentação inicial

---

## Tipos de Mudanças

- `Adicionado` para novas funcionalidades
- `Modificado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correções de bugs
- `Segurança` para vulnerabilidades corrigidas 