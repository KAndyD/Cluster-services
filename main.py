"""Расчёт задания, текстовый вывод и построение допустимой области."""

import argparse
import json
from math import atan2
from pathlib import Path

from model import (VARIABLES, dictionary_text, enumerate_bases, integer_optimum,
                   make_dictionary, objective, vertices)


def build_report():
    solutions = enumerate_bases()
    points = vertices()
    best = max((s for s in solutions if s.feasible), key=lambda s: s.value)
    lines = [
        "РАЗМЕЩЕНИЕ ИНФЕРЕНС-СЕРВИСОВ В КЛАСТЕРЕ",
        "", "А. ФОРМАЛИЗАЦИЯ",
        "x1 — число лёгких сервисов; x2 — число тяжёлых сервисов.",
        "Максимизируем z = 2x1 + 3x2.",
        "Память: 2x1 + 2x2 <= 16. vCPU: x1 + 3x2 <= 18. x1, x2 >= 0.",
        "Каноническая форма:",
        "2x1 + 2x2 + s1 = 16; x1 + 3x2 + s2 = 18; x1, x2, s1, s2 >= 0.",
        "s1 — свободная память, s2 — свободные vCPU.",
        "", "Б. ГЕОМЕТРИЯ", "Вершина | Активные границы | z",
    ]
    for point, boundaries in points.items():
        lines.append(f"({point[0]}, {point[1]}) | {'; '.join(boundaries)} | {objective(*point)}")
    lines += ["Вектор роста цели c = (2, 3). Линии уровня: 2x1 + 3x2 = z.",
              "Последняя общая точка области и сдвигаемой линии уровня — (3, 5), z = 21.",
              "", "В. ВСЕ БАЗИСНЫЕ РЕШЕНИЯ", "Базис | det B | (x1, x2, s1, s2) | Допустимость | z"]
    for solution in solutions:
        names = ", ".join(VARIABLES[i] for i in solution.basis)
        values = ", ".join(map(str, solution.values))
        reason = "да" if solution.feasible else "нет: " + ", ".join(
            f"{VARIABLES[i]} = {value} < 0" for i, value in enumerate(solution.values) if value < 0)
        lines.append(f"{names} | {solution.determinant} | ({values}) | {reason} | {solution.value}")
    for title, basis in [("Стартовый словарь", (2, 3)),
                         ("Промежуточный словарь", (1, 2)),
                         ("Оптимальный словарь", best.basis)]:
        lines += ["", title, dictionary_text(make_dictionary(basis))]
    value, integer_points = integer_optimum()
    lines += ["", "РЕЗУЛЬТАТ", f"Лёгкие: {best.values[0]}; тяжёлые: {best.values[1]}; эффект: {best.value}.",
              f"Свободная память: {best.values[2]}; свободные vCPU: {best.values[3]}.",
              "z = 21 - 3/4*s1 - 1/2*s2 <= 21, поскольку s1, s2 >= 0.",
              f"Целочисленная проверка: z = {value}, оптимальные размещения: {integer_points}.",
              "Оптимум ЛП целочисленный и единственный; округление не требуется."]
    payload = {
        "variable_order": VARIABLES,
        "bases": [{"basis": [VARIABLES[i] for i in s.basis], "determinant": s.determinant,
                   "values": [str(x) for x in s.values], "feasible": s.feasible,
                   "objective": str(s.value)} for s in solutions],
        "vertices": [{"point": [str(x) for x in p], "active_boundaries": active,
                      "objective": str(objective(*p))} for p, active in points.items()],
        "optimum": {"light": int(best.values[0]), "heavy": int(best.values[1]),
                    "effect": int(best.value), "memory_used": 16, "vcpu_used": 18},
        "integer_optima": integer_points,
    }
    return "\n".join(lines) + "\n", payload


def draw_plot(output_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError("Для графика установите зависимости: python -m pip install -r requirements.txt. "
                           "Или запустите расчёт с --no-plot.") from error

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")
    points = list(vertices())
    center = (sum(p[0] for p in points)/len(points), sum(p[1] for p in points)/len(points))
    points.sort(key=lambda p: atan2(float(p[1]-center[1]), float(p[0]-center[0])))
    ax.fill([float(p[0]) for p in points], [float(p[1]) for p in points],
            color="#cbded8", alpha=0.8, label="Допустимая область", zorder=1)
    xs = [i/100 for i in range(951)]
    ax.plot(xs, [(16-2*x)/2 for x in xs], color="#2563eb", lw=2,
            label=r"Память: $2x_1+2x_2=16$")
    ax.plot(xs, [(18-x)/3 for x in xs], color="#d97706", lw=2,
            label=r"vCPU: $x_1+3x_2=18$")
    ax.plot(xs, [(21-2*x)/3 for x in xs], color="#7c3aed", ls="--", lw=2,
            label=r"Оптимальный уровень: $2x_1+3x_2=21$")
    ax.plot(xs, [(12-2*x)/3 for x in xs], color="#7c3aed", ls=":", lw=1.2, alpha=0.55,
            label=r"Линия уровня: $z=12$")
    # Нормаль к линиям уровня имеет то же направление, что и c = (2, 3).
    ax.annotate("", xy=(3, 3.5), xytext=(1, 0.5),
                arrowprops={"arrowstyle": "->", "color": "#334155", "lw": 2})
    ax.text(0.35, 3.25, r"$c=(2,3)$" + "\nрост эффекта", color="#334155")
    offsets = {(0, 0): (10, 12), (8, 0): (-85, 12), (0, 6): (10, 12), (3, 5): (24, 20)}
    for point in points:
        x, y = map(float, point)
        optimal = point == (3, 5)
        ax.scatter(x, y, s=150 if optimal else 45, marker="*" if optimal else "o",
                   color="#15803d" if optimal else "#0f172a", zorder=5)
        label = f"({point[0]}, {point[1]}) · z = {objective(*point)}"
        if optimal:
            label = "Оптимум\n" + label
        ax.annotate(label, (x, y), xytext=offsets[point], textcoords="offset points",
                    fontsize=11, fontweight="bold" if optimal else "normal",
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 3})
    ax.set(xlim=(-0.4, 9.5), ylim=(-0.4, 8.7),
           xlabel=r"Лёгкие сервисы, $x_1$", ylabel=r"Тяжёлые сервисы, $x_2$")
    ax.set_title("Размещение сервисов при ограничениях памяти и vCPU\n"
                 "3 лёгких + 5 тяжёлых → эффект 21", loc="left", fontsize=15, pad=18)
    ax.set_xticks(range(10))
    ax.set_yticks(range(9))
    ax.set_aspect("equal", adjustable="box")
    ax.axhline(0, color="#64748b", lw=0.8)
    ax.axvline(0, color="#64748b", lw=0.8)
    ax.grid(alpha=0.15)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.95)
    fig.savefig(output_dir / "feasible_region.png", dpi=180)
    fig.savefig(output_dir / "feasible_region.svg")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="ЛП: размещение лёгких и тяжёлых инференс-сервисов.")
    parser.add_argument("--no-plot", action="store_true", help="Расчёт без matplotlib и графиков")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "results",
                        help="Папка результатов (по умолчанию results рядом со скриптом)")
    args = parser.parse_args()
    report, payload = build_report()
    print(report)
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "solution.txt").write_text(report, encoding="utf-8")
        (args.output_dir / "solution.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.no_plot:
            draw_plot(args.output_dir)
    except (OSError, RuntimeError) as error:
        parser.exit(1, f"Ошибка: {error}\n")
    print(f"Результаты: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
