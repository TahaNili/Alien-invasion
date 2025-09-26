import math
from src.bullet import ShipBullet


class DummyShip:
    def __init__(self):
        self.rect = type('R', (), {'centerx': 400, 'centery': 300})
        self.center = [400.0, 300.0]
        self.angle = 0.0


def test_fire_parity_override():
    s = DummyShip()
    sb = ShipBullet(s)
    # default angle is ship.angle
    assert sb.angle == 0.0
    # override to PI/2
    sb.set_angle_override(math.pi/2, s)
    assert abs(sb.angle - math.pi/2) < 1e-9


def test_fire_parity_nose_position():
    s = DummyShip()
    sb = ShipBullet(s)
    # ship nose offset at angle 0.0
    # expected y decrease by ~30
    assert sb.rect.centery == s.rect.centery - 30
