"""
Base Actor System
=================

Sistema base para todos os atores do jogo.
"""

import time
from enum import Enum
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field

from position import Position, Direction


class ActorType(Enum):
    """Tipos de atores."""
    UNKNOWN = "unknown"
    PLAYER = "player"
    MONSTER = "monster"
    NPC = "npc"
    ITEM = "item"
    PET = "pet"
    HOMUNCULUS = "homunculus"
    MERCENARY = "mercenary"
    PORTAL = "portal"
    SKILL = "skill"
    TRAP = "trap"


class ActorStatus(Enum):
    """Status possíveis de um ator."""
    UNKNOWN = "unknown"
    ALIVE = "alive"
    DEAD = "dead"
    SITTING = "sitting"
    WALKING = "walking"
    ATTACKING = "attacking"
    CASTING = "casting"
    STUNNED = "stunned"
    SLEEPING = "sleeping"
    FROZEN = "frozen"


@dataclass
class ActorStats:
    """Estatísticas básicas de um ator."""
    hp: int = 0
    max_hp: int = 0
    sp: int = 0
    max_sp: int = 0
    level: int = 1
    job_level: int = 1
    exp: int = 0
    job_exp: int = 0
    
    # Stats básicas
    str_: int = 1  # 'str' é palavra reservada
    agi: int = 1
    vit: int = 1
    int_: int = 1  # 'int' é palavra reservada
    dex: int = 1
    luk: int = 1
    
    # Stats derivadas
    atk: int = 0
    matk: int = 0
    def_: int = 0  # 'def' é palavra reservada
    mdef: int = 0
    hit: int = 0
    flee: int = 0
    crit: int = 0
    aspd: int = 0
    
    def hp_percent(self) -> float:
        """Retorna percentual de HP."""
        if self.max_hp == 0:
            return 0.0
        return (self.hp / self.max_hp) * 100.0
    
    def sp_percent(self) -> float:
        """Retorna percentual de SP."""
        if self.max_sp == 0:
            return 0.0
        return (self.sp / self.max_sp) * 100.0
    
    def is_alive(self) -> bool:
        """Verifica se está vivo."""
        return self.hp > 0


