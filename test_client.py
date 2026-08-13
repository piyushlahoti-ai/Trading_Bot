import unittest
from unittest.mock import MagicMock, patch
import requests

from binance.exceptions import BinanceAPIException
from bot.client import validate_credentials, redact_sensitive_info


class TestClientCredentials(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock()

    def test_redact_sensitive_info(self) -> None:
        """Test that sensitive information is successfully redacted from dicts and lists."""
        sensitive_data = {
            "apiKey": "123456",
            "api_secret": "abcdef",
            "signature": "mysig",
            "normal_field": "public",
            "nested": {
                "token": "secret_token",
                "other": "val"
            },
            "list_field": [
                {"secret": "xyz", "val": 1},
                {"val": 2}
            ]
        }
        redacted = redact_sensitive_info(sensitive_data)
        self.assertEqual(redacted["apiKey"], "[REDACTED]")
        self.assertEqual(redacted["api_secret"], "[REDACTED]")
        self.assertEqual(redacted["signature"], "[REDACTED]")
        self.assertEqual(redacted["normal_field"], "public")
        self.assertEqual(redacted["nested"]["token"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["other"], "val")
        self.assertEqual(redacted["list_field"][0]["secret"], "[REDACTED]")
        self.assertEqual(redacted["list_field"][0]["val"], 1)
        self.assertEqual(redacted["list_field"][1]["val"], 2)

    def test_validate_credentials_wallet_balance_success(self) -> None:
        """Test verification succeeds and balance is parsed using walletBalance."""
        self.mock_client.futures_account.return_value = {
            "assets": [
                {"asset": "USDT", "walletBalance": "250.75"},
                {"asset": "BTC", "walletBalance": "0.015"}
            ]
        }
        # This should execute without errors
        validate_credentials(self.mock_client)
        self.mock_client.futures_account.assert_called_once()

    def test_validate_credentials_legacy_balance_success(self) -> None:
        """Test verification succeeds and balance is parsed using balance (legacy format)."""
        self.mock_client.futures_account.return_value = {
            "assets": [
                {"asset": "USDT", "balance": "100.50"},
                {"asset": "BTC", "balance": "0.005"}
            ]
        }
        validate_credentials(self.mock_client)
        self.mock_client.futures_account.assert_called_once()

    def test_validate_credentials_missing_balance_keys_regression(self) -> None:
        """Regression test for KeyError when assets list contains dictionaries without balance fields."""
        self.mock_client.futures_account.return_value = {
            "assets": [
                {"asset": "USDT"},  # balance and walletBalance are missing
                {"asset": "BTC", "someOtherField": "data"}
            ]
        }
        # Should succeed without KeyError and default balance to 'N/A'
        validate_credentials(self.mock_client)
        self.mock_client.futures_account.assert_called_once()

    def test_validate_credentials_missing_assets_array(self) -> None:
        """Test verification succeeds even if assets array is completely missing or is not a list."""
        self.mock_client.futures_account.return_value = {
            "feeTier": 0,
            "canTrade": True
        }
        # Should succeed and default balance to 'N/A'
        validate_credentials(self.mock_client)

        self.mock_client.futures_account.return_value = {
            "assets": "not_a_list"
        }
        validate_credentials(self.mock_client)

    def test_validate_credentials_api_exception(self) -> None:
        """Test validation propagates BinanceAPIException when credentials are invalid."""
        response = requests.Response()
        response.status_code = 401
        response._content = b'{"code":-2008,"msg":"Invalid API-key, IP, or permissions for action."}'
        
        self.mock_client.futures_account.side_effect = BinanceAPIException(
            response, 401, "Invalid API-key, IP, or permissions for action."
        )
        
        with self.assertRaises(BinanceAPIException):
            validate_credentials(self.mock_client)


if __name__ == "__main__":
    unittest.main()
