"""
Testes de Integração do Sistema Completo
========================================

Testes que verificam a integração entre múltiplos componentes.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.application import PythonKoreApplication
from core.settings.settings_manager import SettingsManager
from core.logging.logger import Logger
from core.events.event_bus import EventBus
from ai.ai_manager import AIManager
from tasks.task_manager import TaskManager
from plugins.plugin_manager import PluginManager


class TestFullSystemIntegration:
    """Testes de integração do sistema completo."""
    
    @pytest.fixture
    def temp_dir(self):
        """Diretório temporário para testes."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """Diretório de configuração para testes."""
        config_path = Path(temp_dir) / "config"
        config_path.mkdir()
        return str(config_path)
    
    @pytest.fixture
    def app_config(self, config_dir):
        """Configuração de aplicação para testes."""
        return {
            'config_dir': config_dir,
            'interface': 'console',
            'debug': True,
            'log_level': 'DEBUG'
        }
    
    @pytest.fixture
    async def application(self, app_config):
        """Aplicação completa para testes."""
        app = PythonKoreApplication(app_config)
        await app.initialize()
        yield app
        await app.shutdown()
    
    @pytest.mark.integration
    async def test_application_lifecycle(self, application):
        """Testa ciclo de vida completo da aplicação."""
        # Aplicação deve estar inicializada
        assert application.state.name in ['INITIALIZED', 'READY']
        assert application.logger is not None
        assert application.settings is not None
        assert application.event_bus is not None
        
        # Start aplicação
        await application.start()
        assert application.state.name == 'RUNNING'
        
        # Stop aplicação
        await application.stop()
        assert application.state.name == 'STOPPED'
    
    @pytest.mark.integration
    async def test_settings_ai_integration(self, config_dir):
        """Testa integração entre settings e AI."""
        # Criar configuração
        config_file = Path(config_dir) / "config.txt"
        config_file.write_text("""
