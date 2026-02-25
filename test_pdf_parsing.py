"""
Тест PDF парсера — полный цикл: загрузка PDF → парсинг → структурирование Groq.
Использование: python test_pdf_parsing.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Цвета
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}✓ {msg}{RESET}")
def err(msg):  print(f"  {RED}✗ {msg}{RESET}")
def info(msg): print(f"  {YELLOW}→ {msg}{RESET}")
def hdr(msg):  print(f"\n{BOLD}{YELLOW}{'─'*60}\n  {msg}\n{'─'*60}{RESET}")


async def test_pdf_parsing():
    """Полное тестирование PDF парсера и структурирования Groq."""
    
    hdr("📄 PDF Parsing & Resume Structuring Test")
    
    try:
        from app.services.pdf_service import pdf_service
        from app.services.groq_service import groq_service
        
        # Список PDF файлов для тестирования
        pdf_files = []
        for fname in ["sample_resume.pdf", "sample_resume_detailed.pdf"]:
            if os.path.exists(fname):
                pdf_files.append(fname)
        
        if not pdf_files:
            err("PDF файлы не найдены!")
            return False
        
        results = {}
        
        for pdf_file in pdf_files:
            print(f"\n{'─'*60}")
            print(f"  Тестируем: {pdf_file}")
            print(f"{'─'*60}")
            
            try:
                # 1️⃣ Загружаем PDF
                info(f"Загружаем PDF файл...")
                with open(pdf_file, "rb") as f:
                    pdf_bytes = f.read()
                
                file_size_kb = len(pdf_bytes) / 1024
                ok(f"PDF загружен: {file_size_kb:.1f} KB")
                
                # 2️⃣ Парсим текст
                info(f"Извлекаем текст из PDF...")
                text = await pdf_service.extract_text(pdf_bytes)
                
                if len(text) < 50:
                    err(f"Текст слишком короткий ({len(text)} символов)")
                    results[pdf_file] = False
                    continue
                
                ok(f"Текст извлечен: {len(text)} символов")
                info(f"Начало текста: {text[:80]}...")
                
                # 3️⃣ Структурируем через Groq
                info(f"Структурируем резюме через Groq...")
                structured = await groq_service.structure_resume_data(text)
                
                ok(f"✓ Навыки найдены: {len(structured.get('skills', []))} шт")
                ok(f"✓ Технологии найдены: {len(structured.get('technologies', []))} шт")
                ok(f"✓ Опыт: {len(structured.get('experience', ''))} символов")
                ok(f"✓ Образование: {structured.get('education', 'не указано')[:60]}...")
                
                # Вывод найденных данных
                print()
                print(f"  {BOLD}НАЙДЕННЫЕ НАВЫКИ:{RESET}")
                for skill in structured['skills'][:5]:
                    print(f"    • {skill}")
                if len(structured['skills']) > 5:
                    print(f"    ... и еще {len(structured['skills'])-5}")
                
                print(f"\n  {BOLD}ТЕХНОЛОГИИ:{RESET}")
                for tech in structured['technologies'][:8]:
                    print(f"    • {tech}")
                if len(structured['technologies']) > 8:
                    print(f"    ... и еще {len(structured['technologies'])-8}")
                
                results[pdf_file] = True
                
            except Exception as e:
                err(f"Ошибка при обработке {pdf_file}: {str(e)[:100]}")
                results[pdf_file] = False
        
        # Итоги
        hdr("📊 Итоги тестирования PDF")
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for pdf, success in results.items():
            status = f"{GREEN}✓ OK{RESET}" if success else f"{RED}✗ FAIL{RESET}"
            print(f"  {pdf:40s} {status}")
        
        print(f"\n  {BOLD}{passed}/{total} файлов обработано успешно{RESET}\n")
        
        return passed == total
        
    except Exception as e:
        err(f"Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_pdf_parsing())
    exit(0 if result else 1)
