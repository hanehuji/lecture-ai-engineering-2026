"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_save_learning_log_appends_json_lines(monkeypatch, tmp_path):
    log_path = tmp_path / "learning_log" / "records.jsonl"
    monkeypatch.setattr(tools, "LEARNING_LOG_PATH", log_path)

    tools.save_learning_log("RAG", "検索結果を使って回答を補強する", "評価方法を調べる")
    tools.save_learning_log("LoRA", "追加学習の手法", "QLoRAとの違いを整理する")

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    assert records[0]["topic"] == "RAG"
    assert records[0]["learned"] == "検索結果を使って回答を補強する"
    assert records[0]["next_step"] == "評価方法を調べる"
    assert records[0]["saved_at"]


def test_save_learning_log_requires_topic_and_learned_content(monkeypatch, tmp_path):
    log_path = tmp_path / "records.jsonl"
    monkeypatch.setattr(tools, "LEARNING_LOG_PATH", log_path)

    result = tools.save_learning_log(" ", "学んだこと")

    assert "保存できません" in result
    assert not log_path.exists()


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
