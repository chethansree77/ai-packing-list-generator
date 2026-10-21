import os
import json
import re
import time
import uuid

import streamlit as st
from dotenv import load_dotenv
from google import genai

import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Packing List Generator",
    page_icon="🧳",
    layout="wide"
)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY is not found in your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)


# =========================================================
# FILE PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(
    BASE_DIR,
    "packing_data.json"
)


# =========================================================
# LOAD SAVED TRIPS
# =========================================================

def load_saved_trips():

    if not os.path.exists(DATA_FILE):
        return []

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except Exception:

        return []


# =========================================================
# SAVE TRIPS
# =========================================================

def save_trips(trips):

    try:

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                trips,
                file,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:

        st.error(
            f"❌ Could not save trip data: {e}"
        )


# =========================================================
# FIND DESTINATION
# =========================================================

@st.cache_data(ttl=600)
def find_destination(place):

    if not place:
        return None

    try:

        geolocator = Nominatim(
            user_agent="ai_packing_list_generator"
        )

        location = geolocator.geocode(
            f"{place}, India",
            timeout=10
        )

        if location is None:

            location = geolocator.geocode(
                place,
                timeout=10
            )

        if location:

            return {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address
            }

    except Exception:

        return None

    return None


# =========================================================
# SESSION STATE
# =========================================================

if "packing_data" not in st.session_state:
    st.session_state.packing_data = None

if "destination" not in st.session_state:
    st.session_state.destination = ""

if "days" not in st.session_state:
    st.session_state.days = 1

if "season" not in st.session_state:
    st.session_state.season = "Summer"

if "current_trip_id" not in st.session_state:
    st.session_state.current_trip_id = None

if "map_location" not in st.session_state:
    st.session_state.map_location = None

if "last_input_signature" not in st.session_state:
    st.session_state.last_input_signature = (
        "",
        1,
        "Summer"
    )

if "checkbox_version" not in st.session_state:
    st.session_state.checkbox_version = 1


# =========================================================
# SAVED TRIPS
# =========================================================

saved_trips = load_saved_trips()


# =========================================================
# LOAD TRIP
# =========================================================

def load_trip(trip):

    st.session_state.packing_data = (
        trip.get(
            "packing_data",
            {}
        )
    )

    st.session_state.destination = (
        trip.get(
            "destination",
            ""
        )
    )

    st.session_state.days = int(
        trip.get(
            "days",
            1
        )
    )

    st.session_state.season = (
        trip.get(
            "season",
            "Summer"
        )
    )

    st.session_state.current_trip_id = (
        trip.get("id")
    )

    st.session_state.map_location = (
        find_destination(
            st.session_state.destination
        )
    )

    st.session_state.last_input_signature = (
        st.session_state.destination.strip().lower(),
        st.session_state.days,
        st.session_state.season
    )

    st.session_state.checkbox_version += 1


# =========================================================
# START NEW TRIP
# =========================================================

def start_new_trip():

    st.session_state.packing_data = None

    st.session_state.destination = ""

    st.session_state.days = 1

    st.session_state.season = "Summer"

    st.session_state.current_trip_id = None

    st.session_state.map_location = None

    st.session_state.last_input_signature = (
        "",
        1,
        "Summer"
    )

    st.session_state.checkbox_version += 1


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

/* =====================================================
   MAIN BACKGROUND
   ===================================================== */

.stApp {

    background:
        linear-gradient(
            135deg,
            #eef7ff 0%,
            #fdf4ff 50%,
            #f1fff7 100%
        );

}


/* =====================================================
   MAIN TITLE
   ===================================================== */

