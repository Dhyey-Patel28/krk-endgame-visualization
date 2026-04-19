from pathlib import Path
import json
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

ENGINE_CSV = BASE_DIR / "data" / "krk_engine_full.csv"

BUCKET_ORDER = ["draw", "win_0_2", "win_3_5", "win_6_9", "win_10_plus"]

BUCKET_LABELS = {
    "draw": "Draw",
    "win_0_2": "Win in 0–2",
    "win_3_5": "Win in 3–5",
    "win_6_9": "Win in 6–9",
    "win_10_plus": "Win in 10+",
}

PIECE_FILTER_LABELS = {
    "all": "All pieces",
    "white_rook": "White rook",
    "white_king": "White king",
    "black_king": "Black king",
}


def mover_piece(row):
    move_from = row.get("move_from")
    if not isinstance(move_from, str):
        return None

    if move_from == row.get("wr_square"):
        return "white_rook"
    if move_from == row.get("wk_square"):
        return "white_king"
    if move_from == row.get("bk_square"):
        return "black_king"
    return "other"


def aggregate_edges(piece_df: pd.DataFrame) -> list[dict]:
    grouped = {}

    for _, row in piece_df.iterrows():
        move_from = row.get("move_from")
        move_to = row.get("move_to")
        piece = row.get("mover_piece")

        if not isinstance(move_from, str) or not isinstance(move_to, str):
            continue
        if piece not in {"white_rook", "white_king", "black_king"}:
            continue

        key = (move_from, move_to, piece)
        grouped[key] = grouped.get(key, 0) + 1

    edges = []
    for (move_from, move_to, piece), count in grouped.items():
        edges.append({
            "from": move_from,
            "to": move_to,
            "piece": piece,
            "count": int(count),
        })

    edges.sort(key=lambda d: (-d["count"], d["piece"], d["from"], d["to"]))
    return edges


