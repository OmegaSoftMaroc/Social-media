import pipeline.run_daily as rd


def test_main_alerts_telegram_on_failure(monkeypatch):
    sent = {}

    def boom():
        raise RuntimeError("Aucun bloc JSON dans la sortie du curator")

    monkeypatch.setattr(rd, "run", boom)
    monkeypatch.setattr(rd, "send_telegram", lambda t: sent.__setitem__("text", t))

    assert rd.main() == 1
    assert "ÉCHEC" in sent["text"]
    assert "Aucun bloc JSON" in sent["text"]


def test_main_ok_no_alert(monkeypatch):
    called = {"send": False}
    monkeypatch.setattr(rd, "run", lambda: 5)
    monkeypatch.setattr(rd, "send_telegram",
                        lambda t: called.__setitem__("send", True))
    assert rd.main() == 0
    assert called["send"] is False


def test_main_survives_alert_failure(monkeypatch):
    """Si l'envoi Telegram échoue aussi, main ne doit pas lever (exit 1 propre)."""
    def boom():
        raise RuntimeError("panne pipeline")

    def send_fail(_):
        raise ConnectionError("telegram down")

    monkeypatch.setattr(rd, "run", boom)
    monkeypatch.setattr(rd, "send_telegram", send_fail)
    assert rd.main() == 1
