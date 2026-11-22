"""Profanity filter: tiers, disguises, false positives, and API behaviour."""

import pytest

from app.services.moderation import ContentFilter

strict = ContentFilter("mild")


@pytest.mark.parametrize(
    "text",
    [
        "What the hell is this",
        "Damn, that was slow",
        "This is shit",
        "FUCK this",
        "absolutely fucking useless",
        "fuuuuck",
        "sh1t happens",
        "what the h3ll",
    ],
)
def test_blocks_profanity_and_common_disguises(text):
    assert not strict.is_clean(text)


@pytest.mark.parametrize(
    "text",
    [
        "Hello, I use AI at work",
        "I wrote a shell script",
        "Scunthorpe is a town",
        "We need to assess the class of tools",
        "Mitochondria is the powerhouse of the cell",
        "Their prickly attitude",
    ],
)
def test_allows_innocent_words_that_contain_blocked_ones(text):
    assert strict.is_clean(text)


def test_levels_block_from_the_chosen_tier_upwards():
    moderate = ContentFilter("moderate")
    assert moderate.is_clean("what the hell")
    assert not moderate.is_clean("this is shit")
    assert not moderate.is_clean("fuck")

    strong = ContentFilter("strong")
    assert strong.is_clean("this is shit")
    assert not strong.is_clean("fuck")

    assert ContentFilter("off").is_clean("fuck this")


# ── API ──────────────────────────────────────────────────────


def test_rejected_topic_never_creates_an_interview(client):
    response = client.post("/api/interviews", json={"topic": "why work is hell"})
    assert response.status_code == 422
    assert response.json()["code"] == "inappropriate_language"
    assert client.get("/api/interviews").json() == []


def test_rejected_answer_keeps_the_question_open(client, interview):
    client.post(f"/api/interviews/{interview['id']}/start")
    response = client.post(
        f"/api/interviews/{interview['id']}/answers", json={"answer": "It's fucking great"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "inappropriate_language"

    current = client.get(f"/api/interviews/{interview['id']}").json()
    assert len(current["turns"]) == 1
    assert current["turns"][0]["answer"] is None


def test_rejected_plan_edit_keeps_the_original_plan(client, interview):
    plan = [dict(o) for o in interview["plan"]]
    plan[0]["goal"] = "Find out what the hell they do"
    response = client.put(f"/api/interviews/{interview['id']}/plan", json={"objectives": plan})
    assert response.status_code == 422

    current = client.get(f"/api/interviews/{interview['id']}").json()
    assert current["plan"] == interview["plan"]
