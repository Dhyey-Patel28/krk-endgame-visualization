from pathlib import Path
import json
import time

import pandas as pd
import chess
import chess.engine

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_CSV = BASE_DIR / "data" / "krk_baseline.csv"
OUTPUT_CSV = BASE_DIR / "data" / "krk_engine_full.csv"
OUTPUT_JSON = BASE_DIR / "data" / "krk_engine_full.json"

BUCKET_ORDER = ["draw", "win_0_2", "win_3_5", "win_6_9", "win_10_plus"]

STOCKFISH_PATH = Path(
    os.environ.get(
        "STOCKFISH_PATH",
        str(BASE_DIR / "third_party" / "stockfish" / "stockfish-windows-x86-64-avx2.exe")
    )
)

SEARCH_DEPTH = 10
SAVE_EVERY = 500


def load_positions(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["target_bucket"] = pd.Categorical(
        df["target_bucket"],
        categories=BUCKET_ORDER,
        ordered=True,
    )
    return df


def board_part_from_row(row) -> str:
    board = [["" for _ in range(8)] for _ in range(8)]

    board[8 - int(row["wk_rank"])][int(row["wk_file"]) - 1] = "K"
    board[8 - int(row["wr_rank"])][int(row["wr_file"]) - 1] = "R"
    board[8 - int(row["bk_rank"])][int(row["bk_file"]) - 1] = "k"

    fen_rows = []
    for rank in board:
        empty_count = 0
        fen_rank = ""

        for square in rank:
            if square == "":
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_rank += str(empty_count)
                    empty_count = 0
                fen_rank += square

        if empty_count > 0:
            fen_rank += str(empty_count)

        fen_rows.append(fen_rank)

    return "/".join(fen_rows)


def build_fen(board_part: str, turn: str) -> str:
    return f"{board_part} {turn} - - 0 1"


def infer_turn(board_part: str) -> tuple[str | None, list[str]]:
    legal_turns = []

    for turn in ["w", "b"]:
        board = chess.Board(build_fen(board_part, turn))
        if board.is_valid():
            legal_turns.append(turn)

    if not legal_turns:
        return None, []

    if "w" in legal_turns:
        return "w", legal_turns

    return legal_turns[0], legal_turns


def score_to_fields(score_obj: chess.engine.PovScore) -> dict:
    result = {
        "score_cp": None,
        "mate_in": None,
        "score_text": None,
    }

    if score_obj is None:
        return result

    relative = score_obj.white()

    if relative.is_mate():
        result["mate_in"] = relative.mate()
        result["score_text"] = f"mate {relative.mate()}"
    else:
        cp = relative.score()
        result["score_cp"] = cp
        result["score_text"] = f"{cp} cp"

    return result


def analyse_position(engine: chess.engine.SimpleEngine, fen: str) -> dict:
    board = chess.Board(fen)

    if not board.is_valid():
        return {
            "legal_position": False,
            "best_move": None,
            "move_from": None,
            "move_to": None,
            "pv_uci": None,
            "pv_san": None,
            "score_cp": None,
            "mate_in": None,
            "score_text": "invalid board",
        }

    info = engine.analyse(
        board,
        chess.engine.Limit(depth=SEARCH_DEPTH),
        info=chess.engine.INFO_SCORE | chess.engine.INFO_PV,
    )

    pv_moves = info.get("pv", [])
    best_move = pv_moves[0].uci() if pv_moves else None
    move_from = best_move[:2] if best_move else None
    move_to = best_move[2:4] if best_move else None
    pv_uci = " ".join(move.uci() for move in pv_moves[:6]) if pv_moves else None

    pv_san = None
    if pv_moves:
        temp_board = board.copy()
        san_moves = []
        for move in pv_moves[:6]:
            try:
                san_moves.append(temp_board.san(move))
                temp_board.push(move)
            except Exception:
                break
        pv_san = " ".join(san_moves) if san_moves else None

    return {
        "legal_position": True,
        "best_move": best_move,
        "move_from": move_from,
        "move_to": move_to,
        "pv_uci": pv_uci,
        "pv_san": pv_san,
        **score_to_fields(info.get("score")),
    }


def save_outputs(result_df: pd.DataFrame) -> None:
    result_df.to_csv(OUTPUT_CSV, index=False)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result_df.to_dict(orient="records"), f, indent=2)


def main():
    if not STOCKFISH_PATH.exists():
        raise FileNotFoundError(
            f"Stockfish executable not found at:\n{STOCKFISH_PATH}\n\n"
            "Edit STOCKFISH_PATH in engine_krk_full.py to the correct .exe file."
        )

    df = load_positions(INPUT_CSV)
    print("Loaded positions:", df.shape)

    results = []
    start_time = time.time()

    with chess.engine.SimpleEngine.popen_uci(str(STOCKFISH_PATH)) as engine:
        for idx, row in df.iterrows():
            board_part = board_part_from_row(row)
            inferred_turn, legal_turns = infer_turn(board_part)

            if inferred_turn is None:
                analysis = {
                    "inferred_turn": None,
                    "legal_turn_options": "",
                    "fen_used": None,
                    "legal_position": False,
                    "best_move": None,
                    "move_from": None,
                    "move_to": None,
                    "pv_uci": None,
                    "pv_san": None,
                    "score_cp": None,
                    "mate_in": None,
                    "score_text": "invalid for both turns",
                }
            else:
                fen_used = build_fen(board_part, inferred_turn)
                analysis = analyse_position(engine, fen_used)
                analysis["inferred_turn"] = inferred_turn
                analysis["legal_turn_options"] = ",".join(legal_turns)
                analysis["fen_used"] = fen_used

            results.append({
                "position_id": int(row["position_id"]),
                "target_bucket": row["target_bucket"],
                "target_raw": row["target_raw"],
                "target_depth": row["target_depth"],
                "wk_square": row["wk_square"],
                "wr_square": row["wr_square"],
                "bk_square": row["bk_square"],
                "fen_original": row["fen"],
                **analysis,
            })

            if (idx + 1) % SAVE_EVERY == 0:
                elapsed = time.time() - start_time
                print(f"Processed {idx + 1}/{len(df)} rows | elapsed {elapsed:.1f}s")
                save_outputs(pd.DataFrame(results))

    result_df = pd.DataFrame(results)
    save_outputs(result_df)

    elapsed = time.time() - start_time

    print("\nSaved:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_JSON}")

    print(f"\nFinished in {elapsed:.1f} seconds")

    print("\nValidity summary:")
    print(result_df["legal_position"].value_counts(dropna=False))

    print("\nMate summary:")
    print(result_df["mate_in"].notna().value_counts())

    print("\nTop best moves:")
    print(result_df["best_move"].value_counts(dropna=True).head(20))


if __name__ == "__main__":
    main()