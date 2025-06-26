"""
AI States
=========

Estados da inteligência artificial do PythonKore.
"""

from enum import Enum
from typing import Dict, Any, Optional, Callable


class AIStates(Enum):
    """Estados principais da AI (equivalente ao OpenKore)."""
    # Estados básicos
    OFF = "off"                  # AI desligada
    MANUAL = "manual"            # Controle manual
    AUTO = "auto"               # AI automática
    
    # Estados de inicialização
    LOADING = "loading"          # Carregando
    CONNECTING = "connecting"    # Conectando
    AUTHENTICATING = "auth"      # Autenticando
    
    # Estados de jogo
    IN_GAME = "in_game"         # No jogo
    CHARACTER_SELECT = "char_select"  # Seleção de personagem
    
    # Estados de combate
    COMBAT = "combat"           # Em combate
    ATTACKING = "attacking"     # Atacando
    CASTING = "casting"         # Conjurando skill
    
    # Estados de movimento
    MOVING = "moving"           # Movendo
    PATH_FINDING = "pathfinding"  # Calculando rota
    FOLLOWING = "following"     # Seguindo alguém
    
    # Estados de ação
    TALKING = "talking"         # Conversando com NPC
    SHOPPING = "shopping"       # Comprando/vendendo
    TRADING = "trading"         # Trocando com player
    LOOTING = "looting"         # Coletando itens
    
    # Estados de recuperação
    RESTING = "resting"         # Descansando (HP/SP)
    HEALING = "healing"         # Se curando
    SITTING = "sitting"         # Sentado
    
    # Estados de emergência
    EMERGENCY = "emergency"     # Situação de emergência
    ESCAPING = "escaping"       # Fugindo
    DEAD = "dead"              # Morto
    
    # Estados de economia
    VENDING = "vending"         # Vendendo no shop
    STORING = "storing"         # Usando storage
    
    # Estados especiais
    IDLE = "idle"              # Ocioso
    PAUSED = "paused"          # Pausado
    ERROR = "error"            # Erro


class AISubStates(Enum):
    """Sub-estados mais específicos."""
    # Combat sub-states
    SELECTING_TARGET = "selecting_target"
    APPROACHING_TARGET = "approaching_target"
    USING_SKILL = "using_skill"
    WAITING_SKILL = "waiting_skill"
    
    # Movement sub-states
    CALCULATING_PATH = "calculating_path"
    WALKING_TO_TARGET = "walking_to_target"
    AVOIDING_OBSTACLE = "avoiding_obstacle"
    
    # Recovery sub-states
    FINDING_SAFE_SPOT = "finding_safe_spot"
    USING_ITEM = "using_item"
    WAITING_RECOVERY = "waiting_recovery"
    
    # Social sub-states
    WAITING_NPC_RESPONSE = "waiting_npc_response"
    SELECTING_OPTION = "selecting_option"
    WAITING_TRADE = "waiting_trade"


class AIMode(Enum):
    """Modos de operação da AI."""
    CONSERVATIVE = "conservative"  # Conservador (seguro)
    BALANCED = "balanced"         # Balanceado
    AGGRESSIVE = "aggressive"     # Agressivo
    CUSTOM = "custom"            # Customizado


class AIPriority(Enum):
    """Prioridades de ações."""
    EMERGENCY = 100    # Emergência (fuga, cura crítica)
    HIGH = 80         # Alta (combate, morte iminente)
    NORMAL = 50       # Normal (movimento, ações básicas)
    LOW = 20          # Baixa (loot, organização)
    IDLE = 1          # Ocioso (espera)


class AICondition:
    """
    Condição para transição de estados.
    
    Representa uma condição que deve ser verdadeira para
    que uma transição de estado ocorra.
    """
    
    def __init__(self, 
                 name: str,
                 check_function: Callable[[Dict[str, Any]], bool],
                 description: str = ""):
        """
        Inicializa condição.
        
        Args:
            name: Nome da condição
            check_function: Função que verifica a condição
            description: Descrição da condição
        """
        self.name = name
        self.check_function = check_function
        self.description = description
        self.last_check_result: Optional[bool] = None
        self.check_count = 0
    
    def check(self, context: Dict[str, Any]) -> bool:
        """
        Verifica se a condição é verdadeira.
        
        Args:
            context: Contexto da AI com dados necessários
            
        Returns:
            True se condição satisfeita
        """
        try:
            result = self.check_function(context)
            self.last_check_result = result
            self.check_count += 1
            return result
        except Exception:
            self.last_check_result = False
            return False
    
    def __str__(self) -> str:
        """Representação string."""
        return f"Condition({self.name})"


