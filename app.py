import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import random
import zipfile, os, glob
import pandas as pd

st.set_page_config(page_title="🌳 수종별 지도 뷰어", layout="wide")

st.title("🌳 수종별 지도 뷰어")
st.write("임상도 Shapefile(.zip)을 업로드하고, 수종을 선택하면 지도에 표시됩니다.")

uploaded_file = st.file_uploader("📂 Shapefile ZIP 업로드", type=["zip"])

if uploaded_file:
    extract_folder = "data"
    os.makedirs(extract_folder, exist_ok=True)
    
    # ZIP 해제
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)
    
    # shapefile 탐색
    shp_files = glob.glob(os.path.join(extract_folder, "*.shp"))
    if not shp_files:
        st.error("❌ Shapefile(.shp)을 ZIP 안에서 찾을 수 없습니다.")
    else:
        shp_path = shp_files[0]
        st.success(f"✅ {os.path.basename(shp_path)} 파일을 불러왔습니다.")
        
        # 데이터 불러오기
        gdf = gpd.read_file(shp_path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        
        # 수종 컬럼
        species_col = "KOFTR_NM"
        if species_col not in gdf.columns:
            st.error(f"'{species_col}' 컬럼을 찾을 수 없습니다. 실제 컬럼명을 확인하세요.")
        else:
            species_list = sorted(gdf[species_col].dropna().unique())
            selected_species = st.multiselect("🌲 지도에 표시할 수종 선택", species_list)
            
            if selected_species:
                filtered_gdf = gdf[gdf[species_col].isin(selected_species)]
                center = [
                    filtered_gdf.geometry.centroid.y.mean(),
                    filtered_gdf.geometry.centroid.x.mean()
                ]
                m = folium.Map(location=center, zoom_start=9)
                
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
                
                st_folium(m, width=900, height=600)
            else:
                st.info("👈 왼쪽에서 수종을 선택하세요.")

