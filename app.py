# app.py
import pandas as pd
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import zipfile
import os
import glob
import random

st.set_page_config(layout="wide", page_title="전주시 수종 지도 🌳")

# -----------------------------
# 초기화
# -----------------------------
if "species_gdfs" not in st.session_state:
    st.session_state.species_gdfs = []
if "jeonju_gdf" not in st.session_state:
    st.session_state.jeonju_gdf = None

# -----------------------------
# 파일 업로드
# -----------------------------
st.sidebar.header("1️⃣ 파일 업로드")

species_zip = st.sidebar.file_uploader("🌲 수종 데이터 ZIP 업로드", type="zip")
boundary_zip = st.sidebar.file_uploader("🗺️ 전주시 경계 ZIP 업로드", type="zip")

# -----------------------------
# 수종 데이터 처리
# -----------------------------
if species_zip:
    with zipfile.ZipFile(species_zip, "r") as zip_ref:
        zip_ref.extractall("species_data")
    shp_files = glob.glob(os.path.join("species_data", "*.shp"))
    if shp_files:
        st.session_state.species_gdfs = []
        for shp in shp_files:
            gdf = gpd.read_file(shp)  # engine 제거
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            st.session_state.species_gdfs.append(gdf)
        st.success(f"✅ {len(shp_files)}개의 수종 shapefile 불러오기 완료!")

# -----------------------------
# 전주시 경계 처리
# -----------------------------
if boundary_zip:
    with zipfile.ZipFile(boundary_zip, "r") as zip_ref:
        zip_ref.extractall("boundary_data")
    boundary_shp_files = glob.glob(os.path.join("boundary_data", "*.shp"))
    if boundary_shp_files:
        jeonju_gdf = gpd.read_file(boundary_shp_files[0])
        if jeonju_gdf.crs != "EPSG:4326":
            jeonju_gdf = jeonju_gdf.to_crs(epsg=4326)
        st.session_state.jeonju_gdf = jeonju_gdf
        st.success("✅ 전주시 경계 불러오기 완료!")

# -----------------------------
# 수종 선택
# -----------------------------
if st.session_state.species_gdfs and st.session_state.jeonju_gdf is not None:
    all_gdf = gpd.GeoDataFrame(pd.concat(st.session_state.species_gdfs, ignore_index=True))
    species_col = "KOFTR_NM"
    if species_col not in all_gdf.columns:
        st.error(f"❌ '{species_col}' 컬럼이 없습니다.")
    else:
        species_list = sorted(all_gdf[species_col].dropna().unique())
        selected_species = st.multiselect("2️⃣ 수종 선택", options=species_list)

        if selected_species:
            filtered_gdf = all_gdf[all_gdf[species_col].isin(selected_species)]

            # 지도 중심 (전주시 중심)
            center = [st.session_state.jeonju_gdf.geometry.centroid.y.mean(),
                      st.session_state.jeonju_gdf.geometry.centroid.x.mean()]
            m = folium.Map(location=center, zoom_start=11)

            # 전주시 경계 추가
            folium.GeoJson(
                st.session_state.jeonju_gdf,
                name="전주시 경계",
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': 'black',
                    'weight': 2
                },
                tooltip="전주시"
            ).add_to(m)

            # 수종별 색상
            color_map = {s: f'#{random.randint(0, 0xFFFFFF):06x}' for s in selected_species}
            for _, row in filtered_gdf.iterrows():
                sname = row[species_col]
                folium.GeoJson(
                    row['geometry'],
                    tooltip=f"{species_col}: {sname}",
                    style_function=lambda x, color=color_map[sname]: {
                        'fillColor': color,
                        'color': color,
                        'weight': 1,
                        'fillOpacity': 0.6
                    }
                ).add_to(m)

            st.subheader("🌐 지도 미리보기")
            st_folium(m, width=1000, height=600)








