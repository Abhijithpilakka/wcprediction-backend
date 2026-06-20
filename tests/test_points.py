"""
Tests for the points calculation engine.
Run with: pytest tests/
"""
import pytest
from app.services.points import calc_points, calc_base_points


class TestBasePoints:
    def test_exact_score(self):
        assert calc_base_points(2, 1, 2, 1) == 6

    def test_correct_winner_and_goal_diff(self):
        # 3-1 vs actual 2-0 → same diff (+2) same winner
        assert calc_base_points(3, 1, 2, 0) == 4

    def test_correct_winner_only(self):
        assert calc_base_points(2, 0, 3, 1) == 3

    def test_correct_draw(self):
        assert calc_base_points(1, 1, 2, 2) == 3

    def test_one_team_score_correct(self):
        assert calc_base_points(2, 0, 2, 3) == 1

    def test_wrong_prediction(self):
        assert calc_base_points(0, 0, 3, 1) == 0

    def test_exact_draw(self):
        assert calc_base_points(0, 0, 0, 0) == 6


class TestMultiplier:
    def test_group_stage(self):
        assert calc_points(2, 1, 2, 1, 1.0) == 6

    def test_round_of_16(self):
        assert calc_points(2, 1, 2, 1, 1.2) == 7  # 6 * 1.2 = 7.2 → 7

    def test_quarter_final(self):
        assert calc_points(2, 1, 2, 1, 1.5) == 9

    def test_semi_final(self):
        assert calc_points(2, 1, 2, 1, 1.8) == 11  # 6 * 1.8 = 10.8 → 11

    def test_final(self):
        assert calc_points(2, 1, 2, 1, 2.5) == 15

    def test_wrong_with_multiplier(self):
        assert calc_points(0, 0, 3, 1, 2.5) == 0
