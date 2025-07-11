import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(
    page_title='EDM Streams Dashboard',
    page_icon=':musical_note:',
    layout='wide'  # Use full screen width
)

@st.cache_data
def get_edm_data():
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    df = pd.read_csv(DATA_FILENAME, delimiter=';', header=None, low_memory=False)
    # First three rows are headers
    artist_row = df.iloc[0]
    song_row = df.iloc[1]
    data = df.iloc[3:].reset_index(drop=True)
    data.columns = artist_row  # Use artist names as columns
    return data, artist_row, song_row

data, artist_row, song_row = get_edm_data()

st.title(":musical_note: EDM Streams Dashboard")
st.write("Compare combined stream volume for each artist (all songs summed).")

# Convert date column to datetime for filtering
data = data.copy()
data['Date'] = pd.to_datetime(data[data.columns[0]], errors='coerce')

# Build artist -> list of columns mapping (grouping all columns with the same artist name)
artist_cols = {}
for idx, artist in enumerate(artist_row[1:]):  # skip 'Date' column
    artist = str(artist).strip()
    col = data.columns[idx+1]  # +1 to skip 'Date'
    if artist not in artist_cols:
        artist_cols[artist] = []
    artist_cols[artist].append(col)

# Only unique artist names in the dropdown
artist_names = sorted(artist_cols.keys())
selected_artists = st.multiselect(
    "Select Artist(s) to compare (combined streams of all their songs)",
    artist_names,
    default=artist_names[:2]
)

# Year range slider
min_year = data['Date'].dt.year.min()
max_year = data['Date'].dt.year.max()
year_range = st.slider(
    "Select Year Range",
    int(min_year), int(max_year), (int(min_year), int(max_year))
)

# Add normalization option
norm_option = st.radio(
    "Stream Value Display",
    ["Raw Streams", "Indexed (0-100 per artist)"],
    horizontal=True
)

if selected_artists:
    combined_df = pd.DataFrame({'Date': data['Date']})
    for artist in selected_artists:
        cols = artist_cols[artist]
        # Sum streams across all songs for this artist
        streams = data[cols].apply(pd.to_numeric, errors='coerce').sum(axis=1)
        if norm_option == "Indexed (0-100 per artist)":
            # Min-max scale each artist's streams to 0-100
            min_val = streams.min()
            max_val = streams.max()
            if max_val > min_val:
                streams = (streams - min_val) / (max_val - min_val) * 100
            else:
                streams = 0  # If all values are the same
        combined_df[artist] = streams

    # Filter by year range
    combined_df = combined_df[
        (combined_df['Date'].dt.year >= year_range[0]) &
        (combined_df['Date'].dt.year <= year_range[1])
    ]

    # Melt for Altair
    df_melt = combined_df.melt(id_vars='Date', var_name='Artist', value_name='Streams')
    chart = alt.Chart(df_melt).mark_line().encode(
        x='Date:T',
        y='Streams:Q',
        color=alt.Color('Artist:N', scale=alt.Scale(scheme='tableau20')),
        tooltip=['Artist', 'Date', 'Streams']
    ).properties(
        width='container',  # Use full container width
        height=400,
        title="Combined Streams Over Time by Artist"
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df_melt)
else:
    st.info("Please select at least one artist to view the data.")
