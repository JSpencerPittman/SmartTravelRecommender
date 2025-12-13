import tempfile
from pathlib import Path

from django.test import TestCase  # type: ignore

from chatbot.pdf import PDFCreator


class PDFCreatorTests(TestCase):
    def test_create_pdf(self):
        pdf_creator = PDFCreator("Test Title", "Test Content")
        result = pdf_creator.create()

        pdf_data = result.read()
        self.assertGreater(len(pdf_data), 0)
        self.assertTrue(pdf_data.startswith(b"%PDF"))

    def test_save_to_file(self):
        pdf_creator = PDFCreator("Trip Plan", "Day 1: Paris")

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.pdf"
            pdf_creator.save_to_file(file_path)

            self.assertTrue(file_path.exists())
            self.assertGreater(file_path.stat().st_size, 0)
