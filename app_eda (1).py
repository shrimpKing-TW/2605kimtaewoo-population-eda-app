import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("연도별 지역 인구 추이")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', dayfirst=True, infer_datetime_format=True)
        tabs = st.tabs([
            "1. 인구 통계 데이터 분석",
            "2. 인구 연도별 추이 시각화",
            "3. 지역별 인구 변화량 순위 분석",
            "4. 증감률 상위 지역 및 연도 분석",
            "5. 지역별 인구 누적 영역 그래프",
            "6. 인구 EDA 전체 분석 탭 구조",
        ])
        # -------------------------
        # 1. 인구 통계 데이터 분석
        # -------------------------
        with st.expander("📈 인구 통계 분석 (population_trends.csv)"):
            pop_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv", key="population")
            if pop_file:
                pop_df = pd.read_csv(pop_file)
            
                # 컬럼명 확인용 출력 (필요 시 주석처리 가능)
                st.write("컬럼명:", pop_df.columns.tolist())

                # 탭 구조로 분석
                tabs = st.tabs(["1. 데이터 미리보기", "2. 결측치 처리", "3. 기초 통계", "4. 데이터 구조"])

                with tabs[0]:
                    st.subheader("1️⃣ 원본 데이터 미리보기")
                    st.dataframe(pop_df.head())

                with tabs[1]:
                    st.subheader("2️⃣ '세종' 지역 결측치('-') → 0 처리")
                    if '행정구역' in pop_df.columns:
                        sejong_mask = pop_df['행정구역'].astype(str).str.contains("세종")
                        pop_df.loc[sejong_mask] = pop_df.loc[sejong_mask].replace("-", "0")
                        st.write("✅ '세종' 지역 결측치가 '0'으로 처리되었습니다.")
                        st.dataframe(pop_df[sejong_mask].head())
                    else:
                        st.warning("⚠️ '행정구역' 컬럼이 없습니다. CSV 파일의 컬럼명을 확인해주세요.")

                with tabs[2]:
                    st.subheader("3️⃣ 숫자형 컬럼 변환 및 요약 통계")
                    numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
                    for col in numeric_cols:
                        if col in pop_df.columns:
                            pop_df[col] = pd.to_numeric(pop_df[col], errors='coerce')
                    pop_df[numeric_cols] = pop_df[numeric_cols].fillna(0)
                    st.dataframe(pop_df[numeric_cols].describe())

                with tabs[3]:
                    st.subheader("4️⃣ 데이터프레임 구조 (`df.info()`)") 
                    import io
                    buffer = io.StringIO()
                    pop_df.info(buf=buffer)
                    st.text(buffer.getvalue())
        # -------------------------
        # 2. 인구 연도별 추이 시각화
        # -------------------------
        with st.expander("📊 Population Trend Visualization"):
            pop_file = st.file_uploader("Upload population_trends.csv", type="csv", key="population_trend_viz")
            if pop_file:
                pop_df = pd.read_csv(pop_file)

                tabs = st.tabs(["Trend by Year"])

                with tabs[0]:
                    st.subheader("Yearly Population Trend with 2035 Projection")

                    # 필수 컬럼 체크
                    required_cols = ['연도', '지역', '인구', '출생아수(명)', '사망자수(명)']
                    missing_cols = [c for c in required_cols if c not in pop_df.columns]
                    if missing_cols:
                        st.warning(f"Missing columns in uploaded file: {missing_cols}")
                    else:
                        # '전국' 데이터 필터링
                        national_df = pop_df[pop_df['지역'] == '전국'].copy()

                        # 숫자형 변환
                        for col in ['연도', '인구', '출생아수(명)', '사망자수(명)']:
                            national_df[col] = pd.to_numeric(national_df[col], errors='coerce')

                        # 결측치 제거
                        national_df = national_df.dropna(subset=['연도', '인구'])

                        # 연도 오름차순 정렬
                        national_df = national_df.sort_values('연도')

                        years = national_df['연도'].astype(int).tolist()
                        population = national_df['인구'].astype(int).tolist()

                        # 최근 3년 평균 출생/사망자수 계산
                        recent = national_df.tail(3)
                        avg_birth = recent['출생아수(명)'].mean()
                        avg_death = recent['사망자수(명)'].mean()

                        # 2035년 인구 예측
                        latest_year = national_df['연도'].max()
                        latest_pop = national_df.loc[national_df['연도'] == latest_year, '인구'].values[0]
                        years_into_future = 2035 - latest_year
                        projected_2035 = int(latest_pop + years_into_future * (avg_birth - avg_death))

                        # 그래프 데이터 확장
                        years.append(2035)
                        population.append(projected_2035)

                        # 시각화
                        import matplotlib.pyplot as plt

                        fig, ax = plt.subplots(figsize=(8, 5))
                        ax.plot(years, population, marker='o', linestyle='-')
                        ax.set_title("Population Trend and 2035 Projection")
                        ax.set_xlabel("Year")
                        ax.set_ylabel("Population")

                        # 2035년 예측값 강조 표시
                        ax.annotate(f"2035: {projected_2035:,}", xy=(2035, projected_2035),
                                    xytext=(2030, projected_2035 + 100000),
                                    arrowprops=dict(arrowstyle="->", color="red"),
                                    fontsize=10, color="red")

                        st.pyplot(fig)


        # -------------------------
        # 3. 지역별 인구 변화량 순위 분석
        # -------------------------
        with st.expander("📊 Regional Population Change Analysis"):
            file = st.file_uploader("Upload population_trends.csv", type="csv", key="regional_change")
            if file:
                df = pd.read_csv(file)

                tabs = st.tabs(["Population Change"])

                with tabs[0]:
                    st.subheader("📉 Regional Population Change (Last 5 Years)")

                    # 전국 제외
                    region_df = df[df['행정구역'] != '전국'].copy()

                    # 숫자형 변환
                    for col in ['인구']:
                        region_df[col] = pd.to_numeric(region_df[col], errors='coerce')
                    region_df = region_df.dropna(subset=['연도', '인구'])

                    # 최근 5년 추출
                    latest_year = region_df['연도'].max()
                    recent_years = sorted(region_df['연도'].unique())[-5:]
                    filtered = region_df[region_df['연도'].isin(recent_years)]

                    # 지역별 변화량 계산
                    pivot = filtered.pivot_table(index='행정구역', columns='연도', values='인구')
                    pivot = pivot.dropna()  # 결측 제거

                    pivot['change'] = pivot[recent_years[-1]] - pivot[recent_years[0]]
                    pivot['rate'] = ((pivot['change'] / pivot[recent_years[0]]) * 100).round(2)

                    # 영어 지역명 매핑
                    region_kr_to_en = {
                        '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                        '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                        '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                        '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                        '제주': 'Jeju'
                    }
                    pivot['region'] = pivot.index.map(region_kr_to_en)

                    # 단위 변환 (천명)
                    pivot['change_thousands'] = (pivot['change'] / 1000).round(1)

                    # 변화량 시각화
                    import seaborn as sns
                    import matplotlib.pyplot as plt

                    sorted_change = pivot.sort_values('change_thousands', ascending=False)

                    fig1, ax1 = plt.subplots(figsize=(10, 6))
                    sns.barplot(data=sorted_change, x='change_thousands', y='region', ax=ax1, palette='Blues_r')
                    ax1.set_title("Population Change by Region (Thousands)")
                    ax1.set_xlabel("Change (Thousands)")
                    ax1.set_ylabel("Region")

                    # 막대에 값 표시
                    for i, v in enumerate(sorted_change['change_thousands']):
                        ax1.text(v + 5, i, f"{v:.1f}", va='center', fontsize=9)

                    st.pyplot(fig1)

                    # 변화율 시각화
                    sorted_rate = pivot.sort_values('rate', ascending=False)

                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    sns.barplot(data=sorted_rate, x='rate', y='region', ax=ax2, palette='RdYlGn')
                    ax2.set_title("Population Change Rate by Region (%)")
                    ax2.set_xlabel("Rate (%)")
                    ax2.set_ylabel("Region")

                    for i, v in enumerate(sorted_rate['rate']):
                        ax2.text(v + 0.5, i, f"{v:.2f}%", va='center', fontsize=9)

                    st.pyplot(fig2)

                    # 해설
                    st.markdown("""
                    ### 📌 Interpretation
                    - The **population change chart** shows absolute change (in thousands) over the last 5 years.
                    - The **rate chart** shows percent increase or decrease over the same period.
                    - Some regions (e.g., Sejong) may show high growth rate despite small population.
                    - Regions with negative values are experiencing population decline and may require policy attention.
                    """)
        # -------------------------
        # 4. 증감률 상위 지역 및 연도 분석
        # -------------------------
        with st.expander("📈 Top Population Changes by Region & Year"):
            file = st.file_uploader("Upload population_trends.csv", type="csv", key="top_change")
            if file:
                df = pd.read_csv(file)

                tabs = st.tabs(["Top Changes Table"])

                with tabs[0]:
                    st.subheader("📋 Top 100 Yearly Changes (Δ Population)")

                    # 전국 제외
                    df = df[df['행정구역'] != '전국'].copy()
                    df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
                    df = df.dropna(subset=['인구', '연도'])

                    # 연도 정렬
                    df = df.sort_values(['행정구역', '연도'])

                    # 증감 계산
                    df['증감'] = df.groupby('행정구역')['인구'].diff()

                    # 상위 100개 증감 정렬
                    top100 = df.dropna(subset=['증감']).copy()
                    top100['증감_절댓값'] = top100['증감'].abs()
                    top100 = top100.sort_values('증감_절댓값', ascending=False).head(100)

                    # 천단위 콤마 포맷 적용
                    top100_display = top100[['행정구역', '연도', '인구', '증감']].copy()
                    top100_display['인구'] = top100_display['인구'].apply(lambda x: f"{int(x):,}")
                    top100_display['증감'] = top100_display['증감'].apply(lambda x: f"{int(x):,}")

                    # 스타일링: 증감값에 컬러바 적용
                    def color_gradient(val):
                        try:
                            v = int(val.replace(",", ""))
                        except:
                            return ""
                        color = f"background-color: rgba({255 if v < 0 else 0}, {0 if v < 0 else 0}, {255 if v > 0 else 0}, 0.2)"
                        return color

                    styled = top100_display.style.applymap(color_gradient, subset=['증감']) \
                                                 .set_properties(**{'text-align': 'center'}) \
                                                 .hide(axis="index")

                    st.dataframe(styled, use_container_width=True)

                    # 해설
                    st.markdown("""
                    ### 🔍 Interpretation
                    - This table shows the **top 100 most significant changes** in population (positive or negative).
                    - Color-coded highlights:  
                      - 🔵 Blue: Significant increase  
                      - 🔴 Red: Significant decrease  
                    - Useful to identify years and regions with demographic shocks (e.g., urban migration, new development, depopulation).
                    """)
        # -------------------------
        # 5. 지역별 인구 누적 영역 그래프
        # -------------------------
        with st.expander("📊 Stacked Area Chart by Region"):
            file = st.file_uploader("Upload population_trends.csv", type="csv", key="stacked_area")
            if file:
                df = pd.read_csv(file)

                tabs = st.tabs(["Stacked Area Chart"])

                with tabs[0]:
                    st.subheader("📈 Population Stacked Area Chart by Region")

                    # 전처리
                    df = df[df['행정구역'] != '전국'].copy()
                    df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
                    df = df.dropna(subset=['인구', '연도'])

                    # 지역명 영문 변환
                    region_map = {
                        '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                        '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                        '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                        '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                        '제주': 'Jeju'
                    }
                    df['Region_EN'] = df['행정구역'].map(region_map)

                    # 피벗 테이블 생성
                    pivot_df = df.pivot_table(index='연도', columns='Region_EN', values='인구', aggfunc='sum')
                    pivot_df = pivot_df.sort_index()

                    # 시각화 (stacked area chart using matplotlib)
                    import matplotlib.pyplot as plt

                    fig, ax = plt.subplots(figsize=(12, 6))
                    pivot_df.plot.area(ax=ax, cmap='tab20')

                    ax.set_title("Population Trend by Region (Stacked Area)")
                    ax.set_xlabel("Year")
                    ax.set_ylabel("Population")
                    ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0), title="Region")

                    st.pyplot(fig)

                    st.markdown("""
                    ### 🧭 Interpretation
                    - This stacked area chart shows the population distribution by region over time.
                    - Larger colored bands indicate regions with higher population.
                    - Use this chart to observe growth trends and compare relative size between regions.
                    """)
        # -------------------------
        # 6. 인구 EDA 전체 분석 탭 구조
        # -------------------------
        with st.expander("🧠 Population Trends Full EDA (Tabbed)"):
            file = st.file_uploader("Upload population_trends.csv", type="csv", key="full_eda")
            if file:
                df = pd.read_csv(file)
                df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
                df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
                df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')

                region_map = {
                    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                    '제주': 'Jeju'
                }

                df['Region_EN'] = df['행정구역'].map(region_map)

                tabs = st.tabs(["📌 Basic Stats", "📈 Yearly Trend", "🗺️ Regional", "🔄 Change Top100", "🌈 Stacked Viz"])

                # 1. 기초 통계
                with tabs[0]:
                    st.subheader("Basic Statistics")
                    st.write("**Missing Value Check**")
                    st.dataframe(df.isnull().sum())
                    st.write("**Data Types / Info**")
                    import io
                    buffer = io.StringIO()
                    df.info(buf=buffer)
                    st.text(buffer.getvalue())
                    st.write("**Describe (Numerical)**")
                    st.dataframe(df.describe())

                # 2. 연도별 추이 + 예측
                with tabs[1]:
                    st.subheader("Yearly Population Trend with 2035 Forecast")
                    national = df[df['행정구역'] == '전국'].copy()
                    national = national.sort_values('연도')
                    recent = national.tail(3)
                    avg_birth = recent['출생아수(명)'].mean()
                    avg_death = recent['사망자수(명)'].mean()
                    latest_year = national['연도'].max()
                    latest_pop = national[national['연도'] == latest_year]['인구'].values[0]
                    projected_2035 = int(latest_pop + (2035 - latest_year) * (avg_birth - avg_death))
                    import matplotlib.pyplot as plt
                    years = national['연도'].tolist() + [2035]
                    pops = national['인구'].tolist() + [projected_2035]
                    fig, ax = plt.subplots()
                    ax.plot(years, pops, marker='o')
                    ax.set_title("Population Trend (National)")
                    ax.set_xlabel("Year")
                    ax.set_ylabel("Population")
                    ax.annotate(f"2035: {projected_2035:,}", xy=(2035, projected_2035),
                                xytext=(2028, projected_2035 + 100000),
                                arrowprops=dict(arrowstyle="->", color="red"))
                    st.pyplot(fig)

                # 3. 지역별 분석 (5년 변화량, 비율)
                with tabs[2]:
                    st.subheader("Top Region Changes - Last 5 Years")
                    df_region = df[df['행정구역'] != '전국'].copy()
                    latest_year = df_region['연도'].max()
                    recent_years = sorted(df_region['연도'].unique())[-5:]
                    pivot = df_region[df_region['연도'].isin(recent_years)].pivot_table(
                        index='행정구역', columns='연도', values='인구'
                    ).dropna()
                    pivot['change'] = pivot[recent_years[-1]] - pivot[recent_years[0]]
                    pivot['rate'] = (pivot['change'] / pivot[recent_years[0]]) * 100
                    pivot['Region_EN'] = pivot.index.map(region_map)
                    sorted_change = pivot.sort_values('change', ascending=False)
                    import seaborn as sns
                    fig1, ax1 = plt.subplots(figsize=(10, 6))
                    sns.barplot(x=(sorted_change['change']/1000), y=sorted_change['Region_EN'], ax=ax1)
                    ax1.set_title("Change (Thousands)")
                    st.pyplot(fig1)
                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    sns.barplot(x=sorted_change['rate'], y=sorted_change['Region_EN'], ax=ax2)
                    ax2.set_title("Change Rate (%)")
                    st.pyplot(fig2)

                # 4. 증감 Top 100
                with tabs[3]:
                    st.subheader("Top 100 Yearly Change Records")
                    df_diff = df[df['행정구역'] != '전국'].copy()
                    df_diff = df_diff.sort_values(['행정구역', '연도'])
                    df_diff['증감'] = df_diff.groupby('행정구역')['인구'].diff()
                    top100 = df_diff.dropna(subset=['증감']).copy()
                    top100['abs'] = top100['증감'].abs()
                    top100 = top100.sort_values('abs', ascending=False).head(100)
                    top100['증감'] = top100['증감'].apply(lambda x: f"{int(x):,}")
                    top100['인구'] = top100['인구'].apply(lambda x: f"{int(x):,}")
                    def color_map(val):
                        v = int(val.replace(",", ""))
                        return "background-color: rgba(255,0,0,0.2)" if v < 0 else "background-color: rgba(0,0,255,0.2)"
                    styled = top100[['행정구역', '연도', '인구', '증감']].style.applymap(color_map, subset=['증감'])
                    st.dataframe(styled, use_container_width=True)

                # 5. 누적 영역 그래프
                with tabs[4]:
                    st.subheader("Stacked Area Chart by Region")
                    pivot_area = df[df['행정구역'] != '전국'].pivot_table(
                        index='연도', columns='Region_EN', values='인구'
                    )
                    fig, ax = plt.subplots(figsize=(12, 6))
                    pivot_area.plot.area(ax=ax, cmap='tab20')
                    ax.set_title("Population by Region (Stacked)")
                    ax.set_xlabel("Year")
                    ax.set_ylabel("Population")
                    st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()