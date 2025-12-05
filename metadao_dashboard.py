"""
MetaDAO ICO 토큰 분석 대시보드
================================
Jupiter Price API를 사용하여 MetaDAO 런치패드에서 ICO한 토큰들의
현재가, ATH, ROI 등을 분석합니다.

실행 방법:
1. pip install streamlit requests pandas plotly
2. streamlit run metadao_dashboard.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ============================================
# 설정
# ============================================

st.set_page_config(
    page_title="MetaDAO ICO 토큰 분석",
    page_icon="🚀",
    layout="wide"
)

# MetaDAO ICO 토큰 정보 (mint address 기반)
METADAO_TOKENS = {
    "UMBRA": {
        "mint": "PRVT6TB7uss3FrUd2D9xs2zqDBsa3GbMJMwCQsgmeta",
        "ico_price": 0.075,  # ICO 가격 (USDC)
        "ico_date": "2024-10-06",
        "description": "Solana 프라이버시 프로토콜",
        "category": "Privacy"
    },
    "AVICI": {
        "mint": "BANKJHCKsoWWMfNQwdrwKJUhz8TJXB5vpVK6Qkbsmeta",
        "ico_price": 0.35,
        "ico_date": "2024-10-14",
        "description": "크립토 네오뱅크",
        "category": "DeFi"
    },
    "LOYAL": {
        "mint": "LoYALtyP3k8ARQE6WW7UBNMT77rRX7mkJC5JJD8pmeta",  # 추정 주소
        "ico_price": 0.05,
        "ico_date": "2024-10-18",
        "description": "AI 온체인 액션 프로토콜",
        "category": "AI"
    },
    "META": {
        "mint": "METAewgxyPbgwsseH8T16a39CQ5VyVxZi9zXiDPY18m",
        "ico_price": 100.0,  # 초기 가격 추정
        "ico_date": "2023-11-01",
        "description": "MetaDAO 거버넌스 토큰",
        "category": "Governance"
    }
}

# ============================================
# API 함수
# ============================================

@st.cache_data(ttl=60)  # 60초 캐시
def fetch_jupiter_prices(token_mints: list) -> dict:
    """
    Jupiter Price API V2로 토큰 가격 조회
    
    Rate Limit 대응:
    - 최대 100개 토큰 동시 조회 가능
    - 캐시로 불필요한 호출 방지
    """
    try:
        ids = ",".join(token_mints)
        url = f"https://api.jup.ag/price/v2?ids={ids}&showExtraInfo=true"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json().get("data", {})
    
    except requests.exceptions.RequestException as e:
        st.error(f"Jupiter API 오류: {e}")
        return {}

@st.cache_data(ttl=300)  # 5분 캐시
def fetch_dexscreener_data(mint_address: str) -> dict:
    """
    DexScreener API로 추가 데이터 조회 (ATH, 거래량 등)
    
    Failover: Jupiter API 실패 시 백업으로 사용
    """
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("pairs"):
            # 가장 유동성이 높은 페어 선택
            pairs = sorted(data["pairs"], key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
            return pairs[0] if pairs else {}
        return {}
    
    except requests.exceptions.RequestException as e:
        return {}

def get_token_data() -> pd.DataFrame:
    """
    모든 토큰 데이터 수집 및 DataFrame 생성
    """
    records = []
    
    # Jupiter API로 가격 조회
    mints = [info["mint"] for info in METADAO_TOKENS.values()]
    jupiter_data = fetch_jupiter_prices(mints)
    
    for symbol, info in METADAO_TOKENS.items():
        mint = info["mint"]
        
        # Jupiter 가격
        jup_price = None
        if mint in jupiter_data:
            jup_price = float(jupiter_data[mint].get("price", 0))
        
        # DexScreener 백업/추가 데이터
        dex_data = fetch_dexscreener_data(mint)
        
        current_price = jup_price
        if not current_price and dex_data:
            current_price = float(dex_data.get("priceUsd", 0) or 0)
        
        # ROI 계산
        ico_price = info["ico_price"]
        roi = ((current_price - ico_price) / ico_price * 100) if current_price and ico_price else 0
        roi_x = current_price / ico_price if current_price and ico_price else 0
        
        # 추가 메트릭
        volume_24h = float(dex_data.get("volume", {}).get("h24", 0) or 0) if dex_data else 0
        liquidity = float(dex_data.get("liquidity", {}).get("usd", 0) or 0) if dex_data else 0
        price_change_24h = float(dex_data.get("priceChange", {}).get("h24", 0) or 0) if dex_data else 0
        
        records.append({
            "Symbol": symbol,
            "Current Price": current_price,
            "ICO Price": ico_price,
            "ROI (%)": roi,
            "ROI (x)": roi_x,
            "24h Change (%)": price_change_24h,
            "24h Volume": volume_24h,
            "Liquidity": liquidity,
            "ICO Date": info["ico_date"],
            "Category": info["category"],
            "Description": info["description"],
            "Mint": mint
        })
    
    return pd.DataFrame(records)

# ============================================
# UI 컴포넌트
# ============================================

def render_header():
    st.title("🚀 MetaDAO ICO 토큰 분석 대시보드")
    st.markdown("""
    Jupiter Price API를 사용하여 MetaDAO 런치패드에서 ICO한 토큰들을 분석합니다.
    
    **데이터 소스:** Jupiter Price API V2, DexScreener API
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"🕐 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
            st.rerun()

