from __future__ import annotations

from contextlib import contextmanager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box


_BAR_WIDTH = 20


def _bar(value: float, max_val: float, width: int = _BAR_WIDTH) -> str:
    if max_val == 0:
        return "░" * width
    filled = int(value / max_val * width)
    return "█" * filled + "░" * (width - filled)


_TYPE_COLORS = {
    "numeric": "cyan",
    "categorical": "magenta",
    "datetime": "green",
    "boolean": "yellow",
}


class Display:
    def __init__(self, no_color: bool = False) -> None:
        self.console = Console(no_color=no_color, highlight=False)

    def print_header(self, filename: str) -> None:
        title = Text()
        title.append("🔍 csv-detective", style="bold white")
        title.append(f"  {filename}", style="dim")
        self.console.print()
        self.console.print(Panel(title, border_style="bright_magenta", padding=(0, 2)))

    def print_success(self, msg: str) -> None:
        self.console.print(f"\n[bold green]✓[/] {msg}")

    def print_error(self, msg: str) -> None:
        self.console.print(f"\n[bold red]✗ Error:[/] {msg}")

    @contextmanager
    def progress(self, label: str):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as prog:
            prog.add_task(label, total=None)
            yield

    # ------------------------------------------------------------------ #
    #  File info                                                           #
    # ------------------------------------------------------------------ #

    def print_file_info(self, info: dict, summary: dict) -> None:
        self.console.print("\n[bold]📋 Overview[/]", style="bright_magenta")

        missing_pct = round(info["missing_cells"] / max(info["total_cells"], 1) * 100, 1)

        cards = [
            _metric(str(info["rows"]), "Rows"),
            _metric(str(info["columns"]), "Columns"),
            _metric(info["file_size"], "File size"),
            _metric(str(info["duplicate_rows"]), "Duplicate rows"),
            _metric(f"{missing_pct}%", "Missing data"),
            _metric(str(summary["numeric_cols"]), "Numeric cols"),
            _metric(str(summary["categorical_cols"]), "Categorical cols"),
        ]
        self.console.print(Columns(cards, equal=False, padding=(0, 2)))

    # ------------------------------------------------------------------ #
    #  Column profiles                                                     #
    # ------------------------------------------------------------------ #

    def print_column_profiles(self, profiles: list[dict]) -> None:
        self.console.print("\n[bold]🗂  Column profiles[/]", style="bright_magenta")

        table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim")
        table.add_column("Column", min_width=20)
        table.add_column("Type", width=12)
        table.add_column("Missing", justify="right", width=14)
        table.add_column("Unique", justify="right", width=8)
        table.add_column("Stats / Top values", min_width=30)

        for p in profiles:
            color = _TYPE_COLORS.get(p["type"], "white")
            type_tag = f"[{color}]{p['type']}[/]"

            missing_str = (
                f"[red]{p['missing_pct']}%[/]"
                if p["missing_pct"] > 0
                else "[dim]0%[/]"
            )

            if p["type"] == "numeric":
                stats = (
                    f"[dim]mean[/] [white]{p.get('mean', '—')}[/]  "
                    f"[dim]min[/] [white]{p.get('min', '—')}[/]  "
                    f"[dim]max[/] [white]{p.get('max', '—')}[/]"
                )
                if p.get("outliers", 0) > 0:
                    stats += f"  [yellow]⚠ {p['outliers']} outliers[/]"
            elif p["type"] == "categorical":
                top = p.get("top_values", [])
                stats = "  ".join(
                    f"[dim]{v['value']}[/] [white]{v['count']}[/]"
                    for v in top[:3]
                )
            else:
                stats = "[dim]—[/]"

            table.add_row(
                f"[bold]{p['name']}[/]",
                type_tag,
                missing_str,
                str(p["unique"]),
                stats,
            )

        self.console.print(table)

    # ------------------------------------------------------------------ #
    #  Missing values                                                      #
    # ------------------------------------------------------------------ #

    def print_missing(self, profiles: list[dict]) -> None:
        missing = [p for p in profiles if p["missing"] > 0]
        if not missing:
            self.console.print("\n[bold green]✓ No missing values found.[/]")
            return

        self.console.print("\n[bold]⚠  Missing values[/]", style="bright_magenta")
        table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim")
        table.add_column("Column", min_width=20)
        table.add_column("Missing", justify="right")
        table.add_column("%", justify="right")
        table.add_column("", min_width=22)

        max_pct = max(p["missing_pct"] for p in missing)
        for p in sorted(missing, key=lambda x: x["missing_pct"], reverse=True):
            bar = _bar(p["missing_pct"], max_pct)
            color = "red" if p["missing_pct"] > 20 else "yellow"
            table.add_row(
                p["name"],
                str(p["missing"]),
                f"[{color}]{p['missing_pct']}%[/]",
                f"[dim]{bar}[/]",
            )
        self.console.print(table)

    # ------------------------------------------------------------------ #
    #  Outliers                                                            #
    # ------------------------------------------------------------------ #

    def print_outliers(self, profiles: list[dict]) -> None:
        outliers = [p for p in profiles if p["type"] == "numeric" and p.get("outliers", 0) > 0]
        if not outliers:
            self.console.print("\n[bold green]✓ No outliers detected.[/]")
            return

        self.console.print("\n[bold]📊 Outliers (IQR method)[/]", style="bright_magenta")
        table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim")
        table.add_column("Column", min_width=20)
        table.add_column("Outliers", justify="right")
        table.add_column("Min", justify="right")
        table.add_column("Max", justify="right")
        table.add_column("Mean", justify="right")
        table.add_column("Std", justify="right")

        for p in sorted(outliers, key=lambda x: x["outliers"], reverse=True):
            table.add_row(
                p["name"],
                f"[yellow]{p['outliers']}[/]",
                str(p.get("min", "—")),
                str(p.get("max", "—")),
                str(p.get("mean", "—")),
                str(p.get("std", "—")),
            )
        self.console.print(table)
        self.console.print()


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _metric(value: str, label: str) -> Panel:
    content = Text()
    content.append(value + "\n", style="bold white")
    content.append(label, style="dim")
    return Panel(content, border_style="dim", padding=(0, 1), width=18)