.main-title {

    text-align: center;

    font-size: 48px;

    font-weight: 800;

    background:
        linear-gradient(
            90deg,
            #2563eb,
            #7c3aed,
            #ec4899
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

    margin-top: 5px;

    margin-bottom: 5px;

}


/* =====================================================
   SUBTITLE
   ===================================================== */

.subtitle {

    text-align: center;

    font-size: 18px;

    color: #475569;

    margin-bottom: 28px;

}


/* =====================================================
   SECTION TITLE
   ===================================================== */

.section-title {

    font-size: 23px;

    font-weight: 750;

    color: #172554;

    margin-bottom: 12px;

}


/* =====================================================
   RESULT TITLE
   ===================================================== */

.result-title {

    font-size: 36px;

    font-weight: 800;

    color: #172554;

    margin-top: 28px;

    margin-bottom: 5px;

}


/* =====================================================
   CARDS
   ===================================================== */

div[data-testid="stVerticalBlockBorderWrapper"] {

    border-radius: 22px !important;

    border:
        1px solid
        rgba(255,255,255,0.95) !important;

    box-shadow:
        0 10px 28px
        rgba(30,41,59,0.08) !important;

    background:
        rgba(255,255,255,0.82) !important;

    transition:
        transform 0.25s ease,
        box-shadow 0.25s ease !important;

}


div[data-testid="stVerticalBlockBorderWrapper"]:hover {

    transform:
        translateY(-4px)
        scale(1.005);

    box-shadow:
        0 16px 36px
        rgba(30,41,59,0.14) !important;

}


/* =====================================================
   BUTTON
   ===================================================== */

div.stButton > button {

    width: 100%;

    border: none;

    border-radius: 15px;

    padding: 13px 20px;

    font-size: 18px;

    font-weight: 750;

    color: white;

    background:
        linear-gradient(
            90deg,
            #2388ff,
            #7048f5,
            #ed4aa3
        );

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;

}


div.stButton > button:hover {

    transform: scale(1.025);

    box-shadow:
        0 10px 25px
        rgba(112,72,245,0.30);

}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {

    border-radius: 13px;

}


/* =====================================================
   SELECTBOX
   ===================================================== */

div[data-baseweb="select"] {

    border-radius: 13px;

}


/* =====================================================
   MAP STATUS
   ===================================================== */

.map-status {

    padding: 10px 14px;

    border-radius: 12px;

    background: #eff6ff;

    color: #1d4ed8;

    font-size: 15px;

    font-weight: 600;

    margin-bottom: 10px;

}


/* =====================================================
   FOOTER
   ===================================================== */

.footer-text {

    text-align: center;

    font-size: 17px;

    font-weight: 700;

    color: #172554;

    padding: 8px;

}


/* =====================================================
   PROFESSIONAL COMPLETION
   ===================================================== */

.professional-complete {

    text-align: center;

    padding:
        15px
        10px
        10px
        10px;

}


.professional-icon {

    width: 58px;

    height: 58px;

    margin:
        0 auto
        12px auto;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 50%;

    background: #16a34a;

    color: white;

    font-size: 30px;

    font-weight: 800;

    box-shadow:
        0 8px 18px
        rgba(22,163,74,0.20);

}


.professional-title {

    font-size: 27px;

    font-weight: 800;

    color: #166534;

    margin-bottom: 7px;

}


.professional-status {

    display: inline-block;

    padding:
        6px 14px;

    border-radius: 20px;

    background: #dcfce7;

    color: #15803d;

    font-size: 12px;

    font-weight: 800;

    letter-spacing: 1px;

    margin-bottom: 12px;

}


.professional-message {

    font-size: 16px;

    color: #334155;

    margin-bottom: 7px;

}


.professional-trip {

    font-size: 14px;

    color: #64748b;

}


/* =====================================================
   CHECKBOX
   ===================================================== */

div[data-testid="stCheckbox"] {

    padding:
        5px 0;

}


div[data-testid="stCheckbox"] label {

    font-weight: 700;

    cursor: pointer;

}


div[data-testid="stCheckbox"] label > div:first-child {

    cursor: pointer;

}


div[data-testid="stCheckbox"] label:hover {

    color: #4f46e5;

}


/* =====================================================
   PROGRESS
   ===================================================== */

div[data-testid="stProgress"] {

    margin-top: 8px;

    margin-bottom: 8px;

}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    '🧳 AI Packing List Generator'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '✨ Pack smarter. Travel happier. '
    'Let AI prepare your checklist.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SAVED TRIPS
# =========================================================

with st.expander(
    f"💾 My Saved Trips ({len(saved_trips)})"
):

    if not saved_trips:

        st.info(
            "No saved trips yet. "
            "Generate your first packing list!"
        )

    else:

        st.caption(
            "Your trips and packing progress "
            "are saved permanently."
        )

        for trip in reversed(saved_trips):

            trip_id = trip.get("id")

            trip_destination = trip.get(
                "destination",
                "Trip"
            )

            trip_days = trip.get(
                "days",
                1
            )

            trip_season = trip.get(
                "season",
                "Summer"
            )

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                if (
                    trip_id
                    ==
                    st.session_state.current_trip_id
                ):

                    st.markdown(
                        f"### 🟢 "
                        f"{trip_destination.title()}"
                    )

                else:

                    st.markdown(
                        f"### 🧳 "
                        f"{trip_destination.title()}"
                    )

                st.caption(
                    f"📅 {trip_days} days  •  "
                    f"🌤️ {trip_season}"
                )

            with col2:

                if st.button(
                    "📂 Open",
                    key=f"open_{trip_id}"
                ):

                    load_trip(trip)

                    st.rerun()

        st.divider()

        if st.button(
            "➕ Start New Trip",
            key="new_trip_button"
        ):

            start_new_trip()

            st.rerun()


# =========================================================
# TRIP INPUT
# =========================================================

with st.container(border=True):

    st.markdown(
        '<div class="section-title">'
        '🌍 Plan Your Trip'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1.2, 0.8, 0.8]
    )


    # =====================================================
    # DESTINATION
    # =====================================================

    with col1:

        destination = st.text_input(
            "📍 Destination",
            value=st.session_state.destination,
            placeholder="Your holiday destination..."
        )


    # =====================================================
    # DAYS
    # =====================================================

    with col2:

        days = st.number_input(
            "📅 Number of travel days",
            min_value=1,
            max_value=100,
            value=st.session_state.days
        )


    # =====================================================
    # SEASON
    # =====================================================

    with col3:

        season_options = [
            "Summer",
            "Winter",
            "Monsoon",
            "Spring",
            "Autumn"
        ]

        if (
            st.session_state.season
            in season_options
        ):

            current_season_index = (
                season_options.index(
                    st.session_state.season
                )
            )

        else:

            current_season_index = 0

        season = st.selectbox(
            "🌤️ Season",
            season_options,
            index=current_season_index
        )


