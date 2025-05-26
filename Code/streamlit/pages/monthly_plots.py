import streamlit as st
import glob

# Loading all images from the directory
# And splitting the images into lists by year
years = {}
for image_path in glob.glob("monthly/*.png"):
    # Normalizing the path to ensure it works on all systems
    image_path = image_path.replace("\\", "/")
    year = image_path.split("/")[-1].split("-")[0]
    if year not in years:
        years[year] = []
    years[year].append(image_path)

st.title("Monthly Plots")

# Display images using tabs in a grid layout
tabs = st.tabs(years.keys())
for year, tab in zip(years.keys(), tabs):
    with tab:
        st.header(year)
        cols = st.columns(3)
        for i, image_path in enumerate(years[year]):
            with cols[i % 3]:
                st.image(image_path, use_container_width=True, output_format="JPEG")
                st.caption(image_path.split("/")[-1])
