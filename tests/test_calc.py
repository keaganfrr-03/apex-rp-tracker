from app.calc import match_net


def test_eighth_place_example():
    # 1 kill 14 + assist 14 + participation 7 = 35 combat; placement 20; entry 38
    assert match_net(14, 14, 7, 20, 38) == 17


def test_negative_game_and_entry_sign():
    assert match_net(0, 0, 0, 0, 38) == -38
    assert match_net(0, 0, 0, 0, -38) == -38   # a typed minus does not flip it