# =========================================================
# DETECT INPUT CHANGES
# =========================================================

new_signature = (
    destination.strip().lower(),
    int(days),
    season
)

old_signature = (
    st.session_state.last_input_signature
)


if new_signature != old_signature:

    st.session_state.destination = (
        destination.strip()
    )

    st.session_state.days = int(days)

    st.session_state.season = season

    st.session_state.current_trip_id = None

    st.session_state.checkbox_version += 1

    if destination.strip():

        st.session_state.map_location = (
            find_destination(
                destination.strip()
            )
        )

    else:

        st.session_state.map_location = None

    st.session_state.last_input_signature = (
        new_signature
    )


# =========================================================
# GENERATE BUTTON
# =========================================================

generate = st.button(
    "✨ Generate Packing List"
)


# =========================================================
# GEMINI FUNCTION
# =========================================================

def generate_with_gemini(prompt):

    max_attempts = 3

    for attempt in range(max_attempts):

        try:

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

            return response

        except Exception as e:

            error_text = str(e).lower()

            network_error = (
                "11001" in error_text
                or "getaddrinfo failed" in error_text
                or "name or service not known"
                in error_text
            )

            temporary_error = (
                "503" in error_text
                or "unavailable" in error_text
                or "429" in error_text
                or "resource_exhausted"
                in error_text
            )

            if (
                network_error
                or temporary_error
            ):

                if attempt < 2:

                    time.sleep(
                        2 ** attempt
                    )

                    continue

                if network_error:

                    raise ConnectionError(
                        "NETWORK_ERROR"
                    )

                if (
                    "503"
                    in error_text
                    or
                    "unavailable"
                    in error_text
                ):

                    raise ConnectionError(
                        "GEMINI_BUSY"
                    )

                if (
                    "429"
                    in error_text
                    or
                    "resource_exhausted"
                    in error_text
                ):

                    raise ConnectionError(
                        "RATE_LIMIT"
                    )

            raise e

    return None


