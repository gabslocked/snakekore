"""
Math Utils
==========

Utilidades matemáticas para o PythonKore.
"""

import math
import random
from typing import List, Tuple, Union, Optional


class MathUtils:
    """
    Utilidades matemáticas.
    
    Funcionalidades:
    - Cálculos de distância
    - Interpolação
    - Estatísticas básicas
    - Funções de RO (damage, exp, etc.)
    """
    
    @staticmethod
    def distance_2d(x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calcula distância euclidiana 2D.
        
        Args:
            x1, y1: Ponto 1
            x2, y2: Ponto 2
            
        Returns:
            Distância
        """
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
        """
        Calcula distância Manhattan.
        
        Args:
            x1, y1: Ponto 1
            x2, y2: Ponto 2
            
        Returns:
            Distância Manhattan
        """
        return abs(x2 - x1) + abs(y2 - y1)
    
    @staticmethod
    def chebyshev_distance(x1: int, y1: int, x2: int, y2: int) -> int:
        """
        Calcula distância Chebyshev (xadrez).
        
        Args:
            x1, y1: Ponto 1
            x2, y2: Ponto 2
            
        Returns:
            Distância Chebyshev
        """
        return max(abs(x2 - x1), abs(y2 - y1))
    
    @staticmethod
    def angle_between_points(x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calcula ângulo entre dois pontos em radianos.
        
        Args:
            x1, y1: Ponto 1
            x2, y2: Ponto 2
            
        Returns:
            Ângulo em radianos
        """
        return math.atan2(y2 - y1, x2 - x1)
    
    @staticmethod
    def normalize_angle(angle: float) -> float:
        """
        Normaliza ângulo para [0, 2π).
        
        Args:
            angle: Ângulo em radianos
            
        Returns:
            Ângulo normalizado
        """
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle
    
    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        """
        Interpolação linear.
        
        Args:
            a: Valor inicial
            b: Valor final
            t: Fator (0.0 a 1.0)
            
        Returns:
            Valor interpolado
        """
        return a + (b - a) * t
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """
        Limita valor entre min e max.
        
        Args:
            value: Valor a limitar
            min_val: Valor mínimo
            max_val: Valor máximo
            
        Returns:
            Valor limitado
        """
        return max(min_val, min(value, max_val))
    
    @staticmethod
    def percentage(value: float, total: float) -> float:
        """
        Calcula percentual.
        
        Args:
            value: Valor
            total: Total
            
        Returns:
            Percentual (0.0 a 100.0)
        """
        if total == 0:
            return 0.0
        return (value / total) * 100.0
    
    @staticmethod
    def average(values: List[Union[int, float]]) -> float:
        """
        Calcula média.
        
        Args:
            values: Lista de valores
            
        Returns:
            Média
        """
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    @staticmethod
    def median(values: List[Union[int, float]]) -> float:
        """
        Calcula mediana.
        
        Args:
            values: Lista de valores
            
        Returns:
            Mediana
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]
    
    @staticmethod
    def standard_deviation(values: List[Union[int, float]]) -> float:
        """
        Calcula desvio padrão.
        
        Args:
            values: Lista de valores
            
        Returns:
            Desvio padrão
        """
        if len(values) < 2:
            return 0.0
        
        avg = MathUtils.average(values)
        variance = sum((x - avg) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    @staticmethod
    def random_range(min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
        """
        Gera número aleatório no intervalo.
        
        Args:
            min_val: Valor mínimo
            max_val: Valor máximo
            
        Returns:
            Número aleatório
        """
        if isinstance(min_val, int) and isinstance(max_val, int):
            return random.randint(min_val, max_val)
        else:
            return random.uniform(min_val, max_val)
    
    @staticmethod
    def random_bool(probability: float = 0.5) -> bool:
        """
        Gera booleano aleatório.
        
        Args:
            probability: Probabilidade de True (0.0 a 1.0)
            
        Returns:
            Booleano aleatório
        """
        return random.random() < probability
    
    @staticmethod
    def weighted_choice(choices: List[Tuple[any, float]]) -> any:
        """
        Escolha aleatória ponderada.
        
        Args:
            choices: Lista de (item, peso)
            
        Returns:
            Item escolhido
        """
        if not choices:
            return None
        
        total_weight = sum(weight for _, weight in choices)
        if total_weight <= 0:
            return random.choice([item for item, _ in choices])
        
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for item, weight in choices:
            current_weight += weight
            if r <= current_weight:
                return item
        
        return choices[-1][0]  # Fallback
    
    # Funções específicas do RO
    @staticmethod
    def calculate_exp_needed(current_level: int, target_level: int, base_exp_table: List[int]) -> int:
        """
        Calcula EXP necessária para subir de nível.
        
        Args:
            current_level: Nível atual
            target_level: Nível alvo
            base_exp_table: Tabela de EXP base
            
        Returns:
            EXP necessária
        """
        if target_level <= current_level or target_level >= len(base_exp_table):
            return 0
        
        total_exp = 0
        for level in range(current_level, target_level):
            if level < len(base_exp_table):
                total_exp += base_exp_table[level]
        
        return total_exp
    
    @staticmethod
    def calculate_damage_variance(base_damage: int, variance_percent: float = 5.0) -> int:
        """
        Calcula variação de dano.
        
        Args:
            base_damage: Dano base
            variance_percent: Percentual de variação
            
        Returns:
            Dano com variação
        """
        variance = base_damage * (variance_percent / 100.0)
        return int(base_damage + random.uniform(-variance, variance))
    
    @staticmethod
    def calculate_hit_rate(accuracy: int, flee: int) -> float:
        """
        Calcula taxa de acerto.
        
        Args:
            accuracy: Precisão do atacante
            flee: Esquiva do defensor
            
        Returns:
            Taxa de acerto (0.0 a 1.0)
        """
        if accuracy <= 0:
            return 0.0
        
        hit_rate = (accuracy - flee) / accuracy
        return MathUtils.clamp(hit_rate, 0.05, 0.95)  # Min 5%, Max 95%
    
    @staticmethod
    def calculate_critical_rate(luk: int, critical_bonus: int = 0) -> float:
        """
        Calcula taxa de crítico.
        
        Args:
            luk: Atributo LUK
            critical_bonus: Bônus adicional de crítico
            
        Returns:
            Taxa de crítico (0.0 a 1.0)
        """
        base_crit = luk * 0.3  # Fórmula simplificada
        total_crit = base_crit + critical_bonus
        return MathUtils.clamp(total_crit / 100.0, 0.01, 0.5)  # Min 1%, Max 50%
    
    @staticmethod
    def calculate_aspd(agi: int, dex: int, weapon_delay: int) -> float:
        """
        Calcula ASPD (Attack Speed).
        
        Args:
            agi: Atributo AGI
            dex: Atributo DEX
            weapon_delay: Delay da arma
            
        Returns:
            ASPD
        """
        if weapon_delay <= 0:
            return 200.0  # ASPD máximo
        
        # Fórmula simplificada do RO
        aspd_bonus = (agi + dex) * 0.5
        base_aspd = 200 - weapon_delay
        
        return MathUtils.clamp(base_aspd + aspd_bonus, 100, 200)
    
    @staticmethod
    def is_in_range(x1: int, y1: int, x2: int, y2: int, range_distance: int) -> bool:
        """
        Verifica se está no alcance.
        
        Args:
            x1, y1: Posição 1
            x2, y2: Posição 2
            range_distance: Alcance
            
        Returns:
            True se estiver no alcance
        """
        return MathUtils.chebyshev_distance(x1, y1, x2, y2) <= range_distance
    
    @staticmethod
    def round_to_nearest(value: float, nearest: float) -> float:
        """
        Arredonda para o valor mais próximo.
        
        Args:
            value: Valor a arredondar
            nearest: Valor de referência
            
        Returns:
            Valor arredondado
        """
        return round(value / nearest) * nearest 