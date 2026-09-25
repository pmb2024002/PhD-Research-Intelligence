import streamlit as st
import pandas as pd
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# MITOCHONDRIAL RESEARCH INTELLIGENCE — HOMEPAGE
# ============================================================

st.set_page_config(
    page_title="Mitochondrial Research Intelligence",
    page_icon="🧬",
    layout="wide",
)

st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
        margin-bottom: 18px;
    }
    div[data-testid="stTabs"] button {
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "pipeline"))



def format_discovered_at(value: str) -> str:
    """Format an ISO timestamp (as stored in Supabase, UTC) into a
    readable IST 'D Mon YYYY, H:MM AM/PM' string. Returns '' if value
    is missing/invalid. Always converts to Asia/Kolkata regardless of
    the server's own local timezone (local machine vs Streamlit Cloud
    can differ), so the displayed time is consistent everywhere."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_ist = dt.astimezone(ZoneInfo("Asia/Kolkata"))
        return dt_ist.strftime("%d %b %Y, %I:%M %p IST")
    except (ValueError, TypeError):
        return ""


def centered_caption(text: str):
    """Render a caption centered under a full-width diagram (st.caption
    is always left-aligned, which looks off-center under a centered SVG)."""
    st.markdown(
        f'<div style="text-align:center; color:#94a3b8; font-size:0.85rem; '
        f'margin-top:-8px;">{text}</div>',
        unsafe_allow_html=True,
    )


def render_svg(svg_markup: str):
    """
    Render inline SVG safely. Streamlit's markdown parser treats
    lines with 4+ leading spaces as a code block (standard Markdown
    behavior), which breaks indented multi-line SVG. It also treats
    blank lines as paragraph breaks, which splits one <svg> element
    into multiple HTML fragments and breaks rendering. This strips
    per-line leading whitespace AND drops blank lines before
    rendering, so the SVG is always parsed as one continuous raw
    HTML block.
    """
    lines = [
        line.strip()
        for line in svg_markup.strip().split("\n")
        if line.strip()
    ]
    cleaned = "\n".join(lines)
    st.markdown(cleaned, unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div style="
        font-size: 2.7rem;
        font-weight: 700;
        line-height: 1.12;
        letter-spacing: -0.025em;
        margin: 0;
        padding: 0;
    ">
        🧬 Mitochondrial Research Intelligence
    </div>

    <div style="
        width: 95px;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #a855f7);
        border-radius: 4px;
        margin-top: 14px;
        margin-bottom: 14px;
    "></div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 16px;
        max-width: 700px;
    ">
        An evidence-based literature intelligence platform tracking
        mitochondrial dysfunction and cellular senescence research in
        aging, combining automated PubMed discovery with structured,
        AI-assisted evidence extraction.
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def get_homepage_stats():
    canonical_count = 0
    v2_count = 0
    discovered_count = 0

    try:
        canonical_df = pd.read_csv(
            BASE_DIR / "data" / "production_v1" / "human_preference_layer_v1.csv"
        )
        canonical_count = len(canonical_df)
    except Exception:
        pass

    try:
        import json
        v2_path = BASE_DIR / "data" / "processed" / "v2" / "all_papers_v2_combined.json"
        with open(v2_path, "r", encoding="utf-8") as f:
            v2_count = len(json.load(f))
    except Exception:
        pass

    try:
        from supabase_client import get_client
        client = get_client()
        result = client.table("discovered_papers").select("pmid").execute()
        discovered_count = len(result.data or [])
    except Exception:
        pass

    return canonical_count, v2_count, discovered_count


canonical_count, v2_count, discovered_count = get_homepage_stats()
papers_tracked = canonical_count + discovered_count

stat_col1, stat_col2 = st.columns(2)

with stat_col1:
    st.metric(
        "Papers tracked",
        papers_tracked if papers_tracked else "—",
        help="Grows automatically as new papers are discovered via PubMed search.",
    )

with stat_col2:
    st.metric(
        "Deep evidence extractions",
        v2_count if v2_count else "—",
        help="Papers with full AI-assisted mechanism/evidence extraction (V2 pipeline).",
    )

st.markdown("<div style='margin-bottom: 8px'></div>", unsafe_allow_html=True)


# ============================================================
# NEW PAPERS CHECKER (TOP PRIORITY SECTION)
# ============================================================

with st.expander("🆕 Check for New Aging & Senescence Research", expanded=False):

    st.caption(
        "Searches PubMed live for the latest cellular senescence / "
        "mitochondrial dysfunction literature not yet in the database."
    )

    if st.button("🔍 Check PubMed now", type="primary"):

        with st.spinner("Searching PubMed..."):


            from check_new_papers import check_for_new_papers

            new_df = check_for_new_papers()

            # Exclude papers already saved -- they show in Saved Papers instead
            from supabase_client import get_saved_pmids
            if len(new_df) > 0:
                _saved_pmids = get_saved_pmids()
                new_df = new_df[
                    ~new_df["pmid"].astype(str).isin(_saved_pmids)
                ]

        st.session_state["new_papers_df"] = new_df

    new_df = st.session_state.get("new_papers_df")

    if new_df is not None:

        if len(new_df) == 0:
            st.info("No new papers found since the canonical dataset was built.")
        else:
            st.success(f"Found {len(new_df)} new paper(s)!")

            for _, nrow in new_df.iterrows():

                pmid = nrow.get("pmid", "")

                with st.container(border=True):

                    st.markdown(f"**{nrow.get('title', 'Untitled')}**")

                    st.caption(
                        f"{nrow.get('journal', '')} • "
                        f"{nrow.get('publication_date', '')} • "
                        f"PMID {pmid}"
                    )

                    _discovered_str = format_discovered_at(nrow.get("discovered_at", ""))
                    if _discovered_str:
                        st.caption(f"🕒 Discovered: {_discovered_str}")

                    abstract = nrow.get("abstract", "")
                    if abstract:
                        st.write(
                            abstract[:400]
                            + ("..." if len(abstract) > 400 else "")
                        )

                    url = nrow.get("pubmed_url", "")
                    if url:
                        st.link_button("🔗 Open in PubMed", url)

                    quick_key = f"quick_analysis_{pmid}"

                    btn_col1, btn_col2 = st.columns(2)

                    with btn_col1:
                        if st.button("🔬 Quick Analyze", key=f"analyze_btn_{pmid}"):

                            with st.spinner("Analyzing abstract..."):


                                from quick_analyze import quick_analyze_paper

                                try:
                                    result = quick_analyze_paper(
                                        title=nrow.get("title", ""),
                                        abstract=abstract,
                                    )
                                    st.session_state[quick_key] = result
                                except Exception as exc:
                                    st.error(f"Analysis failed: {exc}")

                    with btn_col2:

                        from supabase_client import (
                            get_saved_pmids,
                            save_paper,
                            unsave_paper,
                        )

                        currently_saved = str(pmid) in get_saved_pmids()

                        if currently_saved:

                            if st.button(
                                "✅ Saved — Unsave",
                                key=f"unsave_btn_{pmid}",
                            ):
                                unsave_paper(pmid)
                                st.rerun()

                        else:

                            if st.button(
                                "⭐ Save for Later",
                                key=f"save_btn_{pmid}",
                            ):
                                save_paper(nrow.to_dict())
                                st.rerun()

                    if quick_key in st.session_state:

                        result = st.session_state[quick_key]

                        st.markdown("**🔑 Key Findings:**")
                        st.write(result.get("key_findings", ""))

                        st.markdown("**🎯 Relevance:**")
                        st.write(result.get("relevance", ""))

                        st.markdown("**📝 Conclusion:**")
                        st.write(result.get("conclusion", ""))

st.divider()


# ============================================================
# RESEARCH STORY
# ============================================================

from supabase_client import get_research_story

_story = get_research_story()

with st.expander("📖 Research Story: The Field at a Glance", expanded=False):

    if _story and _story.get("content"):

        st.caption(
            f"Generated: {_story.get('generated_at', '')} · "
            f"Covers {_story.get('papers_covered', 0)} papers"
        )

        st.markdown(_story["content"])

        if st.button("🔄 Regenerate Now", key="regenerate_story_btn"):
            with st.spinner("Regenerating research story..."):
                try:
                    from generate_story import generate_and_save
                    generate_and_save()
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not regenerate: {exc}")

    else:
        st.info("No research story generated yet.")
        if st.button("✨ Generate Research Story", key="generate_story_btn"):
            with st.spinner("Generating research story (this may take 20-30 seconds)..."):
                try:
                    from generate_story import generate_and_save
                    generate_and_save()
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not generate: {exc}")

st.divider()


# ============================================================
# SAVED PAPERS
# ============================================================

from supabase_client import get_saved_papers, unsave_paper

_saved_list = get_saved_papers()

if len(_saved_list) > 0:

    with st.expander(f"⭐ Saved Papers ({len(_saved_list)})", expanded=False):

        for srow in _saved_list:

            with st.container(border=True):

                st.markdown(f"**{srow.get('title', 'Untitled')}**")

                st.caption(
                    f"{srow.get('journal', '')} • "
                    f"{srow.get('publication_date', '')} • "
                    f"PMID {srow.get('pmid', '')} • "
                    f"Saved {srow.get('saved_at', '')}"
                )

                surl = srow.get("pubmed_url", "")
                if surl:
                    st.link_button(
                        "🔗 Open in PubMed",
                        surl,
                        key=f"saved_link_{srow.get('pmid', '')}",
                    )

                if st.button(
                    "🗑️ Remove",
                    key=f"remove_{srow.get('pmid', '')}",
                ):
                    unsave_paper(srow.get("pmid", ""))
                    st.rerun()

st.divider()


# ============================================================
# ABOUT THE RESEARCHER (merged with PhD research overview)
# ============================================================

with st.container(border=True):

    about_col1, about_col2 = st.columns([1, 3])

    with about_col1:

        PROFILE_PHOTO = BASE_DIR / "assets" / "profile_photo.jpg"

        if PROFILE_PHOTO.exists():
            import base64

            photo_bytes = PROFILE_PHOTO.read_bytes()
            photo_b64 = base64.b64encode(photo_bytes).decode()

            st.markdown(
                f"""
                <img src="data:image/jpeg;base64,{photo_b64}" style="
                    width: 150px;
                    height: 150px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 3px solid #3b82f6;
                " />
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="
                    width: 90px;
                    height: 90px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #3b82f6, #a855f7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2.2rem;
                    font-weight: 700;
                    color: white;
                ">
                    AK
                </div>
                """,
                unsafe_allow_html=True,
            )

    with about_col2:
        st.markdown("### About the Researcher")
        st.markdown(
            """
