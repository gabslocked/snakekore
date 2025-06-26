"""
Configuration Validators
=========================

Sistema de validação de arquivos de configuração.
"""

from typing import Dict, Any, List, Optional


class ConfigValidator:
    """Validador de configurações."""
    
    def __init__(self):
        """Inicializa o validador."""
        self.validation_rules = {
            'config.txt': self._validate_config,
            'sys.txt': self._validate_sys,
            'timeouts.txt': self._validate_timeouts,
            'mon_control.txt': self._validate_mon_control,
            'items_control.txt': self._validate_items_control,
        }
    
    def validate(self, internal_name: str, data: Dict[str, Any]) -> bool:
        """
        Valida dados de configuração.
        
        Args:
            internal_name: Nome interno do arquivo
            data: Dados a serem validados
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            if internal_name in self.validation_rules:
                return self.validation_rules[internal_name](data)
            else:
                # Validação genérica
                return self._validate_generic(data)
                
        except Exception as e:
            print(f"Erro na validação de {internal_name}: {e}")
            return False
    
    def _validate_config(self, data: Dict[str, Any]) -> bool:
        """Valida config.txt."""
        required_fields = []  # Não há campos obrigatórios
        
        # Valida tipos de dados específicos
        numeric_fields = [
            'attackAuto', 'attackAuto_party', 'attackAuto_onlyWhenSafe',
            'attackDistance', 'attackMaxDistance', 'attackMaxRouteTime',
            'attackMinPlayerDistance', 'attackMinPortalDistance',
            'attackUseWeapon', 'autoMoveOnDeath', 'autoRestart',
            'avoidGM_near', 'avoidGM_talk', 'avoidListUsers',
            'lockMap', 'lockMap_x', 'lockMap_y', 'lockMap_randX', 'lockMap_randY'
        ]
        
        for field in numeric_fields:
            if field in data:
                try:
                    if isinstance(data[field], str):
                        float(data[field])
                except (ValueError, TypeError):
                    print(f"Campo {field} deve ser numérico")
                    return False
        
        return True
    
    def _validate_sys(self, data: Dict[str, Any]) -> bool:
        """Valida sys.txt."""
        # Validação básica do sys.txt
        return True
    
    def _validate_timeouts(self, data: Dict[str, Any]) -> bool:
        """Valida timeouts.txt."""
        # Todos os valores devem ser numéricos
        for key, value in data.items():
            if not isinstance(value, (int, float)):
                print(f"Timeout {key} deve ser numérico")
                return False
            if value < 0:
                print(f"Timeout {key} não pode ser negativo")
                return False
        
        return True
    
    def _validate_mon_control(self, data: Dict[str, Any]) -> bool:
        """Valida mon_control.txt."""
        valid_actions = ['', '0', '1', '2', '3', '-1', '-2', '-3']
        
        for monster, action in data.items():
            if action not in valid_actions:
                print(f"Ação inválida para {monster}: {action}")
                return False
        
        return True
    
    def _validate_items_control(self, data: Dict[str, Any]) -> bool:
        """Valida items_control.txt."""
        valid_actions = ['', '0', '1', '2', '3', '-1']
        
        for item, action in data.items():
            if action not in valid_actions:
                print(f"Ação inválida para {item}: {action}")
                return False
        
        return True
    
    def _validate_generic(self, data: Dict[str, Any]) -> bool:
        """Validação genérica para arquivos não específicos."""
        # Por enquanto, aceita qualquer coisa
        return True 