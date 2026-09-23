import streamlit as st
from pathlib import Path


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

HERO_IMAGE = BASE_DIR / "assets" / "mitochondria_hero.png"

STRUCTURE_FUNCTION_IMAGE = (
    BASE_DIR / "assets" / "mitochondria_structure_function.png"
)

def render_svg(svg_markup: str):
    """
    Render inline SVG safely. Streamlit's markdown parser treats
    lines with 4+ leading spaces as a code block (standard Markdown
    behavior), which breaks indented multi-line SVG. This strips
    per-line leading whitespace before rendering so the SVG is
    always parsed as raw HTML, not a code block.
    """
    cleaned = "\n".join(
        line.strip() for line in svg_markup.strip().split("\n")
    )
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
        margin-bottom: 20px;
    "></div>
    """,
    unsafe_allow_html=True,
)


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

            import sys as _sys
            _sys.path.insert(0, str(BASE_DIR / "pipeline"))

            from check_new_papers import check_for_new_papers

            new_df = check_for_new_papers()

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

                    if st.button("🔬 Quick Analyze", key=f"analyze_btn_{pmid}"):

                        with st.spinner("Analyzing abstract..."):

                            import sys as _sys
                            _sys.path.insert(0, str(BASE_DIR / "pipeline"))

                            from quick_analyze import quick_analyze_paper

                            try:
                                result = quick_analyze_paper(
                                    title=nrow.get("title", ""),
                                    abstract=abstract,
                                )
                                st.session_state[quick_key] = result
                            except Exception as exc:
                                st.error(f"Analysis failed: {exc}")

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
                    width: 90px;
                    height: 90px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 2px solid #3b82f6;
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
Dual-degree (M.Tech + PhD) Scholar, Bioinformatics
**Indian Institute of Information Technology, Allahabad (IIIT-A)**

Supervised by **Prof. Pritish K. Varadwaj**.
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

- **Cellular signaling** — regulating calcium levels and reactive
  oxygen species (ROS)
- **Apoptosis** — controlling programmed cell death pathways
- **Metabolic regulation** — integrating nutrient and energy status
- **Mitochondrial dynamics** — continuously undergoing **fission**
  (dividing) and **fusion** (merging) to maintain a healthy network
- **Mitophagy** — the selective clearance of damaged mitochondria via
  autophagy, a key quality-control mechanism

As cells age, mitochondrial function tends to decline: energy
production becomes less efficient, ROS accumulates, and the balance
between fission/fusion and mitophagy breaks down. This
**mitochondrial dysfunction** is increasingly recognized as a driver
-- not just a consequence -- of **cellular senescence**, the
irreversible growth arrest linked to aging and age-related disease.
        """
    )

with image_col:
    if HERO_IMAGE.exists():
        st.image(str(HERO_IMAGE), width=380)

st.divider()


# ============================================================
# LEARN — MITOCHONDRIA & AGING (EDUCATIONAL SECTION)
# ============================================================

