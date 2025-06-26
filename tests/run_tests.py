#!/usr/bin/env python3
"""
Test Runner
===========

Runner principal para executar todos os testes do PythonKore.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
import time

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_command(command: list, cwd: str = None) -> tuple:
    """
    Executa comando e retorna resultado.
    
    Args:
        command: Lista com comando e argumentos
        cwd: Diretório de trabalho
        
    Returns:
        Tupla (success, output, error)
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        return (
            result.returncode == 0,
            result.stdout,
            result.stderr
        )
    except subprocess.TimeoutExpired:
        return False, "", "Test execution timed out"
    except Exception as e:
        return False, "", str(e)


def check_pytest_available() -> bool:
    """Verifica se pytest está disponível."""
    try:
        subprocess.run(['python', '-m', 'pytest', '--version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_pytest():
    """Instala pytest se não estiver disponível."""
    print("📦 Instalando pytest...")
    
    success, output, error = run_command([
        'python', '-m', 'pip', 'install', 'pytest', 'pytest-asyncio'
    ])
    
    if success:
        print("✅ pytest instalado com sucesso!")
        return True
    else:
        print(f"❌ Erro ao instalar pytest: {error}")
        return False


def run_unit_tests(verbose: bool = False, coverage: bool = False) -> bool:
    """
    Executa testes unitários.
    
    Args:
        verbose: Modo verboso
        coverage: Executar com coverage
        
    Returns:
        True se todos os testes passaram
    """
    print("🧪 Executando testes unitários...")
    
    command = ['python', '-m', 'pytest', 'tests/unit/']
    
    if verbose:
        command.append('-v')
    
    if coverage:
        command.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
    
    command.extend(['-m', 'unit'])  # Apenas testes marcados como unit
    
    success, output, error = run_command(command)
    
    if success:
        print("✅ Testes unitários passaram!")
        if verbose:
            print(output)
        return True
    else:
        print("❌ Testes unitários falharam!")
        print(error)
        if verbose:
            print(output)
        return False


def run_integration_tests(verbose: bool = False) -> bool:
    """
    Executa testes de integração.
    
    Args:
        verbose: Modo verboso
        
    Returns:
        True se todos os testes passaram
    """
    print("🔗 Executando testes de integração...")
    
    command = ['python', '-m', 'pytest', 'tests/integration/']
    
    if verbose:
        command.append('-v')
    
    command.extend(['-m', 'integration'])  # Apenas testes marcados como integration
    
    success, output, error = run_command(command)
    
    if success:
        print("✅ Testes de integração passaram!")
        if verbose:
            print(output)
        return True
    else:
        print("❌ Testes de integração falharam!")
        print(error)
        if verbose:
            print(output)
        return False


def run_all_tests(verbose: bool = False, coverage: bool = False, 
                  include_slow: bool = False) -> bool:
    """
    Executa todos os testes.
    
    Args:
        verbose: Modo verboso
        coverage: Executar com coverage
        include_slow: Incluir testes lentos
        
    Returns:
        True se todos os testes passaram
    """
    print("🚀 Executando todos os testes...")
    
    command = ['python', '-m', 'pytest', 'tests/']
    
    if verbose:
        command.append('-v')
    
    if coverage:
        command.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
    
    if not include_slow:
        command.extend(['-m', 'not slow'])  # Excluir testes lentos
    
    success, output, error = run_command(command)
    
    if success:
        print("✅ Todos os testes passaram!")
        if verbose:
            print(output)
        return True
    else:
        print("❌ Alguns testes falharam!")
        print(error)
        if verbose:
            print(output)
        return False


def run_specific_test(test_path: str, verbose: bool = False) -> bool:
    """
    Executa teste específico.
    
    Args:
        test_path: Caminho para o teste
        verbose: Modo verboso
        
    Returns:
        True se o teste passou
    """
    print(f"🎯 Executando teste específico: {test_path}")
    
    command = ['python', '-m', 'pytest', test_path]
    
    if verbose:
        command.append('-v')
    
    success, output, error = run_command(command)
    
    if success:
        print("✅ Teste passou!")
        if verbose:
            print(output)
        return True
    else:
        print("❌ Teste falhou!")
        print(error)
        if verbose:
            print(output)
        return False


def validate_test_environment() -> bool:
    """Valida ambiente de testes."""
    print("🔍 Validando ambiente de testes...")
    
    # Verificar estrutura de diretórios
    test_dir = Path(__file__).parent
    required_dirs = ['unit', 'integration']
    
    for dir_name in required_dirs:
        dir_path = test_dir / dir_name
        if not dir_path.exists():
            print(f"❌ Diretório não encontrado: {dir_path}")
            return False
    
    # Verificar arquivos importantes
    required_files = ['conftest.py', '__init__.py']
    
    for file_name in required_files:
        file_path = test_dir / file_name
        if not file_path.exists():
            print(f"❌ Arquivo não encontrado: {file_path}")
            return False
    
    # Verificar src directory
    src_dir = test_dir.parent / "src"
    if not src_dir.exists():
        print(f"❌ Diretório src não encontrado: {src_dir}")
        return False
    
    print("✅ Ambiente de testes válido!")
    return True


def show_test_summary():
    """Mostra resumo dos testes disponíveis."""
    print("\n📋 Resumo dos Testes Disponíveis:")
    print("=" * 50)
    
    test_dir = Path(__file__).parent
    
    # Contar testes unitários
    unit_tests = list((test_dir / "unit").glob("test_*.py"))
    print(f"🧪 Testes Unitários: {len(unit_tests)}")
    for test_file in unit_tests:
        print(f"   - {test_file.name}")
    
    # Contar testes de integração
    integration_tests = list((test_dir / "integration").glob("test_*.py"))
    print(f"🔗 Testes de Integração: {len(integration_tests)}")
    for test_file in integration_tests:
        print(f"   - {test_file.name}")
    
    print(f"\n📊 Total de arquivos de teste: {len(unit_tests) + len(integration_tests)}")


def main():
    """Função principal do runner de testes."""
    parser = argparse.ArgumentParser(
        description="Runner de testes do PythonKore",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_tests.py                    # Executa todos os testes
  python run_tests.py --unit             # Apenas testes unitários
  python run_tests.py --integration      # Apenas testes de integração
  python run_tests.py --coverage         # Com coverage
  python run_tests.py --slow             # Incluir testes lentos
  python run_tests.py --test test_ai.py  # Teste específico
        """
    )
    
    parser.add_argument(
        '--unit', '-u',
        action='store_true',
        help='Executar apenas testes unitários'
    )
    
    parser.add_argument(
        '--integration', '-i',
        action='store_true',
        help='Executar apenas testes de integração'
    )
    
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Executar com coverage'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso'
    )
    
    parser.add_argument(
        '--slow', '-s',
        action='store_true',
        help='Incluir testes lentos'
    )
    
    parser.add_argument(
        '--test', '-t',
        type=str,
        help='Executar teste específico'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Mostrar resumo dos testes'
    )
    
    parser.add_argument(
        '--install-deps',
        action='store_true',
        help='Instalar dependências de teste'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validar ambiente de testes'
    )
    
    args = parser.parse_args()
    
    # Mudar para diretório do projeto
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    print("🐍 PythonKore Test Runner")
    print("=" * 40)
    
    # Validar ambiente se solicitado
    if args.validate:
        if not validate_test_environment():
            sys.exit(1)
        return
    
    # Mostrar resumo se solicitado
    if args.summary:
        show_test_summary()
        return
    
    # Instalar dependências se solicitado
    if args.install_deps:
        if not install_pytest():
            sys.exit(1)
        return
    
    # Verificar pytest
    if not check_pytest_available():
        print("❌ pytest não está disponível!")
        print("💡 Execute: python run_tests.py --install-deps")
        sys.exit(1)
    
    # Validar ambiente
    if not validate_test_environment():
        sys.exit(1)
    
    start_time = time.time()
    success = True
    
    try:
        # Executar testes baseado nos argumentos
        if args.test:
            success = run_specific_test(args.test, args.verbose)
        elif args.unit:
            success = run_unit_tests(args.verbose, args.coverage)
        elif args.integration:
            success = run_integration_tests(args.verbose)
        else:
            success = run_all_tests(args.verbose, args.coverage, args.slow)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️  Tempo de execução: {execution_time:.2f}s")
        
        if success:
            print("🎉 Todos os testes executados com sucesso!")
            sys.exit(0)
        else:
            print("💥 Alguns testes falharam!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 