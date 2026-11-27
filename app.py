"""Plant Disease Detection Web App — Streamlit entry point.

Run locally:  streamlit run app.py
Every page from the legacy single-file app is preserved. Models load lazily
(only when a page that needs them is opened) and are checksum-verified before
first use. Predictions are labeled as uncalibrated model scores.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from plant_app.config import get_settings  # noqa: E402
from plant_app.database.connection import (  # noqa: E402
    DatabaseUnavailableError,
    insert_crop_record,
    list_crop_records,
)
from plant_app.inference.predictor import InferenceError, predict_image  # noqa: E402
from plant_app.inference.preprocessing import (  # noqa: E402
    ImageTooLargeError,
    InvalidImageError,
    load_image_from_bytes,
)
from plant_app.models.registry import (  # noqa: E402
    ManifestError,
    ModelNotFoundError,
    load_manifest,
    load_model,
)
from plant_app.services.qa import answer_question  # noqa: E402
from plant_app.services.weather import get_weather  # noqa: E402
from plant_app.services.web_search import web_search  # noqa: E402
from plant_app.utils.images import human_size  # noqa: E402

st.set_page_config(
    page_title="Plant Disease Detection",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

DISCLAIMER = (
    "Educational prototype. Predictions are uncalibrated model scores, not a "
    "diagnosis. Always confirm with a local agricultural extension officer."
)

VACCINATION_ROWS = [
    ("Cattle", "Foot and Mouth Disease", "Ovac FMD", "Varies by vaccine"),
    ("Cattle", "Brucellosis", "RB-51", "Varies by vaccine"),
    ("Sheep", "Foot and Mouth Disease", "Ovac FMD", "Varies by vaccine"),
    ("Sheep", "Clostridial Diseases", "Covexin", "Varies by vaccine"),
    ("Goats", "Foot and Mouth Disease", "Ovac FMD", "Varies by vaccine"),
    ("Goats", "Clostridial Diseases", "Covexin", "Varies by vaccine"),
    ("Poultry (Chickens)", "Newcastle Disease", "Newcastle B1 Vaccine", "Varies by vaccine"),
    ("Poultry (Chickens)", "Avian Influenza", "Nobilis Influenza H5N1", "Varies by vaccine"),
    ("Poultry (Chickens)", "Gumboro Disease", "Gumboro IBDV Vaccine", "Varies by vaccine"),
    ("Poultry (Chickens)", "Infectious Bronchitis", "IB Vaccine", "Varies by vaccine"),
    ("Swine (Pigs)", "Foot and Mouth Disease", "Ovac FMD", "Varies by vaccine"),
    ("Swine (Pigs)", "Swine Fever", "Suvaxyn", "Varies by vaccine"),
    ("Horses", "Rabies", "Raboral V-RG", "Varies by vaccine"),
]

ROTATION_ROWS = [
    ("Rainy Season", "Loamy Soil", "April - October",
     "Maize, Okra, Peppers, Tomatoes, Eggplant, Watermelon, Cucumber, Okro, Sorghum, Cowpeas"),
    ("Rainy Season", "Sandy Soil", "April - October",
     "Vegetables, Maize, Tomato, Amaranth, Pepper, Beans, Yam"),
    ("Rainy Season", "Clayey Soil", "April - October",
     "Eggplant, Okro, Cassava, Millet, Yam, Pumpkin, Maize"),
    ("Rainy Season", "Organic Matter", "April - October",
     "Maize, Cassava, Tomatoes, Peppers, Beans, Cowpeas"),
    ("Dry Season", "Loamy Soil", "November - March",
     "Maize, Cassava, Tomatoes, Peppers, Beans, Cowpeas"),
    ("Dry Season", "Sandy Soil", "November - March",
     "Maize, Tomatoes, Okra, Watermelon, Sweet Potatoes"),
    ("Dry Season", "Clayey Soil", "November - March",
     "Yam, Plantains, Cocoyam, Cassava, Sweet Potatoes"),
    ("Dry Season", "Organic Matter", "November - March",
     "Maize, Cassava, Tomatoes, Peppers, Beans, Cowpeas"),
    ("Rainy Season", "Loamy Soil", "May - November",
     "Maize, Okra, Peppers, Tomatoes, Eggplant, Watermelon, Cucumber, Okro, Sorghum, Cowpeas"),
    ("Rainy Season", "Sandy Soil", "May - November",
     "Vegetables, Maize, Tomato, Amaranth, Pepper, Beans, Yam"),
    ("Rainy Season", "Clayey Soil", "May - November",
     "Eggplant, Okro, Cassava, Millet, Yam, Pumpkin, Maize"),
    ("Rainy Season", "Organic Matter", "May - November",
     "Maize, Cassava, Tomatoes, Peppers, Beans, Cowpeas"),
]


def manifest_data() -> dict:
    return load_manifest()


@st.cache_resource(show_spinner="Loading model…")
def cached_load_model(key: str):
    manifest = manifest_data()
    return load_model(key, manifest)


def classifier_page(key: str, title: str, blurb: str) -> None:
    st.markdown(f"### {title}")
    st.info(DISCLAIMER, icon="ℹ️")
    try:
        model = cached_load_model(key)
    except (ModelNotFoundError, ManifestError) as exc:
        st.error(f"Model unavailable: {exc}")
        return
    st.caption(
        f"Artifact: `{model_manifest_entry(key, 'path')}` · input {model.input_size[0]}×{model.input_size[1]}×3 · "
        f"{model.output_classes} classes · SHA-256 verified"
    )
    st.write(blurb)
    settings = get_settings()
    uploaded = st.file_uploader(
        "Upload a leaf photo (JPG, PNG, BMP, or WEBP)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key=f"uploader_{key}",
    )
    if uploaded is None:
        st.stop()
    if uploaded.size > settings.max_upload_mb * 1024 * 1024:
        st.error(
            f"File is {human_size(uploaded.size)}; the limit is {settings.max_upload_mb} MB."
        )
        st.stop()
    try:
        img, meta = load_image_from_bytes(uploaded.getvalue(), max_mb=settings.max_upload_mb)
    except (InvalidImageError, ImageTooLargeError) as exc:
        st.error(f"Rejected upload: {exc}")
        return
    if meta.was_exif_rotated:
        st.caption("Image was rotated according to its EXIF orientation metadata.")
    col_img, col_out = st.columns([1, 2])
    with col_img:
        st.image(img, width='stretch')
    with col_out:
        try:
            pred = predict_image(img, model, max_mb=settings.max_upload_mb)
        except InferenceError as exc:
            st.error(f"Inference failed: {exc}")
            return
        st.markdown("**Prediction (uncalibrated model score):**")
        st.subheader(pred.top_class)
        st.metric("Top-1 score", f"{pred.top_score:.2%}")
        if not model.classes_verified:
            st.caption(
                "Class-name ordering is inherited from the legacy app and could not be "
                "verified against a training label file."
            )
        if pred.low_margin_warning:
            st.warning(pred.low_margin_warning, icon="⚠️")
        st.markdown("**All class probabilities:**")
        st.bar_chart(pd.DataFrame(pred.probabilities, columns=["class", "score"]).set_index("class"))
        st.caption(
            "Scores come from a softmax head on an uncalibrated model. Do not treat "
            "them as calibrated probabilities or as a definitive diagnosis; seek "
            "expert confirmation."
        )


def model_manifest_entry(key: str, field: str):
    manifest = manifest_data()
    return manifest["models"][key].get(field, "")


def home_page() -> None:
    st.title("Plant Disease Detection Web App")
    st.markdown(
        "An educational tool for detecting crop diseases and pests from photographs, "
        "plus practical farming guides. Built for the African smallholder context."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image(str(ROOT / "assets" / "planting.png"))
    with c2:
        st.image(str(ROOT / "assets" / "Watering.jpg"))
    with c3:
        st.image(str(ROOT / "assets" / "weeding.jpg"))
    st.markdown("### What this app can do")
    st.markdown(
        "- Classify **tomato**, **pepper**, and **potato** leaf photos into disease/healthy classes\n"
        "- Detect **pests** from insect photos\n"
        "- Crop rotation and livestock-vaccination reference guides\n"
        "- Weather outlook, web search, and Q&A (where external services are configured)\n"
        "- A small crop-record book (SQLite demo by default; MySQL optional)"
    )
    st.warning(
        "The classifiers are small custom CNNs trained on curated leaf-image datasets. "
        "Their outputs are **uncalibrated model scores**. This app is not a diagnostic "
        "medical/veterinary/agronomic device.", icon="⚠️"
    )
    st.markdown(
        "Research context: this web app is separate from the published field study "
        "(Abraham et al., *PMLR* 319:16–25, 2026). See `docs/research_reproducibility.md` "
        "for the precise relationship."
    )


def getting_started_page() -> None:
    st.title("Getting Started with Farming")
    steps = [
        ("Step 1: Buying Seeds",
         ["Research the crops suitable for your region and climate.",
          "Choose reputable seed suppliers or local markets.",
          "Check seed certification and germination guarantees where available."]),
        ("Step 2: Planting",
         ["Prepare the soil by clearing debris and adding compost (manure).",
          "Follow the recommended planting depth and spacing for each crop."]),
        ("Step 3: Fertilization",
         ["Choose the right type of fertilizer based on your crop's nutrient requirements.",
          "Follow recommended fertilizer application rates and timings."]),
        ("Step 4: Watering",
         ["Water your crops regularly, but avoid overwatering, which can lead to root rot.",
          "Use a watering schedule that matches your crop's water needs."]),
        ("Step 5: Pest Control",
         ["Identify common pests in your region and monitor your crops regularly.",
          "Use organic or chemical pest control methods as needed, following label instructions."]),
        ("Step 6: Harvesting",
         ["Harvest crops at the right time. Different crops have different maturity periods.",
          "Use appropriate tools for harvesting to avoid damage to the crops."]),
    ]
    for title, tips in steps:
        st.markdown(f"#### {title}")
        for tip in tips:
            st.markdown(f"- {tip}")
    st.info(
        "General guidance assembled from the legacy app's original content "
        "(attributed there to local agricultural experts, without records we can cite). "
        "Confirm locally with your agricultural extension officer.", icon="📚"
    )


def rotation_page() -> None:
    st.header("Crop Rotation Advisor")
    st.write("This tool helps you find crop rotation options based on the season and soil type.")
    df = pd.DataFrame(ROTATION_ROWS, columns=["Season", "Soil Type", "Months", "Crops"]).drop_duplicates()
    col1, col2 = st.columns(2)
    with col1:
        selected_season = st.selectbox("Select Season", sorted(df["Season"].unique()))
    with col2:
        selected_soil = st.selectbox("Select Soil Type", sorted(df["Soil Type"].unique()))
    filtered = df[(df["Season"] == selected_season) & (df["Soil Type"] == selected_soil)]
    st.subheader("Crop Rotation Options:")
    if filtered.empty:
        st.write("No entry for this combination; try another soil type.")
    else:
        for _, row in filtered.iterrows():
            st.write(f"**Months:** {row['Months']}")
            st.write(f"**Possible crops to plant:** {row['Crops']}")
    st.caption(
        "Educational reference inherited from the legacy app (attributed to local "
        "agricultural experts, without citable records). Confirm with your agricultural "
        "extension officer before planting decisions."
    )


def vaccination_page() -> None:
    st.header("Farm Animal Vaccination Guide")
    st.write(
        "Select a farm animal, and get information about common diseases they are "
        "vaccinated against, along with vaccine names and dosages."
    )
    df = pd.DataFrame(VACCINATION_ROWS, columns=["Animal", "Disease", "Vaccine Name", "Dosage"])
    selected = st.selectbox("Select a Farm Animal", sorted(df["Animal"].unique()))
    st.write(f"Common Diseases and Vaccines for {selected}")
    st.dataframe(df[df["Animal"] == selected], width='stretch')
    st.caption(
        "Educational information only, inherited from the legacy app (attributed to "
        "local veterinary professionals, without citable records). Vaccination "
        "schedules and product names vary by country and change over time - always "
        "confirm with a licensed veterinarian.")


def qa_page() -> None:
    st.header("Question Answering")
    settings = get_settings()
    question = st.text_area("Ask an agricultural question:")
    if st.button("Ask"):
        answer, note = answer_question(question, settings.openai_api_key)
        if answer is None:
            st.info(note)
        else:
            st.subheader("Answer:")
            st.write(answer)
            st.caption(note)


def record_page() -> None:
    st.header("Record Input")
    st.write("Store a crop record. Uses the built-in SQLite demonstration database by default; set DB_MODE=mysql for a real server (see .env.example).")
    with st.form("record_form"):
        crop_name = st.text_input("Crop name", max_chars=120)
        field_name = st.text_input("Field name", max_chars=120)
        quantity = st.number_input("Quantity (e.g., kg harvested)", min_value=0.0, max_value=1_000_000.0, step=0.1)
        planting = st.date_input("Planting date")
        harvest = st.date_input("Harvest date")
        notes = st.text_area("Notes", height=80)
        submitted = st.form_submit_button("Save record")
    if submitted:
        try:
            rec_id = insert_crop_record(
                crop_name=crop_name, field_name=field_name, quantity=quantity,
                planting_date=str(planting), harvest_date=str(harvest), notes=notes,
            )
            st.success(f"Saved record #{rec_id}.")
        except (ValueError, DatabaseUnavailableError) as exc:
            st.error(f"Could not save: {exc}")


def retrieve_page() -> None:
    st.header("Retrieve Crop Data for Analysis")
    try:
        rows = list_crop_records()
    except (DatabaseUnavailableError, ValueError) as exc:
        st.error(f"Could not read records: {exc}")
        return
    if not rows:
        st.info("No crop records yet. Add some on the Record Input page.")
        return
    df = pd.DataFrame(rows)
    st.dataframe(df, width='stretch')
    if df["quantity"].notna().any() and df["quantity"].astype(float).sum() > 0:
        st.subheader("Yield Distribution")
        st.bar_chart(df.set_index("crop_name")["quantity"].astype(float))


def weather_page() -> None:
    st.header("Weather")
    city = st.text_input("City or town", placeholder="e.g., Ibadan")
    if st.button("Check Weather"):
        report, note = get_weather(city)
        if report is None:
            st.info(note)
        else:
            st.subheader(f"Current conditions - {report.location}")
            col1, col2 = st.columns(2)
            col1.metric("Temperature", f"{report.temperature_c} °C" if report.temperature_c is not None else "n/a")
            col2.metric("Humidity", f"{report.humidity_pct} %" if report.humidity_pct is not None else "n/a")
            st.caption(report.description)
            st.markdown("**3-day outlook**")
            for d in report.daily_forecast:
                st.write(f"- {d['date']}: min {d['temp_min_c']} °C / max {d['temp_max_c']} °C (WMO code {d['weather_code']})")
            st.caption(note)


def search_page() -> None:
    st.header("Google Search")
    settings = get_settings()
    query = st.text_input("Search query")
    if st.button("Search"):
        results, note = web_search(query, settings.serpapi_api_key)
        if results is None:
            st.info(note)
        else:
            st.subheader("Search Results:")
            for r in results:
                st.markdown(f"**[{r['title']}]({r['link']})**")
                st.write(r["snippet"])
            st.caption(note)


def feedback_page() -> None:
    st.header("Feedback")
    with st.form("feedback_form"):
        _name = st.text_input("Name")
        _email = st.text_input("Email")
        feedback = st.text_area("Feedback")
        submitted = st.form_submit_button("Submit feedback")
    if submitted:
        if not feedback.strip():
            st.error("Feedback text is required.")
        else:
            st.success("Thank you - feedback noted for the maintainers. (This prototype stores feedback nowhere persistent; use GitHub issues for a durable record.)")
    st.markdown(
        "Maintainer contact and contribution info: see the repository README "
        "([github.com/saaga23/plant_disease_detection_web_app](https://github.com/saaga23/plant_disease_detection_web_app))."
    )


def main() -> None:
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox(
        "Choose a page",
        [
            "Home",
            "Getting Started",
            "Tomato Disease Classifier",
            "Pepper Disease Classifier",
            "Potato Disease Classifier",
            "Pest Detection",
            "Crop Rotation Advisor",
            "Farm Animal Vaccination Guide",
            "Question Answering",
            "Record Input",
            "Retrieve Crop Data for Analysis",
            "Weather",
            "Google Search",
            "Feedback",
        ],
    )
    if app_mode == "Home":
        home_page()
    elif app_mode == "Getting Started":
        getting_started_page()
    elif app_mode == "Tomato Disease Classifier":
        classifier_page("tomato", "Tomato Disease Classifier",
                        "Upload a tomato leaf photo to classify it into one of 10 disease/health classes.")
    elif app_mode == "Pepper Disease Classifier":
        classifier_page("pepper", "Pepper Disease Classifier",
                        "Upload a pepper leaf photo to classify it as bacterial spot or healthy.")
    elif app_mode == "Potato Disease Classifier":
        classifier_page("potato", "Potato Disease Classifier",
                        "Upload a potato leaf photo to classify it as early blight, late blight, or healthy.")
    elif app_mode == "Pest Detection":
        classifier_page("pest", "Pest Detection",
                        "Upload an insect photo to classify it into one of 13 pest/health categories.")
    elif app_mode == "Crop Rotation Advisor":
        rotation_page()
    elif app_mode == "Farm Animal Vaccination Guide":
        vaccination_page()
    elif app_mode == "Question Answering":
        qa_page()
    elif app_mode == "Record Input":
        record_page()
    elif app_mode == "Retrieve Crop Data for Analysis":
        retrieve_page()
    elif app_mode == "Weather":
        weather_page()
    elif app_mode == "Google Search":
        search_page()
    elif app_mode == "Feedback":
        feedback_page()


if __name__ == "__main__":
    main()
