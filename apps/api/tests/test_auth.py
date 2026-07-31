def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_disables_cache(client):
    response = client.get("/api/v1/exams")
    assert response.headers["cache-control"].startswith("no-store")


def test_register_login_and_profile(client):
    payload = {"email": "aluno@example.com", "full_name": "Aluno Teste", "password": "senha-segura"}
    registered = client.post("/api/v1/auth/register", json=payload)
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    profile = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == payload["email"]

    logged_in = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert logged_in.status_code == 200


def test_owner_study_flow(client):
    dashboard = client.get("/api/v1/study/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["stats"]["total_tasks"] == 4

    task = dashboard.json()["tasks"][0]
    toggled = client.patch(f"/api/v1/study/tasks/{task['id']}/toggle")
    assert toggled.status_code == 200
    assert toggled.json()["is_completed"] is True

    questions = client.get("/api/v1/study/questions")
    assert questions.status_code == 200
    assert len(questions.json()) >= 5

    question = questions.json()[0]
    answered = client.post(
        f"/api/v1/study/questions/{question['id']}/answer",
        json={"selected_option": 0, "response_time_seconds": 12},
    )
    assert answered.status_code == 200
    assert "explanation" in answered.json()

    errors = client.get("/api/v1/reviews/errors")
    assert errors.status_code == 200
    assert len(errors.json()) == 1

    reviews = client.get("/api/v1/reviews/due")
    assert reviews.status_code == 200
    assert len(reviews.json()) == 1


def test_simulation_flow(client):
    created = client.post("/api/v1/simulations")
    assert created.status_code == 201
    simulation = created.json()
    assert simulation["total"] == 5

    first = simulation["questions"][0]
    saved = client.post(
        f"/api/v1/simulations/{simulation['id']}/questions/{first['question_id']}",
        json={"selected_option": 0},
    )
    assert saved.status_code == 200

    finished = client.post(f"/api/v1/simulations/{simulation['id']}/finish")
    assert finished.status_code == 200
    assert finished.json()["answered"] == 1


def test_question_import_deduplicates_and_tracks_source(client):
    payload = {
        "source_name": "Lote de teste",
        "organization": "Passa Fácil",
        "board": "Autoral",
        "exam_year": 2026,
        "rights_status": "authorial",
        "import_batch": "test-001",
        "questions": [{
            "external_key": "teste-001-q1",
            "topic_slug": "seguranca-1",
            "statement": "Qual alternativa representa um teste autoral de segurança?",
            "options": ["Alternativa A", "Alternativa B", "Alternativa C"],
            "correct_option": 1,
            "explanation": "Questão usada para validar o importador.",
        }],
    }
    first = client.post("/api/v1/question-bank/import", json=payload)
    assert first.status_code == 200
    assert first.json()["imported"] == 1
    second = client.post("/api/v1/question-bank/import", json=payload)
    assert second.status_code == 200
    assert second.json()["duplicates"] == 1


def test_pdf_inspection_creates_review_preview(client):
    from io import BytesIO

    from reportlab.pdfgen import canvas

    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    lines = [
        "1 Qual alternativa identifica a camada de transporte do modelo TCP/IP?",
        "A) Ethernet",
        "B) TCP",
        "C) IP",
        "D) ARP",
    ]
    y = 800
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 24
    pdf.save()
    stream.seek(0)

    response = client.post(
        "/api/v1/question-bank/pdf/inspect",
        data={
            "source_name": "PDF de teste autoral",
            "document_type": "exam",
            "rights_status": "authorial",
        },
        files={"file": ("teste.pdf", stream.getvalue(), "application/pdf")},
    )
    assert response.status_code == 201
    assert response.json()["page_count"] == 1
    assert response.json()["candidate_count"] == 1
    assert response.json()["status"] == "review"

    answer_stream = BytesIO()
    answer_pdf = canvas.Canvas(answer_stream)
    answer_pdf.drawString(50, 800, "GABARITO DEFINITIVO")
    answer_pdf.drawString(50, 770, "1 - B")
    answer_pdf.save()
    answer_stream.seek(0)
    answer_response = client.post(
        "/api/v1/question-bank/pdf/inspect",
        data={
            "source_name": "Gabarito de teste autoral",
            "document_type": "answer_key",
            "rights_status": "authorial",
        },
        files={"file": ("gabarito.pdf", answer_stream.getvalue(), "application/pdf")},
    )
    assert answer_response.status_code == 201
    assert answer_response.json()["answer_count"] == 1

    associated = client.post(
        "/api/v1/question-bank/pdf/associate",
        json={
            "exam_job_id": response.json()["id"],
            "answer_key_job_id": answer_response.json()["id"],
        },
    )
    assert associated.status_code == 200
    assert associated.json()["matched_answers"] == 1
    assert associated.json()["ready_for_review"] == 1

    drafts = client.get("/api/v1/question-bank/drafts")
    assert drafts.status_code == 200
    draft = drafts.json()[0]
    assert draft["page_number"] == 1
    assert draft["image_url"]
    image = client.get(draft["image_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"

    topic = client.get("/api/v1/question-bank/topics").json()[0]
    reviewed = client.patch(
        f"/api/v1/question-bank/drafts/{draft['id']}",
        json={
            "statement": draft["statement"],
            "options": draft["options"],
            "correct_option": draft["correct_option"],
            "topic_id": topic["id"],
            "reviewer_note": "Questão conferida com o recorte original.",
            "status": "reviewed",
        },
    )
    assert reviewed.status_code == 200
    published = client.post(f"/api/v1/question-bank/drafts/{draft['id']}/publish")
    assert published.status_code == 201
    assert published.json()["owner_available"] is True
