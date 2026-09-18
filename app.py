import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime


# ============================================================
# CANONICAL STREAMLIT APPLICATION V1
# ============================================================

st.set_page_config(
    page_title="Mitochondrial Research Intelligence",
    page_icon="🧬",
    layout="wide",
)


BASE_DIR = Path(__file__).resolve().parent

PRIORITY_FILE = (
    BASE_DIR
    / "data"
    / "production_v1"
    / "human_preference_layer_v1.csv"
)

EXPLANATION_FILE = (
    BASE_DIR
    / "data"
    / "production_v1"
    / "canonical_explanations_v1.csv"
)

LIVE_FEEDBACK_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "user_feedback_live.csv"
)


# ============================================================
# HELPERS
# ============================================================

def clean_value(value, default="Not detected"):
    if pd.isna(value):
        return default
    value = str(value).strip()
    if value.lower() in {"", "nan", "none"}:
        return default
    return value


def evidence_label(level):
    mapping = {
        0: "Absent",
        1: "Mentioned",
        2: "Investigated / associated",
        3: "Strong / direct",
    }
    try:
        return mapping.get(int(level), "Unknown")
    except Exception:
        return "Unknown"


def load_main_data():
    if not PRIORITY_FILE.exists():
        raise FileNotFoundError(
            f"Missing canonical priority file:\n{PRIORITY_FILE}"
        )

    if not EXPLANATION_FILE.exists():
        raise FileNotFoundError(
            f"Missing canonical explanation file:\n{EXPLANATION_FILE}"
        )

    priority = pd.read_csv(PRIORITY_FILE)

    explanation = pd.read_csv(
        EXPLANATION_FILE,
        usecols=["pmid", "canonical_explanation_v1"],
    )

    if priority["pmid"].duplicated().any():
        raise ValueError("Duplicate PMIDs detected in priority dataset.")

    if explanation["pmid"].duplicated().any():
        raise ValueError("Duplicate PMIDs detected in explanation dataset.")

    df = priority.merge(
        explanation,
        on="pmid",
        how="left",
        validate="one_to_one",
    )

    if len(df) != 250:
        raise ValueError(
            f"Expected 250 canonical papers, found {len(df)}."
        )

    if df["pmid"].nunique() != 250:
        raise ValueError("Canonical dataset does not contain 250 unique PMIDs.")

    return df


@st.cache_data
def get_data():
    return load_main_data()


def load_live_feedback():
    if not LIVE_FEEDBACK_FILE.exists():
        return pd.DataFrame(
            columns=[
                "pmid",
                "user_relevance",
                "user_reason",
                "timestamp",
            ]
        )

    df = pd.read_csv(LIVE_FEEDBACK_FILE)

    if "pmid" not in df.columns:
        return pd.DataFrame(
            columns=[
                "pmid",
                "user_relevance",
                "user_reason",
                "timestamp",
            ]
        )

    for col in ["user_relevance", "user_reason"]:
        if col not in df.columns:
            df[col] = ""

    return df


def save_live_feedback(pmid, label, reason):
    feedback = load_live_feedback()

    feedback = feedback[
        feedback["pmid"].astype(str) != str(pmid)
    ].copy()

    new_row = pd.DataFrame(
        [{
            "pmid": str(pmid),
            "user_relevance": label,
            "user_reason": reason,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }]
    )

    feedback = pd.concat(
        [feedback, new_row],
        ignore_index=True,
    )

    LIVE_FEEDBACK_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    feedback.to_csv(
        LIVE_FEEDBACK_FILE,
        index=False,
    )


# ============================================================
# LOAD
# ============================================================

try:
    df = get_data()
except Exception as exc:
    st.error("Canonical literature database could not be loaded.")
    st.code(str(exc))
    st.stop()


feedback_df = load_live_feedback()


# ============================================================
# HEADER
# ============================================================

st.title("🧬 Mitochondrial Research Intelligence")


st.divider()


# ============================================================
# MITOCHONDRIAL VISUAL
# ============================================================

HERO_IMAGE = BASE_DIR / "assets" / "mitochondria_hero.png"


if HERO_IMAGE.exists():
    _, image_col, _ = st.columns([1.5, 5, 1.5])

    with image_col:
        st.image(
            str(HERO_IMAGE),
            width=650,
            caption="Mitochondrial architecture and cellular energy metabolism",
        )
st.divider()

# ============================================================
# TOP METRICS
# ============================================================

total_papers = len(df)

critical = int(
    (df["final_priority_category"] == "Critical").sum()
)

high = int(
    (df["final_priority_category"] == "High").sum()
)

moderate = int(
    (df["final_priority_category"] == "Moderate").sum()
)

