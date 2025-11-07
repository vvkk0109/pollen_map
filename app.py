# app.py
import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import zipfile
import os
import glob
import random

st.set_page_config(page_title="전주시 수종 지도", layout="wide")

# 전역 변수
gdf = None
jeonju_gdf = None

st.title("🌳 전주시 수종 지도")

# 1️⃣ 수종 데이터 여러 ZIP 업로드 가능
species_zips = st.file_uploader(
    "🌲 수종 데이터 ZIP 업로드 (여러 개 가능)", type=["zip"], accept_multiple_files=True
)

if species_zips:
    species_gdfs = []
    for species_zip in species_zips:
        with zipfile.ZipFile(species_zip, "r") as zip_ref:
            extract_folder = "species_data"
            os.makedirs(extract_folder, exist_ok=True)
            zip_ref.extractall(extract_folder)

        shp_files = glob.glob(os.path.join(extract_folder, "*.shp"))
        for shp in shp_files:
            species_gdfs.append(gpd.read_file(shp))

    if species_gdfs:
        gdf = gpd.GeoDataFrame(pd.concat(species_gdfs, ignore_index=True))
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        st.success(f"✅ 수종 데이터 불러오기 완료! (행 수: {len(gdf)})")
    else:
        st.error("❌ .shp 파일을 찾을 수 없습니다!")

# 2️⃣ 전주시 경계 ZIP 업로드
boundary_zip = st.file_uploader("🗺️ 전주시 경계 ZIP 업로드", type=["zip"])
if boundary_zip:
    with zipfile.ZipFile(boundary_zip, "r") as zip_ref:
        boundary_folder = "boundary_data"
        os.makedirs(boundary_folder, exist_ok=True)
        zip_ref.extractall(boundary_folder)

    boundary_shp_files = glob.glob(os.path.join(boundary_folder, "*.shp"))
    if boundary_shp_files:
        jeonju_gdf = gpd.read_file(boundary_shp_files[0])
        if gdf is not None and jeonju_gdf.crs != gdf.crs:
            jeonju_gdf = jeonju_gdf.to_crs(gdf.crs)
        st.success(f"✅ 전주시 경계 불러오기 완료! (행 수: {len(jeonju_gdf)})")
    else:
        st.error("❌ 전주시 경계 Shapefile이 없습니다!")

# 3️⃣ 수종 선택 및 지도 생성
if gdf is not None and jeonju_gdf is not None:
    species_col = "KOFTR_NM"
    if species_col not in gdf.columns:
        st.error(f"❌ '{species_col}' 컬럼이 없습니다.")
    else:
        species_list = sorted(gdf[species_col].dropna().unique())
        selected_species = st.multiselect("수종 선택", species_list)

        if selected_species:
            filtered_gdf = gdf[gdf[species_col].isin(selected_species)]
            if len(filtered_gdf) == 0:
                st.warning("⚠️ 선택한 수종이 데이터에 없습니다.")
            else:
                # 지도 중심 계산 (경고 제거용 투영 좌표계)
                projected = filtered_gdf.to_crs(epsg=5179)  # UTM-K
                centroid = projected.geometry.centroid
                center = [centroid.y.mean(), centroid.x.mean()]

                # folium 지도 생성
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

                # 지도 표시
                st_folium(m, width=1200, height=800)