class BaseActor:
    """
    Classe base para todos os atores do jogo.
    
    Representa qualquer entidade visível no jogo:
    - Jogadores
    - Monstros
    - NPCs
    - Itens
    - Pets
    - etc.
    """
    
    def __init__(self, 
                 actor_id: int,
                 actor_type: ActorType = ActorType.UNKNOWN,
                 name: str = ""):
        """
        Inicializa um ator.
        
        Args:
            actor_id: ID único do ator
            actor_type: Tipo do ator
            name: Nome do ator
        """
        # Identificação
        self.id = actor_id
        self.type = actor_type
        self.name = name
        self.display_name = name
        
        # Posição e movimento
        self.position = Position(0, 0)
        self.destination = Position(0, 0)
        self.direction = Direction.SOUTH
        self.is_moving = False
        
        # Estado
        self.status = ActorStatus.UNKNOWN
        self.stats = ActorStats()
        
        # Visual
        self.job_id = 0
        self.hair_style = 0
        self.hair_color = 0
        self.clothes_color = 0
        self.head_dir = 0
        self.body_dir = 0
        self.weapon = 0
        self.shield = 0
        self.head_top = 0
        self.head_mid = 0
        self.head_bottom = 0
        self.robe = 0
        
        # Flags e estados
        self.is_dead = False
        self.is_sitting = False
        self.is_hidden = False
        self.is_cloaked = False
        
        # Timestamps
        self.last_seen = time.time()
        self.spawn_time = time.time()
        self.last_movement = 0.0
        self.last_action = 0.0
        
        # Dados adicionais
        self.properties: Dict[str, Any] = {}
        self.buffs: Set[int] = set()
        self.debuffs: Set[int] = set()
        
        # Dados de guild
        self.guild_id = 0
        self.guild_name = ""
        self.guild_title = ""
        self.guild_emblem = 0
        
        # Dados de party
        self.party_id = 0
        self.party_name = ""
    
    def update_position(self, x: int, y: int) -> None:
        """
        Atualiza posição do ator.
        
        Args:
            x: Coordenada X
            y: Coordenada Y
        """
        self.position.x = x
        self.position.y = y
        self.last_movement = time.time()
    
    def set_destination(self, x: int, y: int) -> None:
        """
        Define destino do movimento.
        
        Args:
            x: Coordenada X de destino
            y: Coordenada Y de destino
        """
        self.destination.x = x
        self.destination.y = y
        self.is_moving = True
    
    def stop_movement(self) -> None:
        """Para o movimento do ator."""
        self.is_moving = False
        self.destination = self.position.copy()
    
    def distance_to(self, other: 'BaseActor') -> float:
        """
        Calcula distância para outro ator.
        
        Args:
            other: Outro ator
            
        Returns:
            Distância em células
        """
        return self.position.distance_to(other.position)
    
    def distance_to_position(self, pos: Position) -> float:
        """
        Calcula distância para uma posição.
        
        Args:
            pos: Posição
            
        Returns:
            Distância em células
        """
        return self.position.distance_to(pos)
    
    def is_in_range(self, other: 'BaseActor', range_: int) -> bool:
        """
        Verifica se outro ator está no alcance.
        
        Args:
            other: Outro ator
            range_: Alcance em células
            
        Returns:
            True se está no alcance
        """
        return self.distance_to(other) <= range_
    
    def update_stats(self, stats_data: Dict[str, Any]) -> None:
        """
        Atualiza estatísticas do ator.
        
        Args:
            stats_data: Dados das estatísticas
        """
        for key, value in stats_data.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)
    
    def add_buff(self, buff_id: int) -> None:
        """
        Adiciona um buff.
        
        Args:
            buff_id: ID do buff
        """
        self.buffs.add(buff_id)
    
    def remove_buff(self, buff_id: int) -> None:
        """
        Remove um buff.
        
        Args:
            buff_id: ID do buff
        """
        self.buffs.discard(buff_id)
    
    def has_buff(self, buff_id: int) -> bool:
        """
        Verifica se tem um buff.
        
        Args:
            buff_id: ID do buff
            
        Returns:
            True se tem o buff
        """
        return buff_id in self.buffs
    
    def add_debuff(self, debuff_id: int) -> None:
        """
        Adiciona um debuff.
        
        Args:
            debuff_id: ID do debuff
        """
        self.debuffs.add(debuff_id)
    
    def remove_debuff(self, debuff_id: int) -> None:
        """
        Remove um debuff.
        
        Args:
            debuff_id: ID do debuff
        """
        self.debuffs.discard(debuff_id)
    
    def has_debuff(self, debuff_id: int) -> bool:
        """
        Verifica se tem um debuff.
        
        Args:
            debuff_id: ID do debuff
            
        Returns:
            True se tem o debuff
        """
        return debuff_id in self.debuffs
    
    def set_property(self, key: str, value: Any) -> None:
        """
        Define uma propriedade customizada.
        
        Args:
            key: Chave da propriedade
            value: Valor da propriedade
        """
        self.properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Obtém uma propriedade customizada.
        
        Args:
            key: Chave da propriedade
            default: Valor padrão
            
        Returns:
            Valor da propriedade
        """
        return self.properties.get(key, default)
    
    def has_property(self, key: str) -> bool:
        """
        Verifica se tem uma propriedade.
        
        Args:
            key: Chave da propriedade
            
        Returns:
            True se tem a propriedade
        """
        return key in self.properties
    
    def update_last_seen(self) -> None:
        """Atualiza timestamp de última visualização."""
        self.last_seen = time.time()
    
    def time_since_last_seen(self) -> float:
        """
        Retorna tempo desde última visualização.
        
        Returns:
            Tempo em segundos
        """
        return time.time() - self.last_seen
    
    def is_player(self) -> bool:
        """Verifica se é um jogador."""
        return self.type == ActorType.PLAYER
    
    def is_monster(self) -> bool:
        """Verifica se é um monstro."""
        return self.type == ActorType.MONSTER
    
    def is_npc(self) -> bool:
        """Verifica se é um NPC."""
        return self.type == ActorType.NPC
    
    def is_item(self) -> bool:
        """Verifica se é um item."""
        return self.type == ActorType.ITEM
    
    def is_pet(self) -> bool:
        """Verifica se é um pet."""
        return self.type == ActorType.PET
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte ator para dicionário.
        
        Returns:
            Dicionário com dados do ator
        """
        return {
            'id': self.id,
            'type': self.type.value,
            'name': self.name,
            'position': self.position.to_dict(),
            'destination': self.destination.to_dict(),
            'direction': self.direction.value,
            'is_moving': self.is_moving,
            'status': self.status.value,
            'stats': {
                'hp': self.stats.hp,
                'max_hp': self.stats.max_hp,
                'sp': self.stats.sp,
                'max_sp': self.stats.max_sp,
                'level': self.stats.level
            },
            'is_dead': self.is_dead,
            'is_sitting': self.is_sitting,
            'last_seen': self.last_seen,
            'buffs': list(self.buffs),
            'debuffs': list(self.debuffs),
            'properties': self.properties.copy()
        }
    
    def __str__(self) -> str:
        """Representação string do ator."""
        return f"{self.type.value.title()}({self.name or self.id}, {self.position})"
    
    def __repr__(self) -> str:
        """Representação detalhada do ator."""
        return (f"BaseActor(id={self.id}, type={self.type.value}, "
                f"name='{self.name}', pos={self.position})") 