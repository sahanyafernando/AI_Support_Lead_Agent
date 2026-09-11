from lead_scoring import calculate_lead_score


def test_hot_lead_score():
    result = calculate_lead_score(75, 15000, 30, True)
    assert result.score == 95
    assert result.status == "HOT"


def test_warm_lead_score():
    result = calculate_lead_score(20, 1500, 120, False)
    assert result.score == 40
    assert result.status == "WARM"


def test_cold_when_information_missing():
    result = calculate_lead_score()
    assert result.score == 0
    assert result.status == "COLD"
