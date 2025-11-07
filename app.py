import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import zipfile
import os
import glob
import random

st.set_page_config(page_title="🌳 전주시 수종 지도", layout="wide")
st.title("🌳 전주시 수종 지도")

# 폴더 생성
os.makedirs("species_data", exist_ok=True)
os.makedirs("boundary_data", exist_ok=True)

# 1️⃣ 수종 데이터 ZIP 업로드 (여러 개)
uploaded_species_files = st.file_uploader(
    "🌲 수종 데이터 ZIP 업로드 (여러 개 선택 가능)", 
    type="zip", 
    accept_multiple_files=True
)

# 2️⃣ 전주시 경계 ZIP 업로드 (1개)
uploaded_boundary_file = st.file_uploader(
    "🗺️ 전주시 경계 ZIP 업로드", 
    type="zip"
)

gdf = None
jeonju_gdf = None

# --- 수종 데이터 처리 ---
if uploaded_species_files:
    species_gdfs = []
    for uploaded_file in uploaded_species_files:
        zip_path = os.path.join("species_data", uploaded_file.name)
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        # ZIP 풀기
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            extract_folder = os.path.join("species_data", uploaded_file.name.split(".")[0])
            os.makedirs(extract_folder, exist_ok=True)
            zip_ref.extractall(extract_folder)
        shp_files = glob.glob(os.path.join(extract_folder, "*.shp"))
        if shp_files:
            gdf_file = gpd.read_file(shp_files[0])
            if gdf_file.crs != "EPSG:4326":
                gdf_file = gdf_file.to_crs(epsg=4326)
            species_gdfs.append(gdf_file)
    if species_gdfs:
        gdf = gpd.GeoDataFrame(pd.concat(species_gdfs, ignore_index=True))
        st.success(f"✅ 수종 데이터 불러오기 완료! (총 {len(gdf)} 행)")

# --- 전주시 경계 처리 ---
if uploaded_boundary_file:
    boundary_zip_path = os.path.join("boundary_data", uploaded_boundary_file.name)
    with open(boundary_zip_path, "wb") as f:
        f.write(uploaded_boundary_file.getbuffer())
    with zipfile.ZipFile(boundary_zip_path, "r") as zip_ref:
        extract_folder = os.path.join("boundary_data", uploaded_boundary_file.name.split(".")[0])
        os.makedirs(extract_folder, exist_ok=True)
        zip_ref.extractall(extract_folder)
    shp_files = glob.glob(os.path.join(extract_folder, "*.shp"))
    if shp_files:
        jeonju_gdf = gpd.read_file(shp_files[0])
        if gdf is not None and jeonju_gdf.crs != gdf.crs:
            jeonju_gdf = jeonju_gdf.to_crs(gdf.crs)
        st.success(f"✅ 전주시 경계 불러오기 완료! (총 {len(jeonju_gdf)} 행)")

# --- 수종 선택 ---
if gdf is not None and jeonju_gdf is not None:
    species_col = "KOFTR_NM"
    if species_col not in gdf.columns:
        st.error(f"❌ '{species_col}' 컬럼이 없습니다.")
    else:
        species_list = sorted(gdf[species_col].dropna().unique())
        selected_species = st.multiselect("🌿 수종 선택", options=species_list)
        
        if selected_species:
            # 필터링
            filtered_gdf = gdf[gdf[species_col].isin(selected_species)]
            if len(filtered_gdf) == 0:
                st.warning("⚠️ 선택한 수종이 데이터에 없습니다.")
            else:
                # 지도 중심 계산
                center = [filtered_gdf.geometry.centroid.y.mean(),
                          filtered_gdf.geometry.centroid.x.mean()]
                m = folium.Map(location=center, zoom_start=11)

                # 전주시 경계 추가
                folium.GeoJson(
                    jeonju_gdf,
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

                # Streamlit에 지도 표시
                st_folium(m, width=700, height=500)


