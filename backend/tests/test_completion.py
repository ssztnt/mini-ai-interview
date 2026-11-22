from app.models import Finding, Sentiment, Summary
from app.services.analysis import analyze_answers, label_for
from app.services.interviews import keep_verbatim_quotes


def complete(client, interview_id):
    return client.post(f"/api/interviews/{interview_id}/complete")


def test_complete_returns_summary_and_classic_analysis(client, answered):
    r = complete(client, answered["id"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["completed_at"]
    assert body["summary"]["overview"]
    assert len(body["summary"]["findings"]) == len(body["plan"])
    assert body["analysis"]["method"] == "VADER + YAKE"
    assert len(body["analysis"]["answer_scores"]) == len(body["plan"])
    assert body["analysis"]["keywords"]


def test_complete_saves_a_json_file(client, answered, isolated_data_dir):
    complete(client, answered["id"])
    files = list(isolated_data_dir.glob(f"*_{answered['id']}.json"))
    assert len(files) == 1
    assert '"status": "completed"' in files[0].read_text()


def test_completed_interview_is_readable_and_listed(client, answered):
    complete(client, answered["id"])
    assert client.get(f"/api/interviews/{answered['id']}").json()["status"] == "completed"

    history = client.get("/api/interviews").json()
    assert [row["id"] for row in history] == [answered["id"]]
    assert history[0]["topic"] == "AI in the workplace"
    assert history[0]["sentiment"] in {"positive", "neutral", "negative", "mixed"}


def test_cannot_complete_before_all_answers(client, interview):
    client.post(f"/api/interviews/{interview['id']}/start")
    assert complete(client, interview["id"]).status_code == 409


def test_cannot_complete_twice(client, answered):
    complete(client, answered["id"])
    assert complete(client, answered["id"]).status_code == 409


def test_history_is_empty_initially(client):
    assert client.get("/api/interviews").json() == []


# ── Classic analysis ──────────────────────────────────────────


def test_vader_scores_each_answer():
    result = analyze_answers(["I absolutely love this, it is wonderful!", "This is terrible."])
    assert result.answer_scores[0] > 0.5
    assert result.answer_scores[1] < -0.3


def test_sentiment_labels():
    assert label_for([0.6, 0.7]) == "positive"
    assert label_for([-0.6, -0.4]) == "negative"
    assert label_for([0.0, 0.01]) == "neutral"
    assert label_for([0.6, -0.5]) == "mixed"


def test_keywords_are_lowercase_and_limited():
    text = "Remote work gives me flexibility. Remote work also makes collaboration harder."
    keywords = analyze_answers([text]).keywords
    assert 0 < len(keywords) <= 8
    assert all(k == k.lower() for k in keywords)


# ── Quote verification ────────────────────────────────────────


def make_summary(quotes: list[str]) -> Summary:
    return Summary(
        overview="o",
        findings=[Finding(objective=f"T{i}", finding="f", quote=q) for i, q in enumerate(quotes)],
        themes=[],
        key_points=[],
        sentiment=Sentiment(label="neutral", score=0, rationale="r"),
        emotions=[],
        keywords=[],
    )


def test_verbatim_quotes_are_kept_and_invented_ones_dropped():
    answers = ["I use it  every day for emails.", "It sometimes makes things up."]
    summary = keep_verbatim_quotes(
        make_summary(['"I use it every day"', "It often fabricates facts"]), answers
    )
    assert summary.findings[0].quote == '"I use it every day"'  # whitespace/quotes tolerated
    assert summary.findings[1].quote == ""  # paraphrase, not verbatim