live_labels = int(
    feedback_df["user_relevance"]
    .astype(str)
    .str.strip()
    .ne("")
    .sum()
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📚 Papers", total_papers)

with col2:
    st.metric("🔥 Critical", critical)

with col3:
    st.metric("⭐ High", high)

with col4:
    st.metric("📊 Moderate", moderate)

with col5:
    st.metric("🧑‍🔬 Live Labels", live_labels)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Literature Filters")

category_options = [
    "All",
    "Critical",
    "High",
    "Moderate",
    "Low",
    "Peripheral",
]

selected_category = st.sidebar.selectbox(
    "Scientific Priority",
    category_options,
)

min_score = st.sidebar.slider(
    "Minimum Scientific Priority Score",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=1.0,
)

min_p_relevant = st.sidebar.slider(
    "Minimum P(Relevant)",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05,
)

o5_options = ["All", 0, 1, 2, 3]

selected_o5 = st.sidebar.selectbox(
    "O5 Mechanistic Connection Level",
    o5_options,
)

search_term = st.sidebar.text_input(
    "Search title / abstract / evidence",
    placeholder="DRP1, PINK1, mitophagy...",
)

sort_option = st.sidebar.selectbox(
    "Sort By",
    [
        "Scientific Priority",
        "Human Relevance Probability",
        "Publication Date",
    ],
)


# ============================================================
# FILTER DATA
# ============================================================

filtered = df.copy()

if selected_category != "All":
    filtered = filtered[
        filtered["final_priority_category"] == selected_category
    ]

filtered = filtered[
    filtered["final_phd_priority_score"] >= min_score
]

filtered = filtered[
    filtered["P_relevant"] >= min_p_relevant
]

if selected_o5 != "All":
    filtered = filtered[
        filtered["O5_mechanistic_connection_level"] == int(selected_o5)
    ]

if search_term.strip():

    q = search_term.strip()

    mask = (
        filtered["title"]
        .fillna("")
        .str.contains(q, case=False, regex=False)
        |
        filtered["abstract"]
        .fillna("")
        .str.contains(q, case=False, regex=False)
        |
        filtered["gene_evidence_genes"]
        .fillna("")
        .str.contains(q, case=False, regex=False)
        |
        filtered["mitochondrial_process_evidence"]
        .fillna("")
        .str.contains(q, case=False, regex=False)
        |
        filtered["senescence_evidence"]
        .fillna("")
        .str.contains(q, case=False, regex=False)
        |
        filtered["model_evidence"]
        .fillna("")
        .str.contains(q, case=False, regex=False)
        |
        filtered["omics_evidence"]
        .fillna("")
        .str.contains(q, case=False, regex=False)
    )

    filtered = filtered[mask]


# ============================================================
# SORT
# ============================================================

if sort_option == "Scientific Priority":
    filtered = filtered.sort_values(
        "final_phd_priority_score",
        ascending=False,
    )

elif sort_option == "Human Relevance Probability":
    filtered = filtered.sort_values(
        "P_relevant",
        ascending=False,
    )

else:
    filtered = filtered.sort_values(
        "publication_date",
        ascending=False,
    )


# ============================================================
# SUMMARY
# ============================================================

st.subheader("📖 Literature Explorer")

st.write(
    f"Showing **{len(filtered)}** of **{total_papers}** canonical papers."
)

if len(filtered) == 0:
    st.warning("No papers match the selected filters.")
    st.stop()


# ============================================================
# PAPER CARDS
# ============================================================

for _, row in filtered.iterrows():

    title = clean_value(
        row.get("title"),
        "Untitled paper",
    )

    pmid = clean_value(
        row.get("pmid"),
        "",
    )

    score = float(
        row.get(
            "final_phd_priority_score",
            0,
        )
    )

    rank = int(
        row.get(
            "final_phd_rank",
            0,
        )
    )

    category = clean_value(
        row.get("final_priority_category"),
        "Unknown",
    )

    p_not = float(
        row.get(
            "P_not_relevant",
            0,
        )
    )

    p_maybe = float(
        row.get(
            "P_maybe",
            0,
        )
    )

    p_relevant = float(
        row.get(
            "P_relevant",
            0,
        )
    )

    journal = clean_value(
        row.get("journal"),
        "Unknown journal",
    )

    publication_date = clean_value(
        row.get("publication_date"),
        "",
    )

    with st.container(border=True):

        st.markdown(
            f"### #{rank} — {title}"
        )

        st.caption(
            f"{journal} • {publication_date} • PMID {pmid}"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Scientific Priority",
                f"{score:.2f}",
            )

        with c2:
            st.metric(
                "Category",
                category,
            )

        with c3:
            st.metric(
                "P(Relevant)",
                f"{p_relevant:.3f}",
            )

        with c4:
            st.metric(
                "O5 Mechanistic",
                f"{int(row.get('O5_mechanistic_connection_level', 0))}/3",
            )

        # ----------------------------------------------------
        # EVIDENCE
        # ----------------------------------------------------

        with st.expander("🔬 Canonical Evidence"):

            e1, e2 = st.columns(2)

            with e1:

                st.write(
                    "**Priority genes**"
                )

                st.write(
                    clean_value(
                        row.get("gene_evidence_genes"),
                        "None detected",
                    )
                )

                st.caption(
                    f"Level: "
                    f"{evidence_label(row.get('gene_evidence_level', 0))}"
                )

                st.write(
                    "**Mitochondrial processes**"
                )

                st.write(
                    clean_value(
                        row.get("mitochondrial_process_evidence"),
                        "None detected",
                    )
                )

                st.caption(
                    f"Level: "
                    f"{evidence_label(row.get('mitochondrial_process_evidence_level', 0))}"
                )

                st.write(
                    "**Senescence evidence**"
                )

                st.write(
                    clean_value(
                        row.get("senescence_evidence"),
                        "None detected",
                    )
                )

                st.caption(
                    f"Level: "
                    f"{evidence_label(row.get('senescence_evidence_level', 0))}"
                )

            with e2:

                st.write(
                    "**Experimental model**"
                )

                st.write(
                    clean_value(
                        row.get("model_evidence"),
                        "None detected",
                    )
                )

                st.caption(
                    f"Level: "
                    f"{evidence_label(row.get('model_evidence_level', 0))}"
                )

                st.write(
                    "**Omics evidence**"
                )

                st.write(
                    clean_value(
                        row.get("omics_evidence"),
                        "None detected",
                    )
                )

                st.caption(
                    f"Level: "
                    f"{evidence_label(row.get('omics_evidence_level', 0))}"
                )

        # ----------------------------------------------------
        # OBJECTIVE ALIGNMENT
        # ----------------------------------------------------

        with st.expander("🎯 PhD Objective Alignment"):

            o1, o2, o3 = st.columns(3)

            with o1:
                st.metric(
                    "O2 Multi-omics",
                    f"{int(row.get('O2_multiomics_integration_level', 0))}/3",
                )

            with o2:
                st.metric(
                    "O3 Hub Genes",
                    f"{int(row.get('O3_hub_gene_level', 0))}/2",
                )

            with o3:
                st.metric(
                    "O4 Core Processes",
                    f"{int(row.get('O4_core_mito_process_level', 0))}/2",
                )

            st.caption(
                "O1 conserved-signature evidence is excluded from the "
                "current Scientific Priority score pending final definition."
            )

        # ----------------------------------------------------
        # HUMAN PREFERENCE
        # ----------------------------------------------------

        with st.expander("🧑‍🔬 Human Preference Layer"):

            st.write(
                "Current calibrated probability mapping:"
            )

            h1, h2, h3 = st.columns(3)

            with h1:
                st.metric(
                    "P(Not Relevant)",
                    f"{p_not:.3f}",
                )

            with h2:
                st.metric(
                    "P(Maybe)",
                    f"{p_maybe:.3f}",
                )

            with h3:
                st.metric(
                    "P(Relevant)",
                    f"{p_relevant:.3f}",
                )

            st.caption(
                "This probability layer is secondary to Scientific Priority "
                "and is based on the current 110-paper human-label dataset."
            )

        # ----------------------------------------------------
        # EXPLANATION
        # ----------------------------------------------------

        with st.expander("💡 Why this paper is here"):

            explanation = clean_value(
                row.get("canonical_explanation_v1"),
                "No explanation available.",
            )

            st.text(explanation)

        # ----------------------------------------------------
        # ABSTRACT
        # ----------------------------------------------------

        with st.expander("📄 Abstract"):

            st.write(
                clean_value(
                    row.get(
                        "abstract"
                    ),
                    "Abstract unavailable.",
                )
            )

        # ----------------------------------------------------
        # PUBMED
        # ----------------------------------------------------

        pubmed_url = clean_value(
            row.get(
                "pubmed_url"
            ),
            "",
        )

        if pubmed_url:
            st.link_button(
                "🔗 Open in PubMed",
                pubmed_url,
            )

        # ----------------------------------------------------
        # LIVE USER ASSESSMENT
        # ----------------------------------------------------

        with st.expander("📝 Add New Assessment"):

            existing = feedback_df[
                feedback_df["pmid"].astype(str)
                == str(pmid)
            ]

            current_label = ""

            current_reason = ""

            if len(existing) > 0:

                current_label = clean_value(
                    existing.iloc[-1]["user_relevance"],
                    "",
                )

                current_reason = clean_value(
                    existing.iloc[-1]["user_reason"],
                    "",
                )

            labels = [
                "Not labeled",
                "Relevant",
                "Maybe",
                "Not Relevant",
            ]

            try:
                default_index = labels.index(current_label)
            except ValueError:
                default_index = 0

            selected_label = st.radio(
                "Your assessment",
                labels,
                index=default_index,
                horizontal=True,
                key=f"label_{pmid}",
            )

            reason = st.text_area(
                "Optional reason",
                value=current_reason if current_reason else "",
                key=f"reason_{pmid}",
                height=80,
            )

            if st.button(
                "💾 Save Assessment",
                key=f"save_{pmid}",
            ):

                saved_label = (
                    ""
                    if selected_label == "Not labeled"
                    else selected_label
                )

                save_live_feedback(
                    pmid,
                    saved_label,
                    reason,
                )

                st.success(
                    "Assessment saved separately from the calibration dataset."
                )

                st.rerun()
