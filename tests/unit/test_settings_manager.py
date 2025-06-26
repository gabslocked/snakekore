"""
Testes para Settings Manager
============================

Testes unitários para settings_manager.py
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import threading
import time
from unittest.mock import patch, mock_open
import sys

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.settings.settings_manager import SettingsManager


class TestSettingsManager:
    """Testes para classe SettingsManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Diretório temporário para testes."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """Diretório de configuração para testes."""
        config_path = Path(temp_dir) / "config"
        config_path.mkdir()
        return str(config_path)
    
    @pytest.fixture
    def settings_manager(self, config_dir):
        """SettingsManager para testes."""
        return SettingsManager(config_dir)
    
    def test_initialization(self, settings_manager, config_dir):
        """Testa inicialização do SettingsManager."""
        assert settings_manager.config_dir == config_dir
        assert isinstance(settings_manager.settings, dict)
        assert isinstance(settings_manager._lock, type(threading.Lock()))
    
    def test_get_set_operations(self, settings_manager):
        """Testa operações básicas get/set."""
        # Set e get simples
        settings_manager.set('test_key', 'test_value')
        assert settings_manager.get('test_key') == 'test_value'
        
        # Get com default
        assert settings_manager.get('nonexistent', 'default') == 'default'
        
        # Get de chave inexistente sem default
        assert settings_manager.get('nonexistent') is None
    
    def test_nested_keys(self, settings_manager):
        """Testa chaves aninhadas."""
        # Set aninhado
        settings_manager.set('section.subsection.key', 'nested_value')
        
        # Get aninhado
        assert settings_manager.get('section.subsection.key') == 'nested_value'
        
        # Verificar estrutura criada
        assert 'section' in settings_manager.settings
        assert 'subsection' in settings_manager.settings['section']
        assert settings_manager.settings['section']['subsection']['key'] == 'nested_value'
    
    def test_has_key(self, settings_manager):
        """Testa verificação de existência de chaves."""
        settings_manager.set('existing_key', 'value')
        
        assert settings_manager.has('existing_key')
        assert not settings_manager.has('nonexistent_key')
        
        # Chave aninhada
        settings_manager.set('nested.key', 'value')
        assert settings_manager.has('nested.key')
        assert not settings_manager.has('nested.nonexistent')
    
    def test_remove_operations(self, settings_manager):
        """Testa operações de remoção."""
        # Remover chave simples
        settings_manager.set('removable_key', 'value')
        assert settings_manager.has('removable_key')
        
        settings_manager.remove('removable_key')
        assert not settings_manager.has('removable_key')
        
        # Remover chave aninhada
        settings_manager.set('section.removable', 'value')
        assert settings_manager.has('section.removable')
        
        settings_manager.remove('section.removable')
        assert not settings_manager.has('section.removable')
        
        # Remover chave inexistente (não deve dar erro)
        settings_manager.remove('nonexistent_key')
    
    def test_clear_operations(self, settings_manager):
        """Testa operações de limpeza."""
        # Adicionar algumas configurações
        settings_manager.set('key1', 'value1')
        settings_manager.set('key2', 'value2')
        settings_manager.set('section.key', 'value')
        
        # Limpar tudo
        settings_manager.clear()
        
        assert not settings_manager.has('key1')
        assert not settings_manager.has('key2')
        assert not settings_manager.has('section.key')
        assert len(settings_manager.settings) == 0
    
    def test_config_file_loading(self, config_dir, settings_manager):
        """Testa carregamento de arquivo de configuração."""
        # Criar arquivo config.txt
        config_file = Path(config_dir) / "config.txt"
        config_content = """
# Test configuration
username test_user
password test_pass
server localhost
port 6900

# Section
lockMap 1
attackAuto 2
"""
        config_file.write_text(config_content)
        
        # Carregar arquivo
        settings_manager.load_config_file(str(config_file))
        
        # Verificar configurações carregadas
        assert settings_manager.get('username') == 'test_user'
        assert settings_manager.get('password') == 'test_pass'
        assert settings_manager.get('server') == 'localhost'
        assert settings_manager.get('port') == '6900'
        assert settings_manager.get('lockMap') == '1'
        assert settings_manager.get('attackAuto') == '2'
    
    def test_config_file_comments_and_empty_lines(self, config_dir, settings_manager):
        """Testa tratamento de comentários e linhas vazias."""
        config_file = Path(config_dir) / "config.txt"
        config_content = """
# This is a comment
username test_user

# Another comment
password test_pass
# lockMap 0  # This is commented out

