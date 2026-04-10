def normalize_chatbot_response(raw: dict, *, conversation_id: str, chatbot_session_id: str | None) -> dict:
    reply_text = raw.get("reply") if isinstance(raw.get("reply"), str) else None
    if not reply_text:
        message_obj = raw.get("message")
        if isinstance(message_obj, dict):
            reply_text = message_obj.get("text") if isinstance(message_obj.get("text"), str) else None

    actions = raw.get("actions") if isinstance(raw.get("actions"), list) else []
    intent = raw.get("intent") if isinstance(raw.get("intent"), str) else None
    handoff_requested = bool(raw.get("handoff_requested") or (isinstance(raw.get("handoff"), dict) and raw["handoff"].get("requested")))

    return {
        "conversation_id": conversation_id,
        "session_id": chatbot_session_id,
        "status": raw.get("status") if isinstance(raw.get("status"), str) else "ok",
        "reply": {
            "text": reply_text or "",
            "actions": actions,
        },
        "intent": intent,
        "handoff": {
            "requested": handoff_requested,
            "reason": raw.get("handoff_reason") if isinstance(raw.get("handoff_reason"), str) else None,
        },
        "meta": {
            "source": "chatbot1",
            "raw": raw,
        },
    }
