"""Точная модель размещения двух типов сервисов."""

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

F = Fraction
VARIABLES = ("x1", "x2", "s1", "s2")
A = ((2, 2, 1, 0), (1, 3, 0, 1))
B = (16, 18)
C = (2, 3, 0, 0)
BOUNDARIES = (
    (2, 2, 16, "2x1 + 2x2 = 16"),
    (1, 3, 18, "x1 + 3x2 = 18"),
    (1, 0, 0, "x1 = 0"),
    (0, 1, 0, "x2 = 0"),
)


def solve_2x2(matrix, rhs):
    """Решить систему двух уравнений по формулам Крамера."""
    (a, b), (c, d) = matrix
    determinant = a * d - b * c
    if determinant == 0:
        raise ValueError("Система не имеет единственного решения.")
    return (F(rhs[0] * d - b * rhs[1], determinant),
            F(a * rhs[1] - rhs[0] * c, determinant))


def feasible(x1, x2):
    return x1 >= 0 and x2 >= 0 and 2*x1 + 2*x2 <= 16 and x1 + 3*x2 <= 18


def objective(x1, x2):
    return 2*x1 + 3*x2


@dataclass(frozen=True)
class BasicSolution:
    basis: tuple
    values: tuple
    determinant: int

    @property
    def feasible(self):
        return all(value >= 0 for value in self.values)

    @property
    def value(self):
        return objective(*self.values[:2])


@dataclass(frozen=True)
class Dictionary:
    basis: tuple
    nonbasis: tuple
    constants: tuple
    coefficients: tuple
    objective_constant: Fraction
    objective_coefficients: tuple


def basis_matrix(basis):
    if len(basis) != 2 or len(set(basis)) != 2 or any(i not in range(4) for i in basis):
        raise ValueError("Базис должен содержать два разных индекса от 0 до 3.")
    return tuple(tuple(row[i] for i in basis) for row in A)


def enumerate_bases():
    """Перебрать все C(4, 2) наборов столбцов канонической модели."""
    solutions = []
    for basis in combinations(range(4), 2):
        matrix = basis_matrix(basis)
        determinant = matrix[0][0]*matrix[1][1] - matrix[0][1]*matrix[1][0]
        # Для данной модели все шесть пар невырождены.
        if determinant == 0:
            continue
        values = [F(0)] * 4
        for index, value in zip(basis, solve_2x2(matrix, B)):
            values[index] = value
        solutions.append(BasicSolution(basis, tuple(values), determinant))
    return solutions


def vertices():
    """Найти вершины независимо от перебора базисов: пересечь граничные прямые."""
    points = {}
    for first, second in combinations(BOUNDARIES, 2):
        matrix = (first[:2], second[:2])
        try:
            point = solve_2x2(matrix, (first[2], second[2]))
        except ValueError:
            continue
        if feasible(*point):
            points[point] = tuple(line[3] for line in BOUNDARIES
                                  if line[0]*point[0] + line[1]*point[1] == line[2])
    return points


def make_dictionary(basis):
    """Вычислить x_B = B^-1 b - B^-1 N x_N и строку цели."""
    basis = tuple(basis)
    matrix = basis_matrix(basis)
    nonbasis = tuple(i for i in range(4) if i not in basis)
    constants = solve_2x2(matrix, B)
    columns = [solve_2x2(matrix, (-A[0][j], -A[1][j])) for j in nonbasis]
    coefficients = tuple(tuple(column[i] for column in columns) for i in range(2))
    z0 = sum(C[i]*value for i, value in zip(basis, constants))
    costs = tuple(F(C[j]) + sum(C[basis[i]]*coefficients[i][k] for i in range(2))
                  for k, j in enumerate(nonbasis))
    return Dictionary(basis, nonbasis, constants, coefficients, z0, costs)


def integer_optimum():
    """Независимо проверить конечное множество целочисленных размещений."""
    points = [(x1, x2) for x1 in range(9) for x2 in range(7) if feasible(x1, x2)]
    best = max(objective(*point) for point in points)
    return best, tuple(point for point in points if objective(*point) == best)


def expression(constant, coefficients, names):
    result = str(constant)
    for coefficient, name in zip(coefficients, names):
        if coefficient:
            sign = " + " if coefficient > 0 else " - "
            factor = "" if abs(coefficient) == 1 else f"{abs(coefficient)}*"
            result += f"{sign}{factor}{name}"
    return result


def dictionary_text(dictionary):
    names = [VARIABLES[i] for i in dictionary.nonbasis]
    lines = ["Базис: " + ", ".join(VARIABLES[i] for i in dictionary.basis),
             "Небазисные: " + ", ".join(names)]
    for i, constant, coefficients in zip(dictionary.basis, dictionary.constants, dictionary.coefficients):
        lines.append(f"{VARIABLES[i]} = {expression(constant, coefficients, names)}")
    lines.append("z = " + expression(dictionary.objective_constant, dictionary.objective_coefficients, names))
    return "\n".join(lines)
