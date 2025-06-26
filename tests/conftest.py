"""
PyTest Configuration
===================

Configuração e fixtures para testes do PythonKore.
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Generator, Dict, Any

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.logging.logger import Logger
from core.events.event_bus import EventBus
from core.settings.settings_manager import SettingsManager
from plugins.plugin_manager import PluginManager
from ai.ai_manager import AIManager
from tasks.task_manager import TaskManager
from world.field import Field
from world.coordinate_system import Coordinate


@pytest.fixture
def logger() -> Logger:
    """Fixture para logger de teste."""
    return Logger(level="DEBUG", log_file=None)


@pytest.fixture
def event_bus() -> EventBus:
    """Fixture para event bus de teste."""
    return EventBus()


@pytest.fixture
def settings_manager(tmp_path) -> SettingsManager:
    """Fixture para settings manager de teste."""
    # Cria diretório temporário para configurações
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Cria arquivo config.txt básico
    config_file = config_dir / "config.txt"
    config_file.write_text("""
# Test configuration
username test_user
password test_pass
server test_server
char test_char
""")
    
    sm = SettingsManager(str(config_dir))
    sm.load_config_file(str(config_file))
    return sm


@pytest.fixture
def plugin_manager(logger, event_bus) -> PluginManager:
    """Fixture para plugin manager de teste."""
    return PluginManager(logger=logger, event_bus=event_bus)


@pytest.fixture
def ai_manager(logger, event_bus) -> AIManager:
    """Fixture para AI manager de teste."""
    return AIManager(logger=logger, event_bus=event_bus)


@pytest.fixture
def task_manager(logger, event_bus) -> TaskManager:
    """Fixture para task manager de teste."""
    return TaskManager(logger=logger, event_bus=event_bus)


@pytest.fixture
def test_field() -> Field:
    """Fixture para campo de teste."""
    field = Field("test_field", 100, 100)
    field.loaded = True
    return field


@pytest.fixture
def test_coordinates() -> Dict[str, Coordinate]:
    """Fixture para coordenadas de teste."""
    return {
        'origin': Coordinate(0, 0),
        'center': Coordinate(50, 50),
        'corner': Coordinate(99, 99),
        'invalid': Coordinate(-1, -1)
    }


@pytest.fixture
def mock_network():
    """Fixture para rede mock."""
    mock = MagicMock()
    mock.is_connected.return_value = False
    mock.connect.return_value = True
    mock.disconnect.return_value = True
    mock.send_packet.return_value = True
    return mock


@pytest.fixture
def sample_plugin_config() -> Dict[str, Any]:
    """Fixture para configuração de plugin de teste."""
    return {
        'enabled': True,
        'debug': False,
        'test_setting': 'test_value',
        'numeric_setting': 42,
        'list_setting': ['item1', 'item2', 'item3']
    }


@pytest.fixture
def event_loop():
    """Fixture para loop de eventos async."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Fixtures para dados de teste específicos do RO
@pytest.fixture
def sample_character_data() -> Dict[str, Any]:
    """Fixture para dados de personagem de teste."""
    return {
        'name': 'TestChar',
        'level': 50,
        'job_level': 25,
        'class': 'Knight',
        'hp': 5000,
        'max_hp': 5000,
        'sp': 500,
        'max_sp': 500,
        'exp': 1000000,
        'job_exp': 50000,
        'stats': {
            'str': 50,
            'agi': 30,
            'vit': 40,
            'int': 20,
            'dex': 35,
            'luk': 25
        },
        'position': {
            'x': 150,
            'y': 200,
            'map': 'prontera'
        }
    }


@pytest.fixture
def sample_item_data() -> Dict[str, Any]:
    """Fixture para dados de item de teste."""
    return {
        'id': 501,
        'name': 'Red Potion',
        'quantity': 10,
        'type': 'consumable',
        'weight': 70,
        'description': 'A healing potion'
    }


@pytest.fixture
def sample_monster_data() -> Dict[str, Any]:
    """Fixture para dados de monstro de teste."""
    return {
        'id': 1002,
        'name': 'Poring',
        'level': 1,
        'hp': 50,
        'max_hp': 50,
        'position': {
            'x': 100,
            'y': 150
        },
        'aggressive': False,
        'element': 'neutral'
    }


# Helpers para testes
class TestHelper:
    """Classe helper para testes."""
    
    @staticmethod
    def create_mock_event(event_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Cria evento mock para testes."""
        return {
            'type': event_type,
            'timestamp': 1234567890.0,
            'data': data or {}
        }
    
    @staticmethod
    def assert_event_emitted(event_bus: EventBus, event_type: str) -> bool:
        """Verifica se evento foi emitido."""
        # TODO: Implementar verificação de eventos
        return True
    
    @staticmethod
    def wait_for_condition(condition_func, timeout: float = 5.0) -> bool:
        """Aguarda condição ser verdadeira com timeout."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(0.1)
        
        return False


@pytest.fixture
def test_helper() -> TestHelper:
    """Fixture para helper de testes."""
    return TestHelper()


# Configurações do pytest
def pytest_configure(config):
    """Configuração do pytest."""
    # Adiciona markers customizados
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )
    config.addinivalue_line(
        "markers", "network: marca testes que precisam de rede"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica itens da coleção de testes."""
    # Adiciona marker 'unit' para testes em test_unit/
    # Adiciona marker 'integration' para testes em test_integration/
    for item in items:
        if "test_unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# Fixtures de teardown
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Limpeza automática após cada teste."""
    yield
    # Cleanup code aqui se necessário
    pass 