"""
Тесты для SSL-бота
Запуск: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import socket
import ssl
import logging

# Импортируем функции из основного бота
from ssl_bot import (
    get_certificate,
    format_certificate,
    escape_markdown,
    user_info,
    ZoneFormatter
)

class TestSSLBot:
    """Тестирование основных функций SSL-бота"""

    def test_escape_markdown(self):
        """Тест экранирования Markdown специальных символов"""
        test_cases = [
            ("_italic_", "\\_italic\\_"),
            ("*bold*", "\\*bold\\*"),
            ("[link](url)", "\\[link\\]\\(url\\)"),
            ("Normal text", "Normal text"),
            ("Mix _*_ text", "Mix \\_\\*\\_ text"),
        ]
        
        for input_text, expected in test_cases:
            assert escape_markdown(input_text) == expected, f"Failed for: {input_text}"

    def test_get_certificate_timeout(self):
        """Тест таймаута при подключении"""
        with patch('socket.create_connection') as mock_socket:
            mock_socket.side_effect = socket.timeout("Connection timeout")
            
            with pytest.raises(socket.timeout):
                get_certificate("example.com", 443)

    @patch('ssl.create_default_context')
    @patch('socket.create_connection')
    def test_get_certificate_success(self, mock_socket_create, mock_ssl_context):
        """Тест успешного получения сертификата"""
        # Мокаем сокет
        mock_sock = MagicMock()
        mock_socket_create.return_value.__enter__.return_value = mock_sock
        
        # Мокаем SSL контекст
        mock_ssl_sock = MagicMock()
        mock_ssl_context.return_value.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
        
        # Мокаем возврат сертификата
        mock_cert = b"fake_certificate_data"
        mock_ssl_sock.getpeercert.return_value = mock_cert
        
        result = get_certificate("example.com", 443)
        assert result == mock_cert

    @patch('OpenSSL.crypto.load_certificate')
    @patch('OpenSSL.crypto.dump_certificate')
    def test_format_certificate(self, mock_dump, mock_load):
        """Тест форматирования сертификата"""
        # Мокаем загрузку сертификата
        mock_cert = MagicMock()
        mock_load.return_value = mock_cert
        
        # Мокаем даты
        mock_cert.get_notBefore.return_value = b"20240101120000Z"
        mock_cert.get_notAfter.return_value = b"20250101120000Z"
        
        # Мокаем дамп PEM
        mock_dump.return_value = b"-----BEGIN CERTIFICATE-----\nFAKE\n-----END CERTIFICATE-----"
        
        pem, validity = format_certificate(b"fake_binary_cert")
        
        assert "BEGIN CERTIFICATE" in pem
        assert "2024.01.01" in validity
        assert "2025.01.01" in validity

    def test_user_info_from_message(self):
        """Тест извлечения информации о пользователе из message"""
        mock_message = Mock()
        mock_message.from_user.id = 12345
        mock_message.from_user.username = "testuser"
        mock_message.from_user.first_name = "Test"
        mock_message.from_user.last_name = "User"
        
        info = user_info(mock_message)
        assert "id=12345" in info
        assert "username=testuser" in info
        assert "name=Test User" in info

    def test_zone_formatter(self):
        """Тест форматтера логов с временной зоной"""
        formatter = ZoneFormatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            tz="Asia/Yekaterinburg"
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Проверяем, что форматтер работает без ошибок
        formatted = formatter.format(record)
        assert "Test message" in formatted

class TestBotIntegration:
    """Интеграционные тесты бота"""

    def test_bot_imports(self):
        """Тест импорта модуля бота"""
        try:
            import ssl_bot
            assert hasattr(ssl_bot, 'bot')
            assert hasattr(ssl_bot, 'TOKEN')
        except ImportError as e:
            pytest.fail(f"Failed to import ssl_bot: {e}")

    @pytest.mark.skipif(
        not os.getenv('RUN_INTEGRATION_TESTS'),
        reason="Integration tests require RUN_INTEGRATION_TESTS=1"
    )
    def test_real_certificate_check(self):
        """Реальный тест проверки сертификата (только при необходимости)"""
        # Проверяем google.com
        cert = get_certificate("google.com", 443)
        assert cert is not None
        
        pem, validity = format_certificate(cert)
        assert "BEGIN CERTIFICATE" in pem
        assert "по" in validity

if __name__ == "__main__":
    pytest.main([__file__, "-v"])