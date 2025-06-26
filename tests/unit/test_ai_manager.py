"""
Testes para AI Manager
======================

Testes unitários para ai_manager.py
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ai.ai_manager import AIManager
from ai.states import AIState
from core.logging.logger import Logger
from core.events.event_bus import EventBus


class TestAIManager:
    """Testes para classe AIManager."""
    
    @pytest.fixture
    def logger(self):
        """Logger mock para testes."""
        return Mock(spec=Logger)
    
    @pytest.fixture  
    def event_bus(self):
        """Event bus mock para testes."""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def ai_manager(self, logger, event_bus):
        """AIManager para testes."""
        return AIManager(logger=logger, event_bus=event_bus)
    
    def test_initialization(self, ai_manager, logger, event_bus):
        """Testa inicialização do AIManager."""
        assert ai_manager.logger == logger
        assert ai_manager.event_bus == event_bus
        assert ai_manager.current_state == AIState.OFF
        assert ai_manager.state_machine is not None
        assert ai_manager.action_queue is not None
        assert ai_manager.context == {}
        assert not ai_manager.running
    
    def test_start_stop(self, ai_manager):
        """Testa start/stop do AIManager."""
        # Inicialmente parado
        assert not ai_manager.running
        
        # Start
        ai_manager.start()
        assert ai_manager.running
        assert ai_manager.current_state == AIState.AUTO
        
        # Stop
        ai_manager.stop()
        assert not ai_manager.running
        assert ai_manager.current_state == AIState.OFF
    
    def test_pause_resume(self, ai_manager):
        """Testa pause/resume do AIManager."""
        ai_manager.start()
        assert ai_manager.current_state == AIState.AUTO
        
        # Pause
        ai_manager.pause()
        assert ai_manager.current_state == AIState.MANUAL
        
        # Resume
        ai_manager.resume()
        assert ai_manager.current_state == AIState.AUTO
    
    def test_set_state(self, ai_manager):
        """Testa mudança manual de estado."""
        # Estado inicial
        assert ai_manager.current_state == AIState.OFF
        
        # Mudança válida
        ai_manager.set_state(AIState.AUTO)
        assert ai_manager.current_state == AIState.AUTO
        
        # Mudança para estado de emergência
        ai_manager.set_state(AIState.EMERGENCY)
        assert ai_manager.current_state == AIState.EMERGENCY
    
    def test_context_management(self, ai_manager):
        """Testa gerenciamento de contexto."""
        # Contexto inicial vazio
        assert ai_manager.context == {}
        
        # Definir contexto
        ai_manager.set_context('test_key', 'test_value')
        assert ai_manager.get_context('test_key') == 'test_value'
        
        # Obter contexto inexistente
        assert ai_manager.get_context('nonexistent', 'default') == 'default'
        
        # Remover contexto
        ai_manager.remove_context('test_key')
        assert ai_manager.get_context('test_key') is None
        
        # Limpar contexto
        ai_manager.set_context('key1', 'value1')
        ai_manager.set_context('key2', 'value2')
        ai_manager.clear_context()
        assert ai_manager.context == {}
    
    @pytest.mark.asyncio
    async def test_add_action(self, ai_manager):
        """Testa adição de ações."""
        action_func = Mock()
        
        # Adicionar ação
        action_id = await ai_manager.add_action(
            action_func, 
            priority=5, 
            context={'test': True}
        )
        
        assert action_id is not None
        assert len(ai_manager.action_queue.actions) == 1
    
    @pytest.mark.asyncio
    async def test_process_actions(self, ai_manager):
        """Testa processamento de ações."""
        # Mock para função de ação
        action_func = Mock()
        action_func.return_value = True
        
        # Adicionar ação
        await ai_manager.add_action(action_func)
        
        # Processar ações
        processed = await ai_manager.process_actions()
        
        assert processed > 0
        action_func.assert_called_once()
    
    def test_emergency_mode(self, ai_manager):
        """Testa modo de emergência."""
        ai_manager.start()
        assert ai_manager.current_state == AIState.AUTO
        
        # Ativar emergência
        ai_manager.emergency()
        assert ai_manager.current_state == AIState.EMERGENCY
        
        # Sair da emergência
        ai_manager.resume()
        assert ai_manager.current_state == AIState.AUTO
    
    def test_statistics(self, ai_manager):
        """Testa obtenção de estatísticas."""
        stats = ai_manager.get_statistics()
        
        # Verifica estrutura das estatísticas
        assert 'current_state' in stats
        assert 'uptime' in stats
        assert 'state_machine' in stats
        assert 'action_queue' in stats
        
        assert stats['current_state'] == AIState.OFF.name
        assert isinstance(stats['uptime'], float)
    
    def test_status(self, ai_manager):
        """Testa obtenção de status."""
        status = ai_manager.get_status()
        
        # Verifica estrutura do status
        assert 'running' in status
        assert 'current_state' in status
        assert 'queue_size' in status
        assert 'context_size' in status
        
        assert status['running'] is False
        assert status['current_state'] == AIState.OFF.name
        assert status['queue_size'] == 0
        assert status['context_size'] == 0
    
    def test_event_emission(self, ai_manager, event_bus):
        """Testa emissão de eventos."""
        # Start emite evento
        ai_manager.start()
        event_bus.emit.assert_called()
        
        # Verifica se evento foi emitido
        calls = event_bus.emit.call_args_list
        assert any('ai_state_changed' in str(call) for call in calls)
    
    def test_logging(self, ai_manager, logger):
        """Testa logging de operações."""
        # Start faz log
        ai_manager.start()
        logger.info.assert_called()
        
        # Stop faz log
        ai_manager.stop()
        logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_state_transitions(self, ai_manager):
        """Testa transições de estado."""
        # OFF -> AUTO
        ai_manager.start()
        assert ai_manager.current_state == AIState.AUTO
        
        # AUTO -> MANUAL
        ai_manager.pause()
        assert ai_manager.current_state == AIState.MANUAL
        
        # MANUAL -> AUTO
        ai_manager.resume()
        assert ai_manager.current_state == AIState.AUTO
        
        # AUTO -> EMERGENCY
        ai_manager.emergency()
        assert ai_manager.current_state == AIState.EMERGENCY
        
        # EMERGENCY -> AUTO
        ai_manager.resume()
        assert ai_manager.current_state == AIState.AUTO
        
        # AUTO -> OFF
        ai_manager.stop()
        assert ai_manager.current_state == AIState.OFF
    
    def test_invalid_operations_when_stopped(self, ai_manager):
        """Testa operações inválidas quando parado."""
        # AI está parada
        assert not ai_manager.running
        
        # Pause não deve funcionar
        ai_manager.pause()
        assert ai_manager.current_state == AIState.OFF
        
        # Resume não deve funcionar
        ai_manager.resume()
        assert ai_manager.current_state == AIState.OFF
        
        # Emergency não deve funcionar
        ai_manager.emergency()
        assert ai_manager.current_state == AIState.OFF
    
    @pytest.mark.asyncio
    async def test_action_execution_order(self, ai_manager):
        """Testa ordem de execução das ações."""
        execution_order = []
        
        def make_action(name):
            def action():
                execution_order.append(name)
                return True
            return action
        
        # Adicionar ações com diferentes prioridades
        await ai_manager.add_action(make_action('low'), priority=1)
        await ai_manager.add_action(make_action('high'), priority=10)
        await ai_manager.add_action(make_action('medium'), priority=5)
        
        # Processar ações
        await ai_manager.process_actions()
        
        # Verificar ordem (maior prioridade primeiro)
        assert execution_order == ['high', 'medium', 'low']
    
    @pytest.mark.asyncio
    async def test_action_failure_handling(self, ai_manager):
        """Testa tratamento de falhas em ações."""
        # Ação que falha
        def failing_action():
            raise Exception("Test error")
        
        # Adicionar ação que falha
        await ai_manager.add_action(failing_action)
        
        # Processar ações (não deve parar o sistema)
        processed = await ai_manager.process_actions()
        
        # Deve processar a ação mesmo que falhe
        assert processed >= 0
    
    def test_context_persistence(self, ai_manager):
        """Testa persistência do contexto."""
        # Definir contexto
        ai_manager.set_context('persistent_data', {'key': 'value'})
        
        # Parar e iniciar AI
        ai_manager.start()
        ai_manager.stop()
        ai_manager.start()
        
        # Contexto deve persistir
        assert ai_manager.get_context('persistent_data') == {'key': 'value'}
    
    def test_cleanup_on_stop(self, ai_manager):
        """Testa limpeza ao parar."""
        ai_manager.start()
        
        # Adicionar alguns dados
        ai_manager.set_context('temp_data', 'temp_value')
        
        # Parar AI
        ai_manager.stop()
        
        # Verificar limpeza
        assert not ai_manager.running
        assert ai_manager.current_state == AIState.OFF
        # Contexto deve ser mantido para próxima sessão
        assert 'temp_data' in ai_manager.context 