import streamlit as st
import glob
from PIL import Image

@st.cache_data
def display():
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
    tabs = st.tabs(sorted(years.keys()))
    for year, tab in zip(sorted(years.keys()), tabs):
        with tab:
            st.header(year)
            cols = st.columns(3)
            for i, image_path in enumerate(sorted(years[year])):
                with cols[i % 3]:
                    img = Image.open(image_path)
                    # Allowing some compression for JPEG format
                    img = img.convert("RGB")
                    img.resize((1600, 720))
                    st.image(img, use_container_width=True, output_format="JPEG")
                    st.caption(image_path.split("/")[-1])

display()