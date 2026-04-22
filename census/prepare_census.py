from pathlib import Path
import json
from typing import Dict, List

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TRAIN_PATH = DATA_DIR / "census-income.data"
TEST_PATH = DATA_DIR / "census-income.test"

OUTPUT_CLEAN = DATA_DIR / "census_selected_clean.csv"
OUTPUT_PATHWAYS_CSV = DATA_DIR / "census_pathways.csv"
OUTPUT_PATHWAYS_JSON = DATA_DIR / "census_pathways.json"
OUTPUT_SUPPORTING_JSON = DATA_DIR / "census_supporting.json"


COLUMN_NAMES = [
    "age",
    "class_of_worker",
    "detailed_industry_recode",
    "detailed_occupation_recode",
    "education",
    "wage_per_hour",
    "enroll_in_edu_inst_last_wk",
    "marital_status",
    "major_industry_code",
    "major_occupation_code",
    "race",
    "hispanic_origin",
    "sex",
    "union_member",
    "reason_for_unemployment",
    "employment_status",
    "capital_gains",
    "capital_losses",
    "dividends_from_stocks",
    "tax_filer_status",
    "region_of_previous_residence",
    "state_of_previous_residence",
    "detailed_household_and_family_stat",
    "detailed_household_summary_in_household",
    "instance_weight",
    "migration_code_change_in_msa",
    "migration_code_change_in_reg",
    "migration_code_move_within_reg",
    "live_in_this_house_1_year_ago",
    "migration_prev_res_in_sunbelt",
    "num_persons_worked_for_employer",
    "family_members_under_18",
    "country_of_birth_father",
    "country_of_birth_mother",
    "country_of_birth_self",
    "citizenship",
    "own_business_or_self_employed",
    "fill_inc_questionnaire_for_veterans_admin",
    "veterans_benefits",
    "weeks_worked_in_year",
    "year",
    "income_bucket_raw",
]


NUMERIC_COLUMNS = [
    "age",
    "detailed_industry_recode",
    "detailed_occupation_recode",
    "wage_per_hour",
    "capital_gains",
    "capital_losses",
    "dividends_from_stocks",
    "instance_weight",
    "num_persons_worked_for_employer",
    "weeks_worked_in_year",
    "year",
]


def clean_string(value: object) -> str:
    return str(value).strip().rstrip(".")


def collapse_education(value: str) -> str:
    low = {
        "Children",
        "Less than 1st grade",
        "1st 2nd 3rd or 4th grade",
        "5th or 6th grade",
        "7th and 8th grade",
        "9th grade",
        "10th grade",
        "11th grade",
        "12th grade no diploma",
    }
    if value in low:
        return "Less than high school"
    if value == "High school graduate":
        return "High school"
    if value == "Some college but no degree":
        return "Some college"
    if value in {
        "Associates degree-occup /vocational",
        "Associates degree-academic program",
    }:
        return "Associate"
    if value == "Bachelors degree(BA AB BS)":
        return "Bachelor"
    if value in {
        "Masters degree(MA MS MEng MEd MSW MBA)",
        "Doctorate degree(PhD EdD)",
        "Prof school degree (MD DDS DVM LLB JD)",
    }:
        return "Graduate / professional"
    return value


def collapse_work_status(value: str) -> str:
    if "Unemployed" in value:
        return "Unemployed"
    if value == "Full-time schedules":
        return "Full-time"
    if value.startswith("PT ") or "part- time" in value or "Part-time" in value:
        return "Part-time"
    if value in {"Not in labor force", "Children or Armed Forces"}:
        return "Not in labor force"
    return "Other"


def collapse_marital_status(value: str) -> str:
    if value in {"Married-civilian spouse present", "Married-A F spouse present"}:
        return "Married, spouse present"
    if value in {"Married-spouse absent", "Separated"}:
        return "Married / separated"
    if value == "Never married":
        return "Never married"
    if value in {"Divorced", "Widowed"}:
        return "Divorced / widowed"
    return value


