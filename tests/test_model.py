"""Проверка геометрии, базисов и эквивалентности словарей исходной модели."""

import unittest
from fractions import Fraction as F

from model import (A, B, enumerate_bases, feasible, integer_optimum,
                   make_dictionary, objective, solve_2x2, vertices)


class ModelTests(unittest.TestCase):
    def test_all_six_bases_satisfy_equalities(self):
        solutions = enumerate_bases()
        self.assertEqual(len(solutions), 6)
        self.assertEqual(sum(s.feasible for s in solutions), 4)
        for solution in solutions:
            for row, rhs in zip(A, B):
                self.assertEqual(sum(a*x for a, x in zip(row, solution.values)), rhs)

    def test_geometry_matches_basic_solutions(self):
        expected = {(F(0), F(0)), (F(8), F(0)), (F(3), F(5)), (F(0), F(6))}
        self.assertEqual(set(vertices()), expected)
        self.assertEqual({s.values[:2] for s in enumerate_bases() if s.feasible}, expected)

    def test_infeasible_bases_are_retained(self):
        invalid = {s.values for s in enumerate_bases() if not s.feasible}
        self.assertEqual(invalid, {(18, 0, -20, 0), (0, 8, 0, -6)})

    def test_dictionaries_preserve_equations_and_objective(self):
        # Проверяем тождества на ненулевых небазисных значениях, а не только в вершинах.
        for solution in enumerate_bases():
            d = make_dictionary(solution.basis)
            for nonbasic in [(F(0), F(0)), (F(2, 3), F(5, 7)), (F(2), F(3))]:
                values = [F(0)]*4
                for j, value in zip(d.nonbasis, nonbasic):
                    values[j] = value
                for i, constant, row in zip(d.basis, d.constants, d.coefficients):
                    values[i] = constant + sum(a*x for a, x in zip(row, nonbasic))
                for row, rhs in zip(A, B):
                    self.assertEqual(sum(a*x for a, x in zip(row, values)), rhs)
                self.assertEqual(d.objective_constant + sum(a*x for a, x in
                                 zip(d.objective_coefficients, nonbasic)), objective(*values[:2]))

    def test_optimality_certificate_and_integer_check(self):
        d = make_dictionary((0, 1))
        self.assertEqual(d.constants, (3, 5))
        self.assertEqual(d.objective_constant, 21)
        self.assertEqual(d.objective_coefficients, (F(-3, 4), F(-1, 2)))
        self.assertEqual(integer_optimum(), (21, ((3, 5),)))

    def test_feasibility_boundaries(self):
        for point in [(0, 0), (8, 0), (3, 5), (0, 6)]:
            self.assertTrue(feasible(*point))
        for point in [(-1, 0), (0, -1), (8, 1), (0, 7)]:
            self.assertFalse(feasible(*point))

    def test_invalid_linear_system_and_basis(self):
        with self.assertRaises(ValueError):
            solve_2x2(((1, 2), (2, 4)), (1, 2))
        for basis in [(0, 0), (0, 4), (0,)]:
            with self.assertRaises(ValueError):
                make_dictionary(basis)


if __name__ == "__main__":
    unittest.main()