class AITransition:
    """
    Transição entre estados da AI.
    
    Define quando e como a AI deve mudar de um estado para outro.
    """
    
    def __init__(self,
                 from_state: AIStates,
                 to_state: AIStates,
                 condition: AICondition,
                 priority: AIPriority = AIPriority.NORMAL,
                 action: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Inicializa transição.
        
        Args:
            from_state: Estado de origem
            to_state: Estado de destino
            condition: Condição para transição
            priority: Prioridade da transição
            action: Ação a executar na transição (opcional)
        """
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.priority = priority
        self.action = action
        self.trigger_count = 0
    
    def can_transition(self, current_state: AIStates, context: Dict[str, Any]) -> bool:
        """
        Verifica se pode fazer a transição.
        
        Args:
            current_state: Estado atual da AI
            context: Contexto da AI
            
        Returns:
            True se pode transicionar
        """
        if current_state != self.from_state:
            return False
        
        if self.condition.check(context):
            self.trigger_count += 1
            return True
        
        return False
    
    def execute_transition(self, context: Dict[str, Any]) -> None:
        """
        Executa ação da transição.
        
        Args:
            context: Contexto da AI
        """
        if self.action:
            try:
                self.action(context)
            except Exception as e:
                # Log error but don't block transition
                print(f"Erro na ação de transição: {e}")
    
    def __str__(self) -> str:
        """Representação string."""
        return f"Transition({self.from_state.value} -> {self.to_state.value})"


# Condições pré-definidas comuns
class CommonConditions:
    """Condições comuns da AI."""
    
    @staticmethod
    def hp_below_percent(percent: float) -> AICondition:
        """Condição: HP abaixo de X%."""
        def check(context: Dict[str, Any]) -> bool:
            player = context.get('player')
            if not player or not hasattr(player, 'stats'):
                return False
            return player.stats.hp_percent() < percent
        
        return AICondition(
            f"hp_below_{percent}%",
            check,
            f"HP abaixo de {percent}%"
        )
    
    @staticmethod
    def sp_below_percent(percent: float) -> AICondition:
        """Condição: SP abaixo de X%."""
        def check(context: Dict[str, Any]) -> bool:
            player = context.get('player')
            if not player or not hasattr(player, 'stats'):
                return False
            return player.stats.sp_percent() < percent
        
        return AICondition(
            f"sp_below_{percent}%",
            check,
            f"SP abaixo de {percent}%"
        )
    
    @staticmethod
    def monster_nearby(range_: int = 5) -> AICondition:
        """Condição: Monstro próximo."""
        def check(context: Dict[str, Any]) -> bool:
            player = context.get('player')
            monsters = context.get('monsters', [])
            
            if not player:
                return False
            
            for monster in monsters:
                if player.distance_to(monster) <= range_:
                    return True
            return False
        
        return AICondition(
            f"monster_nearby_{range_}",
            check,
            f"Monstro a menos de {range_} células"
        )
    
    @staticmethod
    def is_dead() -> AICondition:
        """Condição: Está morto."""
        def check(context: Dict[str, Any]) -> bool:
            player = context.get('player')
            if not player:
                return False
            return player.is_dead or player.stats.hp <= 0
        
        return AICondition(
            "is_dead",
            check,
            "Personagem está morto"
        )
    
    @staticmethod
    def ai_manual() -> AICondition:
        """Condição: AI em modo manual."""
        def check(context: Dict[str, Any]) -> bool:
            ai_mode = context.get('ai_mode')
            return ai_mode == AIMode.CONSERVATIVE
        
        return AICondition(
            "ai_manual",
            check,
            "AI em modo manual"
        )
    
    @staticmethod
    def has_target() -> AICondition:
        """Condição: Tem alvo."""
        def check(context: Dict[str, Any]) -> bool:
            target = context.get('target')
            return target is not None
        
        return AICondition(
            "has_target",
            check,
            "Tem alvo selecionado"
        )
    
    @staticmethod
    def target_in_range(range_: int = 1) -> AICondition:
        """Condição: Alvo no alcance."""
        def check(context: Dict[str, Any]) -> bool:
            player = context.get('player')
            target = context.get('target')
            
            if not player or not target:
                return False
            
            return player.distance_to(target) <= range_
        
        return AICondition(
            f"target_in_range_{range_}",
            check,
            f"Alvo a menos de {range_} células"
        ) 