def collapse_sex(value: str) -> str:
    if value in {"Male", "Female"}:
        return value
    return "Other"


def collapse_income_bucket(value: str) -> str:
    value = clean_string(value)
    if value == "50000+":
        return "> $50K"
    return "<= $50K"


def age_band(age: int) -> str:
    if age < 25:
        return "Under 25"
    if age < 35:
        return "25-34"
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    if age < 65:
        return "55-64"
    return "65+"


def weeks_band(weeks: int) -> str:
    if weeks <= 0:
        return "0 weeks"
    if weeks < 20:
        return "1-19 weeks"
    if weeks < 40:
        return "20-39 weeks"
    if weeks < 50:
        return "40-49 weeks"
    return "50+ weeks"


def read_split(path: Path, split_name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(
        path,
        header=None,
        names=COLUMN_NAMES,
        skipinitialspace=False,
    )

    for col in COLUMN_NAMES:
        if col not in NUMERIC_COLUMNS:
            df[col] = df[col].map(clean_string)

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["split"] = split_name
    return df


def add_grouped_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["education_group"] = df["education"].map(collapse_education)
    df["work_status_group"] = df["employment_status"].map(collapse_work_status)
    df["marital_group"] = df["marital_status"].map(collapse_marital_status)
    df["sex_group"] = df["sex"].map(collapse_sex)
    df["income_bucket"] = df["income_bucket_raw"].map(collapse_income_bucket)
    df["age_band"] = df["age"].fillna(0).astype(int).map(age_band)
    df["weeks_worked_band"] = df["weeks_worked_in_year"].fillna(0).astype(int).map(weeks_band)

    return df


def build_weighted_pathways(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(
            ["education_group", "work_status_group", "marital_group", "income_bucket"],
            dropna=False,
        )["instance_weight"]
        .sum()
        .reset_index(name="weight")
        .sort_values("weight", ascending=False)
    )

    grouped["weight"] = grouped["weight"].round(2)
    return grouped


def sankey_from_pathways(pathways: pd.DataFrame) -> Dict:
    stage_names = [
        ("education_group", "Education"),
        ("work_status_group", "Work status"),
        ("marital_group", "Marital status"),
        ("income_bucket", "Income"),
    ]

    node_lookup: Dict[str, int] = {}
    nodes: List[Dict] = []
    links: List[Dict] = []

    def node_id(stage_key: str, label: str) -> str:
        return f"{stage_key}::{label}"

    def ensure_node(stage_key: str, stage_label: str, label: str) -> int:
        key = node_id(stage_key, label)
        if key not in node_lookup:
            node_lookup[key] = len(nodes)
            nodes.append(
                {
                    "id": key,
                    "name": label,
                    "stage_key": stage_key,
                    "stage_label": stage_label,
                }
            )
        return node_lookup[key]

    link_weights: Dict[tuple, float] = {}

    for _, row in pathways.iterrows():
        values = [
            row["education_group"],
            row["work_status_group"],
            row["marital_group"],
            row["income_bucket"],
        ]
        weight = float(row["weight"])

        for i in range(len(stage_names) - 1):
            source_stage_key, source_stage_label = stage_names[i]
            target_stage_key, target_stage_label = stage_names[i + 1]

            source_idx = ensure_node(source_stage_key, source_stage_label, values[i])
            target_idx = ensure_node(target_stage_key, target_stage_label, values[i + 1])

            key = (source_idx, target_idx)
            link_weights[key] = link_weights.get(key, 0.0) + weight

    for (source_idx, target_idx), value in link_weights.items():
        links.append(
            {
                "source": source_idx,
                "target": target_idx,
                "value": round(value, 2),
            }
        )

    return {"nodes": nodes, "links": links}


def weighted_income_share(
    df: pd.DataFrame,
    group_col: str,
    output_label: str,
) -> List[Dict]:
    grouped = (
        df.groupby([group_col, "income_bucket"], dropna=False)["instance_weight"]
        .sum()
        .reset_index()
    )

    pivot = grouped.pivot_table(
        index=group_col,
        columns="income_bucket",
        values="instance_weight",
        fill_value=0.0,
    )

    if "> $50K" not in pivot.columns:
        pivot["> $50K"] = 0.0
    if "<= $50K" not in pivot.columns:
        pivot["<= $50K"] = 0.0

    pivot["total_weight"] = pivot["> $50K"] + pivot["<= $50K"]
    pivot["share_over_50k"] = pivot["> $50K"] / pivot["total_weight"].where(pivot["total_weight"] != 0, 1)

    pivot = pivot.sort_values(["share_over_50k", "total_weight"], ascending=[False, False])

    rows: List[Dict] = []
    for idx, row in pivot.reset_index().iterrows():
        rows.append(
            {
                output_label: row[group_col],
                "weighted_over_50k": round(float(row["> $50K"]), 2),
                "weighted_under_equal_50k": round(float(row["<= $50K"]), 2),
                "total_weight": round(float(row["total_weight"]), 2),
                "share_over_50k": round(float(row["share_over_50k"]), 4),
            }
        )
    return rows


def export_outputs(df: pd.DataFrame) -> None:
    selected_cols = [
        "split",
        "age",
        "age_band",
        "education",
        "education_group",
        "employment_status",
        "work_status_group",
        "marital_status",
        "marital_group",
        "sex",
        "sex_group",
        "weeks_worked_in_year",
        "weeks_worked_band",
        "instance_weight",
        "income_bucket",
    ]

    df[selected_cols].to_csv(OUTPUT_CLEAN, index=False)

    pathways = build_weighted_pathways(df)
    pathways.to_csv(OUTPUT_PATHWAYS_CSV, index=False)

    sankey_payload = sankey_from_pathways(pathways)

    supporting_payload = {
        "title": "Pathways to $50K",
        "records": int(len(df)),
        "weighted_population": round(float(df["instance_weight"].sum()), 2),
        "top_pathways": pathways.head(25).to_dict(orient="records"),
        "bar_by_education": weighted_income_share(df, "education_group", "education_group"),
        "bar_by_age": weighted_income_share(df, "age_band", "age_band"),
        "bar_by_work_status": weighted_income_share(df, "work_status_group", "work_status_group"),
        "bar_by_sex": weighted_income_share(df, "sex_group", "sex_group"),
    }

    with OUTPUT_PATHWAYS_JSON.open("w", encoding="utf-8") as f:
        json.dump(sankey_payload, f, indent=2)

    with OUTPUT_SUPPORTING_JSON.open("w", encoding="utf-8") as f:
        json.dump(supporting_payload, f, indent=2)


def main() -> None:
    print(f"Reading train file: {TRAIN_PATH.resolve()}")
    print(f"Reading test file:  {TEST_PATH.resolve()}")

    train_df = read_split(TRAIN_PATH, "train")
    test_df = read_split(TEST_PATH, "test")

    df = pd.concat([train_df, test_df], ignore_index=True)
    df = add_grouped_columns(df)

    print("\nShape:")
    print(df.shape)

    print("\nIncome bucket counts (raw rows):")
    print(df["income_bucket"].value_counts())

    print("\nWeighted income totals:")
    print(df.groupby("income_bucket")["instance_weight"].sum().round(2))

    print("\nGrouped variable previews:")
    print(df[[
        "education_group",
        "work_status_group",
        "marital_group",
        "age_band",
        "weeks_worked_band",
        "income_bucket",
    ]].head())

    export_outputs(df)

    print("\nSaved files:")
    print(f"  {OUTPUT_CLEAN.resolve()}")
    print(f"  {OUTPUT_PATHWAYS_CSV.resolve()}")
    print(f"  {OUTPUT_PATHWAYS_JSON.resolve()}")
    print(f"  {OUTPUT_SUPPORTING_JSON.resolve()}")


if __name__ == "__main__":
    main()
