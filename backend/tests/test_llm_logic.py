from app.services.llm_service import is_refusal, calibrate_confidence


# --- is_refusal ----------------------------------------------------------

def test_refusal_detected():
    assert is_refusal("Non ho trovato questa informazione nei documenti disponibili")
    assert is_refusal("Purtroppo non è presente alcun dettaglio a riguardo")

def test_normal_answer_not_refusal():
    assert not is_refusal("Le ferie spettanti sono 30 giorni l'anno.")


# --- calibrate_confidence -------------------------------------------------

def test_confidence_strong_match():
    assert calibrate_confidence(0.75, False) == 1.0

def test_confidence_weak_match():
    assert calibrate_confidence(0.35, False) == 0.0

def test_confidence_mid_match():
    c = calibrate_confidence(0.55, False)
    assert 0.4 < c < 0.6

def test_confidence_halved_when_filtered():
    assert calibrate_confidence(0.70, True) == calibrate_confidence(0.70, False) / 2

def test_confidence_bounds():
    assert calibrate_confidence(1.0, False) <= 1.0
    assert calibrate_confidence(0.0, False) >= 0.0
