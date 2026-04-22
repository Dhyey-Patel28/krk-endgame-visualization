from pathlib import Path
import json
from typing import Dict, List

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

INPUT_PATH = DATA_DIR / "zoo.data"
OUTPUT_CSV = DATA_DIR / "zoo_clean.csv"
OUTPUT_JSON = DATA_DIR / "zoo_dashboard.json"

COLUMN_NAMES = [
    "animal_name",
    "hair",
    "feathers",
    "eggs",
    "milk",
    "airborne",
    "aquatic",
    "predator",
    "toothed",
    "backbone",
    "breathes",
    "venomous",
    "fins",
    "legs",
    "tail",
    "domestic",
    "catsize",
    "type",
]

CLASS_NAMES = {
    1: "mammal",
    2: "bird",
    3: "reptile",
    4: "fish",
    5: "amphibian",
    6: "insect",
    7: "invertebrate",
}

BINARY_TRAITS = [
    "hair",
    "feathers",
    "eggs",
    "milk",
    "airborne",
    "aquatic",
    "predator",
    "toothed",
    "backbone",
    "breathes",
    "venomous",
    "fins",
    "tail",
    "domestic",
    "catsize",
]

NUMERIC_TRAITS = ["legs"]
PCA_FEATURES = BINARY_TRAITS + NUMERIC_TRAITS


def load_zoo_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find zoo.data at:\n{path}\n\n"
            "Place zoo.data inside the project's data/ folder."
        )

    df = pd.read_csv(path, header=None, names=COLUMN_NAMES)

    for column in BINARY_TRAITS + ["type"]:
        df[column] = pd.to_numeric(df[column], errors="raise").astype(int)

    df["legs"] = pd.to_numeric(df["legs"], errors="raise").astype(int)
    df["class_name"] = df["type"].map(CLASS_NAMES)

    if df["class_name"].isna().any():
        bad_values = sorted(df.loc[df["class_name"].isna(), "type"].unique().tolist())
        raise ValueError(f"Found unknown class ids in zoo.data: {bad_values}")

    return df


def build_pca_points(df: pd.DataFrame) -> List[Dict]:
    feature_frame = df[PCA_FEATURES].copy()
    scaled = StandardScaler().fit_transform(feature_frame)

    coordinates = PCA(n_components=2, random_state=42).fit_transform(scaled)

    pca_points: List[Dict] = []
    for row_index, (_, row) in enumerate(df.iterrows()):
        pca_points.append(
            {
                "animal_name": row["animal_name"],
                "class_id": int(row["type"]),
                "class_name": row["class_name"],
                "pc1": float(coordinates[row_index, 0]),
                "pc2": float(coordinates[row_index, 1]),
                "legs": int(row["legs"]),
                "traits": {trait: int(row[trait]) for trait in BINARY_TRAITS},
            }
        )

    return pca_points


def build_heatmap_data(df: pd.DataFrame) -> List[Dict]:
    rows: List[Dict] = []

    grouped = (
        df.groupby(["type", "class_name"], observed=True)[PCA_FEATURES]
        .mean()
        .reset_index()
        .sort_values("type")
    )

    for _, class_row in grouped.iterrows():
        for trait in PCA_FEATURES:
            rows.append(
                {
                    "class_id": int(class_row["type"]),
                    "class_name": class_row["class_name"],
                    "trait": trait,
                    "value": float(class_row[trait]),
                }
            )

    return rows


def build_animal_cards(df: pd.DataFrame) -> List[Dict]:
    animals: List[Dict] = []

    for _, row in df.sort_values(["type", "animal_name"]).iterrows():
        animals.append(
            {
                "animal_name": row["animal_name"],
                "class_id": int(row["type"]),
                "class_name": row["class_name"],
                "legs": int(row["legs"]),
                "traits": {trait: int(row[trait]) for trait in BINARY_TRAITS},
                "active_traits": [trait for trait in BINARY_TRAITS if int(row[trait]) == 1],
            }
        )

    return animals


def build_class_summary(df: pd.DataFrame) -> List[Dict]:
    summary: List[Dict] = []

    counts = (
        df.groupby(["type", "class_name"], observed=True)
        .size()
        .reset_index(name="count")
        .sort_values("type")
    )

    for _, row in counts.iterrows():
        summary.append(
            {
                "class_id": int(row["type"]),
                "class_name": row["class_name"],
                "count": int(row["count"]),
            }
        )

    return summary


def export_clean_csv(df: pd.DataFrame, output_path: Path) -> None:
    ordered_columns = ["animal_name"] + BINARY_TRAITS + NUMERIC_TRAITS + ["type", "class_name"]
    df[ordered_columns].to_csv(output_path, index=False)


def export_dashboard_json(df: pd.DataFrame, output_path: Path) -> None:
    dashboard_payload = {
        "classes": build_class_summary(df),
        "traits": BINARY_TRAITS,
        "numeric_traits": NUMERIC_TRAITS,
        "pca_points": build_pca_points(df),
        "heatmap": build_heatmap_data(df),
        "animals": build_animal_cards(df),
    }

    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(dashboard_payload, file_handle, indent=2)


def main() -> None:
    print(f"Reading input from: {INPUT_PATH.resolve()}")

    df = load_zoo_data(INPUT_PATH)

    print("\nShape:")
    print(df.shape)

    print("\nClass counts:")
    print(df["class_name"].value_counts().sort_index())

    print("\nSample rows:")
    print(df.head())

    export_clean_csv(df, OUTPUT_CSV)
    export_dashboard_json(df, OUTPUT_JSON)

    print("\nSaved files:")
    print(f"  Clean CSV:   {OUTPUT_CSV.resolve()}")
    print(f"  Dashboard:   {OUTPUT_JSON.resolve()}")


if __name__ == "__main__":
    main()