**Ankit Kumar Kushwaha**

Doctoral Researcher, Bioinformatics & Computational Biology

**Indian Institute of Information Technology, Allahabad (IIIT-A)**

Supervised by **Prof. Pritish K. Varadwaj**
            """
        )

    st.markdown(
        """
#### 🔬 PhD Research: *Multi-Omics Analysis of Mitochondrial Dysfunction in Cellular Senescence*

Doctoral research focused on understanding the molecular relationship
between **mitochondrial dysfunction and cellular senescence**, using
computational and multi-omics approaches to investigate conserved
molecular signatures associated with cellular aging.

This platform is a working research tool built from that program --
combining rule-based literature ranking with schema-validated,
locally-run AI evidence extraction -- to systematically track and
understand the mitochondrial dysfunction / cellular senescence
literature.
        """
    )

    about_r1, about_r2 = st.columns(2)

    with about_r1:
        st.markdown(
            """
**Research Areas**
- Mitochondrial Biology
- Cellular Senescence
- Aging Biology
- Bioinformatics & Multi-Omics
            """
        )

    with about_r2:
        st.markdown(
            """
**Research Focus**

Understanding how mitochondrial alterations are associated with the
molecular programs underlying cellular senescence and age-related
cellular dysfunction.
            """
        )

st.divider()


# ============================================================
# MITOCHONDRIA — INTRODUCTION
# ============================================================

intro_col, image_col = st.columns([2.2, 1.3], vertical_alignment="center")

with intro_col:
    st.markdown("## What Are Mitochondria?")
    st.markdown(
        """
Mitochondria are membrane-bound organelles found in nearly every cell
of the body, often called the **"powerhouse of the cell."** Their
primary role is producing **ATP** (adenosine triphosphate), the
molecule that powers almost every cellular process, through a process
called **oxidative phosphorylation**.

