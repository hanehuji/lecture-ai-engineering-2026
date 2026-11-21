from types import SimpleNamespace
from unittest.mock import Mock

from app import ask as ask_module


def test_main_reuses_chat_for_follow_up_questions(monkeypatch):
    chat = Mock()
    chat.send_message.side_effect = [
        SimpleNamespace(text="first answer", usage_metadata=None),
        SimpleNamespace(text="follow-up answer", usage_metadata=None),
    ]
    client = Mock()
    client.chats.create.return_value = chat
    monkeypatch.setattr(ask_module.genai, "Client", Mock(return_value=client))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("sys.argv", ["app.ask", "initial question"])
    monkeypatch.setattr("builtins.input", Mock(side_effect=["follow-up question", "exit"]))

    ask_module.main()

    client.chats.create.assert_called_once_with(model=ask_module.MODEL)
    assert [call.args[0] for call in chat.send_message.call_args_list] == [
        "initial question",
        "follow-up question",
    ]