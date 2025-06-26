"""
Coordinate System
=================

Sistema de coordenadas e direções para navegação no mundo RO.
"""

import math
from enum import Enum
from typing import Tuple, List, Optional, Union
from dataclasses import dataclass


class Direction(Enum):
    """
    Direções de movimento (8 direções).
    
    Compatível com o sistema do OpenKore.
    """
    NORTH = 0      # Norte
    NORTHEAST = 1  # Nordeste
    EAST = 2       # Leste
    SOUTHEAST = 3  # Sudeste
    SOUTH = 4      # Sul
    SOUTHWEST = 5  # Sudoeste
    WEST = 6       # Oeste
    NORTHWEST = 7  # Noroeste
    
    @classmethod
    def from_delta(cls, dx: int, dy: int) -> Optional['Direction']:
        """
        Obtém direção a partir de delta x,y.
        
        Args:
            dx: Delta X
            dy: Delta Y
            
        Returns:
            Direção correspondente ou None
        """
        if dx == 0 and dy == -1:  # Norte
            return cls.NORTH
        elif dx == 1 and dy == -1:  # Nordeste
            return cls.NORTHEAST
        elif dx == 1 and dy == 0:  # Leste
            return cls.EAST
        elif dx == 1 and dy == 1:  # Sudeste
            return cls.SOUTHEAST
        elif dx == 0 and dy == 1:  # Sul
            return cls.SOUTH
        elif dx == -1 and dy == 1:  # Sudoeste
            return cls.SOUTHWEST
        elif dx == -1 and dy == 0:  # Oeste
            return cls.WEST
        elif dx == -1 and dy == -1:  # Noroeste
            return cls.NORTHWEST
        else:
            return None
    
    def to_delta(self) -> Tuple[int, int]:
        """
        Converte direção para delta x,y.
        
        Returns:
            Tupla (dx, dy)
        """
        deltas = {
            Direction.NORTH: (0, -1),
            Direction.NORTHEAST: (1, -1),
            Direction.EAST: (1, 0),
            Direction.SOUTHEAST: (1, 1),
            Direction.SOUTH: (0, 1),
            Direction.SOUTHWEST: (-1, 1),
            Direction.WEST: (-1, 0),
            Direction.NORTHWEST: (-1, -1)
        }
        return deltas[self]
    
    def opposite(self) -> 'Direction':
        """Obtém direção oposta."""
        opposite_map = {
            Direction.NORTH: Direction.SOUTH,
            Direction.NORTHEAST: Direction.SOUTHWEST,
            Direction.EAST: Direction.WEST,
            Direction.SOUTHEAST: Direction.NORTHWEST,
            Direction.SOUTH: Direction.NORTH,
            Direction.SOUTHWEST: Direction.NORTHEAST,
            Direction.WEST: Direction.EAST,
            Direction.NORTHWEST: Direction.SOUTHEAST
        }
        return opposite_map[self]
    
    def is_diagonal(self) -> bool:
        """Verifica se é direção diagonal."""
        return self in [Direction.NORTHEAST, Direction.SOUTHEAST,
                       Direction.SOUTHWEST, Direction.NORTHWEST]
    
    def to_degrees(self) -> float:
        """Converte para graus (0° = Norte)."""
        return self.value * 45.0
    
    def to_radians(self) -> float:
        """Converte para radianos."""
        return math.radians(self.to_degrees())


