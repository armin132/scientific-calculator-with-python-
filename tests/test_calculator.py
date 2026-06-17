import unittest

from main import CalculationError, ExpressionCalculator


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.calculator = ExpressionCalculator()

    def test_basic_math(self):
        self.assertEqual(self.calculator.calculate("2 + 3 * 4"), 14)

    def test_parentheses(self):
        self.assertEqual(self.calculator.calculate("(2 + 3) * 4"), 20)

    def test_power(self):
        self.assertEqual(self.calculator.calculate("2 ^ 8"), 256)

    def test_sine_in_degrees(self):
        self.assertAlmostEqual(self.calculator.calculate("sin(30)"), 0.5, places=12)

    def test_sine_in_radians(self):
        self.calculator.angle_mode = "RAD"
        self.assertAlmostEqual(
            self.calculator.calculate("sin(pi / 2)"),
            1.0,
            places=12,
        )

    def test_inverse_sine(self):
        self.assertAlmostEqual(
            self.calculator.calculate("asin(0.5)"),
            30.0,
            places=12,
        )

    def test_factorial(self):
        self.assertEqual(self.calculator.calculate("factorial(6)"), 720)

    def test_cube_root(self):
        self.assertAlmostEqual(self.calculator.calculate("cbrt(-27)"), -3.0)

    def test_answer_value(self):
        self.calculator.answer = 42
        self.assertEqual(self.calculator.calculate("ans + 8"), 50)

    def test_memory_value(self):
        self.calculator.memory = 12.5
        self.assertEqual(self.calculator.calculate("mem * 2"), 25)

    def test_division_by_zero(self):
        with self.assertRaises(CalculationError):
            self.calculator.calculate("1 / 0")

    def test_unsafe_expression(self):
        with self.assertRaises(CalculationError):
            self.calculator.calculate("__import__('os').system('echo test')")


if __name__ == "__main__":
    unittest.main()
