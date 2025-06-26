"""
Plugin Manager
==============

Gerenciador de plugins do PythonKore.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Set
from collections import defaultdict

from base_plugin import BasePlugin, PluginStatus, PluginType
from core.logging.logger import Logger
from core.events.event_bus import EventBus


class PluginManager:
    """
    Gerenciador de plugins.
    
    Responsável por:
    - Descobrir e carregar plugins
    - Gerenciar ciclo de vida dos plugins
    - Resolver dependências
    - Fornecer API para plugins
    """
    
    def __init__(self,
                 logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None,
                 plugin_dirs: List[Path] = None):
        """
        Inicializa gerenciador de plugins.
        
        Args:
            logger: Logger para debug
            event_bus: Bus de eventos
            plugin_dirs: Diretórios de plugins
        """
        self.logger = logger or Logger(level="INFO")
        self.event_bus = event_bus
        
        # Diretórios de plugins
        self.plugin_dirs = plugin_dirs or []
        self._setup_default_plugin_dirs()
        
        # Plugins registrados
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        
        # Metadados
        self.plugin_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.plugin_dependents: Dict[str, Set[str]] = defaultdict(set)
        
        # Estado
        self.is_initialized = False
        self.auto_load_enabled = True
        self.load_order: List[str] = []
        
        # Estatísticas
        self.stats = {
            'total_discovered': 0,
            'total_loaded': 0,
            'total_active': 0,
            'total_errors': 0,
            'load_time': 0.0
        }
        
        # Hooks globais
        self.global_hooks: Dict[str, List[callable]] = defaultdict(list)
        
        self.logger.info("PluginManager inicializado")
    
    def _setup_default_plugin_dirs(self) -> None:
        """Configura diretórios padrão de plugins."""
        # Diretório builtin
        builtin_dir = Path(__file__).parent / "builtin"
        if builtin_dir.exists():
            self.plugin_dirs.append(builtin_dir)
        
        # Diretório de plugins do usuário
        user_plugins = Path.cwd() / "plugins"
        if user_plugins.exists():
            self.plugin_dirs.append(user_plugins)
    
    def add_plugin_directory(self, directory: Path) -> None:
        """
        Adiciona diretório de plugins.
        
        Args:
            directory: Diretório a adicionar
        """
        if directory.exists() and directory.is_dir():
            self.plugin_dirs.append(directory)
            self.logger.info(f"Diretório de plugins adicionado: {directory}")
        else:
            self.logger.warning(f"Diretório inválido: {directory}")
    
    def discover_plugins(self) -> List[str]:
        """
        Descobre plugins nos diretórios configurados.
        
        Returns:
            Lista de nomes de plugins descobertos
        """
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            self.logger.debug(f"Descobrindo plugins em: {plugin_dir}")
            
            # Procura arquivos .py
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue  # Ignora arquivos privados
                
                plugin_name = plugin_file.stem
                
                try:
                    plugin_class = self._load_plugin_class(plugin_file, plugin_name)
                    if plugin_class:
                        self.plugin_classes[plugin_name] = plugin_class
                        discovered.append(plugin_name)
                        self.logger.debug(f"Plugin descoberto: {plugin_name}")
                
                except Exception as e:
                    self.logger.error(f"Erro ao descobrir plugin {plugin_name}: {e}")
        
        self.stats['total_discovered'] = len(discovered)
        self.logger.info(f"Descobertos {len(discovered)} plugins")
        
        return discovered
    
    def _load_plugin_class(self, plugin_file: Path, plugin_name: str) -> Optional[Type[BasePlugin]]:
        """
        Carrega classe do plugin de um arquivo.
        
        Args:
            plugin_file: Arquivo do plugin
            plugin_name: Nome do plugin
            
        Returns:
            Classe do plugin ou None
        """
        try:
            # Carrega módulo
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Procura classe que herda de BasePlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr != BasePlugin):
                    return attr
            
            self.logger.warning(f"Nenhuma classe BasePlugin encontrada em {plugin_file}")
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar classe do plugin {plugin_name}: {e}")
            return None
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Carrega um plugin específico.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se carregado com sucesso
        """
        if plugin_name in self.plugins:
            self.logger.warning(f"Plugin já carregado: {plugin_name}")
            return True
        
        if plugin_name not in self.plugin_classes:
            self.logger.error(f"Plugin não encontrado: {plugin_name}")
            return False
        
        try:
            # Instancia plugin
            plugin_class = self.plugin_classes[plugin_name]
            plugin = plugin_class(
                logger=self.logger,
                event_bus=self.event_bus
            )
            
            # Carrega plugin
            if plugin.load():
                self.plugins[plugin_name] = plugin
                self.stats['total_loaded'] += 1
                
                # Registra dependências
                if plugin.info:
                    self.plugin_dependencies[plugin_name] = set(plugin.info.dependencies)
                    
                    # Atualiza dependents
                    for dep in plugin.info.dependencies:
                        self.plugin_dependents[dep].add(plugin_name)
                
                self.logger.info(f"Plugin carregado: {plugin_name}")
                return True
            else:
                self.logger.error(f"Falha ao carregar plugin: {plugin_name}")
                self.stats['total_errors'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao instanciar plugin {plugin_name}: {e}")
            self.stats['total_errors'] += 1
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Descarrega um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se descarregado com sucesso
        """
        if plugin_name not in self.plugins:
            self.logger.warning(f"Plugin não carregado: {plugin_name}")
            return True
        
        plugin = self.plugins[plugin_name]
        
        try:
            # Verifica dependents
            dependents = self.plugin_dependents.get(plugin_name, set())
            active_dependents = [dep for dep in dependents if self.is_plugin_active(dep)]
            
            if active_dependents:
                self.logger.warning(f"Plugin {plugin_name} tem dependents ativos: {active_dependents}")
                # Desativa dependents primeiro
                for dep in active_dependents:
                    self.deactivate_plugin(dep)
            
            # Descarrega plugin
            if plugin.unload():
                del self.plugins[plugin_name]
                self.stats['total_loaded'] -= 1
                
                # Remove dependências
                if plugin_name in self.plugin_dependencies:
                    del self.plugin_dependencies[plugin_name]
                
                # Remove de dependents
                for deps in self.plugin_dependents.values():
                    deps.discard(plugin_name)
                
                self.logger.info(f"Plugin descarregado: {plugin_name}")
                return True
            else:
                self.logger.error(f"Falha ao descarregar plugin: {plugin_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao descarregar plugin {plugin_name}: {e}")
            return False
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """
        Ativa um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se ativado com sucesso
        """
        if plugin_name not in self.plugins:
            # Tenta carregar primeiro
            if not self.load_plugin(plugin_name):
                return False
        
        plugin = self.plugins[plugin_name]
        
        # Verifica dependências
        dependencies = self.plugin_dependencies.get(plugin_name, set())
        for dep in dependencies:
            if not self.is_plugin_active(dep):
                self.logger.info(f"Ativando dependência {dep} para {plugin_name}")
                if not self.activate_plugin(dep):
                    self.logger.error(f"Falha ao ativar dependência {dep}")
                    return False
        
        # Ativa plugin
        if plugin.activate():
            self.stats['total_active'] += 1
            self.logger.info(f"Plugin ativado: {plugin_name}")
            return True
        else:
            self.logger.error(f"Falha ao ativar plugin: {plugin_name}")
            return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        Desativa um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se desativado com sucesso
        """
        if plugin_name not in self.plugins:
            return True
        
        plugin = self.plugins[plugin_name]
        
        if plugin.deactivate():
            if plugin.status == PluginStatus.INACTIVE:
                self.stats['total_active'] -= 1
            self.logger.info(f"Plugin desativado: {plugin_name}")
            return True
        else:
            self.logger.error(f"Falha ao desativar plugin: {plugin_name}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Recarrega um plugin.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            True se recarregado com sucesso
        """
        was_active = self.is_plugin_active(plugin_name)
        
        # Descarrega
        if not self.unload_plugin(plugin_name):
            return False
        
        # Redescobre
        self.discover_plugins()
        
        # Carrega novamente
        if not self.load_plugin(plugin_name):
            return False
        
        # Ativa se estava ativo
        if was_active:
            return self.activate_plugin(plugin_name)
        
        return True
    
    def load_all_plugins(self) -> int:
        """
        Carrega todos os plugins descobertos.
        
        Returns:
            Número de plugins carregados
        """
        import time
        start_time = time.time()
        
        # Descobre plugins
        discovered = self.discover_plugins()
        
        # Carrega em ordem de dependências
        loaded_count = 0
        remaining = set(discovered)
        
        while remaining:
            progress_made = False
            
            for plugin_name in list(remaining):
                # Verifica se dependências estão carregadas
                dependencies = self.plugin_dependencies.get(plugin_name, set())
                
                if dependencies.issubset(self.plugins.keys()):
                    if self.load_plugin(plugin_name):
                        loaded_count += 1
                        remaining.remove(plugin_name)
                        progress_made = True
            
            # Se não houve progresso, há dependências circulares ou não resolvidas
            if not progress_made:
                for plugin_name in remaining:
                    self.logger.error(f"Não foi possível carregar plugin {plugin_name} - dependências não resolvidas")
                break
        
        self.stats['load_time'] = time.time() - start_time
        self.logger.info(f"Carregados {loaded_count}/{len(discovered)} plugins em {self.stats['load_time']:.2f}s")
        
        return loaded_count
    
    def activate_all_plugins(self) -> int:
        """
        Ativa todos os plugins carregados.
        
        Returns:
            Número de plugins ativados
        """
        activated_count = 0
        
        # Ativa em ordem de dependências
        for plugin_name in self._get_load_order():
            if self.activate_plugin(plugin_name):
                activated_count += 1
        
        self.logger.info(f"Ativados {activated_count} plugins")
        return activated_count
    
    def _get_load_order(self) -> List[str]:
        """
        Obtém ordem de carregamento baseada em dependências.
        
        Returns:
            Lista ordenada de nomes de plugins
        """
        order = []
        visited = set()
        temp_visited = set()
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                # Dependência circular detectada
                self.logger.warning(f"Dependência circular detectada envolvendo {plugin_name}")
                return
            
            if plugin_name in visited:
                return
            
            temp_visited.add(plugin_name)
            
            # Visita dependências primeiro
            dependencies = self.plugin_dependencies.get(plugin_name, set())
            for dep in dependencies:
                if dep in self.plugins:
                    visit(dep)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            order.append(plugin_name)
        
        # Visita todos os plugins
        for plugin_name in self.plugins.keys():
            visit(plugin_name)
        
        return order
    
    # Consultas e informações
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Obtém plugin por nome."""
        return self.plugins.get(plugin_name)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Verifica se plugin está carregado."""
        return plugin_name in self.plugins
    
    def is_plugin_active(self, plugin_name: str) -> bool:
        """Verifica se plugin está ativo."""
        plugin = self.plugins.get(plugin_name)
        return plugin is not None and plugin.is_active()
    
    def get_loaded_plugins(self) -> List[str]:
        """Obtém lista de plugins carregados."""
        return list(self.plugins.keys())
    
    def get_active_plugins(self) -> List[str]:
        """Obtém lista de plugins ativos."""
        return [name for name, plugin in self.plugins.items() if plugin.is_active()]
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[str]:
        """Obtém plugins por tipo."""
        result = []
        for name, plugin in self.plugins.items():
            if plugin.info and plugin.info.plugin_type == plugin_type:
                result.append(name)
        return result
    
    def find_plugins(self, **criteria) -> List[str]:
        """
        Encontra plugins por critérios.
        
        Args:
            **criteria: Critérios de busca
            
        Returns:
            Lista de nomes de plugins
        """
        results = []
        
        for name, plugin in self.plugins.items():
            match = True
            
            for key, value in criteria.items():
                if key == 'status':
                    if plugin.status != value:
                        match = False
                        break
                elif key == 'type':
                    if not plugin.info or plugin.info.plugin_type != value:
                        match = False
                        break
                elif key == 'author':
                    if not plugin.info or plugin.info.author != value:
                        match = False
                        break
                # Adicione mais critérios conforme necessário
            
            if match:
                results.append(name)
        
        return results
    
    # Hooks globais
    def add_global_hook(self, hook_name: str, handler: callable) -> None:
        """Adiciona hook global."""
        self.global_hooks[hook_name].append(handler)
    
    def remove_global_hook(self, hook_name: str, handler: callable) -> None:
        """Remove hook global."""
        if hook_name in self.global_hooks:
            try:
                self.global_hooks[hook_name].remove(handler)
            except ValueError:
                pass
    
    def call_global_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Chama hooks globais."""
        results = []
        
        for handler in self.global_hooks.get(hook_name, []):
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Erro no hook global {hook_name}: {e}")
        
        return results
    
    # Status e estatísticas
    def get_status(self) -> Dict[str, Any]:
        """Obtém status do gerenciador."""
        return {
            'initialized': self.is_initialized,
            'plugin_dirs': [str(d) for d in self.plugin_dirs],
            'total_plugins': len(self.plugins),
            'active_plugins': len(self.get_active_plugins()),
            'stats': self.stats.copy()
        }
    
    def get_summary(self) -> List[Dict[str, Any]]:
        """Obtém resumo de todos os plugins."""
        summary = []
        
        for name, plugin in self.plugins.items():
            summary.append({
                'name': name,
                'plugin': plugin.to_dict()
            })
        
        return summary
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """Obtém grafo de dependências."""
        return {
            'dependencies': {k: list(v) for k, v in self.plugin_dependencies.items()},
            'dependents': {k: list(v) for k, v in self.plugin_dependents.items()},
            'load_order': self._get_load_order()
        }
    
    def __len__(self) -> int:
        """Número de plugins carregados."""
        return len(self.plugins)
    
    def __contains__(self, plugin_name: str) -> bool:
        """Verifica se plugin está carregado."""
        return plugin_name in self.plugins
    
    def __iter__(self):
        """Itera sobre plugins."""
        return iter(self.plugins.values())
    
    def __str__(self) -> str:
        """Representação string."""
        return f"PluginManager({len(self.plugins)} plugins, {len(self.get_active_plugins())} ativos)" 