# =========================================================
# GENERATE PACKING LIST
# =========================================================

if generate:

    if not destination.strip():

        st.warning(
            "📍 Please enter a destination first."
        )

    else:

        st.session_state.destination = (
            destination.strip()
        )

        st.session_state.days = int(days)

        st.session_state.season = season

        st.session_state.map_location = (
            find_destination(
                destination.strip()
            )
        )

        st.session_state.checkbox_version += 1


        # =================================================
        # GEMINI PROMPT
        # =================================================

        prompt = f"""

You are an expert AI travel packing assistant.

Create a practical packing checklist
for an Indian traveler.

Destination: {destination}

Number of travel days: {days}

Season: {season}

Consider:

- Typical climate of the destination
- Indian regional weather patterns
- Number of travel days
- Comfortable clothing
- Personal hygiene
- Travel essentials
- Weather-related items

Return ONLY valid JSON.

Do not use Markdown.
Do not use code fences.
Do not add explanations outside JSON.

Use exactly this structure:

{{
    "clothes": [
        "item 1",
        "item 2",
        "item 3"
    ],

    "personal_items": [
        "item 1",
        "item 2",
        "item 3"
    ],

    "travel_essentials": [
        "item 1",
        "item 2",
        "item 3"
    ],

    "weather_tips": [
        "tip 1",
        "tip 2",
        "tip 3"
    ]
}}

Requirements:

- Simple
- Practical
- Easy to understand
- Suitable for the destination
- Suitable for the season
- Suitable for the number of days
- Use emojis where useful
- Do not give exact weather forecasts
- Give general seasonal travel advice

"""


        # =================================================
        # AI GENERATION
        # =================================================

        with st.spinner(
            "🤖 AI is preparing your personalized packing list..."
        ):

            try:

                response = generate_with_gemini(
                    prompt
                )

            except ConnectionError as e:

                error_type = str(e)

                if (
                    error_type
                    ==
                    "NETWORK_ERROR"
                ):

                    st.error(
                        "🌐 Network connection problem."
                    )

                    st.info(
                        "Please check your internet "
                        "connection and try again."
                    )

                elif (
                    error_type
                    ==
                    "GEMINI_BUSY"
                ):

                    st.error(
                        "🤖 Gemini is temporarily busy."
                    )

                    st.info(
                        "Please wait a few seconds "
                        "and try again."
                    )

                elif (
                    error_type
                    ==
                    "RATE_LIMIT"
                ):

                    st.warning(
                        "⏳ Gemini request limit reached."
                    )

                    st.info(
                        "Please wait and try again later."
                    )

                response = None


            except Exception as e:

                st.error(
                    f"❌ Gemini Error: {e}"
                )

                response = None


        # =================================================
        # PROCESS RESPONSE
        # =================================================

        if response is not None:

            try:

                ai_text = response.text.strip()

                ai_text = re.sub(
                    r"```json\s*",
                    "",
                    ai_text,
                    flags=re.IGNORECASE
                )

                ai_text = re.sub(
                    r"```\s*",
                    "",
                    ai_text
                )

                ai_text = ai_text.strip()

                data = json.loads(
                    ai_text
                )

                st.session_state.packing_data = (
                    data
                )

                trip_id = uuid.uuid4().hex

                st.session_state.current_trip_id = (
                    trip_id
                )

                new_trip = {

                    "id": trip_id,

                    "destination":
                        destination.strip(),

                    "days":
                        int(days),

                    "season":
                        season,

                    "packing_data":
                        data,

                    "packed_categories": {

                        "clothes":
                            False,

                        "personal_items":
                            False,

                        "travel_essentials":
                            False

                    }

                }

                all_trips = (
                    load_saved_trips()
                )

                all_trips.append(
                    new_trip
                )

                save_trips(
                    all_trips
                )

                st.session_state.last_input_signature = (

                    destination.strip().lower(),

                    int(days),

                    season

                )

                st.success(
                    "🎉 Packing list generated "
                    "and saved permanently!"
                )


            except json.JSONDecodeError:

                st.error(
                    "⚠️ Gemini returned "
                    "an unexpected format."
                )

                st.code(
                    response.text
                )


            except Exception as e:

                st.error(
                    f"❌ Error processing "
                    f"AI response: {e}"
                )


