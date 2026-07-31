import json
import hashlib
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    Exam,
    Question,
    QuestionProvenance,
    StudyTask,
    Subject,
    Subscription,
    Topic,
    User,
)


def seed_tce_sp(db: Session) -> None:
    exam = db.scalar(select(Exam).where(Exam.slug == "tce-sp-2026-ti"))
    catalog = [
        ("portugues", "Língua Portuguesa", "general", 2, ["Interpretação de textos", "Gramática e redação"]),
        ("logica", "Raciocínio Lógico", "general", 2, ["Proposições e equivalências", "Análise combinatória"]),
        ("legislacao", "Legislação e Ética", "general", 2, ["Controle externo", "Ética e administração pública"]),
        ("seguranca", "Segurança da Informação", "specific", 5, ["ISO 27001 e 27002", "Criptografia e controles"]),
        ("governanca", "Governança e Auditoria de TI", "specific", 5, ["COBIT", "ITIL e auditoria"]),
        ("redes", "Redes e Infraestrutura", "specific", 4, ["TCP/IP e roteamento", "Cloud e virtualização"]),
        ("banco-dados", "Banco de Dados", "specific", 4, ["Modelagem e normalização", "SQL e transações"]),
        ("engenharia-software", "Engenharia de Software", "specific", 3, ["Arquitetura e padrões", "DevOps e qualidade"]),
        ("desenvolvimento", "Desenvolvimento de Sistemas", "specific", 3, ["APIs e web", "Algoritmos e linguagens"]),
        ("lgpd", "LGPD", "specific", 4, ["Princípios e bases legais", "Agentes e segurança"]),
    ]
    if not exam:
        exam = Exam(
            slug="tce-sp-2026-ti",
            name="Auditor de Controle Externo — TI",
            organization="TCE-SP",
            board="VUNESP",
            exam_date=date(2026, 10, 11),
            is_published=True,
        )
        for order, (slug, name, category, weight, topics) in enumerate(catalog):
            subject = Subject(
                slug=slug, name=name, category=category, weight=weight, display_order=order
            )
            subject.topics = [
                Topic(slug=f"{slug}-{index}", name=topic, difficulty=3 + (weight >= 5))
                for index, topic in enumerate(topics, start=1)
            ]
            exam.subjects.append(subject)
        db.add(exam)
        db.commit()

    owner = db.scalar(select(User).where(User.email == settings.owner_email))
    if not owner:
        owner = User(
            email=settings.owner_email,
            full_name="Juscelino Carvalho",
            password_hash=hash_password("owner-mode-disabled-password"),
            is_admin=True,
        )
        db.add(owner)
        db.flush()
        db.add(Subscription(user_id=owner.id, plan="pro", status="active"))
        db.commit()

    topics = {topic.slug: topic for topic in db.scalars(select(Topic)).all()}
    if not db.scalar(select(Question).limit(1)):
        question_data = [
            ("seguranca-1", "Na ISO/IEC 27001, qual elemento expressa os resultados pretendidos de segurança da informação?", ["Ativo", "Objetivo de segurança da informação", "Risco residual", "Declaração de aplicabilidade"], 1, "Objetivos de segurança expressam resultados a alcançar e devem ser coerentes com a política."),
            ("governanca-1", "No COBIT, qual princípio do sistema de governança trata da adaptação às necessidades da organização?", ["Abordagem holística", "Sistema dinâmico", "Distinção entre governança e gestão", "Adequação às necessidades empresariais"], 3, "O sistema de governança deve ser adaptado com fatores de desenho às necessidades da organização."),
            ("lgpd-1", "Qual base legal permite tratamento de dados pessoais para cumprir obrigação imposta por lei?", ["Consentimento", "Legítimo interesse", "Cumprimento de obrigação legal ou regulatória", "Proteção do crédito"], 2, "O artigo 7º da LGPD prevê expressamente essa base legal."),
            ("banco-dados-1", "Qual propriedade ACID garante que uma transação seja executada integralmente ou não produza efeito?", ["Consistência", "Isolamento", "Durabilidade", "Atomicidade"], 3, "Atomicidade é a característica tudo ou nada da transação."),
            ("redes-1", "Em uma rede IPv4, qual protocolo associa endereços IP a endereços MAC na rede local?", ["DNS", "ARP", "ICMP", "DHCP"], 1, "ARP resolve o endereço IPv4 conhecido para o endereço físico correspondente."),
        ]
        for topic_slug, statement, options, correct, explanation in question_data:
            db.add(Question(
                topic_id=topics[topic_slug].id,
                statement=statement,
                options=json.dumps(options, ensure_ascii=False),
                correct_option=correct,
                explanation=explanation,
                is_published=True,
            ))

    if not db.scalar(select(StudyTask).where(StudyTask.user_id == owner.id).limit(1)):
        tasks = [
            ("COBIT — objetivos e componentes", "Governança e Auditoria de TI", "theory", 35, "governanca-1"),
            ("Revisão de ISO 27001", "Revisão programada de Segurança", "review", 20, "seguranca-1"),
            ("Questões de LGPD", "Princípios e bases legais", "questions", 25, "lgpd-1"),
            ("Áudio: bases legais da LGPD", "Revisão para ouvir no trânsito", "audio", 15, "lgpd-1"),
        ]
        for title, description, kind, duration, topic_slug in tasks:
            db.add(StudyTask(
                user_id=owner.id,
                topic_id=topics[topic_slug].id,
                title=title,
                description=description,
                activity_type=kind,
                duration_minutes=duration,
                scheduled_date=date.today(),
            ))
    db.flush()
    for question in db.scalars(
        select(Question).where(~Question.provenance.has())
    ).all():
        digest = hashlib.sha256(
            f"{question.statement.strip().lower()}|{question.options}".encode("utf-8")
        ).hexdigest()
        db.add(QuestionProvenance(
            question_id=question.id,
            content_hash=digest,
            source_name=question.source,
            organization="Passa Fácil",
            rights_status="authorial",
            import_batch="seed-v1",
        ))
    db.commit()
