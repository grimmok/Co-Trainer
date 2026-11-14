import copy, pytest
from cotrainer.guard import assert_public, HiddenValueError

OK = {"meta": {}, "coach": {"coaching": {"Taktik": "Gut"}, "mental": {}, "tendencies": ["Taktiktüftler"]},
      "squad": [{"id": 1, "a": {"Pas": 12}}], "pool": []}


def test_clean_data_passes():
    assert assert_public(OK) is OK


@pytest.mark.parametrize("path,key,value", [
    (("squad", 0), "ca", 120), (("squad", 0), "PA", 150), (("squad", 0), "pers", [1] * 8),
    (("squad", 0, "a"), "Cons", 9), (("squad", 0, "a"), "InjPr", 12), (("meta",), "q", 3),
])
def test_forbidden_keys_raise(path, key, value):
    d = copy.deepcopy(OK); node = d
    for p in path: node = node[p]
    node[key] = value
    with pytest.raises(HiddenValueError):
        assert_public(d)


def test_unknown_attribute_key_raises():
    d = copy.deepcopy(OK); d["squad"][0]["a"]["Geheim"] = 3
    with pytest.raises(HiddenValueError, match=r"squad\[0\]\.a\.Geheim"):
        assert_public(d)


def test_coach_numbers_raise():
    d = copy.deepcopy(OK); d["coach"]["coaching"]["Taktik"] = 16
    with pytest.raises(HiddenValueError):
        assert_public(d)


def test_numeric_tendencies_raise():
    d = copy.deepcopy(OK); d["coach"]["tendencies"] = {"Offensive": 10}
    with pytest.raises(HiddenValueError):
        assert_public(d)


@pytest.mark.save
def test_real_result_is_public(ravenna_data):
    assert_public(ravenna_data)
