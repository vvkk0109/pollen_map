# app.py
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import zipfile, os, glob
import random

st.set_page_config(layout="wide", page_title="전주시 수종 지도")

st.title("🌳 전주시 수종 지도 생성기")

# 전역 변수 초기화
if "species_gdfs" not in st.session_state:
    st.session_state.species_gdfs = []

if "jeonju_gdf" not in st.session_state:
    st.session_state.jeonju_gdf = None

# --- 1️⃣ 수종 데이터 ZIP 업로드 ---
species_files = st.file_uploader(
    "🌲 수종 데이터 ZIP 업로드 (여러 파일 가능)", 
    type="zip", 
    accept_multiple_files=True
)

if species_files:
    st.session_state.species_gdfs = []
    for i, species_zip in enumerate(species_files):
        with zipfile.ZipFile(species_zip, "r") as zip_ref:
            extract_folder = f"species_data_{i}"
            os.makedirs(extract_folder, exist_ok=True)
            zip_ref.extractall(extract_folder)

        shp_files = glob.glob(os.path.join(extract_folder, "*.shp"))
        if not shp_files:
            st.warning(f"{species_zip.name}에 .shp 파일이 없습니다!")
            continue

        for shp in shp_files:
            gdf = gpd.read_file(shp, engine="fiona")
            # EPSG:4326로 변환
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            st.session_state.species_gdfs.append(gdf)

    if st.session_state.species_gdfs:
        st.success(f"✅ {len(st.session_state.species_gdfs)}개의 수종 데이터 불러오기 완료!")

# --- 2️⃣ 전주시 경계 업로드 ---
boundary_file = st.file_uploader("🗺️ 전주시 경계 ZIP 업로드", type="zip")

if boundary_file:
    with zipfile.ZipFile(boundary_file, "r") as zip_ref:
        boundary_folder = "boundary_data"
        os.makedirs(boundary_folder, exist_ok=True)
        zip_ref.extractall(boundary_folder)

    boundary_shp_files = glob.glob(os.path.join(boundary_folder, "*.shp"))
    if boundary_shp_files:
        st.session_state.jeonju_gdf = gpd.read_file(boundary_shp_files[0], engine="fiona")
        if st.session_state.jeonju_gdf.crs != "EPSG:4326":
            st.session_state.jeonju_gdf = st.session_state.jeonju_gdf.to_crs(epsg=4326)
        st.success("✅ 전주시 경계 데이터 불러오기 완료!")
    else:
        st.warning("❌ 전주시 경계 Shapefile이 없습니다!")

# --- 3️⃣ 수종 선택 및 지도 생성 ---
if st.session_state.species_gdfs and st.session_state.jeonju_gdf is not None:
    # 모든 수종 데이터 합치기
    gdf = gpd.GeoDataFrame(pd.concat(st.session_state.species_gdfs, ignore_index=True))

    species_col = "KOFTR_NM"
    if species_col not in gdf.columns:
        st.error(f"'{species_col}' 컬럼이 없습니다.")
    else:
        species_list = sorted(gdf[species_col].dropna().unique())
        selected_species = st.multiselect("수종 선택:", species_list)

        if selected_species:
            filtered_gdf = gdf[gdf[species_col].isin(selected_species)]

            # 지도 생성 (전주시 경계 중심)
            jeonju_gdf_proj = st.session_state.jeonju_gdf.to_crs(epsg=5179)  # 투영 CRS
            center_x = jeonju_gdf_proj.geometry.centroid.x.mean()
            center_y = jeonju_gdf_proj.geometry.centroid.y.mean()
            center_point = gpd.GeoSeries([gpd.points_from_xy([center_x], [center_y])[0]], crs=5179).to_crs(epsg=4326)
            m = folium.Map(location=[center_point.y.values[0], center_point.x.values[0]], zoom_start=12)

            # 전주시 경계 추가
            folium.GeoJson(
                st.session_state.jeonju_gdf,
                name="전주시 경계",
                style_function=lambda x: {'fillColor':'transparent','color':'black','weight':2},
                tooltip="전주시"
            ).add_to(m)

            # 수종 색상 매핑
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

            # 지도 표시
            st_folium(m, width=1200, height=800)







