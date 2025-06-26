"""
State Machine
=============

Máquina de estados para a AI do PythonKore.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

from states import AIStates, AITransition, AIPriority, AICondition
from core.logging.logger import Logger
from core.events.event_bus import EventBus


@dataclass
class AIState:
    """
    Estado da AI com metadados.
    """
    state: AIStates
    entered_at: float = field(default_factory=time.time)
    duration: float = 0.0
    entry_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def update_duration(self) -> None:
        """Atualiza duração no estado."""
        self.duration = time.time() - self.entered_at
    
    def __post_init__(self) -> None:
        """Inicialização pós-criação."""
        self.entry_count += 1


class StateMachine:
    """
    Máquina de estados da AI.
    
    Gerencia transições entre estados da AI baseado em condições.
    Similar ao sistema do OpenKore mas mais estruturado.
    """
    
    def __init__(self, 
                 initial_state: AIStates = AIStates.OFF,
                 logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None):
        """
        Inicializa máquina de estados.
        
        Args:
            initial_state: Estado inicial
            logger: Logger para debug
            event_bus: Bus de eventos
        """
        self.logger = logger or Logger("StateMachine")
        self.event_bus = event_bus
        
        # Estado atual
        self.current_state = AIState(initial_state)
        self.previous_state: Optional[AIState] = None
        
        # Histórico de estados
        self.state_history: List[AIState] = [self.current_state]
        self.max_history = 100
        
        # Transições
        self.transitions: List[AITransition] = []
        self.transition_map: Dict[AIStates, List[AITransition]] = {}
        
        # Contexto global da AI
        self.context: Dict[str, Any] = {}
        
        # Estatísticas
        self.state_stats: Dict[AIStates, Dict[str, Any]] = {}
        self.transition_count = 0
        
        # Controle
        self.is_running = False
        self.update_interval = 0.1  # 100ms
        self.last_update = time.time()
        
        # Inicializa estatísticas
        self._init_state_stats()
        
        self.logger.info(f"StateMachine inicializada em estado: {initial_state.value}")
    
    def _init_state_stats(self) -> None:
        """Inicializa estatísticas dos estados."""
        for state in AIStates:
            self.state_stats[state] = {
                'total_time': 0.0,
                'entry_count': 0,
                'transition_count': 0,
                'last_entered': None
            }
    
    def add_transition(self, transition: AITransition) -> None:
        """
        Adiciona uma transição.
        
        Args:
            transition: Transição a adicionar
        """
        self.transitions.append(transition)
        
        # Indexa por estado de origem
        if transition.from_state not in self.transition_map:
            self.transition_map[transition.from_state] = []
        
        self.transition_map[transition.from_state].append(transition)
        
        # Ordena por prioridade (maior primeiro)
        self.transition_map[transition.from_state].sort(
            key=lambda t: t.priority.value, 
            reverse=True
        )
        
        self.logger.debug(f"Transição adicionada: {transition}")
    
    def add_transitions(self, transitions: List[AITransition]) -> None:
        """
        Adiciona múltiplas transições.
        
        Args:
            transitions: Lista de transições
        """
        for transition in transitions:
            self.add_transition(transition)
    
    def get_current_state(self) -> AIStates:
        """
        Obtém estado atual.
        
        Returns:
            Estado atual
        """
        return self.current_state.state
    
    def get_state_duration(self) -> float:
        """
        Obtém duração no estado atual.
        
        Returns:
            Duração em segundos
        """
        self.current_state.update_duration()
        return self.current_state.duration
    
    def set_context(self, key: str, value: Any) -> None:
        """
        Define valor no contexto.
        
        Args:
            key: Chave
            value: Valor
        """
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor do contexto.
        
        Args:
            key: Chave
            default: Valor padrão
            
        Returns:
            Valor do contexto
        """
        return self.context.get(key, default)
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """
        Atualiza múltiplos valores do contexto.
        
        Args:
            updates: Dicionário com atualizações
        """
        self.context.update(updates)
    
    def force_state(self, new_state: AIStates, reason: str = "") -> None:
        """
        Força mudança de estado.
        
        Args:
            new_state: Novo estado
            reason: Motivo da mudança forçada
        """
        old_state = self.current_state.state
        
        if old_state == new_state:
            return
        
        self.logger.info(f"Forçando mudança: {old_state.value} -> {new_state.value} ({reason})")
        
        self._change_state(new_state, forced=True)
    
    def can_transition_to(self, target_state: AIStates) -> bool:
        """
        Verifica se pode transicionar para um estado.
        
        Args:
            target_state: Estado alvo
            
        Returns:
            True se pode transicionar
        """
        current = self.current_state.state
        
        # Verifica se existe transição válida
        transitions = self.transition_map.get(current, [])
        
        for transition in transitions:
            if (transition.to_state == target_state and 
                transition.can_transition(current, self.context)):
                return True
        
        return False
    
    def get_possible_transitions(self) -> List[AIStates]:
        """
        Obtém estados possíveis de transição.
        
        Returns:
            Lista de estados possíveis
        """
        current = self.current_state.state
        transitions = self.transition_map.get(current, [])
        
        possible = []
        for transition in transitions:
            if transition.can_transition(current, self.context):
                possible.append(transition.to_state)
        
        return possible
    
    def update(self) -> bool:
        """
        Atualiza máquina de estados.
        
        Verifica condições e executa transições se necessário.
        
        Returns:
            True se houve mudança de estado
        """
        current_time = time.time()
        
        # Throttling
        if current_time - self.last_update < self.update_interval:
            return False
        
        self.last_update = current_time
        
        # Atualiza duração do estado atual
        self.current_state.update_duration()
        
        # Verifica transições possíveis
        current = self.current_state.state
        transitions = self.transition_map.get(current, [])
        
        for transition in transitions:
            if transition.can_transition(current, self.context):
                # Executa transição
                self._execute_transition(transition)
                return True
        
        return False
    
    def _execute_transition(self, transition: AITransition) -> None:
        """
        Executa uma transição.
        
        Args:
            transition: Transição a executar
        """
        old_state = self.current_state.state
        new_state = transition.to_state
        
        self.logger.info(f"Transição: {old_state.value} -> {new_state.value}")
        
        # Executa ação da transição
        transition.execute_transition(self.context)
        
        # Muda estado
        self._change_state(new_state)
        
        # Emite evento
        if self.event_bus:
            self.event_bus.emit('ai_state_changed', 
                             old_state=old_state,
                             new_state=new_state,
                             transition=transition)
    
    def _change_state(self, new_state: AIStates, forced: bool = False) -> None:
        """
        Muda estado interno.
        
        Args:
            new_state: Novo estado
            forced: Se foi mudança forçada
        """
        old_state = self.current_state.state
        
        if old_state == new_state:
            return
        
        # Atualiza estatísticas do estado antigo
        self.current_state.update_duration()
        self.state_stats[old_state]['total_time'] += self.current_state.duration
        
        # Salva estado anterior
        self.previous_state = self.current_state
        
        # Cria novo estado
        self.current_state = AIState(new_state)
        
        # Atualiza estatísticas do novo estado
        self.state_stats[new_state]['entry_count'] += 1
        self.state_stats[new_state]['last_entered'] = time.time()
        
        if not forced:
            self.state_stats[new_state]['transition_count'] += 1
        
        self.transition_count += 1
        
        # Adiciona ao histórico
        self.state_history.append(self.current_state)
        
        # Limita histórico
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
        
        self.logger.debug(f"Estado mudou: {old_state.value} -> {new_state.value}")
    
    def get_state_stats(self) -> Dict[AIStates, Dict[str, Any]]:
        """
        Obtém estatísticas dos estados.
        
        Returns:
            Dicionário com estatísticas
        """
        # Atualiza duração do estado atual
        self.current_state.update_duration()
        current_stats = self.state_stats.copy()
        current_stats[self.current_state.state]['total_time'] += self.current_state.duration
        
        return current_stats
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtém resumo da máquina de estados.
        
        Returns:
            Dicionário com resumo
        """
        stats = self.get_state_stats()
        
        return {
            'current_state': self.current_state.state.value,
            'state_duration': self.get_state_duration(),
            'total_transitions': self.transition_count,
            'states_count': len([s for s in stats.values() if s['entry_count'] > 0]),
            'most_used_state': max(stats.keys(), key=lambda s: stats[s]['total_time']).value,
            'uptime': sum(s['total_time'] for s in stats.values()),
            'transitions_registered': len(self.transitions)
        }
    
    def reset(self, initial_state: AIStates = AIStates.OFF) -> None:
        """
        Reseta máquina de estados.
        
        Args:
            initial_state: Estado inicial após reset
        """
        self.logger.info("Resetando StateMachine")
        
        # Reset estado
        self.current_state = AIState(initial_state)
        self.previous_state = None
        
        # Reset histórico
        self.state_history = [self.current_state]
        
        # Reset estatísticas
        self._init_state_stats()
        self.transition_count = 0
        
        # Reset contexto
        self.context.clear()
    
    def is_in_state(self, *states: AIStates) -> bool:
        """
        Verifica se está em algum dos estados especificados.
        
        Args:
            states: Estados a verificar
            
        Returns:
            True se está em algum dos estados
        """
        return self.current_state.state in states
    
    def was_in_state(self, state: AIStates, last_n: int = 5) -> bool:
        """
        Verifica se esteve em um estado recentemente.
        
        Args:
            state: Estado a verificar
            last_n: Últimos N estados a verificar
            
        Returns:
            True se esteve no estado
        """
        recent_states = self.state_history[-last_n:] if last_n > 0 else self.state_history
        return any(s.state == state for s in recent_states)
    
    def __str__(self) -> str:
        """Representação string."""
        return f"StateMachine({self.current_state.state.value}, {self.get_state_duration():.1f}s)" 