st.markdown("## 📖 Learn: Mitochondria, Aging & Disease")
st.caption(
    "A deeper dive — from basic structure to advanced disease "
    "mechanisms. All diagrams below are original illustrations, "
    "not reproductions of published figures."
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
them apart from most other organelles:

- **Outer membrane** — smooth, permeable to small molecules and ions
  via channel proteins called porins.
- **Intermembrane space** — the thin gap between the outer and inner
  membranes; a critical site for proton accumulation during ATP
  production.
- **Inner membrane** — highly folded into structures called
  **cristae**, which dramatically increase surface area for the
  enzyme complexes that generate ATP. It is far less permeable than
  the outer membrane, allowing a proton gradient to build up.
- **Matrix** — the innermost compartment, containing mitochondrial
  DNA (mtDNA), ribosomes, and enzymes for the citric acid (Krebs)
  cycle.

Unlike most organelles, mitochondria contain their **own circular
DNA** (inherited maternally) and can **replicate independently** of
the cell cycle — a legacy of their evolutionary origin as free-living
bacteria that were engulfed by an ancestral cell roughly 1.5–2
billion years ago (the endosymbiotic theory).
            """
        )

    with col_image:
        if STRUCTURE_FUNCTION_IMAGE.exists():
            st.image(
                str(STRUCTURE_FUNCTION_IMAGE),
                use_container_width=True,
            )

            st.caption(
                "Mitochondrial structure and major functional compartments."
            )

        else:
            st.warning(
                "Structure & Function image not found."
            )

# ------------------------------------------------------------
# TAB 2: ENERGY PRODUCTION
# ------------------------------------------------------------

with learn_tabs[1]:

    st.markdown(
        """
### How Mitochondria Make Energy

Mitochondria generate ATP primarily through **oxidative
phosphorylation**, a process carried out by the **electron transport
chain (ETC)** — a series of five protein complexes embedded in the
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
    st.caption("The electron transport chain and chemiosmotic ATP production (original diagram).")

    st.markdown(
        """
**In brief:**

1. Nutrients (glucose, fatty acids) are broken down to produce
   electron carriers (NADH, FADH₂) via glycolysis and the citric acid
   cycle.
2. These carriers donate electrons to **Complex I** and **Complex
   II**, which pass electrons down the chain to **Complex III** and
   **Complex IV**.
3. As electrons move through Complexes I, III, and IV, protons (H⁺)
   are pumped from the matrix into the intermembrane space, creating
   an electrochemical gradient.
4. Protons flow back into the matrix through **ATP synthase**, and
   this flow drives the synthesis of ATP from ADP and inorganic
   phosphate.
5. At Complex IV, electrons finally combine with oxygen to form
   water — this is why mitochondria consume the oxygen we breathe.

This process is remarkably efficient but not perfect: a small
fraction of electrons "leak" from the chain and react with oxygen to
form **reactive oxygen species (ROS)** — a byproduct with major
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

First proposed by Denham Harman in the 1970s (building on his
earlier free-radical theory of aging), the **mitochondrial theory of
aging** holds that the slow accumulation of mitochondrial damage —
driven largely by reactive oxygen species (ROS) — is a central
mechanism of biological aging.

**The proposed vicious cycle:**

1. Normal ETC activity generates a small, constant flux of ROS.
2. ROS damage mitochondrial DNA (mtDNA), which lacks the protective
   histones and robust repair machinery of nuclear DNA, making it
   more mutation-prone.
3. Damaged mtDNA can encode defective ETC proteins.
4. Defective ETC complexes leak more electrons, generating **more**
   ROS.
5. Over time, this feedback loop leads to progressively worsening
   mitochondrial function, energy deficits, and cellular damage.

**How this connects to cellular senescence:**

- Dysfunctional mitochondria are a well-established driver of
  **cellular senescence** — a state in which damaged cells stop
  dividing but remain metabolically active, often secreting
  inflammatory molecules (the senescence-associated secretory
  phenotype, or SASP).
- Senescent cells accumulate with age in nearly every tissue,
  contributing to chronic low-grade inflammation ("inflammaging")
  and tissue dysfunction.
- Impaired **mitophagy** (the clearance of damaged mitochondria)
  allows dysfunctional mitochondria to persist and accumulate,
  further amplifying ROS output and senescence induction.
- Reduced **mitochondrial biogenesis** (the production of new,
  healthy mitochondria, regulated in part by the PGC-1α pathway)
  means cells become less able to replace damaged mitochondria as
  they age.

**Important nuance:** the simple "ROS causes aging" version of this
theory has been refined considerably in recent decades. ROS at low,
regulated levels also serve as important **signaling molecules** —
so the relationship between mitochondrial ROS and aging is now
understood as more complex than pure accumulated damage, involving
signaling, adaptive stress responses (mitohormesis), and quality
control failure, not just oxidative damage alone.
        """
    )


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
    st.caption(
        "The 12 Hallmarks of Aging (López-Otín et al., 2013; updated 2023) — "
        "original layout, not a reproduction of the published figure."
    )

    st.markdown(
        """
**Why mitochondrial dysfunction is central:** unlike most other
hallmarks, mitochondrial dysfunction has extensive bidirectional
links to nearly all the others — it contributes to genomic
instability (via ROS-induced DNA damage), drives cellular senescence,
impairs stem cell function, and is itself worsened by deregulated
nutrient sensing and disabled autophagy/mitophagy. This central,
interconnected role is a major reason it is a focus of current aging
and senescence research (including this project's own focus area).
        """
    )


# ------------------------------------------------------------
# TAB 5: CAUSES OF AGING
# ------------------------------------------------------------

with learn_tabs[4]:

    st.markdown(
        """
### What Causes Aging?

Aging is not driven by a single cause — it results from the
interaction of **intrinsic (genetic/biological)** and **extrinsic
(environmental/lifestyle)** factors accumulating over a lifetime.
        """
    )

    cause_col1, cause_col2 = st.columns(2)

    with cause_col1:
        st.markdown(
            """
#### 🧬 Intrinsic Factors

- **Genetic programming** — inherited genes influence baseline
  longevity and disease susceptibility (though genetics is estimated
  to account for only ~20-30% of lifespan variation in humans).
- **Telomere shortening** — the protective caps on chromosome ends
  shorten with each cell division, eventually triggering senescence.
- **Accumulated DNA damage** — from replication errors and oxidative
  stress, faster than repair mechanisms can fully correct.
- **Mitochondrial dysfunction** — declining ATP production and
  rising ROS output, as discussed in the earlier tabs.
- **Epigenetic drift** — age-related changes in DNA methylation and
  chromatin structure that alter gene expression patterns without
  changing the underlying DNA sequence.
- **Stem cell exhaustion** — a gradual decline in the regenerative
  capacity of tissue-specific stem cell pools.
            """
        )

    with cause_col2:
        st.markdown(
            """
#### 🌍 Extrinsic Factors

- **Diet and nutrition** — chronic overnutrition, poor diet quality,
  and metabolic dysregulation accelerate cellular damage.
- **Physical inactivity** — reduces mitochondrial biogenesis and
  cardiovascular/muscular resilience.
- **Chronic stress** — sustained cortisol elevation is linked to
  accelerated telomere attrition and inflammation.
- **Environmental toxins** — UV radiation, air pollution, and
  cigarette smoke increase oxidative and DNA damage.
- **Sleep disruption** — impairs cellular repair processes and
  metabolic regulation.
- **Chronic infections/inflammation** — sustained immune activation
  ("inflammaging") accelerates tissue damage over decades.
            """
        )

    st.markdown(
        """
**Key concept — the interaction of these factors:** intrinsic and
extrinsic factors do not act independently. For example, poor diet
(extrinsic) increases mitochondrial ROS production (intrinsic
mechanism), which accelerates DNA damage (another intrinsic hallmark)
and promotes cellular senescence. This is why aging research
increasingly focuses on **interconnected mechanisms** — like
mitochondrial dysfunction — rather than any single isolated cause.
        """
    )


# ------------------------------------------------------------
# TAB 6: AGE-RELATED DISEASES
# ------------------------------------------------------------

with learn_tabs[5]:

    st.markdown(
        """
### Mitochondrial Dysfunction & Age-Related Disease

Mitochondrial dysfunction and cellular senescence are implicated as
contributing mechanisms across a wide range of age-related diseases,
spanning nearly every organ system.
        """
    )

    disease_col1, disease_col2 = st.columns(2)

    with disease_col1:
        st.markdown(
            """
#### 🧠 Neurodegenerative Diseases
- **Alzheimer's disease** — impaired mitochondrial bioenergetics and
  ROS accumulation in neurons
- **Parkinson's disease** — directly linked to genes (PINK1, PRKN)
  that regulate **mitophagy**
- **Amyotrophic lateral sclerosis (ALS)** — mitochondrial dysfunction
  in motor neurons

#### ❤️ Cardiovascular Disease
- **Atherosclerosis** — senescent vascular cells contribute to
  plaque formation and instability
- **Heart failure** — declining cardiac mitochondrial ATP output
- **Vascular aging/stiffness** — linked to endothelial cell
  senescence

#### 🦴 Musculoskeletal Disease
- **Sarcopenia** (age-related muscle loss) — reduced mitochondrial
  density and function in skeletal muscle
- **Osteoarthritis** — senescent chondrocytes drive cartilage
  degradation
            """
        )

    with disease_col2:
        st.markdown(
            """
#### 🩸 Metabolic Disease
- **Type 2 diabetes** — impaired mitochondrial function in muscle
  and pancreatic beta cells contributes to insulin resistance
- **Non-alcoholic fatty liver disease (NAFLD)** — linked to
  hepatocyte mitochondrial dysfunction

#### 🦠 Cancer
- Cellular senescence has a **complex dual role** — it can suppress
  early tumor growth, but senescent cells that persist can also
  promote tumor progression in surrounding tissue via the SASP
  (senescence-associated secretory phenotype)

#### 👁️ Other Age-Related Conditions
- **Age-related macular degeneration (AMD)** — retinal pigment
  epithelium senescence and mitochondrial dysfunction
- **Chronic kidney disease** — tubular cell senescence
- **Intervertebral disc degeneration** — nucleus pulposus cell
  senescence linked to mitochondrial fission dysregulation
            """
        )

    st.info(
        "💡 This is exactly the research space this tool is built to "
        "track — the papers analyzed above (V1 ranking + V2 deep "
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
            🧬 Mitochondrial Research Intelligence — IIIT Allahabad
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
