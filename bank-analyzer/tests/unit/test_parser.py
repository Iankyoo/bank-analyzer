import io
from unittest.mock import MagicMock, patch

from bank_analyzer.services.parser import download_pdf_from_s3, extract_text_from_pdf


def test_download_pdf_from_s3():
    with patch("bank_analyzer.services.parser.s3_client") as mock_s3:

        def fake_download(bucket, key, fileobj):
            fileobj.write(b"fake pdf content")

        mock_s3.download_fileobj.side_effect = fake_download

        result = download_pdf_from_s3("user_id/test.pdf")

        assert isinstance(result, io.BytesIO)
        assert result.read() == b"fake pdf content"


def test_extract_text_from_pdf():
    with patch("bank_analyzer.services.parser.pdfplumber") as mock_plumber:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Salary 1000.00"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_plumber.open.return_value.__enter__.return_value = mock_pdf

        file_obj = io.BytesIO(b"fake pdf")
        result = extract_text_from_pdf(file_obj)

        assert result == "Salary 1000.00"
