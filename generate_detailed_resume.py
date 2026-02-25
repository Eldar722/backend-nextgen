"""
Расширенный генератор PDF резюме с подробными примерами для тестирования.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors


def create_detailed_resume():
    """Создает подробное резюме для тестирования парсера."""
    
    pdf_path = "sample_resume_detailed.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=0.7*cm,
        leftMargin=0.7*cm,
        topMargin=0.7*cm,
        bottomMargin=0.7*cm,
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'], fontSize=18,
        textColor=colors.HexColor('#003366'), spaceAfter=8
    )
    
    heading_style = ParagraphStyle(
        'Heading', parent=styles['Heading2'], fontSize=12,
        textColor=colors.HexColor('#003366'), spaceAfter=6, spaceBefore=6
    )
    
    normal = styles['Normal']
    
    # Заголовок
    story.append(Paragraph("<b>БОРИС АЛЕКСАНДРОВИЧ КОМАРОВ</b>", title_style))
    story.append(Paragraph("Senior Backend Developer | Python | FastAPI | Kubernetes", normal))
    story.append(Spacer(1, 0.3*cm))
    
    # Контакты
    contacts = [
        ['Email:', 'boris.komarov@techmail.com'],
        ['Phone:', '+7 (921) 234-56-78'],
        ['GitHub:', 'github.com/bkomarov'],
        ['Location:', 'Moscow, Russia'],
        ['LinkedIn:', 'linkedin.com/in/bkomarov'],
    ]
    contacts_table = Table(contacts, colWidths=[2.5*cm, 8*cm])
    contacts_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(contacts_table)
    story.append(Spacer(1, 0.4*cm))
    
    # Профиль
    story.append(Paragraph("<b>ПРОФЕССИОНАЛЬНОЕ РЕЗЮМЕ</b>", heading_style))
    profile = """
    Опытный Senior Backend разработчик с 5+ годами опыта в разработке высоконагруженных систем.
    Специализируюсь на микросервисной архитектуре, асинхронном программировании и масштабировании.
    Имею опыт работы в крупных tech компаниях (Yandex, Mail.ru) и стартапах.
    Лидировал командами до 5 человек, проводил code reviews и технические интервью.
    """
    story.append(Paragraph(profile, normal))
    story.append(Spacer(1, 0.3*cm))
    
    # Технический стек
    story.append(Paragraph("<b>ТЕХНИЧЕСКИЙ СТЕК</b>", heading_style))
    tech_data = [
        ['Языки:', 'Python 3.8-3.12, JavaScript/TypeScript, SQL, Bash'],
        ['Backend:', 'FastAPI, Django, Flask, Starlette, Aiohttp'],
        ['БД:', 'PostgreSQL, Redis, MongoDB, Elasticsearch'],
        ['DevOps:', 'Docker, Docker Compose, Kubernetes, Helm, ArgoCD'],
        ['Cloud:', 'AWS (EC2, S3, RDS), Google Cloud Platform, Yandex Cloud'],
        ['CI/CD:', 'GitHub Actions, GitLab CI, Jenkins, TeamCity'],
        ['Testing:', 'pytest, unittest, coverage, performance testing'],
        ['Tools:', 'Git, Jira, Kafka, RabbitMQ, nginx, pgAdmin'],
    ]
    tech_table = Table(tech_data, colWidths=[3*cm, 9*cm])
    tech_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#003366')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 0.3*cm))
    
    # Опыт
    story.append(Paragraph("<b>ОПЫТ РАБОТЫ</b>", heading_style))
    
    story.append(Paragraph("<b>Senior Backend Developer</b> | Yandex | Sep 2021 – Present", normal))
    story.append(Paragraph(
        "• Разработал микросервисную архитектуру для обработки 100K+ запросов/сек<br/>"
        "• Оптимизировал MongoDB queries, снизил load на 35%<br/>"
        "• Внедрил Kubernetes, автоматизировал развёртывание (ArgoCD, Helm)<br/>"
        "• Лидировал team из 4 разработчиков, провел 50+ code reviews<br/>"
        "• Создал internal library для логирования и метрик (использует вся компания)",
        normal
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>Backend Developer</b> | Mail.ru Cloud Solutions | Jan 2020 – Aug 2021", normal))
    story.append(Paragraph(
        "• Разработал REST API на FastAPI для облачного хранилища (50 млн пользователей)<br/>"
        "• Улучшил performance на 40% через async/await оптимизацию<br/>"
        "• Настроил Kafka для обработки событий в real-time<br/>"
        "• Написал 2000+ строк unit тестов (coverage 92%)<br/>"
        "• Мигрировал legacy code с Django на FastAPI",
        normal
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph("<b>Junior Backend Developer</b> | StartupX | Jun 2019 – Dec 2019", normal))
    story.append(Paragraph(
        "• Разработал REST API на Flask для SaaS платформы<br/>"
        "• Интегрировал Payment Gateway (Stripe, PayPal)<br/>"
        "• Работал с PostgreSQL, реализовал сложные SQL queries<br/>"
        "• Собрал Docker контейнеры и настроил CI/CD",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))
    
    # Образование
    story.append(Paragraph("<b>ОБРАЗОВАНИЕ</b>", heading_style))
    story.append(Paragraph(
        "<b>Magister</b> — Computer Science (Systems & Networks)<br/>"
        "Moscow Institute of Physics and Technology (MIPT) | 2017 – 2019<br/>"
        "GPA: 3.9/4.0",
        normal
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "<b>Sertificates & Courses:</b><br/>"
        "• \"System Design Interview\" — Educative (2023)<br/>"
        "• \"Kubernetes for Developers\" — Linux Academy (2022)<br/>"
        "• \"Advanced Python\" — Coursera (2021)",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))
    
    # Проекты
    story.append(Paragraph("<b>ЗНАЧИМЫЕ ПРОЕКТЫ</b>", heading_style))
    
    story.append(Paragraph(
        "<b>High-Load Chat Platform</b><br/>"
        "FastAPI + Postgres + WebSockets + Redis. 10K concurrent users. "
        "GitHub: github.com/bkomarov/chat-platform",
        normal
    ))
    story.append(Spacer(1, 0.15*cm))
    
    story.append(Paragraph(
        "<b>Data Processing Pipeline</b><br/>"
        "Kafka + Spark + Airflow. Processing 500GB/day of logs. "
        "Real-time analytics dashboards.",
        normal
    ))
    
    # Языки
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>ЯЗЫКИ</b>", heading_style))
    story.append(Paragraph(
        "Russian — Native | English — Fluent (C1, IELTS 7.5) | German — Elementary (A2)",
        normal
    ))
    
    doc.build(story)
    print(f"✓ Подробное резюме создано: {pdf_path}")
    print(f"  Размер: {__import__('os').path.getsize(pdf_path) / 1024:.1f} KB")


if __name__ == "__main__":
    create_detailed_resume()