def load_engine_df(path: Path = ENGINE_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["target_bucket"] = pd.Categorical(
        df["target_bucket"],
        categories=BUCKET_ORDER,
        ordered=True,
    )
    return df


def build_piece_flow_payload(df: pd.DataFrame) -> dict:
    legal_df = df[df["legal_position"] == True].copy()
    legal_df["mover_piece"] = legal_df.apply(mover_piece, axis=1)

    payload = {
        "bucket_order": BUCKET_ORDER,
        "bucket_labels": BUCKET_LABELS,
        "piece_filter_labels": PIECE_FILTER_LABELS,
        "edges": {
            "all": {},
            "white_rook": {},
            "white_king": {},
            "black_king": {},
        },
        "counts": {
            "all": {},
            "white_rook": {},
            "white_king": {},
            "black_king": {},
        },
        "top_moves": {
            "all": {},
            "white_rook": {},
            "white_king": {},
            "black_king": {},
        },
    }

    piece_keys = ["all", "white_rook", "white_king", "black_king"]

    for bucket in BUCKET_ORDER:
        bucket_df = legal_df[legal_df["target_bucket"] == bucket].copy()

        frames = {
            "all": bucket_df,
            "white_rook": bucket_df[bucket_df["mover_piece"] == "white_rook"],
            "white_king": bucket_df[bucket_df["mover_piece"] == "white_king"],
            "black_king": bucket_df[bucket_df["mover_piece"] == "black_king"],
        }

        for piece_key in piece_keys:
            piece_df = frames[piece_key]
            payload["counts"][piece_key][bucket] = int(len(piece_df))
            payload["edges"][piece_key][bucket] = aggregate_edges(piece_df)

            move_counts = piece_df["best_move"].dropna().value_counts().head(10)
            payload["top_moves"][piece_key][bucket] = [
                {"move": move, "count": int(count)}
                for move, count in move_counts.items()
            ]

    return payload


def payload_json(payload: dict) -> str:
    return json.dumps(payload)

def empty_board() -> list[list[float]]:
    return [[0.0 for _ in range(8)] for _ in range(8)]


def square_to_indices(square: str) -> tuple[int, int]:
    file_idx = ord(square[0]) - ord("a")
    rank_idx = 8 - int(square[1])
    return rank_idx, file_idx


def add_square(board: list[list[float]], square: str, weight: float = 1.0) -> None:
    if not isinstance(square, str) or len(square) != 2:
        return
    row, col = square_to_indices(square)
    board[row][col] += weight


def normalize_board(board: list[list[float]]) -> list[list[float]]:
    total = sum(sum(row) for row in board)
    if total == 0:
        return board
    return [[value / total for value in row] for row in board]


def build_heatmap_payload(df: pd.DataFrame) -> dict:
    legal_df = df[df["legal_position"] == True].copy()
    legal_df["mover_piece"] = legal_df.apply(mover_piece, axis=1)

    payload = {
        "bucket_order": BUCKET_ORDER,
        "bucket_labels": BUCKET_LABELS,
        "piece_filter_labels": PIECE_FILTER_LABELS,
        "origin": {
            "all": {},
            "white_rook": {},
            "white_king": {},
            "black_king": {},
        },
        "destination": {
            "all": {},
            "white_rook": {},
            "white_king": {},
            "black_king": {},
        },
        "counts": {
            "all": {},
            "white_rook": {},
            "white_king": {},
            "black_king": {},
        },
    }

    piece_keys = ["all", "white_rook", "white_king", "black_king"]

    for bucket in BUCKET_ORDER:
        bucket_df = legal_df[legal_df["target_bucket"] == bucket].copy()

        frames = {
            "all": bucket_df,
            "white_rook": bucket_df[bucket_df["mover_piece"] == "white_rook"],
            "white_king": bucket_df[bucket_df["mover_piece"] == "white_king"],
            "black_king": bucket_df[bucket_df["mover_piece"] == "black_king"],
        }

        for piece_key in piece_keys:
            piece_df = frames[piece_key]
            payload["counts"][piece_key][bucket] = int(len(piece_df))

            origin_board = empty_board()
            destination_board = empty_board()

            for _, row in piece_df.iterrows():
                add_square(origin_board, row.get("move_from"))
                add_square(destination_board, row.get("move_to"))

            payload["origin"][piece_key][bucket] = normalize_board(origin_board)
            payload["destination"][piece_key][bucket] = normalize_board(destination_board)

    return payload

def square_to_xy(square: str) -> tuple[int, int]:
    file_idx = ord(square[0]) - ord("a") + 1
    rank_idx = int(square[1])
    return file_idx, rank_idx


def geometry_signature_from_row(row) -> tuple:
    wkx, wky = square_to_xy(row["wk_square"])
    wrx, wry = square_to_xy(row["wr_square"])
    bkx, bky = square_to_xy(row["bk_square"])

    wk_bk_cheb = max(abs(wkx - bkx), abs(wky - bky))
    wr_bk_manh = abs(wrx - bkx) + abs(wry - bky)
    bk_edge = min(bkx - 1, 8 - bkx, bky - 1, 8 - bky)
    bk_corner = min(
        max(abs(bkx - 1), abs(bky - 1)),
        max(abs(bkx - 1), abs(bky - 8)),
        max(abs(bkx - 8), abs(bky - 1)),
        max(abs(bkx - 8), abs(bky - 8)),
    )
    wr_aligned = int((wrx == bkx) or (wry == bky))
    wk_support = int(wk_bk_cheb <= 2)

    return (
        wk_bk_cheb,
        wr_bk_manh,
        bk_edge,
        bk_corner,
        wr_aligned,
        wk_support,
    )


def prune_tree(node: dict, min_count: int, max_children: int, depth: int, max_depth: int) -> dict | None:
    if depth > 0 and node["count"] < min_count:
        return None

    if depth >= max_depth:
        return {
            "name": node["name"],
            "count": node["count"],
            "fen": node["fen"],
            "uci_path": node["uci_path"],
            "san_path": node["san_path"],
            "children": [],
        }

    kept_children = []
    for child in node.get("children", []):
        pruned = prune_tree(child, min_count, max_children, depth + 1, max_depth)
        if pruned is not None:
            kept_children.append(pruned)

    kept_children.sort(key=lambda c: (-c["count"], c["name"]))
    kept_children = kept_children[:max_children]

    return {
        "name": node["name"],
        "count": node["count"],
        "fen": node["fen"],
        "uci_path": node["uci_path"],
        "san_path": node["san_path"],
        "children": kept_children,
    }


def build_endgame_sunburst_payload(
    df: pd.DataFrame,
    max_depth: int = 5,
    max_examples_per_signature: int = 18,
    max_children_per_node: int = 48,
    min_bucket_fraction: float = 0.0003,
) -> dict:
    legal_df = df[df["legal_position"] == True].copy()

    payload = {
        "bucket_order": BUCKET_ORDER,
        "bucket_labels": BUCKET_LABELS,
        "trees": {},
    }

    for bucket in BUCKET_ORDER:
        bucket_df = legal_df[legal_df["target_bucket"] == bucket].copy()

        root = {
            "name": "start",
            "count": int(len(bucket_df)),
            "children_map": {},
            "fen": None,
            "uci_path": [],
            "san_path": [],
        }

        seen_signatures = {}

        for _, row in bucket_df.iterrows():
            pv_uci = row.get("pv_uci")
            pv_san = row.get("pv_san")
            fen = row.get("fen_used")

            if not isinstance(pv_uci, str) or not isinstance(pv_san, str) or not isinstance(fen, str):
                continue

            uci_moves = pv_uci.split()[:max_depth]
            san_moves = pv_san.split()[:max_depth]

            if not uci_moves or not san_moves:
                continue

            signature = (
                tuple(san_moves[:3]),
                row.get("best_move"),
                geometry_signature_from_row(row),
            )

            seen_signatures[signature] = seen_signatures.get(signature, 0) + 1
            if seen_signatures[signature] > max_examples_per_signature:
                continue

            current = root

            for ply_index, (uci_move, san_move) in enumerate(zip(uci_moves, san_moves), start=1):
                if san_move not in current["children_map"]:
                    current["children_map"][san_move] = {
                        "name": san_move,
                        "count": 0,
                        "children_map": {},
                        "fen": fen,
                        "uci_path": uci_moves[:ply_index],
                        "san_path": san_moves[:ply_index],
                    }

                child = current["children_map"][san_move]
                child["count"] += 1
                current = child

        def finalize(node):
            children = [finalize(child) for child in node["children_map"].values()]
            children.sort(key=lambda c: (-c["count"], c["name"]))

            return {
                "name": node["name"],
                "count": node["count"],
                "fen": node["fen"],
                "uci_path": node["uci_path"],
                "san_path": node["san_path"],
                "children": children,
            }

        finalized = finalize(root)

        min_count = max(3, int(len(bucket_df) * min_bucket_fraction))
        payload["trees"][bucket] = prune_tree(
            finalized,
            min_count=min_count,
            max_children=max_children_per_node,
            depth=0,
            max_depth=max_depth,
        )

    return payload