# =========================================================
# DISPLAY PACKING LIST
# =========================================================

if st.session_state.packing_data:

    data = st.session_state.packing_data

    clothes = data.get(
        "clothes",
        []
    )

    personal_items = data.get(
        "personal_items",
        []
    )

    travel_essentials = data.get(
        "travel_essentials",
        []
    )

    weather_tips = data.get(
        "weather_tips",
        []
    )

    current_destination = (
        st.session_state.destination
    )

    current_days = (
        st.session_state.days
    )

    current_season = (
        st.session_state.season
    )

    checkbox_version = (
        st.session_state.checkbox_version
    )


    # =====================================================
    # RESULT HEADER
    # =====================================================

    st.markdown(
        '<div class="result-title">'
        '✨ Your AI Packing List'
        '</div>',
        unsafe_allow_html=True
    )


    if current_days == 1:
        day_text = "day"
    else:
        day_text = "days"


    st.markdown(
        f"Here is your personalized checklist "
        f"for **{current_destination.title()}** "
        f"— **{current_days} {day_text}** "
        f"— **{current_season}**."
    )


    # =====================================================
    # MAIN + SIDE
    # =====================================================

    main_col, side_col = st.columns(
        [2.1, 1],
        gap="large"
    )


    # =====================================================
    # MAIN CONTENT
    # =====================================================

    with main_col:

        # =================================================
        # CLOTHES + PERSONAL ITEMS
        # =================================================

        col1, col2 = st.columns(2)


        # =================================================
        # CLOTHES
        # =================================================

        with col1:

            with st.container(border=True):

                st.markdown(
                    "## 👕 Clothes"
                )

                clothes_packed = st.checkbox(
                    "✓ Packed",
                    key=
                    f"clothes_packed_"
                    f"{checkbox_version}"
                )

                st.caption(
                    f"{len(clothes)} items"
                )

                for item in clothes:

                    st.write(
                        f"• {item}"
                    )


        # =================================================
        # PERSONAL ITEMS
        # =================================================

        with col2:

            with st.container(border=True):

                st.markdown(
                    "## 🧴 Personal Items"
                )

                personal_packed = st.checkbox(
                    "✓ Packed",
                    key=
                    f"personal_packed_"
                    f"{checkbox_version}"
                )

                st.caption(
                    f"{len(personal_items)} items"
                )

                for item in personal_items:

                    st.write(
                        f"• {item}"
                    )


        # =================================================
        # TRAVEL ESSENTIALS + WEATHER
        # =================================================

        col3, col4 = st.columns(2)


        # =================================================
        # TRAVEL ESSENTIALS
        # =================================================

        with col3:

            with st.container(border=True):

                st.markdown(
                    "## 🎒 Travel Essentials"
                )

                essentials_packed = st.checkbox(
                    "✓ Packed",
                    key=
                    f"essentials_packed_"
                    f"{checkbox_version}"
                )

                st.caption(
                    f"{len(travel_essentials)} items"
                )

                for item in travel_essentials:

                    st.write(
                        f"• {item}"
                    )


        # =================================================
        # WEATHER TIPS
        # =================================================

        with col4:

            with st.container(border=True):

                st.markdown(
                    "## 🌦️ Weather Tips"
                )

                st.caption(
                    f"{len(weather_tips)} tips"
                )

                for item in weather_tips:

                    st.write(
                        f"🌦️ {item}"
                    )


        # =================================================
        # PACKING PROGRESS
        # =================================================

        packed_categories = 0

        total_categories = 3


        if clothes_packed:
            packed_categories += 1

        if personal_packed:
            packed_categories += 1

        if essentials_packed:
            packed_categories += 1


        with st.container(border=True):

            st.markdown(
                "## 🎒 Packing Progress"
            )


            progress_left, progress_right = (
                st.columns([2, 1])
            )


            with progress_left:

                st.write(
                    "Categories packed"
                )


            with progress_right:

                st.markdown(
                    f"""
                    <div style="
                        text-align:right;
                        font-size:20px;
                        font-weight:700;
                        padding-top:5px;
                    ">
                        {packed_categories}
                        /
                        {total_categories}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


            progress = (
                packed_categories
                /
                total_categories
            )


            st.progress(
                progress
            )


            # =================================================
            # REMAINING CATEGORIES
            # =================================================

            if (
                packed_categories
                <
                total_categories
            ):

                remaining = (
                    total_categories
                    -
                    packed_categories
                )

                if remaining == 1:
                    category_word = "category"
                else:
                    category_word = "categories"


                st.info(
                    f"📋 {remaining} "
                    f"{category_word} remaining."
                )


            # =================================================
            # PACKING COMPLETE
            # =================================================

            else:

                # Use normal Streamlit elements here
                # instead of HTML so no HTML tags appear.

                st.success(
                    "✓ Packing Complete"
                )

                st.markdown(
                    "### 🟢 READY FOR DEPARTURE"
                )

                st.write(
                    "All packing categories are ready."
                )

                st.caption(
                    "Your trip is fully prepared. "
                    "Have a safe and enjoyable journey."
                )


    # =====================================================
    # RIGHT SIDE
    # =====================================================

    with side_col:


        # =================================================
        # DESTINATION CARD
        # =================================================

        with st.container(border=True):

            st.markdown(
                "## 📍 Destination"
            )

            st.write(
                f"📍 **{current_destination.title()}**"
            )

            st.write(
                f"📅 **Travel Days:** "
                f"{current_days}"
            )

            st.write(
                f"🌤️ **Season:** "
                f"{current_season}"
            )


        # =================================================
        # DESTINATION MAP
        # =================================================

        with st.container(border=True):

            st.markdown(
                "## 🗺️ Destination Map"
            )


            map_location = (
                st.session_state.map_location
            )


            if map_location:

                # No HTML tags here.
                # This prevents <b> from appearing.

                st.info(
                    f"📍 Tracking: "
                    f"{current_destination.title()}"
                )


                travel_map = folium.Map(

                    location=[
                        map_location[
                            "latitude"
                        ],
                        map_location[
                            "longitude"
                        ]
                    ],

                    zoom_start=8,

                    tiles="OpenStreetMap"

                )


                folium.Marker(

                    [
                        map_location[
                            "latitude"
                        ],

                        map_location[
                            "longitude"
                        ]
                    ],

                    popup=(
                        f"📍 "
                        f"{current_destination.title()}"
                    ),

                    tooltip=(
                        f"📍 "
                        f"{current_destination.title()}"
                    ),

                    icon=folium.Icon(
                        color="red",
                        icon="info-sign"
                    )

                ).add_to(
                    travel_map
                )


                st_folium(

                    travel_map,

                    width=None,

                    height=350

                )


            else:

                st.info(
                    "📍 Enter a destination above "
                    "to track it on the map."
                )


        # =================================================
        # QUICK TIPS
        # =================================================

        with st.container(border=True):

            st.markdown(
                "## 💡 Quick Tips"
            )

            st.write(
                "✅ Check the local weather "
                "before travelling."
            )

            st.write(
                "✅ Keep important documents safe."
            )

            st.write(
                "✅ Pack according to your activities."
            )

            st.write(
                "💧 Carry enough water."
            )

            st.write(
                "✨ Travel light and enjoy your trip!"
            )


# =========================================================
# FOOTER
# =========================================================

with st.container(border=True):

    footer1, footer2, footer3 = (
        st.columns(3)
    )


    with footer1:

        st.markdown(
            '<div class="footer-text">'
            '🧳 Pack Smart'
            '</div>',
            unsafe_allow_html=True
        )


    with footer2:

        st.markdown(
            '<div class="footer-text">'
            '🌴 Travel Happy'
            '</div>',
            unsafe_allow_html=True
        )


    with footer3:

        st.markdown(
            '<div class="footer-text">'
            '✈️ Explore More'
            '</div>',
            unsafe_allow_html=True
        )