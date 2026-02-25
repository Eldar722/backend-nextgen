"""
Сервис для извлечения текста из PDF резюме.
Использует pdfplumber для парсинга файлов.
"""
import pdfplumber
import io
from typing import Optional
from fastapi import HTTPException, status


class PDFService:
    """Извлечение и обработка текста из PDF файлов."""

    async def extract_text(self, file_bytes: bytes) -> str:
        """
        Извлекает весь текст из PDF документа.
        
        Args:
            file_bytes: Байты PDF файла
            
        Returns:
            Полный текст документа
        """
        try:
            text_parts = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            full_text = "\n".join(text_parts).strip()
            
            if not full_text:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Не удалось извлечь текст из PDF. Возможно файл содержит только изображения.",
                )
            
            return full_text
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при обработке PDF файла: {str(e)}",
            )

    def validate_file_size(self, file_size: int, max_size_mb: int = 10) -> None:
        """Проверяет что файл не превышает максимально допустимый размер."""
        max_bytes = max_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл слишком большой. Максимальный размер: {max_size_mb} МБ",
            )


# Синглтон сервиса
pdf_service = PDFService()
