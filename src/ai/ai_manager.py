"""
AI Manager
==========

Gerenciador principal da inteligência artificial do PythonKore.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional, Callable

from state_machine import StateMachine, AIState
from action_queue import ActionQueue, Action, ActionType
from states import AIStates, AITransition, AIPriority, CommonConditions
from core.logging.logger import Logger
from core.events.event_bus import EventBus
from actors.base_actor import BaseActor


class AIManager:
    """
    Gerenciador principal da AI.
    
    Coordena todos os subsistemas de inteligência artificial:
    - State Machine
    - Action Queue
    - Decision Making
    - Context Management
    
    Equivalente ao AI.pm do OpenKore mas modernizado.
    """
    
    def __init__(self, 
                 logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None):
        """
        Inicializa AI Manager.
        
        Args:
            logger: Logger para debug
            event_bus: Bus de eventos
        """
        self.logger = logger or Logger(level="INFO")
        self.event_bus = event_bus
        
        # Componentes principais
        self.state_machine = StateMachine(
            initial_state=AIStates.OFF,
            logger=self.logger,
            event_bus=self.event_bus
        )
        
        self.action_queue = ActionQueue(
            logger=self.logger,
            event_bus=self.event_bus
        )
        
        # Estado da AI
        self.is_enabled = False
        self.is_auto = False
        self.is_manual = False
        
        # Contexto global
        self.player: Optional[BaseActor] = None
        self.target: Optional[BaseActor] = None
        self.monsters: List[BaseActor] = []
        self.npcs: List[BaseActor] = []
        self.items: List[BaseActor] = []
        self.players: List[BaseActor] = []
        
        # Configurações
        self.ai_config: Dict[str, Any] = {
            'attackAuto': True,
            'attackDistance': 1,
            'followTarget': False,
            'autoLoot': True,
            'sitAuto': True,
            'healAuto': True,
            'skillsAuto': True,
            'avoidPlayers': False,
            'teleportAuto': True,
            'storageAuto': False,
            'buyAuto': False,
            'sellAuto': False
        }
        
        # Callbacks de eventos
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Loop de execução
        self.ai_loop_task: Optional[asyncio.Task] = None
        self.update_interval = 0.05  # 50ms (20 FPS)
        
        # Inicializa transições básicas
        self._setup_basic_transitions()
        
        # Registra handlers de eventos
        self._register_event_handlers()
        
        self.logger.info("AIManager inicializado")
    
    def _setup_basic_transitions(self) -> None:
        """Configura transições básicas da AI."""
        transitions = [
            # OFF -> MANUAL (quando usuário ativa AI manual)
            AITransition(
                AIStates.OFF, AIStates.MANUAL,
                CommonConditions.ai_manual(),
                AIPriority.HIGH
            ),
            
            # MANUAL -> AUTO (quando usuário ativa AI auto)
            AITransition(
                AIStates.MANUAL, AIStates.AUTO,
                self._create_condition("user_enabled_auto", self._check_auto_enabled),
                AIPriority.HIGH
            ),
            
            # AUTO -> DEAD (quando personagem morre)
            AITransition(
                AIStates.AUTO, AIStates.DEAD,
                CommonConditions.is_dead(),
                AIPriority.EMERGENCY
            ),
            
            # AUTO -> EMERGENCY (quando HP crítico)
            AITransition(
                AIStates.AUTO, AIStates.EMERGENCY,
                CommonConditions.hp_below_percent(20),
                AIPriority.EMERGENCY
            ),
            
            # AUTO -> COMBAT (quando há monstro próximo e deve atacar)
            AITransition(
                AIStates.AUTO, AIStates.COMBAT,
                self._create_condition("should_attack", self._check_should_attack),
                AIPriority.HIGH
            ),
            
            # COMBAT -> AUTO (quando não há mais alvo)
            AITransition(
                AIStates.COMBAT, AIStates.AUTO,
                self._create_condition("no_target", self._check_no_target),
                AIPriority.NORMAL
            ),
            
            # EMERGENCY -> HEALING (quando em local seguro)
            AITransition(
                AIStates.EMERGENCY, AIStates.HEALING,
                self._create_condition("safe_location", self._check_safe_location),
                AIPriority.HIGH
            ),
            
            # HEALING -> AUTO (quando HP/SP restaurados)
            AITransition(
                AIStates.HEALING, AIStates.AUTO,
                self._create_condition("hp_sp_ok", self._check_hp_sp_ok),
                AIPriority.NORMAL
            )
        ]
        
        self.state_machine.add_transitions(transitions)
    
    def _create_condition(self, name: str, check_func: Callable) -> Any:
        """Helper para criar condições."""
        from states import AICondition
        return AICondition(name, check_func, f"Condição: {name}")
    
    def _check_auto_enabled(self, context: Dict[str, Any]) -> bool:
        """Verifica se auto AI está habilitada."""
        return self.is_auto
    
    def _check_should_attack(self, context: Dict[str, Any]) -> bool:
        """Verifica se deve atacar."""
        if not self.ai_config.get('attackAuto', False):
            return False
        
        if not self.player:
            return False
        
        # Procura monstros próximos
        for monster in self.monsters:
            distance = self.player.distance_to(monster)
            max_distance = self.ai_config.get('attackDistance', 1) + 3
            
            if distance <= max_distance and not monster.is_dead:
                self.target = monster
                return True
        
        return False
    
    def _check_no_target(self, context: Dict[str, Any]) -> bool:
        """Verifica se não há alvo."""
        if not self.target:
            return True
        
        if self.target.is_dead:
            self.target = None
            return True
        
        if not self.player:
            return True
        
        # Verifica se alvo está muito longe
        distance = self.player.distance_to(self.target)
        max_distance = self.ai_config.get('attackDistance', 1) + 10
        
        if distance > max_distance:
            self.target = None
            return True
        
        return False
    
    def _check_safe_location(self, context: Dict[str, Any]) -> bool:
        """Verifica se está em local seguro."""
        if not self.player:
            return False
        
        # Verifica se não há monstros próximos
        for monster in self.monsters:
            if self.player.distance_to(monster) <= 5 and not monster.is_dead:
                return False
        
        return True
    
    def _check_hp_sp_ok(self, context: Dict[str, Any]) -> bool:
        """Verifica se HP/SP estão OK."""
        if not self.player:
            return False
        
        hp_percent = self.player.stats.hp_percent()
        sp_percent = self.player.stats.sp_percent()
        
        return hp_percent >= 80 and sp_percent >= 50
    
    def _register_event_handlers(self) -> None:
        """Registra handlers de eventos."""
        if not self.event_bus:
            return
        
        # Eventos de estado da AI
        self.event_bus.subscribe('ai_state_changed', self._on_state_changed)
        self.event_bus.subscribe('action_completed', self._on_action_completed)
        self.event_bus.subscribe('action_failed', self._on_action_failed)
        
        # Eventos do jogo
        self.event_bus.subscribe('actor_spawned', self._on_actor_spawned)
        self.event_bus.subscribe('actor_died', self._on_actor_died)
        self.event_bus.subscribe('player_stats_changed', self._on_player_stats_changed)
    
    def start(self) -> None:
        """Inicia AI Manager."""
        if self.ai_loop_task and not self.ai_loop_task.done():
            self.logger.warning("AI já está rodando")
            return
        
        self.is_enabled = True
        self.ai_loop_task = asyncio.create_task(self._ai_loop())
        
        self.logger.info("AI iniciada")
        
        if self.event_bus:
            self.event_bus.emit('ai_started')
    
    def stop(self) -> None:
        """Para AI Manager."""
        self.is_enabled = False
        
        if self.ai_loop_task and not self.ai_loop_task.done():
            self.ai_loop_task.cancel()
        
        # Para todas as ações
        self.action_queue.cancel_all()
        
        # Reseta estado
        self.state_machine.force_state(AIStates.OFF, "AI parada")
        
        self.logger.info("AI parada")
        
        if self.event_bus:
            self.event_bus.emit('ai_stopped')
    
    def enable_auto(self) -> None:
        """Habilita AI automática."""
        self.is_auto = True
        self.is_manual = False
        
        if self.is_enabled:
            self.state_machine.force_state(AIStates.AUTO, "Auto habilitado")
        
        self.logger.info("AI AUTO habilitada")
    
    def enable_manual(self) -> None:
        """Habilita AI manual."""
        self.is_auto = False
        self.is_manual = True
        
        if self.is_enabled:
            self.state_machine.force_state(AIStates.MANUAL, "Manual habilitado")
        
        self.logger.info("AI MANUAL habilitada")
    
    def disable(self) -> None:
        """Desabilita AI."""
        self.is_auto = False
        self.is_manual = False
        
        if self.is_enabled:
            self.state_machine.force_state(AIStates.OFF, "AI desabilitada")
        
        self.logger.info("AI desabilitada")
    
    async def _ai_loop(self) -> None:
        """Loop principal da AI."""
        try:
            while self.is_enabled:
                # Atualiza contexto
                self._update_context()
                
                # Atualiza state machine
                self.state_machine.update()
                
                # Processa ações baseado no estado atual
                await self._process_current_state()
                
                # Executa próxima ação da fila
                await self.action_queue.execute_current()
                
                # Inicia próxima ação se fila não vazia
                if not self.action_queue.executing and self.action_queue.queue:
                    self.action_queue.start_execution()
                
                # Aguarda próximo ciclo
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            self.logger.info("AI loop cancelado")
        except Exception as e:
            self.logger.error(f"Erro no AI loop: {e}")
            self.is_enabled = False
    
    def _update_context(self) -> None:
        """Atualiza contexto da AI."""
        context = {
            'player': self.player,
            'target': self.target,
            'monsters': self.monsters,
            'npcs': self.npcs,
            'items': self.items,
            'players': self.players,
            'ai_config': self.ai_config,
            'is_auto': self.is_auto,
            'is_manual': self.is_manual,
            'timestamp': time.time()
        }
        
        self.state_machine.update_context(context)
    
    async def _process_current_state(self) -> None:
        """Processa estado atual da AI."""
        current_state = self.state_machine.get_current_state()
        
        if current_state == AIStates.AUTO:
            await self._process_auto_state()
        elif current_state == AIStates.COMBAT:
            await self._process_combat_state()
        elif current_state == AIStates.EMERGENCY:
            await self._process_emergency_state()
        elif current_state == AIStates.HEALING:
            await self._process_healing_state()
        elif current_state == AIStates.DEAD:
            await self._process_dead_state()
    
    async def _process_auto_state(self) -> None:
        """Processa estado AUTO."""
        # Verifica se deve fazer algo automaticamente
        if self.ai_config.get('autoLoot', False):
            await self._check_loot()
        
        if self.ai_config.get('sitAuto', False):
            await self._check_sit()
    
    async def _process_combat_state(self) -> None:
        """Processa estado COMBAT."""
        if not self.target or not self.player:
            return
        
        # Verifica se está no alcance
        distance = self.player.distance_to(self.target)
        attack_distance = self.ai_config.get('attackDistance', 1)
        
        if distance > attack_distance:
            # Move para perto do alvo
            self._queue_move_to_target()
        else:
            # Ataca o alvo
            self._queue_attack_target()
    
    async def _process_emergency_state(self) -> None:
        """Processa estado EMERGENCY."""
        # Foge para local seguro ou usa teleporte
        if self.ai_config.get('teleportAuto', False):
            self._queue_teleport()
        else:
            self._queue_find_safe_spot()
    
    async def _process_healing_state(self) -> None:
        """Processa estado HEALING."""
        if not self.player:
            return
        
        hp_percent = self.player.stats.hp_percent()
        sp_percent = self.player.stats.sp_percent()
        
        if hp_percent < 50:
            self._queue_heal()
        
        if sp_percent < 30:
            self._queue_recover_sp()
    
    async def _process_dead_state(self) -> None:
        """Processa estado DEAD."""
        # Aguarda respawn ou decide reviver
        self.logger.info("Personagem morreu, aguardando...")
    
    async def _check_loot(self) -> None:
        """Verifica se há itens para coletar."""
        if not self.player:
            return
        
        for item in self.items:
            distance = self.player.distance_to(item)
            if distance <= 2:
                self._queue_pickup_item(item)
                break
    
    async def _check_sit(self) -> None:
        """Verifica se deve sentar para recuperar HP/SP."""
        if not self.player:
            return
        
        hp_percent = self.player.stats.hp_percent()
        sp_percent = self.player.stats.sp_percent()
        
        if (hp_percent < 90 or sp_percent < 90) and not self.player.is_sitting:
            self._queue_sit()
    
    def _queue_move_to_target(self) -> None:
        """Adiciona ação de mover para alvo."""
        if not self.target:
            return
        
        action = Action(
            action_type=ActionType.MOVE_TO,
            name=f"Move to {self.target.name}",
            executor=lambda: self._execute_move_to(self.target.position),
            priority=AIPriority.HIGH
        )
        
        action.set_parameter('target_pos', self.target.position)
        self.action_queue.add_action(action)
    
    def _queue_attack_target(self) -> None:
        """Adiciona ação de atacar alvo."""
        if not self.target:
            return
        
        action = Action(
            action_type=ActionType.ATTACK,
            name=f"Attack {self.target.name}",
            executor=lambda: self._execute_attack(self.target),
            priority=AIPriority.HIGH
        )
        
        action.set_parameter('target', self.target)
        self.action_queue.add_action(action)
    
    def _queue_teleport(self) -> None:
        """Adiciona ação de teleporte."""
        action = Action(
            action_type=ActionType.TELEPORT,
            name="Emergency Teleport",
            executor=lambda: self._execute_teleport(),
            priority=AIPriority.EMERGENCY
        )
        
        self.action_queue.add_action(action)
    
    def _queue_heal(self) -> None:
        """Adiciona ação de cura."""
        action = Action(
            action_type=ActionType.USE_ITEM,
            name="Use Healing Item",
            executor=lambda: self._execute_heal(),
            priority=AIPriority.HIGH
        )
        
        self.action_queue.add_action(action)
    
    def _queue_sit(self) -> None:
        """Adiciona ação de sentar."""
        action = Action(
            action_type=ActionType.CUSTOM,
            name="Sit",
            executor=lambda: self._execute_sit(),
            priority=AIPriority.NORMAL
        )
        
        self.action_queue.add_action(action)
    
    def _queue_pickup_item(self, item: BaseActor) -> None:
        """Adiciona ação de pegar item."""
        action = Action(
            action_type=ActionType.PICK_ITEM,
            name=f"Pick {item.name}",
            executor=lambda: self._execute_pickup(item),
            priority=AIPriority.LOW
        )
        
        action.set_parameter('item', item)
        self.action_queue.add_action(action)
    
    # Executores de ações (implementação básica/mock)
    def _execute_move_to(self, position) -> bool:
        """Executa movimento."""
        # TODO: Implementar movimento real
        self.logger.debug(f"Movendo para {position}")
        return True
    
    def _execute_attack(self, target) -> bool:
        """Executa ataque."""
        # TODO: Implementar ataque real
        self.logger.debug(f"Atacando {target.name}")
        return True
    
    def _execute_teleport(self) -> bool:
        """Executa teleporte."""
        # TODO: Implementar teleporte real
        self.logger.debug("Usando teleporte")
        return True
    
    def _execute_heal(self) -> bool:
        """Executa cura."""
        # TODO: Implementar cura real
        self.logger.debug("Usando item de cura")
        return True
    
    def _execute_sit(self) -> bool:
        """Executa sentar."""
        # TODO: Implementar sentar real
        self.logger.debug("Sentando")
        return True
    
    def _execute_pickup(self, item) -> bool:
        """Executa pegar item."""
        # TODO: Implementar pickup real
        self.logger.debug(f"Pegando {item.name}")
        return True
    
    # Event handlers
    def _on_state_changed(self, event) -> None:
        """Handler para mudança de estado."""
        old_state = event.kwargs.get('old_state')
        new_state = event.kwargs.get('new_state')
        
        self.logger.info(f"AI mudou estado: {old_state.value} -> {new_state.value}")
    
    def _on_action_completed(self, event) -> None:
        """Handler para ação completada."""
        action = event.kwargs.get('action')
        self.logger.debug(f"Ação completada: {action.name}")
    
    def _on_action_failed(self, event) -> None:
        """Handler para ação falhada."""
        action = event.kwargs.get('action')
        self.logger.warning(f"Ação falhou: {action.name} - {action.error_message}")
    
    def _on_actor_spawned(self, event) -> None:
        """Handler para ator que apareceu."""
        actor = event.kwargs.get('actor')
        if actor.is_monster():
            self.monsters.append(actor)
        elif actor.is_npc():
            self.npcs.append(actor)
        elif actor.is_item():
            self.items.append(actor)
        elif actor.is_player():
            self.players.append(actor)
    
    def _on_actor_died(self, event) -> None:
        """Handler para ator que morreu."""
        actor = event.kwargs.get('actor')
        
        # Remove das listas se for o alvo atual
        if self.target and self.target.id == actor.id:
            self.target = None
    
    def _on_player_stats_changed(self, event) -> None:
        """Handler para mudança de stats do player."""
        # Force state machine to re-evaluate conditions
        pass
    
    # Métodos públicos para controle
    def set_player(self, player: BaseActor) -> None:
        """Define o jogador controlado."""
        self.player = player
        self.logger.info(f"Player definido: {player.name}")
    
    def add_monster(self, monster: BaseActor) -> None:
        """Adiciona monstro à lista."""
        self.monsters.append(monster)
    
    def add_npc(self, npc: BaseActor) -> None:
        """Adiciona NPC à lista."""
        self.npcs.append(npc)
    
    def add_item(self, item: BaseActor) -> None:
        """Adiciona item à lista."""
        self.items.append(item)
    
    def set_config(self, key: str, value: Any) -> None:
        """Define configuração da AI."""
        self.ai_config[key] = value
        self.logger.debug(f"Config atualizada: {key} = {value}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtém status completo da AI.
        
        Returns:
            Dicionário com status
        """
        return {
            'enabled': self.is_enabled,
            'auto': self.is_auto,
            'manual': self.is_manual,
            'state_machine': self.state_machine.get_summary(),
            'action_queue': self.action_queue.get_queue_status(),
            'player': self.player.name if self.player else None,
            'target': self.target.name if self.target else None,
            'monsters_count': len(self.monsters),
            'npcs_count': len(self.npcs),
            'items_count': len(self.items),
            'config': self.ai_config.copy()
        } 