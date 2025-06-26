"""
Position System
===============

Sistema de coordenadas e direções para o jogo RO.
"""

import math
from enum import Enum
from typing import Dict, Any, Tuple
from dataclasses import dataclass


class Direction(Enum):
    """Direções possíveis no jogo."""
    NORTH = 0
    NORTHEAST = 1
    EAST = 2
    SOUTHEAST = 3
    SOUTH = 4
    SOUTHWEST = 5
    WEST = 6
    NORTHWEST = 7
    
    @classmethod
    def from_coordinates(cls, from_x: int, from_y: int, to_x: int, to_y: int) -> 'Direction':
        """
        Calcula direção entre duas coordenadas.
        
        Args:
            from_x: X inicial
            from_y: Y inicial
            to_x: X final
            to_y: Y final
            
        Returns:
            Direção calculada
        """
        dx = to_x - from_x
        dy = to_y - from_y
        
        if dx == 0 and dy == 0:
            return cls.SOUTH  # Padrão
        
        # Calcula ângulo
        angle = math.atan2(dy, dx)
        # Converte para graus
        degrees = math.degrees(angle)
        # Normaliza para 0-360
        if degrees < 0:
            degrees += 360
        
        # Mapeia para direções (8 direções)
        direction_map = [
            (22.5, cls.EAST),
            (67.5, cls.SOUTHEAST),
            (112.5, cls.SOUTH),
            (157.5, cls.SOUTHWEST),
            (202.5, cls.WEST),
            (247.5, cls.NORTHWEST),
            (292.5, cls.NORTH),
            (337.5, cls.NORTHEAST),
            (360, cls.EAST)
        ]
        
        for max_angle, direction in direction_map:
            if degrees <= max_angle:
                return direction
        
        return cls.EAST  # Fallback
    
    def to_offset(self) -> Tuple[int, int]:
        """
        Converte direção para offset de coordenadas.
        
        Returns:
            Tuple (dx, dy)
        """
        offsets = {
            Direction.NORTH: (0, -1),
            Direction.NORTHEAST: (1, -1),
            Direction.EAST: (1, 0),
            Direction.SOUTHEAST: (1, 1),
            Direction.SOUTH: (0, 1),
            Direction.SOUTHWEST: (-1, 1),
            Direction.WEST: (-1, 0),
            Direction.NORTHWEST: (-1, -1)
        }
        return offsets.get(self, (0, 0))


@dataclass
class Position:
    """
    Representa uma posição no mapa.
    
    Coordenadas no RO:
    - X: horizontal (0 = esquerda, aumenta para direita)
    - Y: vertical (0 = topo, aumenta para baixo)
    """
    
    x: int = 0
    y: int = 0
    
    def distance_to(self, other: 'Position') -> float:
        """
        Calcula distância euclidiana para outra posição.
        
        Args:
            other: Outra posição
            
        Returns:
            Distância em células
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def manhattan_distance_to(self, other: 'Position') -> int:
        """
        Calcula distância Manhattan para outra posição.
        
        Args:
            other: Outra posição
            
        Returns:
            Distância Manhattan
        """
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def direction_to(self, other: 'Position') -> Direction:
        """
        Calcula direção para outra posição.
        
        Args:
            other: Posição de destino
            
        Returns:
            Direção para o destino
        """
        return Direction.from_coordinates(self.x, self.y, other.x, other.y)
    
    def move_in_direction(self, direction: Direction, distance: int = 1) -> 'Position':
        """
        Move na direção especificada.
        
        Args:
            direction: Direção do movimento
            distance: Distância a mover
            
        Returns:
            Nova posição
        """
        dx, dy = direction.to_offset()
        return Position(
            self.x + dx * distance,
            self.y + dy * distance
        )
    
    def is_adjacent_to(self, other: 'Position') -> bool:
        """
        Verifica se está adjacente a outra posição.
        
        Args:
            other: Outra posição
            
        Returns:
            True se adjacente
        """
        return self.manhattan_distance_to(other) == 1
    
    def is_diagonal_to(self, other: 'Position') -> bool:
        """
        Verifica se está na diagonal de outra posição.
        
        Args:
            other: Outra posição
            
        Returns:
            True se diagonal
        """
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        return dx == 1 and dy == 1
    
    def is_in_range(self, other: 'Position', range_: int) -> bool:
        """
        Verifica se está no alcance de outra posição.
        
        Args:
            other: Outra posição
            range_: Alcance em células
            
        Returns:
            True se no alcance
        """
        return self.distance_to(other) <= range_
    
    def copy(self) -> 'Position':
        """
        Cria uma cópia da posição.
        
        Returns:
            Nova instância com mesmas coordenadas
        """
        return Position(self.x, self.y)
    
    def to_tuple(self) -> Tuple[int, int]:
        """
        Converte para tupla.
        
        Returns:
            Tuple (x, y)
        """
        return (self.x, self.y)
    
    def to_dict(self) -> Dict[str, int]:
        """
        Converte para dicionário.
        
        Returns:
            Dicionário com x e y
        """
        return {'x': self.x, 'y': self.y}
    
    @classmethod
    def from_tuple(cls, coords: Tuple[int, int]) -> 'Position':
        """
        Cria posição a partir de tupla.
        
        Args:
            coords: Tuple (x, y)
            
        Returns:
            Nova posição
        """
        return cls(coords[0], coords[1])
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Position':
        """
        Cria posição a partir de dicionário.
        
        Args:
            data: Dicionário com x e y
            
        Returns:
            Nova posição
        """
        return cls(data.get('x', 0), data.get('y', 0))
    
    def __add__(self, other: 'Position') -> 'Position':
        """Soma duas posições."""
        return Position(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Position') -> 'Position':
        """Subtrai duas posições."""
        return Position(self.x - other.x, self.y - other.y)
    
    def __eq__(self, other: object) -> bool:
        """Verifica igualdade."""
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y
    
    def __hash__(self) -> int:
        """Hash da posição."""
        return hash((self.x, self.y))
    
    def __str__(self) -> str:
        """Representação string."""
        return f"({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        """Representação detalhada."""
        return f"Position(x={self.x}, y={self.y})"


class Area:
    """
    Representa uma área retangular no mapa.
    """
    
    def __init__(self, x1: int, y1: int, x2: int, y2: int):
        """
        Inicializa área.
        
        Args:
            x1: X mínimo
            y1: Y mínimo
            x2: X máximo
            y2: Y máximo
        """
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
    
    def contains(self, pos: Position) -> bool:
        """
        Verifica se contém uma posição.
        
        Args:
            pos: Posição a verificar
            
        Returns:
            True se contém
        """
        return (self.x1 <= pos.x <= self.x2 and 
                self.y1 <= pos.y <= self.y2)
    
    def center(self) -> Position:
        """
        Retorna centro da área.
        
        Returns:
            Posição central
        """
        return Position(
            (self.x1 + self.x2) // 2,
            (self.y1 + self.y2) // 2
        )
    
    def width(self) -> int:
        """Retorna largura da área."""
        return self.x2 - self.x1 + 1
    
    def height(self) -> int:
        """Retorna altura da área."""
        return self.y2 - self.y1 + 1
    
    def area(self) -> int:
        """Retorna área total."""
        return self.width() * self.height()
    
    def __str__(self) -> str:
        """Representação string."""
        return f"Area({self.x1},{self.y1} to {self.x2},{self.y2})" 