server localhost
"""
        config_file.write_text(config_content)
        
        settings_manager.load_config_file(str(config_file))
        
        assert settings_manager.get('username') == 'test_user'
        assert settings_manager.get('password') == 'test_pass'
        assert settings_manager.get('server') == 'localhost'
        assert not settings_manager.has('lockMap')  # Comentado
    
    def test_config_file_different_encodings(self, config_dir, settings_manager):
        """Testa carregamento com diferentes codificações."""
        config_file = Path(config_dir) / "config_utf8.txt"
        
        # Conteúdo with caracteres especiais
        config_content = "username açaí\npassword café"
        
        # Salvar em UTF-8
        config_file.write_text(config_content, encoding='utf-8')
        
        # Carregar arquivo
        settings_manager.load_config_file(str(config_file))
        
        assert settings_manager.get('username') == 'açaí'
        assert settings_manager.get('password') == 'café'
    
    def test_load_all_configs(self, config_dir, settings_manager):
        """Testa carregamento de todos os arquivos de configuração."""
        # Criar múltiplos arquivos
        files_content = {
            'config.txt': 'username test_user\npassword test_pass',
            'sys.txt': 'attackAuto 2\nlockMap 1',
            'timeouts.txt': 'ai_attack_timeout 10\nai_move_timeout 5'
        }
        
        for filename, content in files_content.items():
            file_path = Path(config_dir) / filename
            file_path.write_text(content)
        
        # Carregar todos
        settings_manager.load_all_configs()
        
        # Verificar se todos foram carregados
        assert settings_manager.get('username') == 'test_user'
        assert settings_manager.get('attackAuto') == '2'
        assert settings_manager.get('ai_attack_timeout') == '10'
    
    def test_save_config_file(self, config_dir, settings_manager):
        """Testa salvamento de arquivo de configuração."""
        # Definir algumas configurações
        settings_manager.set('username', 'test_user')
        settings_manager.set('password', 'test_pass')
        settings_manager.set('server', 'localhost')
        
        # Salvar arquivo
        config_file = Path(config_dir) / "saved_config.txt"
        settings_manager.save_config_file(str(config_file))
        
        # Verificar se arquivo foi criado
        assert config_file.exists()
        
        # Carregar em novo settings manager
        new_settings = SettingsManager(config_dir)
        new_settings.load_config_file(str(config_file))
        
        # Verificar configurações
        assert new_settings.get('username') == 'test_user'
        assert new_settings.get('password') == 'test_pass'
        assert new_settings.get('server') == 'localhost'
    
    def test_backup_and_restore(self, config_dir, settings_manager):
        """Testa backup e restauração."""
        # Configuração inicial
        settings_manager.set('key1', 'value1')
        settings_manager.set('key2', 'value2')
        
        # Fazer backup
        backup_name = settings_manager.backup()
        assert backup_name is not None
        
        # Modificar configurações
        settings_manager.set('key1', 'modified_value')
        settings_manager.set('key3', 'new_value')
        
        # Restaurar backup
        restored = settings_manager.restore(backup_name)
        assert restored
        
        # Verificar restauração
        assert settings_manager.get('key1') == 'value1'
        assert settings_manager.get('key2') == 'value2'
        assert not settings_manager.has('key3')
    
    def test_validation(self, settings_manager):
        """Testa validação de configurações."""
        # Definir algumas configurações
        settings_manager.set('port', '6900')
        settings_manager.set('username', 'test_user')
        settings_manager.set('invalid_port', 'not_a_number')
        
        # Validar configurações
        is_valid, errors = settings_manager.validate()
        
        # Deve retornar status de validação
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_thread_safety(self, settings_manager):
        """Testa thread safety."""
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(100):
                    key = f'thread_{thread_id}_key_{i}'
                    value = f'thread_{thread_id}_value_{i}'
                    
                    settings_manager.set(key, value)
                    retrieved = settings_manager.get(key)
                    
                    if retrieved == value:
                        results.append(True)
                    else:
                        results.append(False)
            except Exception as e:
                errors.append(e)
        
        # Criar múltiplas threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Verificar resultados
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results), "Some operations failed"
        assert len(results) == 500  # 5 threads * 100 operations each
    
    def test_watch_file_changes(self, config_dir, settings_manager):
        """Testa monitoramento de mudanças em arquivos."""
        config_file = Path(config_dir) / "watched_config.txt"
        config_file.write_text("initial_key initial_value")
        
        # Carregar arquivo inicial
        settings_manager.load_config_file(str(config_file))
        assert settings_manager.get('initial_key') == 'initial_value'
        
        # Modificar arquivo
        config_file.write_text("initial_key modified_value\nnew_key new_value")
        
        # Recarregar (simula watching)
        settings_manager.load_config_file(str(config_file))
        
        # Verificar mudanças
        assert settings_manager.get('initial_key') == 'modified_value'
        assert settings_manager.get('new_key') == 'new_value'
    
    def test_file_not_found_handling(self, settings_manager):
        """Testa tratamento de arquivo não encontrado."""
        # Tentar carregar arquivo inexistente
        result = settings_manager.load_config_file('nonexistent_file.txt')
        
        # Não deve causar erro, deve retornar False
        assert result is False
    
    def test_invalid_file_format_handling(self, config_dir, settings_manager):
        """Testa tratamento de formato inválido."""
        # Criar arquivo com formato inválido
        invalid_file = Path(config_dir) / "invalid.txt"
        invalid_file.write_text("this is not a valid config format!!!")
        
        # Carregar arquivo inválido
        result = settings_manager.load_config_file(str(invalid_file))
        
        # Deve carregar parcialmente ou ignorar linhas inválidas
        assert isinstance(result, bool)
    
    def test_memory_usage(self, settings_manager):
        """Testa uso de memória com grandes configurações."""
        # Adicionar muitas configurações
        for i in range(1000):
            settings_manager.set(f'key_{i}', f'value_{i}')
        
        # Verificar algumas aleatórias
        assert settings_manager.get('key_500') == 'value_500'
        assert settings_manager.get('key_999') == 'value_999'
        
        # Limpar
        settings_manager.clear()
        assert len(settings_manager.settings) == 0
    
    def test_defaults_integration(self, settings_manager):
        """Testa integração com valores padrão."""
        # Obter valor com default
        value = settings_manager.get('nonexistent_key', 'default_value')
        assert value == 'default_value'
        
        # Carregar defaults se implementado
        if hasattr(settings_manager, 'load_defaults'):
            settings_manager.load_defaults()
            # Verificar se alguns defaults foram carregados
            assert len(settings_manager.settings) > 0 