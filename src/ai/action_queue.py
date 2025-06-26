"""
Action Queue
============

Sistema de fila de ações para a AI do PythonKore.
"""

import time
import asyncio
from enum import Enum
from typing import List, Optional, Dict, Any, Callable, Union
from dataclasses import dataclass, field

from states import AIPriority
from core.logging.logger import Logger
from core.events.event_bus import EventBus


class ActionStatus(Enum):
    """Status de execução de uma ação."""
    PENDING = "pending"      # Aguardando execução
    RUNNING = "running"      # Executando
    COMPLETED = "completed"  # Completada com sucesso
    FAILED = "failed"        # Falhou
    CANCELLED = "cancelled"  # Cancelada
    TIMEOUT = "timeout"      # Timeout


class ActionType(Enum):
    """Tipos de ações disponíveis."""
    # Movimento
    MOVE_TO = "move_to"
    WALK = "walk"
    TELEPORT = "teleport"
    
    # Combate
    ATTACK = "attack"
    USE_SKILL = "use_skill"
    CAST_SPELL = "cast_spell"
    
    # Interação
    TALK_NPC = "talk_npc"
    PICK_ITEM = "pick_item"
    USE_ITEM = "use_item"
    
    # Social
    SEND_CHAT = "send_chat"
    PARTY_ACTION = "party_action"
    GUILD_ACTION = "guild_action"
    
    # Economia
    BUY_ITEM = "buy_item"
    SELL_ITEM = "sell_item"
    STORE_ITEM = "store_item"
    
    # Sistema
    WAIT = "wait"
    PAUSE = "pause"
    CUSTOM = "custom"


@dataclass
class Action:
    """
    Ação da AI.
    
    Representa uma ação específica que a AI deve executar.
    """
    
    action_type: ActionType
    name: str
    executor: Callable[[], bool]
    priority: AIPriority = AIPriority.NORMAL
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Status da ação
    status: ActionStatus = ActionStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: str = ""
    retry_count: int = 0
    
    # Callbacks
    on_success: Optional[Callable[[], None]] = None
    on_failure: Optional[Callable[[str], None]] = None
    on_retry: Optional[Callable[[int], None]] = None
    
    def get_elapsed_time(self) -> float:
        """
        Obtém tempo decorrido desde o início.
        
        Returns:
            Tempo em segundos
        """
        if self.started_at is None:
            return 0.0
        return time.time() - self.started_at
    
    def is_timed_out(self) -> bool:
        """
        Verifica se a ação expirou.
        
        Returns:
            True se expirou
        """
        if self.timeout <= 0:
            return False
        return self.get_elapsed_time() > self.timeout
    
    def can_retry(self) -> bool:
        """
        Verifica se pode tentar novamente.
        
        Returns:
            True se pode retentar
        """
        return (self.status == ActionStatus.FAILED and 
                self.retry_count < self.max_retries)
    
    def mark_started(self) -> None:
        """Marca ação como iniciada."""
        self.status = ActionStatus.RUNNING
        self.started_at = time.time()
    
    def mark_completed(self) -> None:
        """Marca ação como completada."""
        self.status = ActionStatus.COMPLETED
        self.completed_at = time.time()
        
        if self.on_success:
            try:
                self.on_success()
            except Exception:
                pass  # Não falhar por erro em callback
    
    def mark_failed(self, error: str = "") -> None:
        """
        Marca ação como falhada.
        
        Args:
            error: Mensagem de erro
        """
        self.status = ActionStatus.FAILED
        self.error_message = error
        self.completed_at = time.time()
        
        if self.on_failure:
            try:
                self.on_failure(error)
            except Exception:
                pass
    
    def mark_cancelled(self) -> None:
        """Marca ação como cancelada."""
        self.status = ActionStatus.CANCELLED
        self.completed_at = time.time()
    
    def mark_timeout(self) -> None:
        """Marca ação como timeout."""
        self.status = ActionStatus.TIMEOUT
        self.completed_at = time.time()
        self.error_message = "Timeout"
    
    def prepare_retry(self) -> None:
        """Prepara ação para retry."""
        self.retry_count += 1
        self.status = ActionStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.error_message = ""
        
        if self.on_retry:
            try:
                self.on_retry(self.retry_count)
            except Exception:
                pass
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Obtém parâmetro da ação.
        
        Args:
            key: Chave do parâmetro
            default: Valor padrão
            
        Returns:
            Valor do parâmetro
        """
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """
        Define parâmetro da ação.
        
        Args:
            key: Chave do parâmetro
            value: Valor do parâmetro
        """
        self.parameters[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte ação para dicionário.
        
        Returns:
            Dicionário com dados da ação
        """
        return {
            'action_type': self.action_type.value,
            'name': self.name,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'elapsed_time': self.get_elapsed_time(),
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'error_message': self.error_message,
            'parameters': self.parameters.copy()
        }
    
    def __str__(self) -> str:
        """Representação string."""
        return f"Action({self.name}, {self.status.value}, {self.priority.value})"


