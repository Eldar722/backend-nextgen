"""
Генератор примера PDF резюме для тестирования PDF парсера.
Использование: python generate_sample_resume.py
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from datetime import datetime


def generate_sample_resume():
    """Создаёт файл sample_resume.pdf с примером резюме на русском."""
    
    # Создание PDF
    pdf_path = "sample_resume.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=0.7*cm,
        leftMargin=0.7*cm,
        topMargin=0.7*cm,
        bottomMargin=0.7*cm,
    )
    
    # Контент
    story = []
    
    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=6,
        alignment=0,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#003366'),
        spaceAfter=6,
        spaceBefore=6,
        borderPadding=0,
    )
    
    normal_style = styles['Normal']
    
    # ─────── ФИ И КОНТАКТЫ
    story.append(Paragraph("<b>Иван Иванович Иванов</b><br/>Junior Python Backend Developer", title_style))
    story.append(Spacer(1, 0.2*cm))
    
    contact_data = [
        ['📧 Email:', 'ivan.ivanov@example.com'],
        ['📱 Телефон:', '+7 (999) 123-45-67'],
        ['🔗 GitHub:', 'github.com/ivanov'],
        ['💼 LinkedIn:', 'linkedin.com/in/ivanov'],
        ['📍 Город:', 'Санкт-Петербург'],
    ]
    
    contact_table = Table(contact_data, colWidths=[2.5*cm, 8*cm])
    contact_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 0.4*cm))
    
    # ─────── ПРОФЕССИОНАЛЬНЫЙ ПРОФИЛЬ
    story.append(Paragraph("<b>ПРОФЕССИОНАЛЬНЫЙ ПРОФИЛЬ</b>", heading_style))
    profile_text = """
    Опытный Junior Python разработчик с фокусом на backend разработку и REST API.
    Специализируюсь на FastAPI, PostgreSQL и микросервисной архитектуре.
    Имею 1+ года практического опыта в стартап-среде, принимал участие в разработке 
    высоконагруженных систем обработки данных.
    Стремлюсь к постоянному совершенствованию и изучению новых технологий.
    """
    story.append(Paragraph(profile_text, normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # ─────── КЛЮЧЕВЫЕ КОМПЕТЕНЦИИ
    story.append(Paragraph("<b>КЛЮЧЕВЫЕ КОМПЕТЕНЦИИ</b>", heading_style))
    
    skills_data = [
        ['Язык программирования:', 'Python, SQL, Bash'],
        ['Web фреймворки:', 'FastAPI, Flask, Starlette'],
        ['Базы данных:', 'PostgreSQL, Redis, MongoDB'],
        ['DevOps & Infrastructure:', 'Docker, Docker Compose, Kubernetes (базовые знания)'],
        ['Version Control:', 'Git, GitHub, GitLab'],
        ['API:', 'REST API, GraphQL (базовые знания), gRPC'],
        ['Testing:', 'pytest, unittest, Postman'],
        ['Soft Skills:', 'Командная работа, аналитическое мышление, документирование, быстрое обучение'],
    ]
    
    skills_table = Table(skills_data, colWidths=[4*cm, 10*cm])
    skills_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#003366')),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 0.3*cm))
    
    # ─────── ОПЫТ РАБОТЫ
    story.append(Paragraph("<b>ОПЫТ РАБОТЫ</b>", heading_style))
    
    story.append(Paragraph("<b>Junior Backend Developer</b> — TechStartup Inc. | Jan 2023 – Dec 2023", normal_style))
    story.append(Paragraph(
        "• Разработал REST API микросервис на FastAPI для обработки пользовательских данных<br/>"
        "• Оптимизировал SQL запросы, увеличив скорость обработки на 40%<br/>"
        "• Реализовал интеграцию с внешними API (Google Maps, Stripe)<br/>"
        "• Написал unit-тесты, покрытие кода достигло 85%<br/>"
        "• Развёртывал приложения на Docker и управлял инфраструктурой через Docker Compose",
        normal_style
    ))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph("<b>Intern Backend Developer</b> — DataFlow Systems | Aug 2022 – Dec 2022", normal_style))
    story.append(Paragraph(
        "• Участвовал в разработке backend части системы аналитики данных<br/>"
        "• Работал с PostgreSQL и оптимизацией запросов<br/>"
        "• Интегрировал очередь задач (Celery) для асинхронной обработки<br/>"
        "• Документировал API endpoints",
        normal_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    # ─────── ОБРАЗОВАНИЕ
    story.append(Paragraph("<b>ОБРАЗОВАНИЕ</b>", heading_style))
    
    story.append(Paragraph(
        "<b>Бакалавр — Прикладная информатика</b><br/>"
        "НИУ ИТМО, Информационные системы | 2020 – 2024 (в процессе)<br/>"
        "GPA: 3.8/4.0",
        normal_style
    ))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph(
        "<b>Курсы и сертификаты:</b><br/>"
        "• \"The Complete FastAPI Course\" — Udemy (2023)<br/>"
        "• \"Docker & Kubernetes\" — Coursera (2023)<br/>"
        "• \"Advanced SQL\" — DataCamp (2022)",
        normal_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    # ─────── ПРОЕКТЫ
    story.append(Paragraph("<b>ПРОЕКТЫ</b>", heading_style))
    
    story.append(Paragraph(
        "<b>AI Career Matching Platform</b> — Personal Project | Feb 2024<br/>"
        "Платформа для поиска вакансий с AI анализом совместимости. FastAPI, PostgreSQL, "
        "Gemini API, Docker. GitHub: github.com/ivanov/ai-career-matching",
        normal_style
    ))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph(
        "<b>Real-time Analytics Dashboard</b> — University Project | Dec 2023<br/>"
        "Dashboard для анализа логов в реальном времени. FastAPI, WebSockets, React, "
        "PostgreSQL. Развёрнуто на Heroku.",
        normal_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    # ─────── ЯЗЫКИ
    story.append(Paragraph("<b>ЯЗЫКИ</b>", heading_style))
    story.append(Paragraph(
        "• <b>Русский</b> — Родной язык<br/>"
        "• <b>English</b> — Intermediate (B1, IELTS 6.5)<br/>"
        "• <b>中文</b> — Beginner (A1)",
        normal_style
    ))
    
    # Сборка PDF
    doc.build(story)
    print(f"✓ PDF резюме успешно создано: {pdf_path}")
    print(f"  Размер: {__import__('os').path.getsize(pdf_path) / 1024:.1f} KB")


if __name__ == "__main__":
    generate_sample_resume()
