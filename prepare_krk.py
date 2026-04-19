from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = BASE_DIR / "data" / "krkopt.data"

OUTPUT_CSV = BASE_DIR / "data" / "krk_clean.csv"
OUTPUT_JSON = BASE_DIR / "data" / "krk_clean.json"
OUTPUT_BASELINE_CSV = BASE_DIR / "data" / "krk_baseline.csv"
OUTPUT_BASELINE_JSON = BASE_DIR / "data" / "krk_baseline.json"
OUTPUT_ATLAS_JSON = BASE_DIR / "data" / "krk_atlas_data.json"

FILE_TO_NUM = {c: i for i, c in enumerate("abcdefgh", start=1)}
NUM_TO_FILE = {i: c for c, i in FILE_TO_NUM.items()}

WORD_TO_INT = {
    "draw": -1,
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
}

BUCKET_ORDER = ["draw", "win_0_2", "win_3_5", "win_6_9", "win_10_plus"]

PIECE_COLUMNS = {
    "black_king": ("bk_file", "bk_rank"),
    "white_king": ("wk_file", "wk_rank"),
    "white_rook": ("wr_file", "wr_rank"),
}


def chebyshev_distance(x1, y1, x2, y2):
    return np.maximum((x1 - x2).abs(), (y1 - y2).abs())


def manhattan_distance(x1, y1, x2, y2):
    return (x1 - x2).abs() + (y1 - y2).abs()


def euclidean_distance(x1, y1, x2, y2):
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def nearest_edge_distance(x, y):
    return pd.concat([x - 1, 8 - x, y - 1, 8 - y], axis=1).min(axis=1)


def nearest_corner_distance(x, y):
    corners = [(1, 1), (1, 8), (8, 1), (8, 8)]
    dists = [np.maximum((x - cx).abs(), (y - cy).abs()) for cx, cy in corners]
    return pd.concat(dists, axis=1).min(axis=1)


def distance_to_center_region(x, y):
    centers = [(4, 4), (4, 5), (5, 4), (5, 5)]
    dists = [np.maximum((x - cx).abs(), (y - cy).abs()) for cx, cy in centers]
    return pd.concat(dists, axis=1).min(axis=1)


def target_bucket(depth: int) -> str:
    if depth == -1:
        return "draw"
    if 0 <= depth <= 2:
        return "win_0_2"
    if 3 <= depth <= 5:
        return "win_3_5"
    if 6 <= depth <= 9:
        return "win_6_9"
    return "win_10_plus"


def square_name(file_num: int, rank_num: int) -> str:
    return f"{NUM_TO_FILE[int(file_num)]}{int(rank_num)}"


def build_fen_row(wk_file: int, wk_rank: int, wr_file: int, wr_rank: int, bk_file: int, bk_rank: int) -> str:
    board = [["" for _ in range(8)] for _ in range(8)]

    board[8 - int(wk_rank)][int(wk_file) - 1] = "K"
    board[8 - int(wr_rank)][int(wr_file) - 1] = "R"
    board[8 - int(bk_rank)][int(bk_file) - 1] = "k"

    fen_rows = []
    for row in board:
        empty_count = 0
        fen_row = ""
        for cell in row:
            if cell == "":
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += cell
        if empty_count > 0:
            fen_row += str(empty_count)
        fen_rows.append(fen_row)

    board_part = "/".join(fen_rows)

    # White to move, no castling, no en passant, halfmove 0, fullmove 1
    return f"{board_part} w - - 0 1"


def load_krk(path: Path) -> pd.DataFrame:
    cols = [
        "wk_file", "wk_rank",
        "wr_file", "wr_rank",
        "bk_file", "bk_rank",
        "target_raw",
    ]
    df = pd.read_csv(path, header=None, names=cols)

    for col in ["wk_file", "wr_file", "bk_file"]:
        df[col] = df[col].map(FILE_TO_NUM)

    df["target_depth"] = df["target_raw"].map(WORD_TO_INT)

    if df["target_depth"].isna().any():
        bad = df.loc[df["target_depth"].isna(), "target_raw"].unique().tolist()
        raise ValueError(f"Unexpected target labels: {bad}")

    df["target_bucket"] = df["target_depth"].apply(target_bucket)
    df["target_bucket"] = pd.Categorical(
        df["target_bucket"],
        categories=BUCKET_ORDER,
        ordered=True,
    )

    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    wkx, wky = df["wk_file"], df["wk_rank"]
    wrx, wry = df["wr_file"], df["wr_rank"]
    bkx, bky = df["bk_file"], df["bk_rank"]

    df["bk_edge_dist"] = nearest_edge_distance(bkx, bky)
    df["bk_corner_dist"] = nearest_corner_distance(bkx, bky)
    df["bk_center_dist"] = distance_to_center_region(bkx, bky)

    df["wk_bk_chebyshev"] = chebyshev_distance(wkx, wky, bkx, bky)
    df["wr_bk_manhattan"] = manhattan_distance(wrx, wry, bkx, bky)
    df["wk_wr_chebyshev"] = chebyshev_distance(wkx, wky, wrx, wry)

    df["wk_bk_euclidean"] = euclidean_distance(wkx, wky, bkx, bky)
    df["wr_bk_euclidean"] = euclidean_distance(wrx, wry, bkx, bky)

    df["wr_bk_aligned"] = ((wrx == bkx) | (wry == bky)).astype(int)
    df["wk_support_close"] = (df["wk_bk_chebyshev"] <= 2).astype(int)

    df["bk_on_edge"] = (df["bk_edge_dist"] == 0).astype(int)
    df["bk_in_corner"] = (df["bk_corner_dist"] == 0).astype(int)

    df["wk_square"] = [square_name(f, r) for f, r in zip(df["wk_file"], df["wk_rank"])]
    df["wr_square"] = [square_name(f, r) for f, r in zip(df["wr_file"], df["wr_rank"])]
    df["bk_square"] = [square_name(f, r) for f, r in zip(df["bk_file"], df["bk_rank"])]

    df["position_id"] = np.arange(len(df))
    df["active_color"] = "w"
    df["fullmove_number"] = 1
    df["fen"] = [
        build_fen_row(wkf, wkr, wrf, wrr, bkf, bkr)
        for wkf, wkr, wrf, wrr, bkf, bkr in zip(
            df["wk_file"], df["wk_rank"],
            df["wr_file"], df["wr_rank"],
            df["bk_file"], df["bk_rank"]
        )
    ]

    return df


