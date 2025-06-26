"""
Auto Response Plugin
===================

Plugin para respostas automáticas no chat.
Similar ao autoResponse do OpenKore.
"""

import re
import time
from typing import Dict, List, Any, Optional

from base_plugin import BasePlugin, PluginInfo, PluginType


class AutoResponsePlugin(BasePlugin):
    """
    Plugin de resposta automática.
    
    Funcionalidades:
    - Resposta automática a mensagens no chat
    - Suporte a regex
    - Cooldown entre respostas
    - Blacklist de players
    """
    
    def _setup_plugin_info(self) -> None:
        """Configura informações do plugin."""
        self.info = PluginInfo(
            name="AutoResponse",
            version="1.0.0",
            description="Resposta automática a mensagens no chat",
            author="PythonKore Team",
            plugin_type=PluginType.GAME,
            dependencies=[],
            min_pythonkore_version="1.0.0",
            tags=["chat", "automation", "response"]
        )
    
    def _setup_default_config(self) -> None:
        """Configura valores padrão."""
        super()._setup_default_config()
        
        self.config.set_defaults({
            'enabled': True,
            'cooldown': 5,  # Cooldown em segundos
            'respond_to_pm': True,
            'respond_to_guild': False,
            'respond_to_party': False,
            'blacklist': [],
            'responses': {
                r'(?i)hi|hello|oi|olá': ['Hi there!', 'Hello!', 'Oi!'],
                r'(?i)how are you|como vai': ['I\'m fine, thanks!', 'Estou bem, obrigado!'],
                r'(?i)what.*level|que level': ['I\'m level {level}', 'Sou level {level}'],
                r'(?i)where.*you|onde.*você': ['I\'m at {map}', 'Estou em {map}']
            }
        })
        
        # Estado interno
        self.last_response_time: Dict[str, float] = {}
        self.response_patterns: List[tuple] = []
    
    def on_load(self) -> bool:
        """Carrega o plugin."""
        self._compile_patterns()
        return True
    
    def on_activate(self) -> bool:
        """Ativa o plugin."""
        # Registra handlers de eventos
        self.add_event_handler('chat_message', self._handle_chat_message)
        self.add_event_handler('private_message', self._handle_private_message)
        self.add_event_handler('guild_message', self._handle_guild_message)
        self.add_event_handler('party_message', self._handle_party_message)
        
        self.logger.info("AutoResponse ativado")
        return True
    
    def on_deactivate(self) -> None:
        """Desativa o plugin."""
        self.logger.info("AutoResponse desativado")
    
    def on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Chamado quando configuração muda."""
        if key == 'responses':
            self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compila padrões regex."""
        self.response_patterns = []
        
        responses = self.config.get('responses', {})
        for pattern, reply_list in responses.items():
            try:
                compiled_pattern = re.compile(pattern)
                self.response_patterns.append((compiled_pattern, reply_list))
            except re.error as e:
                self.logger.error(f"Padrão regex inválido '{pattern}': {e}")
    
    def _handle_chat_message(self, event_data: Dict[str, Any]) -> None:
        """Processa mensagem do chat público."""
        if not self.config.get('respond_to_public', True):
            return
        
        self._process_message(
            event_data.get('message', ''),
            event_data.get('player', ''),
            'public'
        )
    
    def _handle_private_message(self, event_data: Dict[str, Any]) -> None:
        """Processa mensagem privada."""
        if not self.config.get('respond_to_pm', True):
            return
        
        self._process_message(
            event_data.get('message', ''),
            event_data.get('player', ''),
            'private'
        )
    
    def _handle_guild_message(self, event_data: Dict[str, Any]) -> None:
        """Processa mensagem da guild."""
        if not self.config.get('respond_to_guild', False):
            return
        
        self._process_message(
            event_data.get('message', ''),
            event_data.get('player', ''),
            'guild'
        )
    
    def _handle_party_message(self, event_data: Dict[str, Any]) -> None:
        """Processa mensagem do party."""
        if not self.config.get('respond_to_party', False):
            return
        
        self._process_message(
            event_data.get('message', ''),
            event_data.get('player', ''),
            'party'
        )
    
    def _process_message(self, message: str, player: str, chat_type: str) -> None:
        """
        Processa mensagem e responde se necessário.
        
        Args:
            message: Mensagem recebida
            player: Nome do jogador
            chat_type: Tipo do chat
        """
        if not message or not player:
            return
        
        # Verifica blacklist
        blacklist = self.config.get('blacklist', [])
        if player.lower() in [name.lower() for name in blacklist]:
            return
        
        # Verifica cooldown
        cooldown = self.config.get('cooldown', 5)
        current_time = time.time()
        
        if player in self.last_response_time:
            if current_time - self.last_response_time[player] < cooldown:
                return
        
        # Procura padrão correspondente
        for pattern, replies in self.response_patterns:
            match = pattern.search(message)
            if match:
                # Seleciona resposta
                import random
                reply = random.choice(replies)
                
                # Substitui variáveis
                reply = self._format_response(reply, player, chat_type)
                
                # Envia resposta
                self._send_response(reply, player, chat_type)
                
                # Atualiza cooldown
                self.last_response_time[player] = current_time
                
                self.logger.debug(f"Auto-resposta para {player}: {reply}")
                break
    
    def _format_response(self, response: str, player: str, chat_type: str) -> str:
        """
        Formata resposta substituindo variáveis.
        
        Args:
            response: Resposta template
            player: Nome do jogador
            chat_type: Tipo do chat
            
        Returns:
            Resposta formatada
        """
        # Variáveis disponíveis
        variables = {
            'player': player,
            'chat_type': chat_type,
            'level': self._get_character_level(),
            'map': self._get_current_map(),
            'time': time.strftime('%H:%M:%S'),
            'date': time.strftime('%d/%m/%Y')
        }
        
        # Substitui variáveis
        for var, value in variables.items():
            response = response.replace(f'{{{var}}}', str(value))
        
        return response
    
    def _get_character_level(self) -> str:
        """Obtém level do personagem."""
        # TODO: Integrar com sistema de character
        return "???"
    
    def _get_current_map(self) -> str:
        """Obtém mapa atual."""
        # TODO: Integrar com sistema de world
        return "???"
    
    def _send_response(self, message: str, target_player: str, chat_type: str) -> None:
        """
        Envia resposta.
        
        Args:
            message: Mensagem a enviar
            target_player: Jogador alvo
            chat_type: Tipo do chat
        """
        # TODO: Integrar com sistema de network/chat
        self.logger.info(f"[{chat_type.upper()}] Auto-resposta: {message}")
        
        # Emite evento para sistema de chat
        if self.event_bus:
            self.event_bus.emit('send_chat_message', {
                'message': message,
                'target': target_player,
                'type': chat_type
            })
    
    # Comandos do plugin
    def add_response(self, pattern: str, replies: List[str]) -> bool:
        """
        Adiciona nova resposta.
        
        Args:
            pattern: Padrão regex
            replies: Lista de respostas possíveis
            
        Returns:
            True se adicionado com sucesso
        """
        try:
            # Testa padrão
            re.compile(pattern)
            
            # Adiciona à configuração
            responses = self.config.get('responses', {})
            responses[pattern] = replies
            self.config.set('responses', responses)
            
            # Recompila padrões
            self._compile_patterns()
            
            self.logger.info(f"Resposta adicionada: {pattern}")
            return True
            
        except re.error as e:
            self.logger.error(f"Padrão regex inválido '{pattern}': {e}")
            return False
    
    def remove_response(self, pattern: str) -> bool:
        """
        Remove resposta.
        
        Args:
            pattern: Padrão a remover
            
        Returns:
            True se removido com sucesso
        """
        responses = self.config.get('responses', {})
        
        if pattern in responses:
            del responses[pattern]
            self.config.set('responses', responses)
            self._compile_patterns()
            
            self.logger.info(f"Resposta removida: {pattern}")
            return True
        
        return False
    
    def add_to_blacklist(self, player: str) -> None:
        """Adiciona jogador à blacklist."""
        blacklist = self.config.get('blacklist', [])
        if player.lower() not in [name.lower() for name in blacklist]:
            blacklist.append(player)
            self.config.set('blacklist', blacklist)
            self.logger.info(f"Jogador adicionado à blacklist: {player}")
    
    def remove_from_blacklist(self, player: str) -> None:
        """Remove jogador da blacklist."""
        blacklist = self.config.get('blacklist', [])
        blacklist = [name for name in blacklist if name.lower() != player.lower()]
        self.config.set('blacklist', blacklist)
        self.logger.info(f"Jogador removido da blacklist: {player}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas do plugin."""
        return {
            'total_patterns': len(self.response_patterns),
            'blacklist_size': len(self.config.get('blacklist', [])),
            'recent_responses': len(self.last_response_time),
            'config': {
                'cooldown': self.config.get('cooldown'),
                'respond_to_pm': self.config.get('respond_to_pm'),
                'respond_to_guild': self.config.get('respond_to_guild'),
                'respond_to_party': self.config.get('respond_to_party')
            }
        } 