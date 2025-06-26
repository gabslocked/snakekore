"""
Base Task
=========

Classe base para todas as tarefas do PythonKore.
"""

import time
import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

from core.logging.logger import Logger


class TaskStatus(Enum):
    """Status de execução de uma tarefa."""
    PENDING = "pending"          # Aguardando execução
    RUNNING = "running"          # Executando
    PAUSED = "paused"           # Pausada
    COMPLETED = "completed"      # Completada com sucesso
    FAILED = "failed"           # Falhou
    CANCELLED = "cancelled"     # Cancelada
    TIMEOUT = "timeout"         # Timeout
    SKIPPED = "skipped"         # Pulada por condição


class TaskPriority(Enum):
    """Prioridades de tarefas."""
    EMERGENCY = 100     # Emergência (fuga, cura crítica)
    CRITICAL = 90       # Crítica (morte iminente)
    HIGH = 80          # Alta (combate, quest principal)
    NORMAL = 50        # Normal (movimento, ações básicas)
    LOW = 20           # Baixa (loot, organização)
    BACKGROUND = 10    # Background (estatísticas)
    IDLE = 1           # Ocioso (espera)


class TaskResult:
    """
    Resultado da execução de uma tarefa.
    """
    
    def __init__(self,
                 status: TaskStatus,
                 message: str = "",
                 data: Dict[str, Any] = None,
                 error: Optional[Exception] = None):
        """
        Inicializa resultado.
        
        Args:
            status: Status final da tarefa
            message: Mensagem descritiva
            data: Dados retornados pela tarefa
            error: Exceção se houve erro
        """
        self.status = status
        self.message = message
        self.data = data or {}
        self.error = error
        self.timestamp = time.time()
    
    def is_success(self) -> bool:
        """Verifica se foi sucesso."""
        return self.status == TaskStatus.COMPLETED
    
    def is_failure(self) -> bool:
        """Verifica se falhou."""
        return self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]
    
    def __str__(self) -> str:
        """Representação string."""
        return f"TaskResult({self.status.value}: {self.message})"


@dataclass
class TaskContext:
    """
    Contexto de execução de uma tarefa.
    
    Contém dados e referências necessárias para execução.
    """
    player: Optional[Any] = None
    target: Optional[Any] = None
    game_state: Dict[str, Any] = field(default_factory=dict)
    ai_config: Dict[str, Any] = field(default_factory=dict)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor do contexto."""
        return self.shared_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Define valor no contexto."""
        self.shared_data[key] = value
    
    def update(self, data: Dict[str, Any]) -> None:
        """Atualiza múltiplos valores."""
        self.shared_data.update(data)


