# Guia de Contribuição 🤝

Obrigado pelo interesse em contribuir com o PythonKore! Este guia te ajudará a começar.

## 📋 Índice

- [Como Contribuir](#como-contribuir)
- [Setup do Ambiente](#setup-do-ambiente)
- [Padrões de Código](#padrões-de-código)
- [Testes](#testes)
- [Pull Requests](#pull-requests)
- [Issues](#issues)
- [Código de Conduta](#código-de-conduta)

## 🚀 Como Contribuir

### Tipos de Contribuição
- 🐛 **Bug Reports**: Relatar problemas encontrados
- 💡 **Feature Requests**: Sugerir novas funcionalidades
- 📝 **Documentação**: Melhorar docs e exemplos
- 🧪 **Testes**: Adicionar ou melhorar testes
- 🔧 **Código**: Implementar features ou corrigir bugs

### Primeiros Passos
1. **Fork** o repositório
2. **Clone** seu fork localmente
3. **Configure** o ambiente de desenvolvimento
4. **Crie** uma branch para sua contribuição
5. **Implemente** suas mudanças
6. **Teste** suas modificações
7. **Submeta** um Pull Request

## 🛠️ Setup do Ambiente

### Pré-requisitos
- Python 3.11+
- Git
- Editor de código (recomendado: VS Code)

### Instalação
```bash
# Clone seu fork
git clone https://github.com/seu-usuario/pythonkore.git
cd pythonkore

# Adicione o repositório original como upstream
git remote add upstream https://github.com/pythonkore/pythonkore.git

# Crie ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale dependências
pip install -r requirements.txt

# Instale dependências de desenvolvimento
pip install -r requirements-dev.txt

# Instale pre-commit hooks
pre-commit install
```

### Verificação do Setup
```bash
# Execute os testes
python tests/run_tests.py

# Verifique linting
flake8 src/ tests/

# Verifique type checking
mypy src/

# Verifique formatação
black --check src/ tests/
```

## 📝 Padrões de Código

### Style Guide
Seguimos o **PEP 8** com algumas adaptações:

- **Linha máxima**: 88 caracteres (black default)
- **Imports**: Organizados com isort
- **Type hints**: Obrigatórios em todas as funções públicas
- **Docstrings**: Google style para todas as classes e funções públicas

### Formatação
```bash
# Formatação automática
black src/ tests/

# Organização de imports
isort src/ tests/

# Verificação de linting
flake8 src/ tests/

# Type checking
mypy src/
```

### Exemplo de Código
```python
"""
Module docstring explaining the purpose.
"""

from typing import Optional, List
import asyncio

from core.logging.logger import Logger


class ExampleClass:
    """
    Example class following our standards.
    
    Args:
        name: The name of the example
        logger: Optional logger instance
    """
    
    def __init__(self, name: str, logger: Optional[Logger] = None) -> None:
        self.name = name
        self.logger = logger or Logger()
    
    async def process_items(self, items: List[str]) -> bool:
        """
        Process a list of items asynchronously.
        
        Args:
            items: List of items to process
            
        Returns:
            True if all items were processed successfully
            
        Raises:
            ValueError: If items list is empty
        """
        if not items:
            raise ValueError("Items list cannot be empty")
        
        self.logger.info(f"Processing {len(items)} items")
        
        for item in items:
            await self._process_single_item(item)
        
        return True
    
    async def _process_single_item(self, item: str) -> None:
        """Process a single item (private method)."""
        # Implementation here
        pass
```

### Naming Conventions
- **Classes**: PascalCase (`AIManager`, `SettingsManager`)
- **Functions/Methods**: snake_case (`process_items`, `get_status`)
- **Variables**: snake_case (`current_state`, `item_count`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private**: Prefixo underscore (`_process_item`, `_internal_state`)

## 🧪 Testes

### Executando Testes
```bash
# Todos os testes
python tests/run_tests.py

# Apenas unit tests
python tests/run_tests.py --unit

# Apenas integration tests
python tests/run_tests.py --integration

# Com coverage
python tests/run_tests.py --coverage

# Teste específico
python tests/run_tests.py --test test_ai_manager.py
```

### Escrevendo Testes
- **Unit tests**: Para testar módulos isoladamente
- **Integration tests**: Para testar interação entre módulos
- **Fixtures**: Use pytest fixtures para setup comum
- **Mocks**: Use mocks para dependências externas

### Exemplo de Teste
```python
"""Test example following our standards."""

import pytest
from unittest.mock import Mock

from ai.ai_manager import AIManager
from core.logging.logger import Logger


class TestAIManager:
    """Tests for AIManager class."""
    
    @pytest.fixture
    def logger(self):
        """Mock logger for tests."""
        return Mock(spec=Logger)
    
    @pytest.fixture
    def ai_manager(self, logger):
        """AIManager instance for tests."""
        return AIManager(logger=logger)
    
    def test_initialization(self, ai_manager, logger):
        """Test AIManager initialization."""
        assert ai_manager.logger == logger
        assert ai_manager.running is False
    
    @pytest.mark.asyncio
    async def test_start_stop(self, ai_manager):
        """Test start/stop functionality."""
        ai_manager.start()
        assert ai_manager.running is True
        
        ai_manager.stop()
        assert ai_manager.running is False
```

### Coverage
- **Mínimo**: 80% coverage para novos módulos
- **Meta**: 90%+ coverage para código crítico
- **Exclusões**: Apenas para código que não pode ser testado

## 📥 Pull Requests

### Antes de Submeter
1. **Sincronize** com upstream
2. **Execute** todos os testes
3. **Verifique** linting e formatting
4. **Atualize** documentação se necessário
5. **Adicione** entrada no CHANGELOG.md

### Template de PR
```markdown
## Descrição
Breve descrição das mudanças implementadas.

## Tipo de Mudança
- [ ] Bug fix (mudança que corrige um problema)
- [ ] Nova feature (mudança que adiciona funcionalidade)
- [ ] Breaking change (mudança que quebra compatibilidade)
- [ ] Documentação (mudança apenas em documentação)

## Como Testar
Passos para testar as mudanças:
1. ...
2. ...

## Checklist
- [ ] Código segue os padrões do projeto
- [ ] Self-review do código realizado
- [ ] Comentários adicionados em código complexo
- [ ] Documentação atualizada
- [ ] Testes adicionados/atualizados
- [ ] Todos os testes passam
- [ ] CHANGELOG.md atualizado
```

### Review Process
1. **Automated checks**: CI/CD verifica testes e linting
2. **Code review**: Maintainers revisam o código
3. **Feedback**: Discussão e melhorias
4. **Approval**: Aprovação final e merge

## 🐛 Issues

### Bug Reports
Use o template de bug report:
```markdown
## Descrição do Bug
Descrição clara e concisa do problema.

## Reprodução
Passos para reproduzir:
1. ...
2. ...

## Comportamento Esperado
O que deveria acontecer.

## Comportamento Atual
O que realmente acontece.

## Ambiente
- OS: [Windows/Linux/Mac]
- Python: [versão]
- PythonKore: [versão]

## Logs
```
Logs relevantes aqui
```

## Screenshots
Se aplicável, adicione screenshots.
```

### Feature Requests
Use o template de feature request:
```markdown
## Descrição da Feature
Descrição clara da funcionalidade desejada.

## Motivação
Por que esta feature seria útil?

## Solução Proposta
Como você imagina que deveria funcionar?

## Alternativas
Outras abordagens consideradas.

## Informações Adicionais
Qualquer contexto adicional.
```

## 📚 Documentação

### Docstrings
Use Google style docstrings:
```python
def example_function(param1: str, param2: int = 0) -> bool:
    """
    Example function with Google style docstring.
    
    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to 0.
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is empty
        
    Example:
        >>> result = example_function("test", 5)
        >>> print(result)
        True
    """
    pass
```

### README Updates
- Mantenha o README.md atualizado
- Adicione exemplos para novas features
- Atualize instalação se necessário

## 🌟 Código de Conduta

### Nossos Valores
- **Respeito**: Trate todos com respeito e cortesia
- **Inclusão**: Ambiente acolhedor para todos
- **Colaboração**: Trabalhe junto para objetivos comuns
- **Qualidade**: Busque sempre a excelência

### Comportamento Esperado
- Use linguagem acolhedora e inclusiva
- Respeite diferentes pontos de vista
- Aceite críticas construtivas
- Foque no que é melhor para a comunidade

### Comportamento Inaceitável
- Linguagem ou imagens sexualizadas
- Trolling, insultos ou ataques pessoais
- Assédio público ou privado
- Publicar informações privadas sem permissão

### Aplicação
Casos de comportamento inaceitável podem ser reportados para [email]. Todas as reclamações serão revisadas e investigadas.

## 🎯 Roadmap de Contribuição

### Iniciante
- Corrigir typos na documentação
- Adicionar testes para código existente
- Implementar validações simples
- Melhorar mensagens de erro

### Intermediário
- Implementar novas features pequenas
- Otimizar performance de módulos
- Adicionar novos plugins builtin
- Melhorar interface de usuário

### Avançado
- Implementar networking RO
- Desenvolver sistema de pathfinding
- Criar interface gráfica
- Otimizar arquitetura core

## 📞 Contato

- **Discord**: [Link do servidor](https://discord.gg/pythonkore)
- **Email**: [maintainers@pythonkore.org](mailto:maintainers@pythonkore.org)
- **Issues**: [GitHub Issues](https://github.com/pythonkore/pythonkore/issues)

---

**Obrigado por contribuir com o PythonKore! 🙏** 