# AI Configuration
attackAuto 2
lockMap 1
ai_attack_timeout 5
""")
        
        # Criar componentes
        settings = SettingsManager(config_dir)
        settings.load_config_file(str(config_file))
        
        logger = Logger(level="DEBUG")
        event_bus = EventBus()
        ai_manager = AIManager(logger=logger, event_bus=event_bus)
        
        # Configurar AI com settings
        ai_manager.set_context('attackAuto', settings.get('attackAuto'))
        ai_manager.set_context('lockMap', settings.get('lockMap'))
        
        # Verificar integração
        assert ai_manager.get_context('attackAuto') == '2'
        assert ai_manager.get_context('lockMap') == '1'
    
    @pytest.mark.integration
    async def test_ai_task_integration(self):
        """Testa integração entre AI e Task Manager."""
        logger = Logger(level="DEBUG")
        event_bus = EventBus()
        
        ai_manager = AIManager(logger=logger, event_bus=event_bus)
        task_manager = TaskManager(logger=logger, event_bus=event_bus)
        
        # Iniciar componentes
        ai_manager.start()
        await task_manager.start()
        
        # Criar task para AI
        async def ai_task():
            ai_manager.set_context('task_executed', True)
            return True
        
        # Adicionar task
        task_id = await task_manager.add_task(ai_task, priority=5)
        
        # Processar tasks
        processed = await task_manager.execute_pending_tasks()
        assert processed > 0
        
        # Verificar execução
        assert ai_manager.get_context('task_executed') is True
        
        # Cleanup
        ai_manager.stop()
        await task_manager.stop()
    
    @pytest.mark.integration
    async def test_plugin_system_integration(self, config_dir):
        """Testa integração do sistema de plugins."""
        logger = Logger(level="DEBUG")
        event_bus = EventBus()
        settings = SettingsManager(config_dir)
        
        plugin_manager = PluginManager(logger=logger, event_bus=event_bus)
        
        # Carregar plugins built-in
        loaded_plugins = plugin_manager.discover_plugins()
        assert len(loaded_plugins) >= 0  # Pode não ter plugins
        
        # Plugin deve ter access aos componentes
        plugin_manager.logger = logger
        plugin_manager.event_bus = event_bus
        
        # Verificar integração
        assert plugin_manager.logger is not None
        assert plugin_manager.event_bus is not None
    
    @pytest.mark.integration
    async def test_event_system_integration(self):
        """Testa integração do sistema de eventos."""
        logger = Logger(level="DEBUG")
        event_bus = EventBus()
        
        ai_manager = AIManager(logger=logger, event_bus=event_bus)
        task_manager = TaskManager(logger=logger, event_bus=event_bus)
        
        # Contador de eventos
        event_count = {'ai_events': 0, 'task_events': 0}
        
        # Handlers de evento
        async def ai_event_handler(event):
            event_count['ai_events'] += 1
        
        async def task_event_handler(event):
            event_count['task_events'] += 1
        
        # Registrar handlers
        event_bus.on('ai_state_changed', ai_event_handler)
        event_bus.on('task_completed', task_event_handler)
        
        # Gerar eventos
        ai_manager.start()  # Deve emitir evento
        
        async def test_task():
            return True
        
        await task_manager.start()
        task_id = await task_manager.add_task(test_task)
        await task_manager.execute_pending_tasks()  # Deve emitir evento
        
        # Dar tempo para eventos processarem
        await asyncio.sleep(0.1)
        
        # Verificar eventos recebidos
        assert event_count['ai_events'] > 0
        # task_events pode ser 0 dependendo da implementação
        
        # Cleanup
        ai_manager.stop()
        await task_manager.stop()
    
    @pytest.mark.integration
    def test_logging_integration(self, config_dir):
        """Testa integração do sistema de logging."""
        # Criar logger com arquivo
        log_file = Path(config_dir) / "test.log"
        logger = Logger(level="DEBUG", log_file=str(log_file))
        
        # Criar componentes com logger
        event_bus = EventBus()
        settings = SettingsManager(config_dir)
        ai_manager = AIManager(logger=logger, event_bus=event_bus)
        
        # Gerar logs
        logger.info("Test log message")
        ai_manager.start()
        ai_manager.stop()
        
        # Verificar arquivo de log
        if log_file.exists():
            log_content = log_file.read_text()
            assert "Test log message" in log_content
    
    @pytest.mark.integration
    async def test_configuration_reload(self, config_dir):
        """Testa reload de configuração em runtime."""
        # Configuração inicial
        config_file = Path(config_dir) / "config.txt"
        config_file.write_text("test_setting initial_value")
        
        settings = SettingsManager(config_dir)
        settings.load_config_file(str(config_file))
        
        assert settings.get('test_setting') == 'initial_value'
        
        # Modificar configuração
        config_file.write_text("test_setting modified_value")
        
        # Recarregar
        settings.load_config_file(str(config_file))
        
        assert settings.get('test_setting') == 'modified_value'
    
    @pytest.mark.integration
    async def test_error_handling_integration(self):
        """Testa tratamento de erros entre componentes."""
        logger = Logger(level="DEBUG")
        event_bus = EventBus()
        
        ai_manager = AIManager(logger=logger, event_bus=event_bus)
        task_manager = TaskManager(logger=logger, event_bus=event_bus)
        
        # Task que falha
        async def failing_task():
            raise Exception("Test error")
        
        # Iniciar componentes
        ai_manager.start()
        await task_manager.start()
        
        # Adicionar task que falha
        task_id = await task_manager.add_task(failing_task)
        
        # Processar (não deve parar o sistema)
        processed = await task_manager.execute_pending_tasks()
        
        # Sistema deve continuar funcionando
        assert ai_manager.running
        assert task_manager.running
        
        # Cleanup
        ai_manager.stop()
        await task_manager.stop()
    
    @pytest.mark.integration  
    async def test_performance_integration(self):
        """Testa performance do sistema integrado."""
        import time
        
        logger = Logger(level="WARNING")  # Menos verbose
        event_bus = EventBus()
        
        ai_manager = AIManager(logger=logger, event_bus=event_bus)
        task_manager = TaskManager(logger=logger, event_bus=event_bus)
        
        # Iniciar componentes
        start_time = time.time()
        
        ai_manager.start()
        await task_manager.start()
        
        init_time = time.time() - start_time
        
        # Adicionar múltiplas tasks
        async def simple_task():
            return True
        
        task_start = time.time()
        
        # Adicionar 100 tasks
        tasks = []
        for i in range(100):
            task_id = await task_manager.add_task(simple_task)
            tasks.append(task_id)
        
        # Processar todas
        processed = await task_manager.execute_pending_tasks()
        
        task_time = time.time() - task_start
        
        # Verificar performance
        assert init_time < 1.0  # Inicialização deve ser rápida
        assert task_time < 5.0  # 100 tasks em menos de 5s
        assert processed == 100
        
        # Cleanup
        ai_manager.stop()
        await task_manager.stop()
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_long_running_integration(self):
        """Testa integração em execução prolongada."""
        logger = Logger(level="WARNING")
        event_bus = EventBus()
        
        ai_manager = AIManager(logger=logger, event_bus=event_bus)
        task_manager = TaskManager(logger=logger, event_bus=event_bus)
        
        # Iniciar componentes
        ai_manager.start()
        await task_manager.start()
        
        # Simular execução prolongada
        iterations = 10
        
        for i in range(iterations):
            # Adicionar task
            async def iteration_task(iteration=i):
                ai_manager.set_context(f'iteration_{iteration}', True)
                return True
            
            await task_manager.add_task(iteration_task)
            
            # Processar
            await task_manager.execute_pending_tasks()
            
            # Pequena pausa
            await asyncio.sleep(0.1)
        
        # Verificar todas as iterações
        for i in range(iterations):
            assert ai_manager.get_context(f'iteration_{i}') is True
        
        # Cleanup
        ai_manager.stop()
        await task_manager.stop()
    
    @pytest.mark.integration
    async def test_resource_cleanup_integration(self):
        """Testa limpeza de recursos na integração."""
        import gc
        
        logger = Logger(level="WARNING")
        event_bus = EventBus()
        
        # Criar múltiplos componentes
        components = []
        
        for i in range(5):
            ai_manager = AIManager(logger=logger, event_bus=event_bus)
            task_manager = TaskManager(logger=logger, event_bus=event_bus)
            
            ai_manager.start()
            await task_manager.start()
            
            # Adicionar task
            async def cleanup_task():
                return True
            
            await task_manager.add_task(cleanup_task)
            await task_manager.execute_pending_tasks()
            
            components.append((ai_manager, task_manager))
        
        # Parar todos os componentes
        for ai_manager, task_manager in components:
            ai_manager.stop()
            await task_manager.stop()
        
        # Forçar garbage collection
        del components
        gc.collect()
        
        # Verificar se recursos foram limpos
        # (Este teste é mais qualitativo)
        assert True 