import argparse
import sys
from pathlib import Path

from .analyzer import CSVAnalyzer
from .display import Display


def main():
    parser = argparse.ArgumentParser(
        prog="csv-detective",
        description="Profile any CSV file — types, missing values, outliers, distributions.",
    )
    parser.add_argument("file", help="Path to the CSV file")
    parser.add_argument("--sep", default=",", help="Column separator (default: ',')")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")
    parser.add_argument("--html", metavar="FILE", help="Export HTML report to FILE")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()
    display = Display(no_color=args.no_color)

    try:
        analyzer = CSVAnalyzer(Path(args.file), sep=args.sep, encoding=args.encoding)
        display.print_header(Path(args.file).name)

        with display.progress("Reading file..."):
            analyzer.load()

        info = analyzer.file_info()
        summary = analyzer.summary()
        profiles = analyzer.column_profiles()

        display.print_file_info(info, summary)
        display.print_column_profiles(profiles)
        display.print_missing(profiles)
        display.print_outliers(profiles)

        if args.html:
            from .html_report import build_html
            html_path = Path(args.html)
            build_html(html_path, analyzer)
            display.print_success(f"HTML report saved → {html_path}")

    except ValueError as exc:
        display.print_error(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