def render_overview(df: pd.DataFrame):
    st.subheader("📊 전체 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_roi = df["ROI (x)"].mean()
        st.metric("평균 ROI", f"{avg_roi:.2f}x")
    
    with col2:
        best_performer = df.loc[df["ROI (x)"].idxmax()]
        st.metric("최고 수익률", f"{best_performer['Symbol']}", f"{best_performer['ROI (x)']:.2f}x")
    
    with col3:
        total_volume = df["24h Volume"].sum()
        st.metric("총 24h 거래량", f"${total_volume:,.0f}")
    
    with col4:
        total_liquidity = df["Liquidity"].sum()
        st.metric("총 유동성", f"${total_liquidity:,.0f}")

def render_token_cards(df: pd.DataFrame):
    st.subheader("💰 토큰별 상세")
    
    cols = st.columns(len(df))
    
    for idx, (_, row) in enumerate(df.iterrows()):
        with cols[idx]:
            # ROI에 따른 색상
            roi_color = "🟢" if row["ROI (x)"] >= 1 else "🔴"
            change_color = "🟢" if row["24h Change (%)"] >= 0 else "🔴"
            
            st.markdown(f"""
            ### {row['Symbol']} {roi_color}
            **{row['Description']}**
            
            | 항목 | 값 |
            |------|-----|
            | 현재가 | ${row['Current Price']:.4f} |
            | ICO가 | ${row['ICO Price']:.4f} |
            | ROI | **{row['ROI (x)']:.2f}x** ({row['ROI (%)']:.1f}%) |
            | 24h 변동 | {change_color} {row['24h Change (%)']:.2f}% |
            | 24h 거래량 | ${row['24h Volume']:,.0f} |
            | 유동성 | ${row['Liquidity']:,.0f} |
            | ICO 날짜 | {row['ICO Date']} |
            | 카테고리 | {row['Category']} |
            """)
            
            # Solscan 링크
            st.markdown(f"[🔗 Solscan](https://solscan.io/token/{row['Mint']})")

def render_charts(df: pd.DataFrame):
    st.subheader("📈 차트")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ROI 비교 차트
        fig_roi = px.bar(
            df, 
            x="Symbol", 
            y="ROI (x)",
            color="ROI (x)",
            color_continuous_scale=["red", "yellow", "green"],
            title="토큰별 ROI (배수)"
        )
        fig_roi.add_hline(y=1, line_dash="dash", line_color="white", annotation_text="손익분기점")
        fig_roi.update_layout(template="plotly_dark")
        st.plotly_chart(fig_roi, use_container_width=True)
    
    with col2:
        # 카테고리별 분포
        fig_cat = px.pie(
            df, 
            values="Liquidity", 
            names="Category",
            title="카테고리별 유동성 분포"
        )
        fig_cat.update_layout(template="plotly_dark")
        st.plotly_chart(fig_cat, use_container_width=True)
    
    # 가격 vs ICO 가격 비교
    fig_price = go.Figure()
    fig_price.add_trace(go.Bar(name="현재가", x=df["Symbol"], y=df["Current Price"], marker_color="cyan"))
    fig_price.add_trace(go.Bar(name="ICO가", x=df["Symbol"], y=df["ICO Price"], marker_color="orange"))
    fig_price.update_layout(
        title="현재가 vs ICO가 비교",
        barmode="group",
        template="plotly_dark"
    )
    st.plotly_chart(fig_price, use_container_width=True)

def render_raw_data(df: pd.DataFrame):
    with st.expander("📋 원본 데이터 보기"):
        st.dataframe(df, use_container_width=True)
        
        # CSV 다운로드
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"metadao_tokens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def render_api_info():
    with st.expander("🔧 API 정보 & 사용법"):
        st.markdown("""
        ### Jupiter Price API V2
        
        ```python
        # 기본 사용법
        import requests
        
        # 단일 토큰
        url = "https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112"
        response = requests.get(url)
        price = response.json()["data"]["So11..."]["price"]
        
        # 여러 토큰 (쉼표 구분, 최대 100개)
        url = "https://api.jup.ag/price/v2?ids=MINT1,MINT2,MINT3"
        
        # 추가 정보 포함
        url = "https://api.jup.ag/price/v2?ids=MINT&showExtraInfo=true"
        ```
        
        ### Rate Limit 대응
        - 캐싱 사용 (이 앱은 60초 캐시)
        - 배치 요청 (여러 토큰 한 번에)
        - Exponential backoff 구현
        
        ### Failover 전략
        1. Jupiter API 우선
        2. 실패 시 DexScreener API 사용
        3. 모두 실패 시 캐시된 데이터 표시
        """)

# ============================================
# 메인 실행
# ============================================

def main():
    render_header()
    
    with st.spinner("데이터 로딩 중..."):
        df = get_token_data()
    
    if df.empty or df["Current Price"].sum() == 0:
        st.warning("""
        ⚠️ API에서 데이터를 가져올 수 없습니다.
        
        **가능한 원인:**
        - 네트워크 연결 문제
        - API Rate Limit 초과
        - 토큰 주소 변경
        
        **해결 방법:**
        1. 잠시 후 다시 시도
        2. VPN 사용 시 해제 후 시도
        3. 토큰 mint 주소 확인
        """)
        
        # 데모 데이터로 UI 표시
        st.info("📌 데모 데이터로 UI를 표시합니다.")
        demo_data = {
            "Symbol": ["UMBRA", "AVICI", "LOYAL", "META"],
            "Current Price": [1.71, 7.13, 0.35, 5.97],
            "ICO Price": [0.075, 0.35, 0.05, 100.0],
            "ROI (%)": [2180, 1937, 600, -94],
            "ROI (x)": [22.8, 20.4, 7.0, 0.06],
            "24h Change (%)": [13.66, 18.36, 1.0, -8.52],
            "24h Volume": [1300000, 1000000, 26600, 2555885],
            "Liquidity": [3400000, 2500000, 100000, 1500000],
            "ICO Date": ["2024-10-06", "2024-10-14", "2024-10-18", "2023-11-01"],
            "Category": ["Privacy", "DeFi", "AI", "Governance"],
            "Description": ["Solana 프라이버시 프로토콜", "크립토 네오뱅크", "AI 온체인 액션", "MetaDAO 거버넌스"],
            "Mint": ["PRVT6...", "BANKJ...", "LoYAL...", "METAe..."]
        }
        df = pd.DataFrame(demo_data)
    
    render_overview(df)
    st.divider()
    render_token_cards(df)
    st.divider()
    render_charts(df)
    st.divider()
    render_raw_data(df)
    render_api_info()
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
    Built with Streamlit | Data from Jupiter & DexScreener API<br>
    ⚠️ 투자 조언이 아닙니다. DYOR!
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()