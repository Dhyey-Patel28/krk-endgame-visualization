# KRK Endgame Visualization Dashboard

Interactive visual analytics project for the King-and-Rook vs King (KRK) chess endgame.

This repository studies how generic multidimensional previews compare with board-native visualizations for static chess positions. The dashboard is organized as a progression from simple supporting views to custom chess-specific views.

## Overview

The dashboard includes:

- a PCA 2D preview used only as a supporting baseline
- a sample-position board showing that each record is a static board state
- an endgame sunburst for representative continuation structure
- board heatmaps for move origins and destinations
- a piece-flow view for aggregated movement patterns

The goal is to show why a standard 2D projection is not sufficient for KRK and why board-aware visual encodings are more effective for this dataset.

## Dataset

The dataset used here is the KRK endgame dataset (`krkopt.data`).

Each row represents a **single static chess position**, not a full game or move history. Each record contains:

- white king position
- white rook position
- black king position
- a target label describing draw or optimal depth-to-win

## Repository structure

A typical project layout is:

```text
.
├─ README.md
├─ LICENSE
├─ .gitignore
├─ vercel.json
├─ build_dashboard.py
├─ prepare_krk.py
├─ engine_krk.py
├─ viz_data.py
├─ viz_template.py
├─ viz_previsualization.py
├─ viz_heatmap.py
├─ viz_piece_flow.py
├─ viz_endgame_sunburst.py
├─ data/
│  ├─ krkopt.data
│  ├─ krk_clean.csv
│  ├─ krk_clean.json
│  ├─ krk_baseline.csv
│  ├─ krk_baseline.json
│  ├─ krk_engine_full.csv
│  └─ krk_engine_full.json
├─ public/
│  └─ krk_dashboard.html
├─ vendor/
│  └─ chess-dataviz/
│     ├─ ChessDataViz.js
│     └─ ChessDataViz.css
└─ third_party/
   └─ stockfish/
      ├─ stockfish-windows-x86-64-avx2.exe
      └─ COPYING.txt
```

## Workflow

### 1. Data preparation

`prepare_krk.py` performs the preprocessing stage:

- loads the original KRK data
- encodes files `a..h` as numeric coordinates `1..8`
- converts textual mate-depth labels to numeric values
- buckets targets into:
  - `draw`
  - `win_0_2`
  - `win_3_5`
  - `win_6_9`
  - `win_10_plus`
- creates derived chess-specific features
- generates square labels and FEN strings
- exports cleaned and baseline-ready files

### 2. Engine augmentation

`engine_krk.py` uses Stockfish offline to:

- validate representative positions
- compute best moves
- extract PV lines
- export engine-enriched data for board-native visualizations

### 3. Dashboard generation

`build_dashboard.py` assembles the final HTML dashboard from modular visualization sections.

## Visualizations

### PCA 2D preview
A supporting baseline only. It gives a quick generic projection and helps justify why PCA 2D is not the main presentation.

### Sample static positions
Shows representative board states from the dataset and makes clear that the original data consists of isolated positions rather than move sequences.

### Endgame tree
An endgame-adapted sunburst inspired by opening visualizations, with a chessboard in the center for representative continuation playback.

### Heatmaps
Shows where engine-recommended moves tend to start or end on the board.

### Piece flow
Shows aggregated movement tendencies for the white rook, white king, and black king.

## Running the project

Install the required Python packages:

```bash
pip install pandas numpy scikit-learn python-chess
```

If Stockfish is used locally, place the executable in:

```text
third_party/stockfish/
```

Build data files in this order:

```bash
python prepare_krk.py
python engine_krk.py
python build_dashboard.py
```

The final static dashboard is written to:

```text
public/krk_dashboard.html
```

## Static deployment

The generated dashboard is designed to work as a static site. The main deployed asset is the built HTML page together with any required local data, vendor files, and static assets.

## Credits and inspiration

The board-centric interaction style and visual inspiration for several parts of this project were informed by ebemunk’s work:

- *A Visual Look at 2 Million Chess Games*
- *chess-dataviz*

Original sources:

- https://blog.ebemunk.com/a-visual-look-at-2-million-chess-games/
- https://ebemunk.com/chess-dataviz/
- https://github.com/ebemunk/chess-dataviz

This project uses a different dataset and custom KRK-specific preprocessing, engine analysis, and visualization logic.

## Stockfish note

Stockfish was downloaded from:

- https://stockfishchess.org/download/

The project uses Stockfish only for **offline engine analysis** during data preparation.

If Stockfish binaries are included in this repository, the corresponding Stockfish license and notices should be preserved in `third_party/stockfish/`.

Official Stockfish sources:

- https://stockfishchess.org/
- https://github.com/official-stockfish/stockfish

## License

The original code in this repository is licensed under the MIT License.

Third-party components keep their own licenses:
- Stockfish: GPLv3
- chess-dataviz: see its original repository and license