Beyond energy production, mitochondria are central to:

- **Cellular signaling** - regulating calcium levels and reactive
  oxygen species (ROS)
- **Apoptosis** - controlling programmed cell death pathways
- **Metabolic regulation** - integrating nutrient and energy status
- **Mitochondrial dynamics** - continuously undergoing **fission**
  (dividing) and **fusion** (merging) to maintain a healthy network
- **Mitophagy** - the selective clearance of damaged mitochondria via
  autophagy, a key quality-control mechanism

As cells age, mitochondrial function tends to decline: energy
production becomes less efficient, ROS accumulates, and the balance
between fission/fusion and mitophagy breaks down. This
**mitochondrial dysfunction** is increasingly recognized as a driver,
not just a consequence, of **cellular senescence**, the irreversible
growth arrest linked to aging and age-related disease.
        """
    )

with image_col:
    render_svg("""
    <svg viewBox="0 0 560 380" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto;">
        <defs>
            <linearGradient id="heroCristae" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#fb923c"/>
                <stop offset="100%" stop-color="#c2410c"/>
            </linearGradient>
        </defs>

        <rect x="40" y="60" width="480" height="220" rx="110" fill="#3b0764" stroke="#c084fc" stroke-width="2.5"/>
        <rect x="66" y="86" width="428" height="168" rx="84" fill="#1e1b4b" stroke="#a78bfa" stroke-width="1.5"/>

        <circle cx="105" cy="115" r="3" fill="#fbbf24"/>
        <circle cx="125" cy="225" r="3" fill="#fbbf24"/>
        <circle cx="440" cy="115" r="3" fill="#fbbf24"/>
        <circle cx="455" cy="215" r="3" fill="#fbbf24"/>
        <circle cx="150" cy="100" r="3" fill="#fbbf24"/>
        <circle cx="400" cy="235" r="3" fill="#fbbf24"/>
        <circle cx="475" cy="150" r="3" fill="#fbbf24"/>
        <circle cx="90" cy="170" r="3" fill="#fbbf24"/>

        <path d="M 88,170
                 C 108,120 138,120 158,170
                 C 178,220 208,220 228,170
                 C 248,120 278,120 298,170
                 C 318,220 348,220 368,170
                 C 388,120 418,120 438,170
                 C 458,120 468,120 478,150"
              fill="none" stroke="url(#heroCristae)" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>

        <circle cx="268" cy="170" r="16" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-dasharray="3 3"/>
        <circle cx="268" cy="170" r="3" fill="#fbbf24"/>
        <circle cx="262" cy="162" r="2" fill="#fbbf24"/>
        <circle cx="277" cy="180" r="2" fill="#fbbf24"/>

        <text x="280" y="345" fill="#93c5fd" font-size="16" text-anchor="middle" font-weight="600">Mitochondrion</text>
    </svg>
    """)
    centered_caption("A mitochondrion, showing the folded inner membrane (cristae) and matrix.")

st.divider()


# ============================================================
# LEARN — MITOCHONDRIA & AGING (EDUCATIONAL SECTION)
# ============================================================

st.markdown("## 📖 Learn: Mitochondria, Aging & Disease")
st.caption(
    "A deeper dive, from basic structure to advanced disease "
    "mechanisms."
)

learn_tabs = st.tabs([
    "🔬 Structure & Function",
    "⚡ Energy Production",
    "🧬 Mitochondria & Aging",
    "🎯 Hallmarks of Aging",
    "🌍 Causes of Aging",
    "🏥 Age-Related Diseases",
])


# ------------------------------------------------------------
# TAB 1: STRUCTURE & FUNCTION
# ------------------------------------------------------------

with learn_tabs[0]:

    col_text, col_image = st.columns([1.1, 1])

    with col_text:
        st.markdown(
            """
### Anatomy of a Mitochondrion

