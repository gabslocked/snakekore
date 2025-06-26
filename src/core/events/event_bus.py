"""
Event Bus System
================

Sistema de eventos assíncrono para PythonKore.
Equivalente ao sistema de hooks do OpenKore.
"""

import asyncio
import weakref
from typing import Dict, List, Callable, Any, Optional, Union
from collections import defaultdict
from event import Event


class EventBus:
    """
    Sistema de eventos assíncrono.
    
    Permite que diferentes partes do sistema se comuniquem
    através de eventos, similar ao sistema de hooks do OpenKore.
    """
    
    def __init__(self):
        """Inicializa o event bus."""
        # Dicionário de event_name -> lista de handlers
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Handlers assíncronos
        self._async_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Weak references para evitar vazamentos de memória
        self._weak_handlers: Dict[str, List] = defaultdict(list)
        
        # Lock para thread safety
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_name: str, handler: Callable, weak: bool = False) -> None:
        """
        Subscreve um handler para um evento.
        
        Args:
            event_name: Nome do evento
            handler: Função handler
            weak: Se deve usar weak reference
        """
        if asyncio.iscoroutinefunction(handler):
            if weak:
                self._weak_handlers[event_name].append(weakref.ref(handler))
            else:
                self._async_handlers[event_name].append(handler)
        else:
            if weak:
                self._weak_handlers[event_name].append(weakref.ref(handler))
            else:
                self._handlers[event_name].append(handler)
    
    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """
        Remove um handler de um evento.
        
        Args:
            event_name: Nome do evento
            handler: Função handler
        """
        # Remove de handlers síncronos
        if handler in self._handlers[event_name]:
            self._handlers[event_name].remove(handler)
        
        # Remove de handlers assíncronos
        if handler in self._async_handlers[event_name]:
            self._async_handlers[event_name].remove(handler)
        
        # Remove weak references
        self._weak_handlers[event_name] = [
            ref for ref in self._weak_handlers[event_name]
            if ref() is not None and ref() != handler
        ]
    
    def emit(self, event_name: str, *args, **kwargs) -> None:
        """
        Emite um evento síncrono.
        
        Args:
            event_name: Nome do evento
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
        """
        # Cria objeto de evento
        event = Event(event_name, *args, **kwargs)
        
        # Chama handlers síncronos
        for handler in self._handlers[event_name]:
            try:
                handler(event)
            except Exception as e:
                # TODO: Usar logger quando disponível
                print(f"Erro em handler para {event_name}: {e}")
        
        # Processa weak references
        alive_refs = []
        for ref in self._weak_handlers[event_name]:
            handler = ref()
            if handler is not None:
                try:
                    handler(event)
                    alive_refs.append(ref)
                except Exception as e:
                    print(f"Erro em weak handler para {event_name}: {e}")
        
        # Limpa weak references mortas
        self._weak_handlers[event_name] = alive_refs
    
    async def emit_async(self, event_name: str, *args, **kwargs) -> None:
        """
        Emite um evento assíncrono.
        
        Args:
            event_name: Nome do evento
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
        """
        async with self._lock:
            # Cria objeto de evento
            event = Event(event_name, *args, **kwargs)
            
            # Coleta todos os handlers
            tasks = []
            
            # Handlers assíncronos
            for handler in self._async_handlers[event_name]:
                tasks.append(asyncio.create_task(handler(event)))
            
            # Handlers síncronos (executados em thread pool)
            for handler in self._handlers[event_name]:
                task = asyncio.create_task(
                    asyncio.to_thread(handler, event)
                )
                tasks.append(task)
            
            # Processa weak references
            alive_refs = []
            for ref in self._weak_handlers[event_name]:
                handler = ref()
                if handler is not None:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(asyncio.create_task(handler(event)))
                    else:
                        task = asyncio.create_task(
                            asyncio.to_thread(handler, event)
                        )
                        tasks.append(task)
                    alive_refs.append(ref)
            
            # Limpa weak references mortas
            self._weak_handlers[event_name] = alive_refs
            
            # Executa todos os handlers
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def on(self, event_name: str, weak: bool = False):
        """
        Decorator para subscrever handlers.
        
        Args:
            event_name: Nome do evento
            weak: Se deve usar weak reference
            
        Returns:
            Decorator
        """
        def decorator(handler: Callable) -> Callable:
            self.subscribe(event_name, handler, weak)
            return handler
        return decorator
    
    def once(self, event_name: str):
        """
        Decorator para handlers que executam apenas uma vez.
        
        Args:
            event_name: Nome do evento
            
        Returns:
            Decorator
        """
        def decorator(handler: Callable) -> Callable:
            def wrapper(event: Event):
                try:
                    handler(event)
                finally:
                    self.unsubscribe(event_name, wrapper)
            
            self.subscribe(event_name, wrapper)
            return handler
        return decorator
    
    def get_handler_count(self, event_name: str) -> int:
        """
        Retorna o número de handlers para um evento.
        
        Args:
            event_name: Nome do evento
            
        Returns:
            Número de handlers
        """
        count = len(self._handlers[event_name])
        count += len(self._async_handlers[event_name])
        
        # Conta weak references vivas
        alive_count = sum(
            1 for ref in self._weak_handlers[event_name]
            if ref() is not None
        )
        count += alive_count
        
        return count
    
    def clear_handlers(self, event_name: Optional[str] = None) -> None:
        """
        Limpa handlers.
        
        Args:
            event_name: Nome do evento (None = todos)
        """
        if event_name:
            self._handlers[event_name].clear()
            self._async_handlers[event_name].clear()
            self._weak_handlers[event_name].clear()
        else:
            self._handlers.clear()
            self._async_handlers.clear()
            self._weak_handlers.clear()


# Instância global
event_bus = EventBus() 