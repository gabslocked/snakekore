"""
Task Manager
============

Gerenciador de tarefas do PythonKore.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

from base_task import BaseTask, TaskStatus, TaskPriority, TaskResult, TaskContext
from core.logging.logger import Logger
from core.events.event_bus import EventBus


class TaskManager:
    """
    Gerenciador de tarefas.
    
    Responsável por:
    - Agendar e executar tarefas
    - Gerenciar dependências
    - Controlar prioridades
    - Monitorar execução
    """
    
    def __init__(self,
                 logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None,
                 max_concurrent_tasks: int = 5,
                 max_queue_size: int = 100):
        """
        Inicializa gerenciador.
        
        Args:
            logger: Logger para debug
            event_bus: Bus de eventos
            max_concurrent_tasks: Máximo de tarefas simultâneas
            max_queue_size: Tamanho máximo da fila
        """
        self.logger = logger or Logger(level="INFO")
        self.event_bus = event_bus
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_queue_size = max_queue_size
        
        # Filas de tarefas
        self.pending_tasks: List[BaseTask] = []
        self.running_tasks: Dict[str, BaseTask] = {}
        self.completed_tasks: List[BaseTask] = []
        self.failed_tasks: List[BaseTask] = []
        
        # Controle de execução
        self.is_running = False
        self.manager_task: Optional[asyncio.Task] = None
        self.task_futures: Dict[str, asyncio.Task] = {}
        
        # Contexto global
        self.global_context = TaskContext()
        
        # Estatísticas
        self.stats = {
            'total_scheduled': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_cancelled': 0,
            'total_timeout': 0,
            'average_execution_time': 0.0,
            'tasks_by_priority': defaultdict(int)
        }
        
        # Configurações
        self.cleanup_interval = 60.0  # Limpeza a cada minuto
        self.max_history = 100  # Máximo de tarefas no histórico
        
        self.logger.info("TaskManager inicializado")
    
    def start(self) -> None:
        """Inicia o gerenciador de tarefas."""
        if self.is_running:
            self.logger.warning("TaskManager já está rodando")
            return
        
        self.is_running = True
        self.manager_task = asyncio.create_task(self._manager_loop())
        
        self.logger.info("TaskManager iniciado")
        
        if self.event_bus:
            self.event_bus.emit('task_manager_started')
    
    def stop(self) -> None:
        """Para o gerenciador de tarefas."""
        self.is_running = False
        
        # Cancela task principal
        if self.manager_task and not self.manager_task.done():
            self.manager_task.cancel()
        
        # Cancela todas as tarefas em execução
        self.cancel_all_tasks()
        
        self.logger.info("TaskManager parado")
        
        if self.event_bus:
            self.event_bus.emit('task_manager_stopped')
    
    def schedule_task(self, task: BaseTask) -> bool:
        """
        Agenda uma tarefa para execução.
        
        Args:
            task: Tarefa a ser agendada
            
        Returns:
            True se agendada com sucesso
        """
        if len(self.pending_tasks) >= self.max_queue_size:
            self.logger.warning(f"Fila cheia, descartando tarefa: {task.name}")
            return False
        
        # Adiciona à fila mantendo ordem de prioridade
        self._insert_by_priority(task)
        
        self.stats['total_scheduled'] += 1
        self.stats['tasks_by_priority'][task.priority.value] += 1
        
        self.logger.debug(f"Tarefa agendada: {task.name} (prioridade: {task.priority.value})")
        
        if self.event_bus:
            self.event_bus.emit('task_scheduled', task=task)
        
        return True
    
    def schedule_tasks(self, tasks: List[BaseTask]) -> int:
        """
        Agenda múltiplas tarefas.
        
        Args:
            tasks: Lista de tarefas
            
        Returns:
            Número de tarefas agendadas
        """
        scheduled = 0
        for task in tasks:
            if self.schedule_task(task):
                scheduled += 1
        return scheduled
    
    def _insert_by_priority(self, task: BaseTask) -> None:
        """Insere tarefa mantendo ordem de prioridade."""
        inserted = False
        for i, existing in enumerate(self.pending_tasks):
            if task.priority.value > existing.priority.value:
                self.pending_tasks.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.pending_tasks.append(task)
    
    async def _manager_loop(self) -> None:
        """Loop principal do gerenciador."""
        try:
            while self.is_running:
                # Executa próximas tarefas
                await self._execute_next_tasks()
                
                # Remove tarefas finalizadas
                await self._cleanup_finished_tasks()
                
                # Limpeza periódica
                await self._periodic_cleanup()
                
                # Aguarda próximo ciclo
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            self.logger.info("Task manager loop cancelado")
        except Exception as e:
            self.logger.error(f"Erro no task manager loop: {e}")
            self.is_running = False
    
    async def _execute_next_tasks(self) -> None:
        """Executa próximas tarefas disponíveis."""
        # Verifica quantas tarefas podemos iniciar
        available_slots = self.max_concurrent_tasks - len(self.running_tasks)
        
        if available_slots <= 0 or not self.pending_tasks:
            return
        
        # Procura tarefas prontas para execução
        tasks_to_start = []
        
        for task in self.pending_tasks[:]:
            if len(tasks_to_start) >= available_slots:
                break
            
            # Verifica se dependências foram atendidas
            if task.has_dependencies_completed():
                tasks_to_start.append(task)
                self.pending_tasks.remove(task)
        
        # Inicia execução das tarefas
        for task in tasks_to_start:
            await self._start_task_execution(task)
    
    async def _start_task_execution(self, task: BaseTask) -> None:
        """Inicia execução de uma tarefa."""
        self.running_tasks[task.task_id] = task
        
        # Cria future para a tarefa
        future = asyncio.create_task(task.run(self.global_context))
        self.task_futures[task.task_id] = future
        
        self.logger.info(f"Iniciando execução: {task.name}")
        
        if self.event_bus:
            self.event_bus.emit('task_started', task=task)
    
    async def _cleanup_finished_tasks(self) -> None:
        """Remove tarefas que finalizaram."""
        finished_tasks = []
        
        for task_id, task in self.running_tasks.items():
            if task.is_finished():
                finished_tasks.append(task_id)
        
        for task_id in finished_tasks:
            task = self.running_tasks.pop(task_id)
            future = self.task_futures.pop(task_id, None)
            
            if future and not future.done():
                future.cancel()
            
            # Move para lista apropriada
            if task.status == TaskStatus.COMPLETED:
                self.completed_tasks.append(task)
                self.stats['total_completed'] += 1
            elif task.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
                self.failed_tasks.append(task)
                if task.status == TaskStatus.FAILED:
                    self.stats['total_failed'] += 1
                else:
                    self.stats['total_timeout'] += 1
            elif task.status == TaskStatus.CANCELLED:
                self.stats['total_cancelled'] += 1
            
            # Atualiza estatísticas
            self._update_execution_stats(task)
            
            self.logger.debug(f"Tarefa finalizada: {task.name} - {task.status.value}")
            
            if self.event_bus:
                self.event_bus.emit('task_finished', task=task)
            
            # Verifica se precisa reagendar (retry)
            if task.can_retry():
                task.retry_count += 1
                task.reset()
                
                # Reagenda após delay
                if task.retry_delay > 0:
                    asyncio.create_task(self._schedule_retry(task))
                else:
                    self.schedule_task(task)
    
    async def _schedule_retry(self, task: BaseTask) -> None:
        """Reagenda tarefa após delay."""
        await asyncio.sleep(task.retry_delay)
        self.schedule_task(task)
        
        if task.on_retry:
            try:
                task.on_retry(task)
            except Exception:
                pass
    
    def _update_execution_stats(self, task: BaseTask) -> None:
        """Atualiza estatísticas de execução."""
        if task.started_at and task.completed_at:
            execution_time = task.completed_at - task.started_at
            
            # Atualiza média de tempo de execução
            total_completed = self.stats['total_completed']
            current_avg = self.stats['average_execution_time']
            
            if total_completed > 0:
                self.stats['average_execution_time'] = (
                    (current_avg * (total_completed - 1) + execution_time) / total_completed
                )
            else:
                self.stats['average_execution_time'] = execution_time
    
    async def _periodic_cleanup(self) -> None:
        """Limpeza periódica de histórico."""
        # Limita tamanho do histórico
        if len(self.completed_tasks) > self.max_history:
            self.completed_tasks = self.completed_tasks[-self.max_history:]
        
        if len(self.failed_tasks) > self.max_history:
            self.failed_tasks = self.failed_tasks[-self.max_history:]
    
    # Controle de tarefas
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancela uma tarefa específica.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se cancelada
        """
        # Procura na fila pendente
        for task in self.pending_tasks[:]:
            if task.task_id == task_id:
                task.cancel()
                self.pending_tasks.remove(task)
                self.stats['total_cancelled'] += 1
                return True
        
        # Procura nas tarefas em execução
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            
            # Cancela future
            future = self.task_futures.get(task_id)
            if future and not future.done():
                future.cancel()
            
            return True
        
        return False
    
    def cancel_all_tasks(self) -> int:
        """
        Cancela todas as tarefas.
        
        Returns:
            Número de tarefas canceladas
        """        
        cancelled = 0
        
        # Cancela tarefas pendentes
        for task in self.pending_tasks[:]:
            task.cancel()
            cancelled += 1
        self.pending_tasks.clear()
        
        # Cancela tarefas em execução
        for task in self.running_tasks.values():
            task.cancel()
            cancelled += 1
        
        # Cancela futures
        for future in self.task_futures.values():
            if not future.done():
                future.cancel()
        
        self.stats['total_cancelled'] += cancelled
        return cancelled
    
    def pause_task(self, task_id: str) -> bool:
        """Pausa uma tarefa."""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].pause()
            return True
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """Resume uma tarefa."""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].resume()
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[BaseTask]:
        """Obtém tarefa por ID."""
        # Procura em todas as listas
        for task_list in [self.pending_tasks, list(self.running_tasks.values()),
                         self.completed_tasks, self.failed_tasks]:
            for task in task_list:
                if task.task_id == task_id:
                    return task
        return None
    
    def find_tasks(self, **criteria) -> List[BaseTask]:
        """
        Encontra tarefas por critérios.
        
        Args:
            **criteria: Critérios de busca (name, status, priority, etc.)
            
        Returns:
            Lista de tarefas que atendem os critérios
        """
        all_tasks = (self.pending_tasks + 
                    list(self.running_tasks.values()) +
                    self.completed_tasks + 
                    self.failed_tasks)
        
        results = []
        for task in all_tasks:
            match = True
            
            for key, value in criteria.items():
                if not hasattr(task, key):
                    match = False
                    break
                
                task_value = getattr(task, key)
                if callable(task_value):
                    task_value = task_value()
                
                if task_value != value:
                    match = False
                    break
            
            if match:
                results.append(task)
        
        return results
    
    # Informações e status
    def get_status(self) -> Dict[str, Any]:
        """Obtém status do gerenciador."""
        return {
            'running': self.is_running,
            'pending_tasks': len(self.pending_tasks),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'max_concurrent': self.max_concurrent_tasks,
            'max_queue_size': self.max_queue_size,
            'stats': self.stats.copy()
        }
    
    def get_summary(self) -> List[Dict[str, Any]]:
        """Obtém resumo de todas as tarefas."""
        summary = []
        
        # Tarefas pendentes
        for task in self.pending_tasks:
            summary.append({
                'queue': 'pending',
                'task': task.to_dict()
            })
        
        # Tarefas em execução
        for task in self.running_tasks.values():
            summary.append({
                'queue': 'running',
                'task': task.to_dict()
            })
        
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas detalhadas."""
        total_tasks = (self.stats['total_completed'] + 
                      self.stats['total_failed'] + 
                      self.stats['total_cancelled'])
        
        success_rate = 0.0
        if total_tasks > 0:
            success_rate = self.stats['total_completed'] / total_tasks * 100
        
        return {
            'total_scheduled': self.stats['total_scheduled'],
            'total_completed': self.stats['total_completed'],
            'total_failed': self.stats['total_failed'],
            'total_cancelled': self.stats['total_cancelled'],
            'total_timeout': self.stats['total_timeout'],
            'success_rate': success_rate,
            'average_execution_time': self.stats['average_execution_time'],
            'tasks_by_priority': dict(self.stats['tasks_by_priority']),
            'current_pending': len(self.pending_tasks),
            'current_running': len(self.running_tasks),
            'uptime': time.time() - (self.global_context.timestamp if self.global_context else time.time())
        }
    
    # Contexto global
    def set_global_context(self, key: str, value: Any) -> None:
        """Define valor no contexto global."""
        self.global_context.set(key, value)
    
    def get_global_context(self, key: str, default: Any = None) -> Any:
        """Obtém valor do contexto global."""
        return self.global_context.get(key, default)
    
    def update_global_context(self, data: Dict[str, Any]) -> None:
        """Atualiza contexto global."""
        self.global_context.update(data)
    
    def __len__(self) -> int:
        """Número total de tarefas."""
        return (len(self.pending_tasks) + 
                len(self.running_tasks) + 
                len(self.completed_tasks) + 
                len(self.failed_tasks))
    
    def __str__(self) -> str:
        """Representação string."""
        return (f"TaskManager(pending: {len(self.pending_tasks)}, "
                f"running: {len(self.running_tasks)}, "
                f"completed: {len(self.completed_tasks)})") 