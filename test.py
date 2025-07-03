import streamlit as st
import pandas as pd
import plotly.express as px

st.title("치유농업 시설 통합 대시보드")

uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

def main_dashboard(df):
    if "sido" not in st.session_state:
        st.session_state["sido"] = "전체"
    if "sigun" not in st.session_state:
        st.session_state["sigun"] = "전체"

    st.sidebar.title("사용자 유형 선택")
    user_type = st.sidebar.radio(
        "대상자 분류",
        ("환자", "치유농업사")
    )

    sido_list = ["전체"] + sorted(df["지역"].dropna().unique())
    sido_sidebar = st.sidebar.selectbox("지역", sido_list, index=sido_list.index(st.session_state["sido"]), key="sido_sb")
    if st.session_state["sido"] != sido_sidebar:
        st.session_state["sido"] = sido_sidebar
        st.session_state["sigun"] = "전체"

    if st.session_state["sido"] != "전체":
        sigun_series = df[df["지역"] == st.session_state["sido"]]["상세주소"].dropna().apply(lambda x: x.split()[0] if len(x.split()) > 0 else "")
        sigun_options = ["전체"] + sorted(sigun_series.unique())
    else:
        sigun_options = ["전체"]

    sigun_sidebar = st.sidebar.selectbox("시군", sigun_options, index=sigun_options.index(st.session_state["sigun"]), key="sigun_sb")
    if st.session_state["sigun"] != sigun_sidebar:
        st.session_state["sigun"] = sigun_sidebar

    sido = st.session_state["sido"]
    sigun = st.session_state["sigun"]
    if sido == "전체":
        filtered_df = df
    elif sigun == "전체":
        filtered_df = df[df["지역"] == sido]
    else:
        filtered_df = df[(df["지역"] == sido) & (df["상세주소"].str.startswith(sigun))]

    def get_map_center_zoom(filtered_df, sido, sigun):
        if not filtered_df.empty:
            center_lat = filtered_df["위도"].mean()
            center_lon = filtered_df["경도"].mean()
            if sido == "전체":
                map_zoom = 6
            elif sigun == "전체":
                map_zoom = 8
            elif len(filtered_df) == 1:
                map_zoom = 13
            elif len(filtered_df) <= 3:
                map_zoom = 11
            else:
                map_zoom = 9
        else:
            center_lat, center_lon = 36.5, 127.8
            map_zoom = 6
        return center_lat, center_lon, map_zoom

    if user_type == "환자":
        st.header("환자 전용 대시보드")
        st.markdown("""
        - 관심 지역의 치유농업 시설 정보를 확인하고, 직접 신청해보세요.
        - 주요 프로그램, 기관 소개, 전화번호 등 정보를 한눈에 볼 수 있습니다.
        """)

        st.markdown("### 🔍 지역(시도/시군) 선택")
        col1, col2 = st.columns([1, 1])
        with col1:
            sido_main = st.selectbox("지역", sido_list, index=sido_list.index(st.session_state["sido"]), key="sido_main")
            if st.session_state["sido"] != sido_main:
                st.session_state["sido"] = sido_main
                st.session_state["sigun"] = "전체"
        if st.session_state["sido"] != "전체":
            sigun_options_main = ["전체"] + sorted(df[df["지역"] == st.session_state["sido"]]["상세주소"].dropna().apply(lambda x: x.split()[0] if len(x.split()) > 0 else "").unique())
        else:
            sigun_options_main = ["전체"]
        with col2:
            sigun_main = st.selectbox("시군", sigun_options_main, index=sigun_options_main.index(st.session_state["sigun"]), key="sigun_main")
            if st.session_state["sigun"] != sigun_main:
                st.session_state["sigun"] = sigun_main

        center_lat, center_lon, map_zoom = get_map_center_zoom(filtered_df, sido, sigun)
        fig = px.scatter_mapbox(
            filtered_df,
            lat="위도",
            lon="경도",
            hover_name="센터 이름",
            hover_data=["지역", "상세주소", "운영시간", "기관 소개"],
            color="지역",
            size_max=15,
            height=400,
        )
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox_center={"lat": center_lat, "lon": center_lon},
            mapbox_zoom=map_zoom
        )
        fig.update_traces(marker=dict(size=14))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("치유농업 시설 목록")
        st.write(f"총 {len(filtered_df)}개 시설이 검색되었습니다.")
        df_display = filtered_df[["센터 이름", "지역", "상세주소", "운영시간", "전화번호"]].reset_index(drop=True)
        df_display.index = df_display.index + 1
        st.dataframe(df_display, use_container_width=True)

        st.subheader("시설별 상세 정보 및 신청")
        if not filtered_df.empty:
            selected_farm = st.selectbox("신청 희망 시설을 선택하세요", filtered_df["센터 이름"].tolist())
            detail = filtered_df[filtered_df["센터 이름"] == selected_farm].iloc[0]
            homepage = str(detail['홈페이지']).strip() if pd.notnull(detail['홈페이지']) else ""
            if homepage and homepage.lower() not in ["nan", "없음", "-", "--"]:
                if not (homepage.startswith("http://") or homepage.startswith("https://")):
                    homepage = "http://" + homepage
                homepage_display = f"- **홈페이지:** [{homepage}]({homepage})"
            else:
                homepage_display = "- **홈페이지:** 등록된 홈페이지가 없습니다."

            st.markdown(f"""
            ### {detail['센터 이름']}
            - **기관 소개:** {detail['기관 소개']}
            - **위치:** {detail['지역']} {detail['상세주소']}
            - **운영시간:** {detail['운영시간']}
            - **전화번호:** {detail['전화번호']}
            {homepage_display}
            """)
            if st.button("이 시설에 프로그램 신청하기"):
                st.success(f"({detail['센터 이름']}) 신청이 완료되었습니다! 해당 기관에서 연락드릴 예정입니다.")
        else:
            st.info("해당 지역에 시설 데이터가 없습니다.")

    elif user_type == "치유농업사":
        st.header("치유농업사 대시보드")
        st.markdown("""
        - 다른 치유농업 시설의 프로그램, 기관 소개, 전화번호, 지역별 현황을 벤치마킹할 수 있습니다.
        - 시도/시군별로 필터링하여 네트워크를 구축해보세요.
        """)
        st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)



        import folium
        import branca.colormap as cm

        st.title("치유 농업사")

        # 📁 1. 엑셀 파일 업로드
        uploaded_file = st.file_uploader("우울증.xlsx 파일을 업로드하세요", type=["xlsx"])

        if uploaded_file is not None:
            # 2. 데이터 읽기
            df = pd.read_excel(uploaded_file, sheet_name="데이터")
            df = df.rename(columns={'기관종류및시도별(2)': '시도'})

            # 3. 시도명 보정
            name_map = {
                '전북특별자치도': '전라북도',
                '강원특별자치도': '강원도',
                '제주특별자치도': '제주도',
                '세종특별자치시': '세종특별자치시'
            }
            df['시도'] = df['시도'].replace(name_map)
            
            # 컬럼명 통일 (혹시 필요시)
            df_map = df.rename(columns={
                '기관종류및시도별(2)': '시도',
                '주요 우울 장애': '우울장애_환자수'
            })

            st.success("데이터 미리보기")
            st.dataframe(df_map.head(10), use_container_width=True)

            # 4. 색상 맵
            min_count = df_map['우울장애_환자수'].min()
            max_count = df_map['우울장애_환자수'].max()
            colormap = cm.linear.YlOrRd_09.scale(min_count, max_count)

            # 5. 지도 생성
            m = folium.Map(location=[36.5, 127.8], zoom_start=7)

            for _, row in df_map.iterrows():
                count = row['우울장애_환자수']
                color = colormap(count)

                folium.Circle(
                    location=[row['위도'], row['경도']],
                    radius=count / 5,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=f"{row['시도']}: {count:,}명"
                ).add_to(m)

                folium.map.Marker(
                    [row['위도'], row['경도']],
                    icon=folium.DivIcon(
                        html=f"""
                        <div style="font-size: 13pt; color: black; font-weight: bold; text-align: center;">
                            {count:,}
                        </div>
                        """
                    )
                ).add_to(m)

            colormap.caption = '2023년 주요 우울장애 환자 수'
            colormap.add_to(m)

            # 6. Streamlit에 folium 지도 띄우기
            st.markdown("#### 지도 시각화")
            st.subheader('우울증 지역 분포도')
            st.components.v1.html(m._repr_html_(), height=400)


        

        uploaded_file = st.file_uploader("이미지 업로드", type=["png", "jpg", "jpeg"])
        st.subheader('치유 농업 가능 부지')        
        if uploaded_file is not None:
            st.image(uploaded_file)


        

        uploaded_file = st.file_uploader("파일을 업로드하세요", type=["xlsx"])
        st.title('치유농업사 자격증 학원')
        if uploaded_file is not None:
            # 2. 데이터 읽기
            df = pd.read_excel(uploaded_file)
            # df = df.rename(columns={'기관종류및시도별(2)': '시도'})

            st.dataframe(df)






    # elif user_type == "정부 복지기관":
    #     st.header("정부 복지기관 대시보드")
    #     st.markdown("""
    #     - 지역별 시설 분포, 기관별 특성, 전화번호 정보를 정책 수립 및 지원자료로 활용하세요.
    #     - 데이터를 다운로드하여 보고서나 정책자료로 활용할 수 있습니다.
    #     """)
    #     st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
    #     csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    #     st.download_button("이 지역 시설 CSV 다운로드", csv, file_name=f"{sido}_{sigun}_치유농업시설.csv")

# ========== 업로드 없으면 안내, 업로드 있으면 본문 실행 ==========
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, thousands=',')
    expected_cols = ["센터 이름", "지역", "상세주소", "위도", "경도", "운영시간", "전화번호", "기관 소개", "홈페이지"]
    df = df.rename(columns={c: c.strip() for c in df.columns})
    df = df[expected_cols]
    st.success("✅ 데이터 업로드 완료!")
    st.dataframe(df, use_container_width=True)
    main_dashboard(df)
else:
    st.info("📁 우측 상단에서 CSV 파일을 업로드해 주세요!")

