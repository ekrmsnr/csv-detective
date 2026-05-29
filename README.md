# 🔍 csv-detective

> Profile any CSV file instantly — column types, missing values, outliers, distributions. One command.

```bash
csv-detective data.csv
```

```
╭──────────────────────────────────────╮
│  🔍 csv-detective  data.csv          │
╰──────────────────────────────────────╯

📋 Overview
╭──────────╮  ╭──────────╮  ╭──────────╮  ╭──────────╮
│ 10,540   │  │ 12       │  │ 4.2 MB   │  │ 3.8%     │
│ Rows     │  │ Columns  │  │ File size│  │ Missing  │
╰──────────╯  ╰──────────╯  ╰──────────╯  ╰──────────╯

🗂  Column profiles
  Column           Type          Missing   Unique   Stats
  ──────────────────────────────────────────────────────
  user_id          categorical   0%        10540    usr_001 3   usr_002 2
  age              numeric       0%        72       mean 34.2   min 18   max 91
  signup_date      datetime      0%        365      —
  country          categorical   2.1%      48       US 4120   UK 1840   DE 980
  revenue          numeric       8.4%      9821     mean 142.3   ⚠ 12 outliers
  is_premium       boolean       0%        2        —

⚠  Missing values
  country   221   2.1%   ████░░░░░░░░░░░░░░░░
  revenue   885   8.4%   ████████████████░░░░

📊 Outliers (IQR method)
  revenue   12   min 0.01   max 99,999.0   mean 142.3
```

## Features

- **Auto type detection** — numeric, categorical, datetime, boolean
- **Missing value analysis** — count and percentage per column, with visual bars
- **Outlier detection** — IQR method flags suspicious values per numeric column
- **Distribution stats** — mean, median, min, max, std for numeric columns
- **Top values** — most frequent values for categorical columns
- **Duplicate row detection** — flags exact duplicate rows
- **HTML export** — shareable dark-mode report

## Installation

```bash
pip install csv-detective
```

Or from source:

```bash
git clone https://github.com/ekrmsnr/csv-detective
cd csv-detective
pip install -e .
```

## Usage

```bash
# Basic profiling
csv-detective data.csv

# Custom separator (semicolon, tab, etc.)
csv-detective data.csv --sep ";"
csv-detective data.tsv --sep "\t"

# Specify encoding
csv-detective data.csv --encoding latin-1

# Export HTML report
csv-detective data.csv --html report.html

# Disable colors (for CI/pipe)
csv-detective data.csv --no-color
```

## Options

| Flag | Default | Description |
|---|---|---|
| `file` | — | Path to the CSV file |
| `--sep CHAR` | `,` | Column separator |
| `--encoding ENC` | `utf-8` | File encoding |
| `--html FILE` | — | Export HTML report |
| `--no-color` | — | Disable rich terminal colors |

## Requirements

- Python ≥ 3.9
- `pandas`, `numpy`, `rich`

## License

MIT
