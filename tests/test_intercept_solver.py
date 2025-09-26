import math

# Smoke test for the intercept solver used in ai_manager.act
# We re-implement the small helper to ensure math is stable.

def intercept_time(rx, ry, vax, vay, b_speed):
    rv = rx * vax + ry * vay
    vv = vax * vax + vay * vay
    rr = rx * rx + ry * ry
    a_q = vv - b_speed * b_speed
    b_q = 2 * rv
    c_q = rr
    if abs(a_q) < 1e-6:
        if abs(b_q) > 1e-6:
            tt = -c_q / b_q
            return tt if tt > 0 else None
        return None
    disc = b_q * b_q - 4 * a_q * c_q
    if disc < 0:
        return None
    sd = math.sqrt(disc)
    t1 = (-b_q + sd) / (2 * a_q)
    t2 = (-b_q - sd) / (2 * a_q)
    candidates = [x for x in (t1, t2) if x > 0]
    return min(candidates) if candidates else None


def test_intercept_stationary_target():
    # stationary target at (100,0), bullet speed 50 units/sec
    t = intercept_time(100, 0, 0, 0, 50)
    assert t is not None
    # expected approx 2.0
    assert abs(t - 2.0) < 0.1


def test_intercept_moving_away():
    # target at (100,0) moving directly away at 10 units/sec, bullet speed 50
    t = intercept_time(100, 0, 10, 0, 50)
    assert t is not None
