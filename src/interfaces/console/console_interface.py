"""
Console Interface
=================

Interface de console interativa para PythonKore.
"""

import asyncio
import cmd
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from core.logging.logger import Logger
from core.events.event_bus import EventBus
from ai.ai_manager import AIManager
from tasks.task_manager import TaskManager


class ConsoleInterface(cmd.Cmd):
    """
    Interface de console interativa.
    
    Fornece comandos para controlar o PythonKore via linha de comando.
    Similar à interface do OpenKore original.
    """
    
    def __init__(self,
                 ai_manager: Optional[AIManager] = None,
                 task_manager: Optional[TaskManager] = None,
                 logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None):
        """
        Inicializa interface de console.
        
        Args:
            ai_manager: Gerenciador de AI
            task_manager: Gerenciador de tarefas
            logger: Logger
            event_bus: Bus de eventos
        """
        super().__init__()
        
        self.ai_manager = ai_manager
        self.task_manager = task_manager
        self.logger = logger or Logger(level="INFO")
        self.event_bus = event_bus
        
        # Configuração do prompt
        self.intro = self._get_intro_message()
        self.prompt = "(PythonKore) "
        
        # Estado da interface
        self.is_running = False
        self.auto_mode = False
        
        # Histórico de comandos
        self.command_history: List[str] = []
        self.max_history = 100
        
        # Comandos customizados
        self.custom_commands: Dict[str, Callable] = {}
        
        # Status da sessão
        self.session_start = datetime.now()
        self.commands_executed = 0
        
        self.logger.info("ConsoleInterface inicializada")
    
    def _get_intro_message(self) -> str:
        """Mensagem de introdução."""
        return """
╔══════════════════════════════════════════════════════════════════════════════╗
║                              PythonKore v0.1.0                              ║
║                          Bot OpenSource para Ragnarok                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Digite 'help' para ver comandos disponíveis ou 'quit' para sair.
        """
    
    def start(self) -> None:
        """Inicia a interface de console."""
        self.is_running = True
        self.logger.info("Console interface iniciada")
        
        # Inicia em thread separada para não bloquear
        console_thread = threading.Thread(target=self.cmdloop, daemon=True)
        console_thread.start()
    
    def stop(self) -> None:
        """Para a interface de console."""
        self.is_running = False
        self.logger.info("Console interface parada")
    
    # Comandos básicos
    def do_status(self, args: str) -> None:
        """Mostra status geral do sistema."""
        print("\n" + "="*60)
        print("STATUS GERAL DO SISTEMA")
        print("="*60)
        
        # Status da AI
        if self.ai_manager:
            ai_status = self.ai_manager.get_status()
            print(f"🤖 AI Status:")
            print(f"   Habilitada: {'✅' if ai_status['enabled'] else '❌'}")
            print(f"   Modo: {'AUTO' if ai_status['auto'] else 'MANUAL' if ai_status['manual'] else 'OFF'}")
            print(f"   Estado atual: {ai_status['state_machine']['current_state']}")
            print(f"   Transições: {ai_status['state_machine']['total_transitions']}")
        
        # Status das tarefas
        if self.task_manager:
            task_status = self.task_manager.get_status()
            print(f"📋 Task Manager:")
            print(f"   Rodando: {'✅' if task_status['running'] else '❌'}")
            print(f"   Pendentes: {task_status['pending_tasks']}")
            print(f"   Executando: {task_status['running_tasks']}")
            print(f"   Completadas: {task_status['completed_tasks']}")
        
        # Status da sessão
        uptime = datetime.now() - self.session_start
        print(f"💻 Sessão:")
        print(f"   Uptime: {uptime}")
        print(f"   Comandos executados: {self.commands_executed}")
        
        print("="*60 + "\n")
    
    def do_ai(self, args: str) -> None:
        """Controla a AI. Uso: ai [on|off|auto|manual|status]"""
        if not self.ai_manager:
            print("❌ AI Manager não disponível")
            return
        
        args = args.strip().lower()
        
        if args == "on" or args == "auto":
            self.ai_manager.enable_auto()
            if not self.ai_manager.is_enabled:
                self.ai_manager.start()
            print("✅ AI AUTO habilitada")
            
        elif args == "manual":
            self.ai_manager.enable_manual()
            if not self.ai_manager.is_enabled:
                self.ai_manager.start()
            print("✅ AI MANUAL habilitada")
            
        elif args == "off":
            self.ai_manager.disable()
            print("❌ AI desabilitada")
            
        elif args == "status":
            status = self.ai_manager.get_status()
            print(f"🤖 AI Status: {status}")
            
        else:
            print("Uso: ai [on|off|auto|manual|status]")
    
    def do_tasks(self, args: str) -> None:
        """Gerencia tarefas. Uso: tasks [start|stop|status|list]"""
        if not self.task_manager:
            print("❌ Task Manager não disponível")
            return
        
        args = args.strip().lower()
        
        if args == "start":
            self.task_manager.start()
            print("✅ Task Manager iniciado")
            
        elif args == "stop":
            self.task_manager.stop()
            print("❌ Task Manager parado")
            
        elif args == "status":
            status = self.task_manager.get_status()
            print(f"📋 Task Status: {status}")
            
        elif args == "list":
            summary = self.task_manager.get_summary()
            if summary:
                print("\n📋 TAREFAS ATIVAS:")
                for item in summary:
                    task = item['task']
                    queue = item['queue']
                    print(f"   [{queue.upper()}] {task['name']} - {task['status']} ({task['progress']:.1f}%)")
            else:
                print("Nenhuma tarefa ativa")
                
        else:
            print("Uso: tasks [start|stop|status|list]")
    
    def do_log(self, args: str) -> None:
        """Controla nível de log. Uso: log [debug|info|warning|error]"""
        args = args.strip().upper()
        
        if args in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            # Atualiza logger global
            self.logger.level = getattr(__import__('logging'), args)
            print(f"✅ Nível de log alterado para: {args}")
        else:
            current_level = self.logger.logger.level
            level_name = {10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR'}.get(current_level, 'UNKNOWN')
            print(f"Nível atual: {level_name}")
            print("Uso: log [debug|info|warning|error]")
    
    def do_clear(self, args: str) -> None:
        """Limpa a tela."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_history(self, args: str) -> None:
        """Mostra histórico de comandos."""
        if not self.command_history:
            print("Nenhum comando no histórico")
            return
        
        print("\n📜 HISTÓRICO DE COMANDOS:")
        for i, cmd in enumerate(self.command_history[-20:], 1):  # Últimos 20
            print(f"  {i:2d}. {cmd}")
        print()
    
    def do_help(self, args: str) -> None:
        """Lista comandos disponíveis."""
        if args:
            # Help específico para um comando
            super().do_help(args)
        else:
            # Help geral
            print("\n🔧 COMANDOS DISPONÍVEIS:")
            print("  status        - Mostra status geral do sistema")
            print("  ai [cmd]      - Controla AI (on/off/auto/manual/status)")
            print("  tasks [cmd]   - Gerencia tarefas (start/stop/status/list)")
            print("  log [level]   - Controla nível de log (debug/info/warning/error)")
            print("  clear         - Limpa a tela")
            print("  history       - Mostra histórico de comandos")
            print("  info          - Informações sobre o PythonKore")
            print("  quit/exit     - Sai do programa")
            print("\nDigite 'help <comando>' para mais detalhes sobre um comando específico.\n")
    
    def do_info(self, args: str) -> None:
        """Informações sobre o PythonKore."""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           PYTHONKORE INFORMATION                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Versão: 0.1.0 (Development)                                                 ║
║ Baseado em: OpenKore                                                         ║
║ Linguagem: Python 3.11+                                                     ║
║ Arquitetura: Async/Modern                                                   ║
║                                                                              ║
║ Características:                                                             ║
║  • Sistema de AI moderno com state machine                                  ║
║  • Networking assíncrono                                                    ║
║  • Sistema de tarefas hierárquico                                           ║
║  • Interfaces múltiplas (Console, Web, GUI)                                 ║
║  • Sistema de plugins extensível                                            ║
║  • Compatibilidade com configurações OpenKore                              ║
║                                                                              ║
║ Desenvolvido com foco em performance, manutenibilidade e extensibilidade.   ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
    
    def do_quit(self, args: str) -> bool:
        """Sai do programa."""
        print("👋 Saindo do PythonKore...")
        
        # Para sistemas se estiverem rodando
        if self.ai_manager and self.ai_manager.is_enabled:
            self.ai_manager.stop()
        
        if self.task_manager and self.task_manager.is_running:
            self.task_manager.stop()
        
        return True
    
    def do_exit(self, args: str) -> bool:
        """Alias para quit."""
        return self.do_quit(args)
    
    # Sobrescreve métodos para capturar comandos
    def onecmd(self, line: str) -> bool:
        """Processa um comando."""
        # Adiciona ao histórico
        if line.strip():
            self.command_history.append(line.strip())
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
            
            self.commands_executed += 1
        
        # Processa comando
        try:
            return super().onecmd(line)
        except Exception as e:
            print(f"❌ Erro ao executar comando: {e}")
            self.logger.error(f"Erro no comando '{line}': {e}")
            return False
    
    def emptyline(self) -> None:
        """Não faz nada em linha vazia."""
        pass
    
    def default(self, line: str) -> None:
        """Comando não reconhecido."""
        cmd = line.split()[0] if line.split() else line
        print(f"❓ Comando não reconhecido: '{cmd}'")
        print("Digite 'help' para ver comandos disponíveis.")
    
    def precmd(self, line: str) -> str:
        """Processa linha antes da execução."""
        # Log do comando (se debug ativo)
        if line.strip():
            self.logger.debug(f"Comando executado: {line}")
        
        return line
    
    def postcmd(self, stop: bool, line: str) -> bool:
        """Processa após execução do comando."""
        return stop
    
    # Métodos utilitários
    def add_custom_command(self, name: str, handler: Callable, help_text: str = "") -> None:
        """
        Adiciona comando customizado.
        
        Args:
            name: Nome do comando
            handler: Função para tratar o comando
            help_text: Texto de ajuda
        """
        self.custom_commands[name] = handler
        
        # Adiciona dinamicamente ao objeto
        setattr(self, f"do_{name}", handler)
        if help_text:
            setattr(self, f"help_{name}", lambda: print(help_text))
    
    def remove_custom_command(self, name: str) -> None:
        """Remove comando customizado."""
        if name in self.custom_commands:
            del self.custom_commands[name]
            
            # Remove do objeto
            if hasattr(self, f"do_{name}"):
                delattr(self, f"do_{name}")
            if hasattr(self, f"help_{name}"):
                delattr(self, f"help_{name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas da interface."""
        uptime = datetime.now() - self.session_start
        
        return {
            'session_start': self.session_start.isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'commands_executed': self.commands_executed,
            'command_history_size': len(self.command_history),
            'custom_commands': len(self.custom_commands),
            'is_running': self.is_running
        } 