@dataclass(frozen=True)
class Coordinate:
    """
    Coordenada no mundo RO.
    
    Sistema de coordenadas:
    - X: 0 = oeste, aumenta para leste
    - Y: 0 = norte, aumenta para sul
    """
    x: int
    y: int
    
    def __post_init__(self):
        """Validação das coordenadas."""
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise ValueError("Coordenadas devem ser inteiros")
        
        if self.x < 0 or self.y < 0:
            raise ValueError("Coordenadas devem ser não-negativas")
    
    def distance_to(self, other: 'Coordinate') -> float:
        """
        Calcula distância euclidiana para outra coordenada.
        
        Args:
            other: Coordenada de destino
            
        Returns:
            Distância em células
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def manhattan_distance_to(self, other: 'Coordinate') -> int:
        """
        Calcula distância Manhattan para outra coordenada.
        
        Args:
            other: Coordenada de destino
            
        Returns:
            Distância Manhattan
        """
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def chebyshev_distance_to(self, other: 'Coordinate') -> int:
        """
        Calcula distância Chebyshev (xadrez) para outra coordenada.
        
        Args:
            other: Coordenada de destino
            
        Returns:
            Distância Chebyshev
        """
        return max(abs(self.x - other.x), abs(self.y - other.y))
    
    def direction_to(self, other: 'Coordinate') -> Optional[Direction]:
        """
        Obtém direção para outra coordenada.
        
        Args:
            other: Coordenada de destino
            
        Returns:
            Direção ou None se for a mesma coordenada
        """
        if self == other:
            return None
        
        dx = other.x - self.x
        dy = other.y - self.y
        
        # Normaliza para -1, 0, 1
        if dx > 0:
            dx = 1
        elif dx < 0:
            dx = -1
        
        if dy > 0:
            dy = 1
        elif dy < 0:
            dy = -1
        
        return Direction.from_delta(dx, dy)
    
    def move(self, direction: Direction, steps: int = 1) -> 'Coordinate':
        """
        Move na direção especificada.
        
        Args:
            direction: Direção do movimento
            steps: Número de passos
            
        Returns:
            Nova coordenada
        """
        dx, dy = direction.to_delta()
        new_x = max(0, self.x + dx * steps)
        new_y = max(0, self.y + dy * steps)
        return Coordinate(new_x, new_y)
    
    def neighbors(self, diagonal: bool = True) -> List['Coordinate']:
        """
        Obtém coordenadas vizinhas.
        
        Args:
            diagonal: Incluir vizinhos diagonais
            
        Returns:
            Lista de coordenadas vizinhas
        """
        neighbors = []
        
        directions = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        if diagonal:
            directions.extend([Direction.NORTHEAST, Direction.SOUTHEAST,
                             Direction.SOUTHWEST, Direction.NORTHWEST])
        
        for direction in directions:
            try:
                neighbor = self.move(direction)
                neighbors.append(neighbor)
            except ValueError:
                # Coordenada inválida (negativa)
                pass
        
        return neighbors
    
    def is_adjacent_to(self, other: 'Coordinate', diagonal: bool = True) -> bool:
        """
        Verifica se é adjacente a outra coordenada.
        
        Args:
            other: Coordenada a verificar
            diagonal: Considerar adjacência diagonal
            
        Returns:
            True se for adjacente
        """
        distance = self.chebyshev_distance_to(other)
        
        if diagonal:
            return distance == 1
        else:
            return distance == 1 and self.manhattan_distance_to(other) == 1
    
    def within_range(self, other: 'Coordinate', range_distance: int) -> bool:
        """
        Verifica se está dentro do alcance de outra coordenada.
        
        Args:
            other: Coordenada de referência
            range_distance: Distância máxima
            
        Returns:
            True se estiver no alcance
        """
        return self.chebyshev_distance_to(other) <= range_distance
    
    def to_tuple(self) -> Tuple[int, int]:
        """Converte para tupla."""
        return (self.x, self.y)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {'x': self.x, 'y': self.y}
    
    @classmethod
    def from_tuple(cls, coords: Tuple[int, int]) -> 'Coordinate':
        """
        Cria coordenada a partir de tupla.
        
        Args:
            coords: Tupla (x, y)
            
        Returns:
            Nova coordenada
        """
        return cls(coords[0], coords[1])
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Coordinate':
        """
        Cria coordenada a partir de dicionário.
        
        Args:
            data: Dicionário com 'x' e 'y'
            
        Returns:
            Nova coordenada
        """
        return cls(data['x'], data['y'])
    
    def __str__(self) -> str:
        """Representação string."""
        return f"({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return f"Coordinate(x={self.x}, y={self.y})"
    
    def __add__(self, other: Union['Coordinate', Tuple[int, int]]) -> 'Coordinate':
        """Soma coordenadas."""
        if isinstance(other, tuple):
            other = Coordinate.from_tuple(other)
        return Coordinate(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: Union['Coordinate', Tuple[int, int]]) -> 'Coordinate':
        """Subtrai coordenadas."""
        if isinstance(other, tuple):
            other = Coordinate.from_tuple(other)
        new_x = max(0, self.x - other.x)
        new_y = max(0, self.y - other.y)
        return Coordinate(new_x, new_y)
    
    def __mul__(self, scalar: int) -> 'Coordinate':
        """Multiplica coordenada por escalar."""
        return Coordinate(self.x * scalar, self.y * scalar)
    
    def __eq__(self, other) -> bool:
        """Igualdade."""
        if not isinstance(other, Coordinate):
            return False
        return self.x == other.x and self.y == other.y
    
    def __hash__(self) -> int:
        """Hash para uso em sets/dicts."""
        return hash((self.x, self.y))
    
    def __lt__(self, other: 'Coordinate') -> bool:
        """Comparação para ordenação."""
        return (self.x, self.y) < (other.x, other.y)


class Area:
    """
    Área retangular no mundo.
    
    Útil para definir zonas, áreas de farming, etc.
    """
    
    def __init__(self, 
                 top_left: Coordinate, 
                 bottom_right: Coordinate,
                 name: str = ""):
        """
        Inicializa área.
        
        Args:
            top_left: Coordenada superior esquerda
            bottom_right: Coordenada inferior direita
            name: Nome da área
        """
        if top_left.x > bottom_right.x or top_left.y > bottom_right.y:
            raise ValueError("Coordenadas da área inválidas")
        
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.name = name
    
    @property
    def width(self) -> int:
        """Largura da área."""
        return self.bottom_right.x - self.top_left.x + 1
    
    @property
    def height(self) -> int:
        """Altura da área."""
        return self.bottom_right.y - self.top_left.y + 1
    
    @property
    def center(self) -> Coordinate:
        """Centro da área."""
        center_x = (self.top_left.x + self.bottom_right.x) // 2
        center_y = (self.top_left.y + self.bottom_right.y) // 2
        return Coordinate(center_x, center_y)
    
    def contains(self, coord: Coordinate) -> bool:
        """
        Verifica se coordenada está dentro da área.
        
        Args:
            coord: Coordenada a verificar
            
        Returns:
            True se estiver dentro
        """
        return (self.top_left.x <= coord.x <= self.bottom_right.x and
                self.top_left.y <= coord.y <= self.bottom_right.y)
    
    def overlaps(self, other: 'Area') -> bool:
        """
        Verifica se há sobreposição com outra área.
        
        Args:
            other: Outra área
            
        Returns:
            True se houver sobreposição
        """
        return not (self.bottom_right.x < other.top_left.x or
                   other.bottom_right.x < self.top_left.x or
                   self.bottom_right.y < other.top_left.y or
                   other.bottom_right.y < self.top_left.y)
    
    def intersection(self, other: 'Area') -> Optional['Area']:
        """
        Obtém interseção com outra área.
        
        Args:
            other: Outra área
            
        Returns:
            Área de interseção ou None
        """
        if not self.overlaps(other):
            return None
        
        left = max(self.top_left.x, other.top_left.x)
        top = max(self.top_left.y, other.top_left.y)
        right = min(self.bottom_right.x, other.bottom_right.x)
        bottom = min(self.bottom_right.y, other.bottom_right.y)
        
        return Area(
            Coordinate(left, top),
            Coordinate(right, bottom),
            f"{self.name}_∩_{other.name}"
        )
    
    def all_coordinates(self) -> List[Coordinate]:
        """
        Obtém todas as coordenadas da área.
        
        Returns:
            Lista de coordenadas
        """
        coords = []
        for y in range(self.top_left.y, self.bottom_right.y + 1):
            for x in range(self.top_left.x, self.bottom_right.x + 1):
                coords.append(Coordinate(x, y))
        return coords
    
    def border_coordinates(self) -> List[Coordinate]:
        """
        Obtém coordenadas da borda da área.
        
        Returns:
            Lista de coordenadas da borda
        """
        coords = []
        
        # Borda superior e inferior
        for x in range(self.top_left.x, self.bottom_right.x + 1):
            coords.append(Coordinate(x, self.top_left.y))
            if self.height > 1:
                coords.append(Coordinate(x, self.bottom_right.y))
        
        # Borda esquerda e direita (excluindo cantos já adicionados)
        for y in range(self.top_left.y + 1, self.bottom_right.y):
            coords.append(Coordinate(self.top_left.x, y))
            if self.width > 1:
                coords.append(Coordinate(self.bottom_right.x, y))
        
        return coords
    
    def random_coordinate(self) -> Coordinate:
        """
        Obtém coordenada aleatória dentro da área.
        
        Returns:
            Coordenada aleatória
        """
        import random
        x = random.randint(self.top_left.x, self.bottom_right.x)
        y = random.randint(self.top_left.y, self.bottom_right.y)
        return Coordinate(x, y)
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            'name': self.name,
            'top_left': self.top_left.to_dict(),
            'bottom_right': self.bottom_right.to_dict(),
            'width': self.width,
            'height': self.height
        }
    
    def __str__(self) -> str:
        """Representação string."""
        name_part = f"{self.name}: " if self.name else ""
        return f"{name_part}{self.top_left} -> {self.bottom_right}"
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return f"Area('{self.name}', {self.top_left}, {self.bottom_right})"
    
    def __contains__(self, coord: Coordinate) -> bool:
        """Suporte para 'in' operator."""
        return self.contains(coord) 