Mitochondria have a distinctive double-membrane structure that sets
them apart from most other organelles. Unlike most organelles,
mitochondria contain their own circular DNA (inherited maternally)
and can replicate independently of the cell cycle, a legacy of their
evolutionary origin as free-living bacteria that were engulfed by an
ancestral cell roughly 1.5 to 2 billion years ago (the endosymbiotic
theory).
            """
        )

        st.markdown("#### Explore each part")

        STRUCTURE_DETAILS = {
            "Outer membrane": (
                "A smooth, relatively permeable boundary studded with "
                "channel proteins called porins, which allow small "
                "molecules and ions to pass through freely. It defines the "
                "outer boundary of the organelle but offers little "
                "resistance to small solutes."
            ),
            "Intermembrane space": (
                "The narrow gap between the outer and inner membranes. "
                "This compartment fills with protons (H+) pumped out "
                "during electron transport, building the electrochemical "
                "gradient that ATP synthase later uses to generate energy."
            ),
            "Inner membrane and cristae": (
                "The inner membrane is folded into finger-like structures "
                "called cristae, which dramatically increase its surface "
                "area. This membrane is far less permeable than the outer "
                "one, which is essential for maintaining the proton "
                "gradient. It houses the electron transport chain and ATP "
                "synthase."
            ),
            "Matrix": (
                "The innermost compartment, enclosed by the inner "
                "membrane. It contains mitochondrial DNA (mtDNA), "
                "ribosomes, and the enzymes of the citric acid (Krebs) "
                "cycle, which generates the electron carriers used by the "
                "electron transport chain."
            ),
            "Mitochondrial DNA (mtDNA)": (
                "A small, circular piece of DNA located in the matrix, "
                "inherited only from the mother. It encodes a small number "
                "of proteins essential for the electron transport chain. "
                "Because mtDNA lacks the protective histones and robust "
                "repair systems of nuclear DNA, it is more prone to "
                "mutation, especially from oxidative damage."
            ),
        }

        selected_part = st.selectbox(
            "Choose a structural part to explore:",
            options=list(STRUCTURE_DETAILS.keys()),
            key="structure_part_select",
        )

        with st.container(border=True):
            st.markdown(f"**{selected_part}**")
            st.write(STRUCTURE_DETAILS[selected_part])

    with col_image:
        render_svg("""
        <svg viewBox="0 0 640 440" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto;">
            <defs>
                <linearGradient id="structCristae" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#fb923c"/>
                    <stop offset="100%" stop-color="#c2410c"/>
                </linearGradient>
            </defs>

            <rect x="60" y="90" width="520" height="240" rx="120" fill="#3b0764" stroke="#c084fc" stroke-width="2.5"/>
            <rect x="88" y="118" width="464" height="184" rx="92" fill="#1e1b4b" stroke="#a78bfa" stroke-width="1.5"/>

            <circle cx="130" cy="150" r="3.5" fill="#fbbf24"/>
            <circle cx="150" cy="270" r="3.5" fill="#fbbf24"/>
            <circle cx="480" cy="150" r="3.5" fill="#fbbf24"/>
            <circle cx="500" cy="260" r="3.5" fill="#fbbf24"/>
            <circle cx="180" cy="130" r="3.5" fill="#fbbf24"/>
            <circle cx="430" cy="280" r="3.5" fill="#fbbf24"/>
            <circle cx="520" cy="180" r="3.5" fill="#fbbf24"/>
            <circle cx="110" cy="210" r="3.5" fill="#fbbf24"/>

            <path d="M 108,210
                     C 132,150 168,150 192,210
                     C 216,270 252,270 276,210
                     C 300,150 336,150 360,210
                     C 384,270 420,270 444,210
                     C 468,150 504,150 528,210"
                  fill="none" stroke="url(#structCristae)" stroke-width="28" stroke-linecap="round" stroke-linejoin="round"/>

            <circle cx="318" cy="210" r="18" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-dasharray="4 4"/>
            <circle cx="318" cy="210" r="3" fill="#fbbf24"/>
            <circle cx="310" cy="200" r="2" fill="#fbbf24"/>
            <circle cx="328" cy="222" r="2" fill="#fbbf24"/>

            <text x="200" y="30" fill="#93c5fd" font-size="15" text-anchor="middle" font-weight="600">Outer membrane</text>
            <line x1="200" y1="37" x2="170" y2="88" stroke="#93c5fd" stroke-width="1.5"/>

            <text x="150" y="62" fill="#c084fc" font-size="15" text-anchor="middle" font-weight="600">Inner membrane</text>
            <line x1="150" y1="69" x2="132" y2="116" stroke="#c084fc" stroke-width="1.5"/>

            <text x="440" y="30" fill="#fdba74" font-size="15" text-anchor="middle" font-weight="600">Cristae</text>
            <text x="440" y="46" fill="#94a3b8" font-size="12" text-anchor="middle">Folds of inner membrane</text>
            <line x1="440" y1="52" x2="400" y2="150" stroke="#fdba74" stroke-width="1.5"/>

            <text x="560" y="150" fill="#e9d5ff" font-size="15" text-anchor="middle" font-weight="600">Matrix</text>
            <line x1="560" y1="157" x2="480" y2="220" stroke="#e9d5ff" stroke-width="1.5"/>

            <text x="70" y="360" fill="#eab308" font-size="15" text-anchor="middle" font-weight="600">Intermembrane space</text>
            <line x1="70" y1="353" x2="100" y2="285" stroke="#eab308" stroke-width="1.5"/>

            <text x="260" y="410" fill="#d1d5db" font-size="15" text-anchor="middle" font-weight="600">Ribosomes</text>
            <line x1="260" y1="403" x2="240" y2="260" stroke="#d1d5db" stroke-width="1.5"/>

            <text x="380" y="410" fill="#fde68a" font-size="15" text-anchor="middle" font-weight="600">Mitochondrial DNA</text>
            <line x1="370" y1="403" x2="330" y2="228" stroke="#fde68a" stroke-width="1.5"/>
        </svg>
        """)

        centered_caption(
            "Mitochondrial structure and major functional compartments."
        )

# ------------------------------------------------------------
# TAB 2: ENERGY PRODUCTION
# ------------------------------------------------------------

with learn_tabs[1]:

    st.markdown(
        """
### How Mitochondria Make Energy

Mitochondria generate ATP primarily through oxidative
phosphorylation, a process carried out by the electron transport
chain (ETC), a series of five protein complexes embedded in the
inner membrane.
        """
    )

    render_svg("""
<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto;">
            <rect x="20" y="110" width="660" height="20" fill="#334155"/>
            <text x="350" y="105" fill="#94a3b8" font-size="12" text-anchor="middle">Inner Mitochondrial Membrane</text>

            <rect x="40" y="90" width="60" height="60" rx="8" fill="#3b82f6"/>
            <text x="70" y="125" fill="white" font-size="12" text-anchor="middle" font-weight="600">I</text>

            <rect x="150" y="95" width="55" height="50" rx="8" fill="#0ea5e9"/>
            <text x="177" y="125" fill="white" font-size="12" text-anchor="middle" font-weight="600">II</text>

            <rect x="255" y="90" width="60" height="60" rx="8" fill="#a855f7"/>
            <text x="285" y="125" fill="white" font-size="12" text-anchor="middle" font-weight="600">III</text>

            <rect x="365" y="90" width="60" height="60" rx="8" fill="#ec4899"/>
            <text x="395" y="125" fill="white" font-size="12" text-anchor="middle" font-weight="600">IV</text>

            <rect x="480" y="80" width="90" height="80" rx="10" fill="#22c55e"/>
            <text x="525" y="115" fill="white" font-size="11" text-anchor="middle" font-weight="600">ATP</text>
            <text x="525" y="132" fill="white" font-size="11" text-anchor="middle" font-weight="600">Synthase</text>

            <path d="M100,100 L150,100" stroke="#facc15" stroke-width="2" marker-end="url(#arrow)"/>
            <path d="M205,100 L255,100" stroke="#facc15" stroke-width="2" marker-end="url(#arrow)"/>
            <path d="M315,100 L365,100" stroke="#facc15" stroke-width="2" marker-end="url(#arrow)"/>
            <text x="230" y="80" fill="#facc15" font-size="11" text-anchor="middle">e⁻ flow</text>

            <path d="M70,90 L70,40" stroke="#f97316" stroke-width="2" marker-end="url(#arrow2)"/>
            <path d="M285,90 L285,40" stroke="#f97316" stroke-width="2" marker-end="url(#arrow2)"/>
            <path d="M395,90 L395,40" stroke="#f97316" stroke-width="2" marker-end="url(#arrow2)"/>
            <text x="380" y="25" fill="#f97316" font-size="11" text-anchor="middle">H⁺ pumped to intermembrane space</text>

            <path d="M550,80 L550,30 L100,30 L100,80" stroke="#f97316" stroke-width="2" fill="none" stroke-dasharray="4,3" marker-end="url(#arrow2)"/>
            <text x="325" y="185" fill="#22c55e" font-size="12" text-anchor="middle">H⁺ flows back through ATP Synthase → ATP produced</text>

            <text x="20" y="170" fill="#94a3b8" font-size="12">Matrix</text>
            <text x="20" y="15" fill="#94a3b8" font-size="12">Intermembrane Space</text>

            <defs>
                <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill="#facc15"/>
                </marker>
                <marker id="arrow2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill="#f97316"/>
                </marker>
            </defs>
        </svg>
