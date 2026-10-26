import json
import os

# Banco de teste em memória (compartilhado via StaticPool). Precisa estar setado
# ANTES de importar `app`, que cria o engine na importação.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Exam, Question, QuestionProvenance, Subject, Topic


def _question(topic, statement, options, correct, *, published=True, difficulty=3):
    return Question(
        topic_id=topic.id,
        statement=statement,
        options=json.dumps(options),
        correct_option=correct,
        explanation=f"Explicação de: {statement[:20]}",
        is_published=published,
        difficulty=difficulty,
    )


@pytest.fixture
def seeded():
    """Semeia um banco mínimo e devolve os ids/objetos úteis às asserções.

    Conteúdo:
      - exam TCE-SP (banca VUNESP) com 2 matérias;
      - q_pub: PUBLICADA, Direito Administrativo / Controle Externo, VUNESP 2025, dif 4;
      - q_pub2: PUBLICADA, Português, procedência FCC 2023, dif 2 (banca vem da procedência);
      - q_unpub: NÃO publicada (sem procedência);
      - q_owner: NÃO publicada + procedência owner_only (restrita ao dono).
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        exam = Exam(
            slug="tce-sp", name="TCE-SP", organization="Tribunal de Contas do Estado de SP",
            board="VUNESP", is_published=True,
        )
        db.add(exam)
        db.flush()

        s_adm = Subject(exam_id=exam.id, slug="direito-administrativo", name="Direito Administrativo")
        s_port = Subject(exam_id=exam.id, slug="portugues", name="Português")
        db.add_all([s_adm, s_port])
        db.flush()

        t_ce = Topic(subject_id=s_adm.id, slug="controle-externo", name="Controle Externo")
        t_int = Topic(subject_id=s_port.id, slug="interpretacao", name="Interpretação de Texto")
        db.add_all([t_ce, t_int])
        db.flush()

        q_pub = _question(
            t_ce, "Sobre o controle externo exercido pelo Tribunal de Contas...",
            ["Alt A", "Alt B", "Alt C", "Alt D"], 2, published=True, difficulty=4,
        )
        q_pub2 = _question(
            t_int, "Assinale a alternativa correta quanto à interpretação do texto...",
            ["Opção 1", "Opção 2", "Opção 3"], 0, published=True, difficulty=2,
        )
        q_unpub = _question(
            t_ce, "Questão ainda não publicada.", ["X", "Y"], 1, published=False,
        )
        q_owner = _question(
            t_ce, "Questão de material owner_only.", ["M", "N"], 0, published=False,
        )
        db.add_all([q_pub, q_pub2, q_unpub, q_owner])
        db.flush()

        db.add_all([
            QuestionProvenance(
                question_id=q_pub.id, content_hash="hash-pub", source_name="Prova TCE-SP 2025",
                board="VUNESP", exam_year=2025, rights_status="authorial",
            ),
            QuestionProvenance(
                question_id=q_pub2.id, content_hash="hash-pub2", source_name="Prova FCC 2023",
                board="FCC", exam_year=2023, rights_status="authorial",
            ),
            QuestionProvenance(
                question_id=q_owner.id, content_hash="hash-owner", source_name="Material do dono",
                board="VUNESP", exam_year=2024, rights_status="owner_only",
            ),
        ])
        db.commit()

        yield {
            "q_pub_id": str(q_pub.id),
            "q_pub2_id": str(q_pub2.id),
            "q_unpub_id": str(q_unpub.id),
            "q_owner_id": str(q_owner.id),
            "q_pub_correct": 2,
        }
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
