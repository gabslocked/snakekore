"""
Event Class
===========

Classe base para eventos do sistema.
"""

from typing import Any, Dict
from datetime import datetime


class Event:
    """
    Classe base para eventos.
    
    Representa um evento que ocorreu no sistema.
    """
    
    def __init__(self, name: str, *args, **kwargs):
        """
        Inicializa o evento.
        
        Args:
            name: Nome do evento
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
        """
        self.name = name
        self.timestamp = datetime.now()
        self.args = args
        self.kwargs = kwargs
        self.cancelled = False
        self.data: Dict[str, Any] = {}
    
    def cancel(self) -> None:
        """Cancela o evento."""
        self.cancelled = True
    
    def is_cancelled(self) -> bool:
        """
        Verifica se o evento foi cancelado.
        
        Returns:
            True se cancelado
        """
        return self.cancelled
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor dos dados do evento.
        
        Args:
            key: Chave
            default: Valor padrão
            
        Returns:
            Valor
        """
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Define um valor nos dados do evento.
        
        Args:
            key: Chave
            value: Valor
        """
        self.data[key] = value
    
    def __repr__(self) -> str:
        """Representação string do evento."""
        return f"Event(name='{self.name}', timestamp={self.timestamp})" 