""")
    centered_caption("The electron transport chain and chemiosmotic ATP production.")

    st.markdown("#### Explore each step")

    ETC_STEPS = {
        "1. Electron carriers formed": (
            "Nutrients such as glucose and fatty acids are broken down "
            "through glycolysis and the citric acid (Krebs) cycle. These "
            "processes produce electron carrier molecules, mainly NADH and "
            "FADH2, which hold high-energy electrons ready to be passed "
            "down the chain."
        ),
        "2. Complex I and Complex II": (
            "NADH donates its electrons to Complex I, and FADH2 donates its "
            "electrons to Complex II. Both complexes pass these electrons "
            "onward to a shared carrier molecule, which ferries them to "
            "Complex III. Complex I also pumps protons across the "
            "membrane as electrons pass through it."
        ),
        "3. Complex III and Complex IV": (
            "Electrons continue down the chain through Complex III and "
            "finally Complex IV. At each of these steps, energy released "
            "by the moving electrons is used to pump protons (H+) from "
            "the matrix into the intermembrane space, building up an "
            "electrochemical gradient across the inner membrane."
        ),
        "4. ATP synthase": (
            "The proton gradient built up in the intermembrane space "
            "represents stored energy, similar to water held behind a "
            "dam. Protons flow back into the matrix through a channel in "
            "ATP synthase, and this flow physically spins part of the "
            "enzyme, driving the synthesis of ATP from ADP and inorganic "
            "phosphate."
        ),
        "5. Oxygen as the final acceptor": (
            "At Complex IV, the electrons that have traveled down the "
            "entire chain finally combine with oxygen to form water. This "
            "is the reason mitochondria, and therefore the body, "
            "continuously consume the oxygen we breathe: oxygen is the "
            "final destination for these electrons."
        ),
    }

    selected_step = st.selectbox(
        "Choose a step to explore:",
        options=list(ETC_STEPS.keys()),
        key="etc_step_select",
    )

    with st.container(border=True):
        st.markdown(f"**{selected_step}**")
        st.write(ETC_STEPS[selected_step])

    st.markdown(
        """
This process is remarkably efficient but not perfect. A small
fraction of electrons "leak" from the chain and react with oxygen to
form reactive oxygen species (ROS), a byproduct with major
implications for aging (see the next tab).
        """
    )


# ------------------------------------------------------------
# TAB 3: MITOCHONDRIA & AGING
# ------------------------------------------------------------

with learn_tabs[2]:

    st.markdown(
        """
### The Mitochondrial Theory of Aging

First proposed by Denham Harman in the 1970s, building on his earlier
free-radical theory of aging, the mitochondrial theory of aging holds
that the slow accumulation of mitochondrial damage, driven largely by
reactive oxygen species (ROS), is a central mechanism of biological
aging. This theory has been refined considerably since it was first
proposed, and the sections below walk through both the original idea
and how modern research has updated it.
        """
    )

    st.markdown("#### Explore the key concepts")

    MITO_AGING_TOPICS = {
        "The proposed vicious cycle": (
            "Normal electron transport chain (ETC) activity generates a "
            "small, constant flux of ROS. This ROS can damage "
            "mitochondrial DNA (mtDNA), which lacks the protective "
            "histones and robust repair machinery of nuclear DNA, making "
            "it more mutation-prone. Damaged mtDNA can then encode "
            "defective ETC proteins, and defective ETC complexes leak "
            "even more electrons, generating more ROS. Over time, this "
            "feedback loop can lead to progressively worsening "
            "mitochondrial function, energy deficits, and cellular "
            "damage."
        ),
        "Link to cellular senescence": (
            "Dysfunctional mitochondria are a well-established driver of "
            "cellular senescence, a state in which damaged cells stop "
            "dividing but remain metabolically active, often secreting "
            "inflammatory molecules known as the senescence-associated "
            "secretory phenotype (SASP). Senescent cells accumulate with "
            "age in nearly every tissue, contributing to chronic "
            "low-grade inflammation (often called 'inflammaging') and "
            "progressive tissue dysfunction."
        ),
        "Role of mitophagy": (
            "Mitophagy is the process by which cells selectively clear "
            "out damaged mitochondria through autophagy. When mitophagy "
            "becomes impaired with age, dysfunctional mitochondria are no "
            "longer cleared efficiently, allowing them to persist and "
            "accumulate. This further amplifies ROS output and drives "
            "additional senescence induction, compounding the problem."
        ),
        "Role of mitochondrial biogenesis": (
            "Mitochondrial biogenesis is the process of producing new, "
            "healthy mitochondria, regulated in part by the PGC-1 alpha "
            "signaling pathway. As this process declines with age, cells "
            "become progressively less able to replace damaged "
            "mitochondria, so the overall mitochondrial population "
            "gradually skews toward less functional organelles."
        ),
        "Modern nuance: ROS as signals, not just damage": (
            "The simple 'ROS causes aging' version of this theory has "
            "been substantially refined in recent decades. ROS at low, "
            "regulated levels also serve as important signaling "
            "molecules that trigger beneficial adaptive stress responses, "
            "a phenomenon called mitohormesis. The current understanding "
            "is that the relationship between mitochondrial ROS and "
            "aging is more complex than pure accumulated damage: it "
            "involves a balance between useful signaling, adaptive "
            "responses, and genuine quality-control failure."
        ),
    }

    selected_topic = st.selectbox(
        "Choose a concept to explore:",
        options=list(MITO_AGING_TOPICS.keys()),
        key="mito_aging_topic_select",
    )

    with st.container(border=True):
        st.markdown(f"**{selected_topic}**")
        st.write(MITO_AGING_TOPICS[selected_topic])


# ------------------------------------------------------------
# TAB 4: HALLMARKS OF AGING
# ------------------------------------------------------------

with learn_tabs[3]:

    st.markdown(
        """