class BaseTask(ABC):
    """
    Classe base para todas as tarefas.
    
    Define interface e comportamento comum para tarefas do sistema.
    Similar ao sistema de comandos do OpenKore mas mais estruturado.
    """
    
    def __init__(self,
                 name: str,
                 priority: TaskPriority = TaskPriority.NORMAL,
                 timeout: float = 30.0,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 auto_retry: bool = True,
                 logger: Optional[Logger] = None):
        """
        Inicializa tarefa base.
        
        Args:
            name: Nome da tarefa
            priority: Prioridade de execução
            timeout: Timeout em segundos (0 = sem timeout)
            max_retries: Máximo de tentativas
            retry_delay: Delay entre tentativas
            auto_retry: Se deve tentar automaticamente
            logger: Logger personalizado
        """
        # Identificação
        self.name = name
        self.task_id = self._generate_id()
        
        # Configuração
        self.priority = priority
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.auto_retry = auto_retry
        
        # Estado
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.error_message = ""
        
        # Tempos
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.last_update = time.time()
        
        # Dados
        self.parameters: Dict[str, Any] = {}
        self.result: Optional[TaskResult] = None
        self.context: Optional[TaskContext] = None
        
        # Callbacks
        self.on_start: Optional[Callable] = None
        self.on_progress: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
        self.on_failure: Optional[Callable] = None
        self.on_retry: Optional[Callable] = None
        
        # Dependências
        self.dependencies: List['BaseTask'] = []
        self.dependents: List['BaseTask'] = []
        
        # Sistema
        self.logger = logger or Logger(level="INFO")
        self._cancelled = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Não pausado por padrão
    
    def _generate_id(self) -> str:
        """Gera ID único para a tarefa."""
        import uuid
        return f"{self.name}_{uuid.uuid4().hex[:8]}"
    
    # Métodos abstratos que devem ser implementados
    @abstractmethod
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        Executa a tarefa.
        
        Args:
            context: Contexto de execução
            
        Returns:
            Resultado da execução
        """
        pass
    
    def can_execute(self, context: TaskContext) -> bool:
        """
        Verifica se a tarefa pode ser executada.
        
        Args:
            context: Contexto atual
            
        Returns:
            True se pode executar
        """
        return True
    
    def get_estimated_duration(self) -> float:
        """
        Estima duração da tarefa em segundos.
        
        Returns:
            Duração estimada
        """
        return 5.0  # Padrão de 5 segundos
    
    def get_description(self) -> str:
        """
        Obtém descrição da tarefa.
        
        Returns:
            Descrição da tarefa
        """
        return f"Tarefa: {self.name}"
    
    # Controle de execução
    async def run(self, context: TaskContext) -> TaskResult:
        """
        Executa a tarefa com controle completo.
        
        Args:
            context: Contexto de execução
            
        Returns:
            Resultado da execução
        """
        try:
            # Verifica se pode executar
            if not self.can_execute(context):
                self.result = TaskResult(
                    TaskStatus.SKIPPED,
                    "Condições não atendidas"
                )
                return self.result
            
            # Inicia execução
            self._start_execution(context)
            
            # Executa com timeout
            if self.timeout > 0:
                try:
                    self.result = await asyncio.wait_for(
                        self._execute_with_pause_check(context),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    self.result = TaskResult(
                        TaskStatus.TIMEOUT,
                        f"Timeout de {self.timeout}s atingido"
                    )
            else:
                self.result = await self._execute_with_pause_check(context)
            
            # Finaliza execução
            self._finish_execution()
            
            return self.result
            
        except asyncio.CancelledError:
            self.result = TaskResult(
                TaskStatus.CANCELLED,
                "Tarefa cancelada"
            )
            self._finish_execution()
            return self.result
            
        except Exception as e:
            self.result = TaskResult(
                TaskStatus.FAILED,
                f"Erro na execução: {e}",
                error=e
            )
            self._finish_execution()
            return self.result
    
    async def _execute_with_pause_check(self, context: TaskContext) -> TaskResult:
        """Executa com verificação de pausa."""
        while True:
            # Verifica se está pausado
            await self._pause_event.wait()
            
            # Verifica se foi cancelado
            if self._cancelled:
                return TaskResult(TaskStatus.CANCELLED, "Cancelado")
            
            # Executa a tarefa
            return await self.execute(context)
    
    def _start_execution(self, context: TaskContext) -> None:
        """Inicia execução."""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        self.context = context
        self.last_update = time.time()
        
        self.logger.debug(f"Iniciando tarefa: {self.name}")
        
        if self.on_start:
            try:
                self.on_start(self)
            except Exception:
                pass
    
    def _finish_execution(self) -> None:
        """Finaliza execução."""
        self.completed_at = time.time()
        self.status = self.result.status if self.result else TaskStatus.FAILED
        
        self.logger.debug(f"Tarefa finalizada: {self.name} - {self.status.value}")
        
        # Chama callback apropriado
        if self.result and self.result.is_success() and self.on_complete:
            try:
                self.on_complete(self, self.result)
            except Exception:
                pass
        elif self.result and self.result.is_failure() and self.on_failure:
            try:
                self.on_failure(self, self.result)
            except Exception:
                pass
    
    # Controle de estado
    def pause(self) -> None:
        """Pausa a tarefa."""
        if self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.PAUSED
            self._pause_event.clear()
            self.logger.debug(f"Tarefa pausada: {self.name}")
    
    def resume(self) -> None:
        """Resume a tarefa."""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            self._pause_event.set()
            self.logger.debug(f"Tarefa resumida: {self.name}")
    
    def cancel(self) -> None:
        """Cancela a tarefa."""
        self._cancelled = True
        self.status = TaskStatus.CANCELLED
        self._pause_event.set()  # Desbloqueia se estiver pausado
        self.logger.debug(f"Tarefa cancelada: {self.name}")
    
    def reset(self) -> None:
        """Reseta a tarefa para estado inicial."""
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.error_message = ""
        self.started_at = None
        self.completed_at = None
        self.result = None
        self._cancelled = False
        self._pause_event.set()
        
        self.logger.debug(f"Tarefa resetada: {self.name}")
    
    # Parâmetros e configuração
    def set_parameter(self, key: str, value: Any) -> None:
        """Define parâmetro da tarefa."""
        self.parameters[key] = value
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Obtém parâmetro da tarefa."""
        return self.parameters.get(key, default)
    
    def update_parameters(self, params: Dict[str, Any]) -> None:
        """Atualiza múltiplos parâmetros."""
        self.parameters.update(params)
    
    def set_timeout(self, timeout: float) -> None:
        """Define timeout da tarefa."""
        self.timeout = timeout
    
    def set_priority(self, priority: TaskPriority) -> None:
        """Define prioridade da tarefa."""
        self.priority = priority
    
    # Dependências
    def add_dependency(self, task: 'BaseTask') -> None:
        """Adiciona dependência."""
        if task not in self.dependencies:
            self.dependencies.append(task)
            task.dependents.append(self)
    
    def remove_dependency(self, task: 'BaseTask') -> None:
        """Remove dependência."""
        if task in self.dependencies:
            self.dependencies.remove(task)
            task.dependents.remove(self)
    
    def has_dependencies_completed(self) -> bool:
        """Verifica se dependências foram completadas."""
        return all(dep.status == TaskStatus.COMPLETED for dep in self.dependencies)
    
    # Status e informações
    def get_elapsed_time(self) -> float:
        """Obtém tempo decorrido."""
        if self.started_at is None:
            return 0.0
        end_time = self.completed_at or time.time()
        return end_time - self.started_at
    
    def get_progress(self) -> float:
        """
        Obtém progresso da tarefa (0.0 a 1.0).
        
        Returns:
            Progresso da tarefa
        """
        if self.status == TaskStatus.COMPLETED:
            return 1.0
        elif self.status == TaskStatus.PENDING:
            return 0.0
        else:
            # Estima baseado no tempo decorrido vs estimado
            elapsed = self.get_elapsed_time()
            estimated = self.get_estimated_duration()
            return min(elapsed / estimated, 0.99) if estimated > 0 else 0.5
    
    def is_finished(self) -> bool:
        """Verifica se a tarefa terminou."""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
            TaskStatus.SKIPPED
        ]
    
    def is_active(self) -> bool:
        """Verifica se a tarefa está ativa."""
        return self.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]
    
    def can_retry(self) -> bool:
        """Verifica se pode tentar novamente."""
        return (self.auto_retry and
                self.retry_count < self.max_retries and
                self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT])
    
    # Informações para debug/monitoramento
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte tarefa para dicionário.
        
        Returns:
            Dicionário com dados da tarefa
        """
        return {
            'task_id': self.task_id,
            'name': self.name,
            'status': self.status.value,
            'priority': self.priority.value,
            'progress': self.get_progress(),
            'elapsed_time': self.get_elapsed_time(),
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'parameters': self.parameters.copy(),
            'dependencies_count': len(self.dependencies),
            'dependents_count': len(self.dependents),
            'description': self.get_description(),
            'estimated_duration': self.get_estimated_duration()
        }
    
    def get_summary(self) -> str:
        """Obtém resumo da tarefa."""
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "🏃",
            TaskStatus.PAUSED: "⏸️",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "🚫",
            TaskStatus.TIMEOUT: "⏰",
            TaskStatus.SKIPPED: "⏭️"
        }.get(self.status, "❓")
        
        elapsed = self.get_elapsed_time()
        progress = self.get_progress() * 100
        
        return f"{status_icon} {self.name} ({progress:.1f}% - {elapsed:.1f}s)"
    
    def __str__(self) -> str:
        """Representação string."""
        return f"Task({self.name}, {self.status.value}, {self.priority.value})"
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return (f"BaseTask(name='{self.name}', "
                f"status={self.status.value}, "
                f"priority={self.priority.value})")
    
    def __lt__(self, other) -> bool:
        """Comparação para ordenação por prioridade."""
        if not isinstance(other, BaseTask):
            return NotImplemented
        return self.priority.value > other.priority.value  # Maior prioridade primeiro
    
    def __eq__(self, other) -> bool:
        """Igualdade baseada no ID."""
        if not isinstance(other, BaseTask):
            return NotImplemented
        return self.task_id == other.task_id 