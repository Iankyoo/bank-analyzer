from unittest.mock import MagicMock, patch

from bank_analyzer.services.memory import find_similar_transaction


def _mock_query_result(distance, category="food"):
    return {
        "metadatas": [[{"category": category}]],
        "distances": [[distance]],
    }


def test_find_similar_transaction_within_threshold():
    with patch("bank_analyzer.services.memory.get_collection") as mock_get_collection:
        mock_collection = MagicMock()
        mock_collection.query.return_value = _mock_query_result(0.1)
        mock_get_collection.return_value = mock_collection

        result = find_similar_transaction("Ifood")

        assert result == "food"


def test_find_similar_transaction_beyond_threshold():
    with patch("bank_analyzer.services.memory.get_collection") as mock_get_collection:
        mock_collection = MagicMock()
        mock_collection.query.return_value = _mock_query_result(0.9)
        mock_get_collection.return_value = mock_collection

        result = find_similar_transaction("Compra desconhecida")

        assert result is None


def test_find_similar_transaction_no_match():
    with patch("bank_analyzer.services.memory.get_collection") as mock_get_collection:
        mock_collection = MagicMock()
        mock_collection.query.return_value = {"metadatas": [[]], "distances": [[]]}
        mock_get_collection.return_value = mock_collection

        result = find_similar_transaction("Nova transação")

        assert result is None