### The Hallmarks of Aging

In 2013, López-Otín and colleagues proposed a widely cited framework
of **nine hallmarks of aging** — common cellular and molecular
features observed across aging organisms. This was expanded to
**twelve hallmarks** in a 2023 update. **Mitochondrial dysfunction**
is one of the core hallmarks, and it interacts closely with several
of the others.
        """
    )

    render_svg("""
<svg viewBox="0 0 560 560" xmlns="http://www.w3.org/2000/svg" style="width:100%; max-width:520px; height:auto; display:block; margin:0 auto;">
            <circle cx="280" cy="280" r="100" fill="#1e293b" stroke="#3b82f6" stroke-width="3"/>
            <text x="280" y="272" fill="#e2e8f0" font-size="15" text-anchor="middle" font-weight="700">12 Hallmarks</text>
            <text x="280" y="292" fill="#94a3b8" font-size="12" text-anchor="middle">of Aging</text>

            <circle cx="280" cy="100" r="55" fill="#f97316"/>
            <text x="280" y="95" fill="white" font-size="10" text-anchor="middle" font-weight="600">Mitochondrial</text>
            <text x="280" y="108" fill="white" font-size="10" text-anchor="middle" font-weight="600">Dysfunction</text>

            <circle cx="440" cy="155" r="50" fill="#334155"/>
            <text x="440" y="150" fill="white" font-size="9" text-anchor="middle">Genomic</text>
            <text x="440" y="162" fill="white" font-size="9" text-anchor="middle">Instability</text>

            <circle cx="495" cy="290" r="50" fill="#334155"/>
            <text x="495" y="285" fill="white" font-size="9" text-anchor="middle">Telomere</text>
            <text x="495" y="297" fill="white" font-size="9" text-anchor="middle">Attrition</text>

            <circle cx="440" cy="425" r="50" fill="#334155"/>
            <text x="440" y="420" fill="white" font-size="9" text-anchor="middle">Epigenetic</text>
            <text x="440" y="432" fill="white" font-size="9" text-anchor="middle">Alterations</text>

            <circle cx="280" cy="480" r="50" fill="#334155"/>
            <text x="280" y="475" fill="white" font-size="9" text-anchor="middle">Loss of</text>
            <text x="280" y="487" fill="white" font-size="9" text-anchor="middle">Proteostasis</text>

            <circle cx="120" cy="425" r="50" fill="#334155"/>
            <text x="120" y="420" fill="white" font-size="9" text-anchor="middle">Disabled</text>
            <text x="120" y="432" fill="white" font-size="9" text-anchor="middle">Macroautophagy</text>

            <circle cx="65" cy="290" r="50" fill="#334155"/>
            <text x="65" y="285" fill="white" font-size="9" text-anchor="middle">Deregulated</text>
            <text x="65" y="297" fill="white" font-size="9" text-anchor="middle">Nutrient Sensing</text>

            <circle cx="120" cy="155" r="50" fill="#334155"/>
            <text x="120" y="150" fill="white" font-size="9" text-anchor="middle">Cellular</text>
            <text x="120" y="162" fill="white" font-size="9" text-anchor="middle">Senescence</text>

            <circle cx="200" cy="65" r="45" fill="#334155"/>
            <text x="200" y="60" fill="white" font-size="8" text-anchor="middle">Stem Cell</text>
            <text x="200" y="72" fill="white" font-size="8" text-anchor="middle">Exhaustion</text>

            <circle cx="360" cy="65" r="45" fill="#334155"/>
            <text x="360" y="60" fill="white" font-size="8" text-anchor="middle">Altered Intercell.</text>
            <text x="360" y="72" fill="white" font-size="8" text-anchor="middle">Communication</text>

            <circle cx="520" cy="220" r="42" fill="#334155"/>
            <text x="520" y="215" fill="white" font-size="8" text-anchor="middle">Chronic</text>
            <text x="520" y="227" fill="white" font-size="8" text-anchor="middle">Inflammation</text>

            <circle cx="520" cy="360" r="42" fill="#334155"/>
            <text x="520" y="355" fill="white" font-size="8" text-anchor="middle">Dysbiosis</text>

            <circle cx="360" cy="500" r="42" fill="#334155"/>
            <text x="360" y="495" fill="white" font-size="8" text-anchor="middle">Splicing</text>
            <text x="360" y="507" fill="white" font-size="8" text-anchor="middle">Dysregulation</text>
        </svg>
""")
    centered_caption(
        "The 12 Hallmarks of Aging (López-Otín et al., 2013; updated 2023)."
    )

    st.markdown(
        """