class ActionQueue:
    """
    Fila de ações da AI.
    
    Gerencia execução sequencial e prioritária de ações.
    Similar ao sistema de comandos do OpenKore.
    """
    
    def __init__(self, 
                 logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None,
                 max_queue_size: int = 100):
        """
        Inicializa fila de ações.
        
        Args:
            logger: Logger para debug
            event_bus: Bus de eventos
            max_queue_size: Tamanho máximo da fila
        """
        self.logger = logger or Logger("ActionQueue")
        self.event_bus = event_bus
        self.max_queue_size = max_queue_size
        
        # Filas
        self.queue: List[Action] = []
        self.executing: Optional[Action] = None
        self.completed: List[Action] = []
        self.failed: List[Action] = []
        
        # Estado
        self.is_paused = False
        self.auto_retry = True
        self.max_history = 50
        
        # Estatísticas
        self.total_executed = 0
        self.total_failed = 0
        self.total_cancelled = 0
        
        self.logger.info("ActionQueue inicializada")
    
    def add_action(self, action: Action) -> bool:
        """
        Adiciona ação à fila.
        
        Args:
            action: Ação a adicionar
            
        Returns:
            True se adicionada com sucesso
        """
        if len(self.queue) >= self.max_queue_size:
            self.logger.warning(f"Fila cheia, descartando ação: {action.name}")
            return False
        
        # Insere mantendo prioridade
        inserted = False
        for i, existing in enumerate(self.queue):
            if action.priority.value > existing.priority.value:
                self.queue.insert(i, action)
                inserted = True
                break
        
        if not inserted:
            self.queue.append(action)
        
        self.logger.debug(f"Ação adicionada: {action.name} (prioridade: {action.priority.value})")
        
        # Emite evento
        if self.event_bus:
            self.event_bus.emit('action_queued', action=action)
        
        return True
    
    def add_actions(self, actions: List[Action]) -> int:
        """
        Adiciona múltiplas ações.
        
        Args:
            actions: Lista de ações
            
        Returns:
            Número de ações adicionadas
        """
        added = 0
        for action in actions:
            if self.add_action(action):
                added += 1
        return added
    
    def get_next_action(self) -> Optional[Action]:
        """
        Obtém próxima ação a executar.
        
        Returns:
            Próxima ação ou None se fila vazia
        """
        if not self.queue or self.is_paused:
            return None
        
        return self.queue[0]
    
    def start_execution(self) -> Optional[Action]:
        """
        Inicia execução da próxima ação.
        
        Returns:
            Ação iniciada ou None
        """
        if self.executing or not self.queue or self.is_paused:
            return None
        
        action = self.queue.pop(0)
        action.mark_started()
        self.executing = action
        
        self.logger.info(f"Executando ação: {action.name}")
        
        # Emite evento
        if self.event_bus:
            self.event_bus.emit('action_started', action=action)
        
        return action
    
    async def execute_current(self) -> bool:
        """
        Executa ação atual.
        
        Returns:
            True se executada com sucesso
        """
        if not self.executing:
            return False
        
        action = self.executing
        
        try:
            # Verifica timeout
            if action.is_timed_out():
                action.mark_timeout()
                self._finish_action(action)
                return False
            
            # Executa ação
            result = action.executor()
            
            if result:
                action.mark_completed()
                self._finish_action(action)
                return True
            else:
                # Ação ainda executando
                return False
                
        except Exception as e:
            error_msg = f"Erro na execução: {e}"
            self.logger.error(f"Erro ao executar {action.name}: {e}")
            action.mark_failed(error_msg)
            self._finish_action(action)
            return False
    
    def _finish_action(self, action: Action) -> None:
        """
        Finaliza execução de uma ação.
        
        Args:
            action: Ação finalizada
        """
        self.executing = None
        
        if action.status == ActionStatus.COMPLETED:
            self.completed.append(action)
            self.total_executed += 1
            self.logger.debug(f"Ação completada: {action.name}")
            
            if self.event_bus:
                self.event_bus.emit('action_completed', action=action)
                
        elif action.status in [ActionStatus.FAILED, ActionStatus.TIMEOUT]:
            # Tenta retry se configurado
            if self.auto_retry and action.can_retry():
                action.prepare_retry()
                
                # Aguarda delay antes de recolocar na fila
                asyncio.create_task(self._retry_action_delayed(action))
                
                self.logger.info(f"Reagendando ação: {action.name} (tentativa {action.retry_count})")
            else:
                self.failed.append(action)
                self.total_failed += 1
                self.logger.warning(f"Ação falhou: {action.name} - {action.error_message}")
                
                if self.event_bus:
                    self.event_bus.emit('action_failed', action=action)
        
        elif action.status == ActionStatus.CANCELLED:
            self.total_cancelled += 1
            
            if self.event_bus:
                self.event_bus.emit('action_cancelled', action=action)
        
        # Limita histórico
        if len(self.completed) > self.max_history:
            self.completed.pop(0)
        
        if len(self.failed) > self.max_history:
            self.failed.pop(0)
    
    async def _retry_action_delayed(self, action: Action) -> None:
        """
        Reagenda ação após delay.
        
        Args:
            action: Ação a reagendar
        """
        await asyncio.sleep(action.retry_delay)
        self.add_action(action)
    
    def cancel_current(self) -> bool:
        """
        Cancela ação atual.
        
        Returns:
            True se cancelada
        """
        if not self.executing:
            return False
        
        action = self.executing
        action.mark_cancelled()
        self._finish_action(action)
        
        self.logger.info(f"Ação cancelada: {action.name}")
        return True
    
    def cancel_all(self) -> int:
        """
        Cancela todas as ações na fila.
        
        Returns:
            Número de ações canceladas
        """
        cancelled = len(self.queue)
        
        for action in self.queue:
            action.mark_cancelled()
        
        self.queue.clear()
        self.total_cancelled += cancelled
        
        # Cancela ação atual também
        if self.executing:
            self.cancel_current()
            cancelled += 1
        
        self.logger.info(f"Canceladas {cancelled} ações")
        return cancelled
    
    def pause(self) -> None:
        """Pausa execução da fila."""
        self.is_paused = True
        self.logger.info("Fila pausada")
    
    def resume(self) -> None:
        """Resume execução da fila."""
        self.is_paused = False
        self.logger.info("Fila resumida")
    
    def clear(self) -> None:
        """Limpa toda a fila e histórico."""
        self.cancel_all()
        self.completed.clear()
        self.failed.clear()
        self.total_executed = 0
        self.total_failed = 0
        self.total_cancelled = 0
        
        self.logger.info("Fila limpa")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Obtém status da fila.
        
        Returns:
            Dicionário com status
        """
        return {
            'queue_size': len(self.queue),
            'executing': self.executing.name if self.executing else None,
            'is_paused': self.is_paused,
            'total_executed': self.total_executed,
            'total_failed': self.total_failed,
            'total_cancelled': self.total_cancelled,
            'completed_count': len(self.completed),
            'failed_count': len(self.failed)
        }
    
    def get_queue_summary(self) -> List[Dict[str, Any]]:
        """
        Obtém resumo das ações na fila.
        
        Returns:
            Lista com resumo das ações
        """
        summary = []
        
        # Ação executando
        if self.executing:
            summary.append({
                'position': 'executing',
                'action': self.executing.to_dict()
            })
        
        # Ações na fila
        for i, action in enumerate(self.queue):
            summary.append({
                'position': i + 1,
                'action': action.to_dict()
            })
        
        return summary
    
    def __len__(self) -> int:
        """Tamanho da fila."""
        return len(self.queue)
    
    def __bool__(self) -> bool:
        """Se tem ações."""
        return len(self.queue) > 0 or self.executing is not None 