def export_json_records(df: pd.DataFrame, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2)


def board_density(df: pd.DataFrame, file_col: str, rank_col: str) -> list[list[float]]:
    board = np.zeros((8, 8), dtype=float)

    for _, row in df[[file_col, rank_col]].iterrows():
        x = int(row[file_col]) - 1
        y = 8 - int(row[rank_col])
        board[y, x] += 1

    if board.sum() > 0:
        board = board / board.sum()

    return board.tolist()


def build_atlas_json(df: pd.DataFrame) -> dict:
    piece_bucket_boards = {}

    for piece_name, (file_col, rank_col) in PIECE_COLUMNS.items():
        piece_bucket_boards[piece_name] = {}
        for bucket in BUCKET_ORDER:
            bucket_rows = df[df["target_bucket"] == bucket]
            piece_bucket_boards[piece_name][bucket] = board_density(bucket_rows, file_col, rank_col)

    metric_names = [
        "bk_edge_dist",
        "bk_corner_dist",
        "bk_center_dist",
        "wk_bk_chebyshev",
        "wr_bk_manhattan",
        "wk_support_close",
    ]

    metric_summary = (
        df.groupby("target_bucket", observed=False)[metric_names]
        .mean()
        .reindex(BUCKET_ORDER)
        .to_dict(orient="index")
    )

    return {
        "bucket_order": BUCKET_ORDER,
        "piece_boards": piece_bucket_boards,
        "metric_summary": metric_summary,
    }


def export_outputs(df: pd.DataFrame) -> None:
    df.to_csv(OUTPUT_CSV, index=False)
    export_json_records(df, OUTPUT_JSON)

    baseline_cols = [
        "position_id",
        "wk_file", "wk_rank",
        "wr_file", "wr_rank",
        "bk_file", "bk_rank",
        "wk_square", "wr_square", "bk_square",
        "fen",
        "target_raw", "target_depth", "target_bucket",
        "bk_edge_dist",
        "bk_corner_dist",
        "bk_center_dist",
        "wk_bk_chebyshev",
        "wr_bk_manhattan",
        "wk_wr_chebyshev",
        "wk_bk_euclidean",
        "wr_bk_euclidean",
        "wr_bk_aligned",
        "wk_support_close",
        "bk_on_edge",
        "bk_in_corner",
    ]
    baseline_df = df[baseline_cols].copy()
    baseline_df.to_csv(OUTPUT_BASELINE_CSV, index=False)
    export_json_records(baseline_df, OUTPUT_BASELINE_JSON)

    atlas_payload = build_atlas_json(df)
    with open(OUTPUT_ATLAS_JSON, "w", encoding="utf-8") as f:
        json.dump(atlas_payload, f, indent=2)


def main() -> None:
    print(f"Reading input from: {INPUT_PATH}")
    df = load_krk(INPUT_PATH)
    df = add_features(df)

    print("\nShape:")
    print(df.shape)

    print("\nTarget bucket counts:")
    print(df["target_bucket"].value_counts(dropna=False).reindex(BUCKET_ORDER))

    print("\nSample FEN rows:")
    print(df[["position_id", "wk_square", "wr_square", "bk_square", "fen", "target_bucket"]].head(5))

    export_outputs(df)

    print("\nSaved:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_JSON}")
    print(f"  {OUTPUT_BASELINE_CSV}")
    print(f"  {OUTPUT_BASELINE_JSON}")
    print(f"  {OUTPUT_ATLAS_JSON}")


if __name__ == "__main__":
    main()