**Why mitochondrial dysfunction is central:** unlike most other
hallmarks, mitochondrial dysfunction has extensive bidirectional
links to nearly all the others. It contributes to genomic instability
(via ROS-induced DNA damage), drives cellular senescence, impairs
stem cell function, and is itself worsened by deregulated nutrient
sensing and disabled autophagy/mitophagy. This central, interconnected
role is a major reason it is a focus of current aging and senescence
research (including this project's own focus area).
        """
    )

    st.markdown("#### Explore each hallmark")
    st.caption("Select a hallmark below to read what it means and how it drives aging.")

    HALLMARK_DETAILS = {
        "Genomic instability": (
            "DNA is constantly damaged by replication errors, radiation, and "
            "reactive chemicals. Repair systems fix most of this, but repair "
            "efficiency declines with age, so mutations and chromosomal "
            "abnormalities slowly accumulate. This raises cancer risk and "
            "impairs normal cell function over time."
        ),
        "Telomere attrition": (
            "Telomeres are protective repetitive DNA sequences that cap the "
            "ends of chromosomes. Because DNA replication cannot fully copy "
            "chromosome ends, telomeres shorten with each cell division. Once "
            "they become critically short, the cell can no longer divide "
            "safely and typically enters senescence or dies."
        ),
        "Epigenetic alterations": (
            "Gene activity is regulated by chemical marks on DNA and histone "
            "proteins (DNA methylation, histone modifications) rather than "
            "the DNA sequence itself. These marks drift with age, silencing "
            "genes that should stay active and activating genes that should "
            "stay silent, disrupting normal cellular identity and function."
        ),
        "Loss of proteostasis": (
            "Cells constantly fold, refold, and degrade proteins to keep only "
            "correctly-functioning ones in circulation. With age, this quality "
            "control weakens, allowing misfolded and damaged proteins to "
            "accumulate as aggregates, a hallmark seen in diseases like "
            "Alzheimer's and Parkinson's."
        ),
        "Disabled macroautophagy": (
            "Autophagy is the process by which cells break down and recycle "
            "their own damaged components, including old organelles and "
            "protein aggregates. Autophagic activity declines with age, "
            "meaning damaged cellular material is cleared more slowly and "
            "builds up, including damaged mitochondria (impaired mitophagy)."
        ),
        "Deregulated nutrient sensing": (
            "Cells constantly monitor nutrient and energy availability through "
            "pathways like insulin/IGF-1, mTOR, and AMPK, adjusting growth and "
            "repair accordingly. With age, this sensing becomes less accurate, "
            "often locking cells into a growth-promoting state even when "
            "resources should instead be devoted to repair and maintenance."
        ),
        "Mitochondrial dysfunction": (
            "Mitochondria progressively lose efficiency at producing ATP, "
            "generate more reactive oxygen species (ROS), and accumulate "
            "mutations in their own DNA. Because mitochondria interact with "
            "nearly every other hallmark of aging, this decline is considered "
            "one of the most central and consequential aging mechanisms "
            "(the focus of this research platform)."
        ),
        "Cellular senescence": (
            "Damaged or stressed cells can permanently stop dividing rather "
            "than risk becoming cancerous, entering a state called "
            "senescence. Senescent cells accumulate with age and secrete "
            "inflammatory signaling molecules (the SASP), which damages "
            "nearby healthy tissue and drives chronic inflammation."
        ),
        "Stem cell exhaustion": (
            "Tissues rely on small pools of stem cells to replace worn-out "
            "or damaged cells throughout life. With age, these stem cell "
            "pools shrink and lose regenerative capacity, so tissues repair "
            "and renew themselves more slowly and less completely."
        ),
        "Altered intercellular communication": (
            "Cells coordinate tissue-wide behavior through hormones, "
            "neurotransmitters, and other signaling molecules. Aging "
            "disrupts these communication networks, contributing to chronic "
            "low-grade inflammation and a breakdown in the coordinated "
            "responses tissues need to stay healthy."
        ),
        "Chronic inflammation": (
            "Often called 'inflammaging,' this is a persistent, low-grade "
            "inflammatory state that develops with age, distinct from acute "
            "infection-fighting inflammation. It is driven partly by "
            "senescent cells (via the SASP) and contributes to nearly every "
            "major age-related disease, from cardiovascular disease to "
            "neurodegeneration."
        ),
        "Dysbiosis": (
            "The trillions of microorganisms living in and on the body (the "
            "microbiome, especially in the gut) shift in composition and "
            "diversity with age. This dysbiosis is linked to increased gut "
            "permeability, chronic inflammation, and metabolic changes that "
            "affect health throughout the body, not just the digestive "
            "system."
        ),
    }

    selected_hallmark = st.selectbox(
        "Choose a hallmark to explore:",
        options=list(HALLMARK_DETAILS.keys()),
        index=list(HALLMARK_DETAILS.keys()).index("Mitochondrial dysfunction"),
    )

    with st.container(border=True):
        st.markdown(f"**{selected_hallmark}**")
        st.write(HALLMARK_DETAILS[selected_hallmark])


# ------------------------------------------------------------
# TAB 5: CAUSES OF AGING
# ------------------------------------------------------------

with learn_tabs[4]:

    st.markdown(
        """
### What Causes Aging?

Aging is not driven by a single cause. It results from the interaction
of intrinsic (genetic and biological) and extrinsic (environmental
and lifestyle) factors accumulating over a lifetime. Explore each
factor below.
        """
    )

    CAUSE_DETAILS = {
        "🧬 Genetic programming (intrinsic)": (
            "Inherited genes influence baseline longevity and disease "
            "susceptibility. However, genetics is estimated to account "
            "for only about 20 to 30 percent of lifespan variation in "
            "humans, meaning lifestyle and environment play a "
            "substantially larger role than most people assume."
        ),
        "🧬 Telomere shortening (intrinsic)": (
            "The protective caps on chromosome ends, called telomeres, "
            "shorten with each cell division because DNA replication "
            "cannot fully copy chromosome tips. Once telomeres become "
            "critically short, the cell can no longer divide safely and "
            "typically enters senescence."
        ),
        "🧬 Accumulated DNA damage (intrinsic)": (
            "DNA is continuously damaged by replication errors, radiation, "
            "and reactive chemicals inside the cell. Repair mechanisms fix "
            "most of this damage, but with age, damage accumulates faster "
            "than repair systems can fully correct it."
        ),
        "🧬 Mitochondrial dysfunction (intrinsic)": (
            "Mitochondria progressively lose efficiency at producing ATP "
            "and generate more reactive oxygen species (ROS) with age, as "
            "discussed in detail in the earlier tabs of this section."
        ),
        "🧬 Epigenetic drift (intrinsic)": (
            "Age-related changes accumulate in DNA methylation and "
            "chromatin structure, which alter gene expression patterns "
            "without changing the underlying DNA sequence itself. This "
            "drift can silence genes that should stay active, or activate "
            "genes that should stay silent."
        ),
        "🧬 Stem cell exhaustion (intrinsic)": (
            "Tissue-specific stem cell pools gradually decline in both "
            "size and regenerative capacity with age, meaning tissues "
            "become slower and less complete at repairing and renewing "
            "themselves."
        ),
        "🌍 Diet and nutrition (extrinsic)": (
            "Chronic overnutrition, poor diet quality, and metabolic "
            "dysregulation accelerate cellular damage over time. Diet is "
            "one of the most modifiable extrinsic factors affecting the "
            "rate of biological aging."
        ),
        "🌍 Physical inactivity (extrinsic)": (
            "A sedentary lifestyle reduces mitochondrial biogenesis (the "
            "production of new, healthy mitochondria) and weakens "
            "cardiovascular and muscular resilience, both of which are "
            "closely tied to healthy aging."
        ),
        "🌍 Chronic stress (extrinsic)": (
            "Sustained elevation of stress hormones like cortisol is "
            "linked to accelerated telomere attrition and heightened "
            "inflammation, connecting psychological stress to measurable "
            "biological aging markers."
        ),
        "🌍 Environmental toxins (extrinsic)": (
            "Exposure to UV radiation, air pollution, and cigarette smoke "
            "increases oxidative stress and DNA damage, compounding the "
            "intrinsic damage that already accumulates naturally with "
            "age."
        ),
        "🌍 Sleep disruption (extrinsic)": (
            "Poor or insufficient sleep impairs the cellular repair "
            "processes and metabolic regulation that normally occur "
            "during rest, reducing the body's capacity to counteract "
            "daily cellular wear and tear."
        ),
        "🌍 Chronic infections and inflammation (extrinsic)": (
            "Sustained immune activation, often called 'inflammaging,' "
            "accelerates tissue damage over decades and is now recognized "
            "as one of the core hallmarks of aging in its own right."
        ),
    }

    selected_cause = st.selectbox(
        "Choose a factor to explore:",
        options=list(CAUSE_DETAILS.keys()),
        key="cause_select",
    )

    with st.container(border=True):
        st.markdown(f"**{selected_cause}**")
        st.write(CAUSE_DETAILS[selected_cause])

    st.markdown(
        """
**Key concept: these factors interact.** Intrinsic and extrinsic
factors do not act independently. For example, poor diet (extrinsic)
increases mitochondrial ROS production (an intrinsic mechanism),
which accelerates DNA damage (another intrinsic hallmark) and
promotes cellular senescence. This is why aging research increasingly
focuses on interconnected mechanisms, like mitochondrial dysfunction,
rather than any single isolated cause.
        """
    )


# ------------------------------------------------------------
# TAB 6: AGE-RELATED DISEASES
# ------------------------------------------------------------

with learn_tabs[5]:

    st.markdown(
        """
### Mitochondrial Dysfunction and Age-Related Disease

Mitochondrial dysfunction and cellular senescence are implicated as
contributing mechanisms across a wide range of age-related diseases,
spanning nearly every organ system. Explore each disease area below.
        """
    )

    DISEASE_DETAILS = {
        "🧠 Neurodegenerative diseases": (
            "Alzheimer's disease involves impaired mitochondrial "
            "bioenergetics and ROS accumulation in neurons. Parkinson's "
            "disease is directly linked to genes (PINK1, PRKN) that "
            "regulate mitophagy, the clearance of damaged mitochondria. "
            "Amyotrophic lateral sclerosis (ALS) is also associated with "
            "mitochondrial dysfunction specifically within motor neurons."
        ),
        "❤️ Cardiovascular disease": (
            "In atherosclerosis, senescent vascular cells contribute to "
            "plaque formation and instability. Heart failure is linked "
            "to declining cardiac mitochondrial ATP output. Vascular "
            "aging and stiffness are connected to endothelial cell "
            "senescence throughout the blood vessel lining."
        ),
        "🦴 Musculoskeletal disease": (
            "Sarcopenia, the age-related loss of muscle mass and "
            "strength, involves reduced mitochondrial density and "
            "function in skeletal muscle. Osteoarthritis is driven "
            "partly by senescent chondrocytes (cartilage cells), which "
            "promote cartilage degradation in the joints."
        ),
        "🩸 Metabolic disease": (
            "In type 2 diabetes, impaired mitochondrial function in "
            "muscle and pancreatic beta cells contributes to insulin "
            "resistance. Non-alcoholic fatty liver disease (NAFLD) is "
            "linked to mitochondrial dysfunction specifically within "
            "liver cells (hepatocytes)."
        ),
        "🦠 Cancer": (
            "Cellular senescence has a complex, dual role in cancer. It "
            "can suppress early tumor growth by halting the division of "
            "damaged cells, but senescent cells that persist over time "
            "can also promote tumor progression in surrounding tissue "
            "through the senescence-associated secretory phenotype "
            "(SASP), which releases inflammatory and growth-promoting "
            "signals."
        ),
        "👁️ Other age-related conditions": (
            "Age-related macular degeneration (AMD) involves retinal "
            "pigment epithelium senescence and mitochondrial "
            "dysfunction. Chronic kidney disease is linked to tubular "
            "cell senescence. Intervertebral disc degeneration involves "
            "nucleus pulposus cell senescence connected to mitochondrial "
            "fission dysregulation."
        ),
    }

    selected_disease = st.selectbox(
        "Choose a disease area to explore:",
        options=list(DISEASE_DETAILS.keys()),
        key="disease_select",
    )

    with st.container(border=True):
        st.markdown(f"**{selected_disease}**")
        st.write(DISEASE_DETAILS[selected_disease])

    st.info(
        "This is exactly the research space this tool is built to "
        "track. The papers analyzed above (V1 ranking and V2 deep "
        "evidence extraction) focus specifically on mitochondrial "
        "dysfunction as a driver of cellular senescence across these "
        "disease contexts."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align: center; padding: 20px 0; color: #94a3b8;">
        <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 10px; color: #e2e8f0;">
            Ankit Kumar Kushwaha
        </div>
        <div style="margin-bottom: 14px;">
            📧 <a href="mailto:ankitkushwaha172000@gmail.com" style="color: #3b82f6; text-decoration: none;">ankitkushwaha172000@gmail.com</a>
            &nbsp;&nbsp;•&nbsp;&nbsp;
            💼 <a href="https://www.linkedin.com/in/ankit-k-kushwaha/" target="_blank" style="color: #3b82f6; text-decoration: none;">LinkedIn</a>
            &nbsp;&nbsp;•&nbsp;&nbsp;
            💻 <a href="https://github.com/pmb2024002" target="_blank" style="color: #3b82f6; text-decoration: none;">GitHub</a>
        </div>
        <div style="font-size: 0.85rem;">
            🧬 Mitochondrial Research Intelligence
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
