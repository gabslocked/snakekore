"""
Base Plugin
===========

Classe base para todos os plugins do PythonKore.
"""

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

from core.logging.logger import Logger
from core.events.event_bus import EventBus


class PluginStatus(Enum):
    """Status do plugin."""
    UNLOADED = "unloaded"        # Não carregado
    LOADING = "loading"          # Carregando
    LOADED = "loaded"            # Carregado
    ACTIVE = "active"            # Ativo
    INACTIVE = "inactive"        # Inativo
    ERROR = "error"              # Erro
    DISABLED = "disabled"        # Desabilitado


class PluginType(Enum):
    """Tipos de plugins."""
    CORE = "core"                # Plugin core do sistema
    AI = "ai"                    # Plugin de AI
    INTERFACE = "interface"      # Plugin de interface
    NETWORK = "network"          # Plugin de rede
    UTILITY = "utility"          # Plugin utilitário
    GAME = "game"               # Plugin específico do jogo
    CUSTOM = "custom"           # Plugin customizado


@dataclass
class PluginInfo:
    """
    Informações do plugin.
    """
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str]
    min_pythonkore_version: str
    homepage: str = ""
    license: str = "MIT"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class PluginConfig:
    """
    Configuração do plugin.
    """
    
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.config: Dict[str, Any] = {}
        self.defaults: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor de configuração."""
        return self.config.get(key, self.defaults.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """Define valor de configuração."""
        self.config[key] = value
    
    def update(self, config: Dict[str, Any]) -> None:
        """Atualiza configuração."""
        self.config.update(config)
    
    def set_defaults(self, defaults: Dict[str, Any]) -> None:
        """Define valores padrão."""
        self.defaults.update(defaults)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'plugin_name': self.plugin_name,
            'config': self.config.copy(),
            'defaults': self.defaults.copy()
        }


class BasePlugin(ABC):
    """
    Classe base para todos os plugins.
    
    Define interface e comportamento comum para plugins do sistema.
    Similar ao sistema de plugins do OpenKore mas mais estruturado.
    """
    
    def __init__(self,
                 logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None):
        """
        Inicializa plugin base.
        
        Args:
            logger: Logger personalizado
            event_bus: Bus de eventos
        """
        # Sistema
        self.logger = logger or Logger(level="INFO")
        self.event_bus = event_bus
        
        # Informações do plugin (deve ser definido pela subclasse)
        self.info: Optional[PluginInfo] = None
        
        # Estado
        self.status = PluginStatus.UNLOADED
        self.loaded_at: Optional[float] = None
        self.activated_at: Optional[float] = None
        self.error_message = ""
        
        # Configuração
        self.config = PluginConfig(self.__class__.__name__)
        
        # Hooks e callbacks
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.command_handlers: Dict[str, Callable] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        
        # Recursos
        self.plugin_dir: Optional[Path] = None
        self.data_dir: Optional[Path] = None
        
        # Dependências
        self.dependencies: List[str] = []
        self.dependents: List[str] = []
        
        # Inicialização
        self._setup_plugin_info()
        self._setup_default_config()
    
    @abstractmethod
    def _setup_plugin_info(self) -> None:
        """
        Configura informações do plugin.
        
        Deve ser implementado pela subclasse para definir self.info.
        """
        pass
    
    def _setup_default_config(self) -> None:
        """
        Configura valores padrão de configuração.
        
        Pode ser sobrescrito pela subclasse.
        """
        self.config.set_defaults({
            'enabled': True,
            'auto_load': True,
            'debug': False
        })
    
    # Métodos do ciclo de vida do plugin
    def load(self) -> bool:
        """
        Carrega o plugin.
        
        Returns:
            True se carregado com sucesso
        """
        try:
            self.status = PluginStatus.LOADING
            self.logger.info(f"Carregando plugin: {self.get_name()}")
            
            # Verifica dependências
            if not self._check_dependencies():
                self.status = PluginStatus.ERROR
                self.error_message = "Dependências não atendidas"
                return False
            
            # Chama método de carregamento personalizado
            if not self.on_load():
                self.status = PluginStatus.ERROR
                self.error_message = "Falha no carregamento personalizado"
                return False
            
            self.status = PluginStatus.LOADED
            self.loaded_at = time.time()
            
            self.logger.info(f"Plugin carregado: {self.get_name()}")
            
            if self.event_bus:
                self.event_bus.emit('plugin_loaded', plugin=self)
            
            return True
            
        except Exception as e:
            self.status = PluginStatus.ERROR
            self.error_message = str(e)
            self.logger.error(f"Erro ao carregar plugin {self.get_name()}: {e}")
            return False
    
    def activate(self) -> bool:
        """
        Ativa o plugin.
        
        Returns:
            True se ativado com sucesso
        """
        if self.status != PluginStatus.LOADED:
            self.logger.warning(f"Plugin {self.get_name()} não está carregado")
            return False
        
        try:
            self.logger.info(f"Ativando plugin: {self.get_name()}")
            
            # Registra handlers de eventos
            self._register_event_handlers()
            
            # Registra comandos
            self._register_commands()
            
            # Chama método de ativação personalizado
            if not self.on_activate():
                self.logger.error(f"Falha na ativação personalizada: {self.get_name()}")
                return False
            
            self.status = PluginStatus.ACTIVE
            self.activated_at = time.time()
            
            self.logger.info(f"Plugin ativado: {self.get_name()}")
            
            if self.event_bus:
                self.event_bus.emit('plugin_activated', plugin=self)
            
            return True
            
        except Exception as e:
            self.status = PluginStatus.ERROR
            self.error_message = str(e)
            self.logger.error(f"Erro ao ativar plugin {self.get_name()}: {e}")
            return False
    
    def deactivate(self) -> bool:
        """
        Desativa o plugin.
        
        Returns:
            True se desativado com sucesso
        """
        if self.status != PluginStatus.ACTIVE:
            return True
        
        try:
            self.logger.info(f"Desativando plugin: {self.get_name()}")
            
            # Chama método de desativação personalizado
            self.on_deactivate()
            
            # Remove handlers de eventos
            self._unregister_event_handlers()
            
            # Remove comandos
            self._unregister_commands()
            
            self.status = PluginStatus.INACTIVE
            
            self.logger.info(f"Plugin desativado: {self.get_name()}")
            
            if self.event_bus:
                self.event_bus.emit('plugin_deactivated', plugin=self)
            
            return True
            
        except Exception as e:
            self.status = PluginStatus.ERROR
            self.error_message = str(e)
            self.logger.error(f"Erro ao desativar plugin {self.get_name()}: {e}")
            return False
    
    def unload(self) -> bool:
        """
        Descarrega o plugin.
        
        Returns:
            True se descarregado com sucesso
        """
        try:
            # Desativa primeiro se estiver ativo
            if self.status == PluginStatus.ACTIVE:
                self.deactivate()
            
            self.logger.info(f"Descarregando plugin: {self.get_name()}")
            
            # Chama método de descarregamento personalizado
            self.on_unload()
            
            self.status = PluginStatus.UNLOADED
            self.loaded_at = None
            self.activated_at = None
            
            self.logger.info(f"Plugin descarregado: {self.get_name()}")
            
            if self.event_bus:
                self.event_bus.emit('plugin_unloaded', plugin=self)
            
            return True
            
        except Exception as e:
            self.status = PluginStatus.ERROR
            self.error_message = str(e)
            self.logger.error(f"Erro ao descarregar plugin {self.get_name()}: {e}")
            return False
    
    # Métodos que podem ser sobrescritos
    def on_load(self) -> bool:
        """
        Chamado quando o plugin é carregado.
        
        Returns:
            True se carregamento foi bem-sucedido
        """
        return True
    
    def on_activate(self) -> bool:
        """
        Chamado quando o plugin é ativado.
        
        Returns:
            True se ativação foi bem-sucedida
        """
        return True
    
    def on_deactivate(self) -> None:
        """Chamado quando o plugin é desativado."""
        pass
    
    def on_unload(self) -> None:
        """Chamado quando o plugin é descarregado."""
        pass
    
    def on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """
        Chamado quando configuração muda.
        
        Args:
            key: Chave da configuração
            old_value: Valor anterior
            new_value: Novo valor
        """
        pass
    
    # Gerenciamento de eventos
    def add_event_handler(self, event_name: str, handler: Callable) -> None:
        """
        Adiciona handler de evento.
        
        Args:
            event_name: Nome do evento
            handler: Função handler
        """
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        
        self.event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable) -> None:
        """Remove handler de evento."""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    def _register_event_handlers(self) -> None:
        """Registra handlers no event bus."""
        if not self.event_bus:
            return
        
        for event_name, handlers in self.event_handlers.items():
            for handler in handlers:
                self.event_bus.subscribe(event_name, handler)
    
    def _unregister_event_handlers(self) -> None:
        """Remove handlers do event bus."""
        if not self.event_bus:
            return
        
        for event_name, handlers in self.event_handlers.items():
            for handler in handlers:
                self.event_bus.unsubscribe(event_name, handler)
    
    # Gerenciamento de comandos
    def add_command(self, command: str, handler: Callable, help_text: str = "") -> None:
        """
        Adiciona comando.
        
        Args:
            command: Nome do comando
            handler: Função handler
            help_text: Texto de ajuda
        """
        self.command_handlers[command] = {
            'handler': handler,
            'help': help_text,
            'plugin': self.get_name()
        }
    
    def remove_command(self, command: str) -> None:
        """Remove comando."""
        if command in self.command_handlers:
            del self.command_handlers[command]
    
    def _register_commands(self) -> None:
        """Registra comandos no sistema."""
        # TODO: Integrar com sistema de comandos
        pass
    
    def _unregister_commands(self) -> None:
        """Remove comandos do sistema."""
        # TODO: Integrar com sistema de comandos
        pass
    
    # Hooks
    def add_hook(self, hook_name: str, handler: Callable) -> None:
        """
        Adiciona hook.
        
        Args:
            hook_name: Nome do hook
            handler: Função handler
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        self.hooks[hook_name].append(handler)
    
    def remove_hook(self, hook_name: str, handler: Callable) -> None:
        """Remove hook."""
        if hook_name in self.hooks:
            try:
                self.hooks[hook_name].remove(handler)
            except ValueError:
                pass
    
    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Chama hooks.
        
        Args:
            hook_name: Nome do hook
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            Lista de resultados dos hooks
        """
        results = []
        
        if hook_name in self.hooks:
            for handler in self.hooks[hook_name]:
                try:
                    result = handler(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Erro no hook {hook_name}: {e}")
        
        return results
    
    # Verificações e validações
    def _check_dependencies(self) -> bool:
        """Verifica se dependências estão atendidas."""
        # TODO: Implementar verificação de dependências
        return True
    
    def is_compatible(self, pythonkore_version: str) -> bool:
        """
        Verifica compatibilidade com versão do PythonKore.
        
        Args:
            pythonkore_version: Versão do PythonKore
            
        Returns:
            True se compatível
        """
        if not self.info:
            return True
        
        # TODO: Implementar verificação de versão semântica
        return True
    
    # Informações e status
    def get_name(self) -> str:
        """Obtém nome do plugin."""
        return self.info.name if self.info else self.__class__.__name__
    
    def get_version(self) -> str:
        """Obtém versão do plugin."""
        return self.info.version if self.info else "unknown"
    
    def get_description(self) -> str:
        """Obtém descrição do plugin."""
        return self.info.description if self.info else ""
    
    def get_uptime(self) -> float:
        """Obtém tempo ativo em segundos."""
        if self.activated_at:
            return time.time() - self.activated_at
        return 0.0
    
    def is_active(self) -> bool:
        """Verifica se plugin está ativo."""
        return self.status == PluginStatus.ACTIVE
    
    def is_loaded(self) -> bool:
        """Verifica se plugin está carregado."""
        return self.status in [PluginStatus.LOADED, PluginStatus.ACTIVE]
    
    def has_error(self) -> bool:
        """Verifica se plugin tem erro."""
        return self.status == PluginStatus.ERROR
    
    # Configuração
    def get_config(self, key: str, default: Any = None) -> Any:
        """Obtém configuração."""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """Define configuração."""
        old_value = self.config.get(key)
        self.config.set(key, value)
        
        # Notifica mudança
        self.on_config_changed(key, old_value, value)
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Atualiza configuração."""
        for key, value in config.items():
            self.set_config(key, value)
    
    # Métodos para debug/monitoramento
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte plugin para dicionário.
        
        Returns:
            Dicionário com dados do plugin
        """
        result = {
            'name': self.get_name(),
            'version': self.get_version(),
            'description': self.get_description(),
            'status': self.status.value,
            'loaded_at': self.loaded_at,
            'activated_at': self.activated_at,
            'uptime': self.get_uptime(),
            'error_message': self.error_message,
            'config': self.config.to_dict(),
            'event_handlers_count': sum(len(handlers) for handlers in self.event_handlers.values()),
            'command_handlers_count': len(self.command_handlers),
            'hooks_count': sum(len(hooks) for hooks in self.hooks.values())
        }
        
        if self.info:
            result.update({
                'author': self.info.author,
                'type': self.info.plugin_type.value,
                'dependencies': self.info.dependencies,
                'homepage': self.info.homepage,
                'license': self.info.license,
                'tags': self.info.tags
            })
        
        return result
    
    def get_summary(self) -> str:
        """Obtém resumo do plugin."""
        status_icon = {
            PluginStatus.UNLOADED: "⚫",
            PluginStatus.LOADING: "🔄",
            PluginStatus.LOADED: "🔵",
            PluginStatus.ACTIVE: "🟢",
            PluginStatus.INACTIVE: "🟡",
            PluginStatus.ERROR: "🔴",
            PluginStatus.DISABLED: "⚪"
        }.get(self.status, "❓")
        
        return f"{status_icon} {self.get_name()} v{self.get_version()} - {self.status.value}"
    
    def __str__(self) -> str:
        """Representação string."""
        return f"Plugin({self.get_name()}, {self.status.value})"
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return (f"BasePlugin(name='{self.get_name()}', "
                f"version='{self.get_version()}', "
                f"status={self.status.value})") 