#!/usr/bin/env python3
"""
PythonKore Main Entry Point
============================

Script principal para execução do PythonKore.
Equivalente ao openkore.pl do OpenKore original.
"""

import sys
import os
import signal
import argparse
from pathlib import Path
from typing import Optional

# Adiciona o diretório src ao path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from core.settings.settings_manager import SettingsManager
from core.application import PythonKoreApp


def parse_arguments() -> argparse.Namespace:
    """
    Parse argumentos da linha de comando.
    
    Returns:
        Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description='PythonKore - Custom Ragnarok Online Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python main.py --interface console
    python main.py --config-dir ./my_config
    python main.py --character "MyChar" --server "MyServer"
        """
    )
    
    # Argumentos principais
    parser.add_argument(
        '--version', 
        action='version', 
        version='PythonKore 0.1.0'
    )
    
    parser.add_argument(
        '--interface', 
        choices=['console', 'gui', 'web'], 
        default='console',
        help='Interface a ser usada (padrão: console)'
    )
    
    parser.add_argument(
        '--config-dir', 
        type=str, 
        metavar='DIR',
        help='Diretório de configurações (padrão: ./control)'
    )
    
    parser.add_argument(
        '--tables-dir', 
        type=str, 
        metavar='DIR',
        help='Diretório de tabelas (padrão: ./tables)'
    )
    
    # Configurações de servidor
    parser.add_argument(
        '--server', 
        type=str, 
        metavar='NAME',
        help='Nome do servidor'
    )
    
    parser.add_argument(
        '--character', 
        type=str, 
        metavar='NAME',
        help='Nome do personagem'
    )
    
    parser.add_argument(
        '--username', 
        type=str, 
        metavar='USER',
        help='Nome de usuário'
    )
    
    parser.add_argument(
        '--password', 
        type=str, 
        metavar='PASS',
        help='Senha (não recomendado por segurança)'
    )
    
    # Argumentos de debug
    parser.add_argument(
        '--verbose', '-v',
        action='count', 
        default=0,
        help='Aumenta o nível de verbosidade'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Habilita modo debug'
    )
    
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Nível de log (padrão: INFO)'
    )
    
    parser.add_argument(
        '--log-file', 
        type=str, 
        metavar='FILE',
        help='Arquivo de log'
    )
    
    # Argumentos especiais
    parser.add_argument(
        '--no-plugins', 
        action='store_true',
        help='Desabilita carregamento de plugins'
    )
    
    parser.add_argument(
        '--plugin-dir', 
        type=str, 
        metavar='DIR',
        help='Diretório de plugins'
    )
    
    parser.add_argument(
        '--command', 
        type=str, 
        metavar='CMD',
        help='Comando a ser executado na inicialização'
    )
    
    return parser.parse_args()


def setup_signal_handlers(app: PythonKoreApp) -> None:
    """
    Configura handlers para sinais do sistema.
    
    Args:
        app: Instância da aplicação
    """
    def signal_handler(signum: int, frame) -> None:
        print(f"\nRecebido sinal {signum}, encerrando...")
        app.shutdown()
        sys.exit(0)
    
    # Configura handlers para SIGINT e SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)


def main() -> int:
    """
    Função principal do PythonKore.
    
    Returns:
        Código de saída
    """
    try:
        # Parse argumentos
        args = parse_arguments()
        
        # Exibe informações da versão
        print("*** PythonKore 0.1.0 - Custom Ragnarok Online Client ***")
        print("*** https://github.com/pythonkore/pythonkore ***")
        print("*** Baseado no OpenKore (http://www.openkore.org/) ***")
        print()
        
        # Cria e configura a aplicação
        app = PythonKoreApp(args)
        
        # Configura handlers de sinais
        setup_signal_handlers(app)
        
        # Executa a aplicação
        return app.run()
        
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
        return 1
    except Exception as e:
        print(f"Erro fatal: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 