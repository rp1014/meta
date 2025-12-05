"""
MetaDAO ICO 토큰 분석 대시보드 v2
==================================
Jupiter Price API + DexScreener API를 사용하여 
MetaDAO 런치패드에서 ICO한 토큰들의 상세 분석

실행 방법:
1. pip install streamlit requests pandas plotly
2. streamlit run metadao_dashboard_v2.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# ============================================
# 페이지 설정
# ============================================
st.set_page_config(
    page_title="MetaDAO ICO 토큰 분석",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# MetaDAO ICO 토큰 데이터 (정확한 민트 주소)
# ============================================
METADAO_TOKENS = {
    "MTNC": {
        "name": "mtnCapital",
        "mint": "mtnc7NNSpAJuvYNmayXU63WhWZGgFzwQ2yeYWqemeta",
        "ico_price": 0.10,  # 추정치
        "ico_raise_usd": 500000,  # 추정치
        "sale_tokens": 5000000,  # 추정치
        "total_supply": 25000000,  # 추정치
        "ico_date": "2024-09-15",
        "tge_timestamp": None,  # TGE 타임스탬프 (Unix)
        "description": "Futarchy 기반 투자 펀드",
        "category": "Investment Fund"
    },
    "OMFG": {
        "name": "Omnipair",
        "mint": "omfgRBnxHsNJh6YeGbGAmWenNkenzsXyBXm3WDhmeta",
        "ico_price": 0.112,
        "ico_raise_usd": 300000,
        "sale_tokens": 2680000,
        "total_supply": 12000000,
        "ico_date": "2024-07-28",
        "tge_timestamp": None,
        "description": "탈중앙화 트레이딩 & 렌딩 프로토콜",
        "category": "DeFi"
    },
    "UMBRA": {
        "name": "Umbra",
        "mint": "PRVT6TB7uss3FrUd2D9xs2zqDBsa3GbMJMwCQsgmeta",
        "ico_price": 0.075,  # $750K / 10M tokens
        "ico_raise_usd": 750000,
        "sale_tokens": 10000000,
        "total_supply": 28500000,
        "ico_date": "2024-10-06",
        "tge_timestamp": None,
        "description": "Solana 프라이버시 프로토콜",
        "category": "Privacy"
    },
    "AVICI": {
        "name": "Avici",
        "mint": "BANKJmvhT8tiJRsBSS1n2HryMBPvT5Ze4HU95DUAmeta",
        "ico_price": 0.35,
        "ico_raise_usd": 3500000,
        "sale_tokens": 10000000,
        "total_supply": 100000000,  # 추정
        "ico_date": "2024-10-14",
        "tge_timestamp": None,
        "description": "크립토 네오뱅크 (Visa 카드)",
        "category": "Payments"
    },
    "LOYAL": {
        "name": "Loyal",
        "mint": "LYLikzBQtpa9ZgVrJsqYGQpR3cC1WMJrBHaXGrQmeta",
        "ico_price": 0.05,
        "ico_raise_usd": 500000,
        "sale_tokens": 10000000,
        "total_supply": 20976923,
        "ico_date": "2024-10-18",
        "tge_timestamp": None,
        "description": "탈중앙화 AI 추론 프로토콜",
        "category": "AI"
    },
    "ZKLSOL": {
        "name": "ZKLSOL",
        "mint": "ZKFHiLAfAFMTcDAuCtjNW54VzpERvoe7PBF9mYgmeta",
        "ico_price": 0.03,  # 추정
        "ico_raise_usd": 300000,
        "sale_tokens": 10000000,
        "total_supply": 100000000,  # 추정
        "ico_date": "2024-10-19",
        "tge_timestamp": None,
        "description": "프라이버시 + LST 스테이킹",
        "category": "Privacy/LST"
    },
    "PAYSTREAM": {
        "name": "Paystream",
        "mint": "PAYZP1W3UmdEsNLJwmH61TNqACYJTvhXy8SCN4Tmeta",
        "ico_price": 0.05,  # 추정
        "ico_raise_usd": 300000,
        "sale_tokens": 6000000,
        "total_supply": 30000000,  # 추정
        "ico_date": "2024-10-27",
        "tge_timestamp": None,
        "description": "P2P 렌딩 프로토콜",
        "category": "DeFi/Lending"
    },
    "SOLO": {
        "name": "Solomon",
        "mint": "SoLo9oxzLDpcq1dpqAgMwgce5WqkRDtNXK7EPnbmeta",
        "ico_price": 0.20,
        "ico_raise_usd": 2000000,  # 최소 목표 (실제 $102M 모금)
        "sale_tokens": 10000000,
        "total_supply": 25800000,
        "ico_date": "2024-11-18",
        "tge_timestamp": None,
        "description": "수익형 스테이블코인 (USDv/sUSDv)",
        "category": "Stablecoin/Yield"
    }
}

# ============================================
# API 함수들
# ============================================

@st.cache_data(ttl=60)
def fetch_jupiter_prices(token_mints: List[str]) -> Dict:
    """Jupiter Price API V2로 현재 가격 조회"""
    try:
        ids = ",".join(token_mints)
        url = f"https://api.jup.ag/price/v2?ids={ids}&showExtraInfo=true"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json().get("data", {})
    except Exception as e:
        st.warning(f"Jupiter API 오류: {e}")
        return {}

@st.cache_data(ttl=120)
def fetch_dexscreener_token(mint_address: str) -> Dict:
    """DexScreener API로 토큰 데이터 조회 (ATH, ATL, 거래량 등)"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("pairs"):
            # 유동성이 가장 높은 페어 선택
            pairs = sorted(
                data["pairs"], 
                key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0), 
                reverse=True
            )
            return pairs[0] if pairs else {}
        return {}
    except Exception as e:
        return {}

@st.cache_data(ttl=300)
def fetch_dexscreener_ohlcv(pair_address: str, timeframe: str = "1h") -> List[Dict]:
    """DexScreener에서 OHLCV 데이터 가져오기 (ATH/ATL 계산용)"""
    try:
        # DexScreener는 직접 OHLCV API를 제공하지 않음
        # 대신 priceChange 데이터 활용
        return []
    except Exception as e:
        return []

@st.cache_data(ttl=300)
def fetch_birdeye_ohlcv(mint_address: str, timeframe: str = "1H", limit: int = 1000) -> List[Dict]:
    """
    Birdeye API로 OHLCV 데이터 가져오기 (무료 API)
    ATH/ATL 및 시간대별 가격 계산용
    """
    try:
        # Birdeye 무료 API (API 키 필요없는 퍼블릭 엔드포인트)
        url = f"https://public-api.birdeye.so/defi/ohlcv"
        params = {
            "address": mint_address,
            "type": timeframe,
            "time_from": int((datetime.now() - timedelta(days=90)).timestamp()),
            "time_to": int(datetime.now().timestamp())
        }
        headers = {"X-API-KEY": "public"}  # 공개 키
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json().get("data", {}).get("items", [])
        return []
    except Exception as e:
        return []

def calculate_ath_atl(dex_data: Dict, ohlcv_data: List[Dict] = None) -> Tuple[Optional[float], Optional[float]]:
    """ATH(최고가)와 ATL(최저가) 계산"""
    ath = None
    atl = None
    
    # OHLCV 데이터가 있으면 사용
    if ohlcv_data:
        highs = [candle.get("h", 0) for candle in ohlcv_data if candle.get("h")]
        lows = [candle.get("l", float('inf')) for candle in ohlcv_data if candle.get("l")]
        if highs:
            ath = max(highs)
        if lows and min(lows) != float('inf'):
            atl = min(lows)
    
    # DexScreener 데이터에서 추정 (priceChange 기반)
    if dex_data and not ath:
        current_price = float(dex_data.get("priceUsd", 0) or 0)
        # 24h 최고/최저
        price_high_24h = dex_data.get("priceChange", {}).get("h24High")
        price_low_24h = dex_data.get("priceChange", {}).get("h24Low")
        
        if price_high_24h:
            ath = float(price_high_24h)
        if price_low_24h:
            atl = float(price_low_24h)
    
    return ath, atl

def calculate_roi(current_price: float, ico_price: float) -> Tuple[float, float]:
    """ROI 계산 (배수, 퍼센트)"""
    if ico_price and ico_price > 0 and current_price:
        roi_x = current_price / ico_price
        roi_pct = (current_price - ico_price) / ico_price * 100
        return roi_x, roi_pct
    return 0, 0

# ============================================
# 데이터 수집 함수
# ============================================

def get_all_token_data() -> pd.DataFrame:
    """모든 토큰 데이터 수집 및 DataFrame 생성"""
    records = []
    
    # Jupiter API로 현재 가격 조회
    mints = [info["mint"] for info in METADAO_TOKENS.values()]
    jupiter_data = fetch_jupiter_prices(mints)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (symbol, info) in enumerate(METADAO_TOKENS.items()):
        status_text.text(f"데이터 수집 중: {info['name']}...")
        progress_bar.progress((idx + 1) / len(METADAO_TOKENS))
        
        mint = info["mint"]
        ico_price = info["ico_price"]
        
        # 현재 가격 (Jupiter 우선, DexScreener 백업)
        current_price = None
        if mint in jupiter_data:
            current_price = float(jupiter_data[mint].get("price", 0) or 0)
        
        # DexScreener 데이터
        dex_data = fetch_dexscreener_token(mint)
        
        if not current_price and dex_data:
            current_price = float(dex_data.get("priceUsd", 0) or 0)
        
        # ATH/ATL 계산
        ath, atl = calculate_ath_atl(dex_data)
        
        # ROI 계산
        roi_x, roi_pct = calculate_roi(current_price, ico_price)
        ath_roi_x, ath_roi_pct = calculate_roi(ath, ico_price) if ath else (None, None)
        atl_roi_x, atl_roi_pct = calculate_roi(atl, ico_price) if atl else (None, None)
        
        # 세일 정보
        sale_tokens = info["sale_tokens"]
        total_supply = info["total_supply"]
        sale_ratio = (sale_tokens / total_supply * 100) if total_supply else 0
        
        # 24h 변동
        price_change_24h = float(dex_data.get("priceChange", {}).get("h24", 0) or 0) if dex_data else 0
        volume_24h = float(dex_data.get("volume", {}).get("h24", 0) or 0) if dex_data else 0
        liquidity = float(dex_data.get("liquidity", {}).get("usd", 0) or 0) if dex_data else 0
        
        # FDV 계산
        fdv = current_price * total_supply if current_price and total_supply else 0
        
        # 가상 매도 수익 계산 (세일 물량 전부 매도 시)
        ico_investment = info["ico_raise_usd"]
        current_value = current_price * sale_tokens if current_price else 0
        profit_usd = current_value - ico_investment if ico_investment else 0
        
        records.append({
            # 기본 정보
            "Symbol": symbol,
            "Name": info["name"],
            "Category": info["category"],
            "Description": info["description"],
            "Mint": mint,
            "ICO Date": info["ico_date"],
            
            # 세일 정보
            "ICO Price": ico_price,
            "ICO Raise (USD)": ico_raise_usd if (ico_raise_usd := info["ico_raise_usd"]) else None,
            "Sale Tokens": sale_tokens,
            "Total Supply": total_supply,
            "Sale Ratio (%)": sale_ratio,
            
            # 현재 가격
            "Current Price": current_price,
            "24h Change (%)": price_change_24h,
            "24h Volume": volume_24h,
            "Liquidity": liquidity,
            "FDV": fdv,
            
            # ATH/ATL
            "ATH": ath,
            "ATL": atl,
            
            # ROI 지표
            "ROI (x)": roi_x,
            "ROI (%)": roi_pct,
            "ATH ROI (x)": ath_roi_x,
            "ATH ROI (%)": ath_roi_pct,
            "ATL ROI (x)": atl_roi_x,
            "ATL ROI (%)": atl_roi_pct,
            
            # 가상 매도 수익
            "Current Value (USD)": current_value,
            "Profit (USD)": profit_usd,
            "Profit (%)": (profit_usd / ico_investment * 100) if ico_investment else 0
        })
        
        # Rate limit 방지
        time.sleep(0.3)
    
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(records)

# ============================================
# UI 컴포넌트
# ============================================

def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("⚙️ 설정")
        
        # 카테고리 필터
        categories = ["All"] + list(set(info["category"] for info in METADAO_TOKENS.values()))
        selected_category = st.selectbox("카테고리 필터", categories)
        
        # 정렬 옵션
        sort_options = {
            "ROI (높은순)": ("ROI (x)", False),
            "ROI (낮은순)": ("ROI (x)", True),
            "ICO 날짜 (최신순)": ("ICO Date", False),
            "유동성 (높은순)": ("Liquidity", False),
            "거래량 (높은순)": ("24h Volume", False)
        }
        sort_by = st.selectbox("정렬 기준", list(sort_options.keys()))
        
        st.divider()
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        # 정보
        st.markdown("""
        ### 📊 데이터 소스
        - Jupiter Price API V2
        - DexScreener API
        
        ### ⚠️ 주의
        - 실시간 데이터는 지연될 수 있음
        - ATH/ATL은 추정치일 수 있음
        - 투자 조언 아님, DYOR!
        """)
        
        return selected_category, sort_options[sort_by]

def render_overview(df: pd.DataFrame):
    """전체 요약 렌더링"""
    st.header("📊 전체 요약")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_raised = df["ICO Raise (USD)"].sum()
        st.metric("총 ICO 모금액", f"${total_raised:,.0f}")
    
    with col2:
        avg_roi = df["ROI (x)"].mean()
        st.metric("평균 ROI", f"{avg_roi:.2f}x")
    
    with col3:
        profitable = len(df[df["ROI (x)"] >= 1])
        st.metric("수익 토큰", f"{profitable}/{len(df)}")
    
    with col4:
        total_volume = df["24h Volume"].sum()
        st.metric("총 24h 거래량", f"${total_volume:,.0f}")
    
    with col5:
        total_liquidity = df["Liquidity"].sum()
        st.metric("총 유동성", f"${total_liquidity:,.0f}")

def render_summary_table(df: pd.DataFrame):
    """요약 테이블 렌더링"""
    st.header("📋 한눈에 보기")
    
    # 표시할 컬럼 선택
    display_cols = [
        "Symbol", "Name", "Category", "ICO Price", "Current Price",
        "ROI (x)", "ROI (%)", "ATH ROI (x)", "ATL ROI (x)",
        "24h Change (%)", "Liquidity", "ICO Date"
    ]
    
    # 데이터 포맷팅
    display_df = df[display_cols].copy()
    
    # 스타일 적용
    def color_roi(val):
        if pd.isna(val):
            return ""
        if val >= 2:
            return "background-color: #1a472a; color: #90EE90"
        elif val >= 1:
            return "background-color: #2d4a3e; color: #98FB98"
        else:
            return "background-color: #4a1a1a; color: #FFB6C1"
    
    styled_df = display_df.style.applymap(
        color_roi, 
        subset=["ROI (x)", "ATH ROI (x)", "ATL ROI (x)"]
    ).format({
        "ICO Price": "${:.4f}",
        "Current Price": "${:.4f}",
        "ROI (x)": "{:.2f}x",
        "ROI (%)": "{:.1f}%",
        "ATH ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ATL ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "24h Change (%)": "{:+.2f}%",
        "Liquidity": "${:,.0f}"
    })
    
    st.dataframe(styled_df, use_container_width=True, height=400)

def render_token_cards(df: pd.DataFrame):
    """토큰별 카드 렌더링"""
    st.header("💰 토큰별 상세")
    
    # 2열 레이아웃
    cols = st.columns(2)
    
    for idx, (_, row) in enumerate(df.iterrows()):
        with cols[idx % 2]:
            with st.container():
                # ROI에 따른 이모지
                if row["ROI (x)"] >= 2:
                    roi_emoji = "🚀"
                elif row["ROI (x)"] >= 1:
                    roi_emoji = "✅"
                else:
                    roi_emoji = "📉"
                
                st.subheader(f"{roi_emoji} {row['Symbol']} - {row['Name']}")
                
                # 메트릭 표시
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric(
                        "현재가",
                        f"${row['Current Price']:.4f}" if row['Current Price'] else "N/A",
                        f"{row['24h Change (%)']:+.2f}%" if row['24h Change (%)'] else None
                    )
                
                with metric_col2:
                    st.metric(
                        "ROI",
                        f"{row['ROI (x)']:.2f}x" if row['ROI (x)'] else "N/A"
                    )
                
                with metric_col3:
                    st.metric(
                        "ATH ROI",
                        f"{row['ATH ROI (x)']:.2f}x" if pd.notna(row['ATH ROI (x)']) else "N/A"
                    )
                
                # 상세 정보
                with st.expander("상세 정보"):
                    st.markdown(f"""
                    **설명:** {row['Description']}
                    
                    | 항목 | 값 |
                    |------|-----|
                    | ICO 가격 | ${row['ICO Price']:.4f} |
                    | ICO 모금액 | ${row['ICO Raise (USD)']:,.0f} |
                    | 세일 토큰 | {row['Sale Tokens']:,.0f} |
                    | 세일 비율 | {row['Sale Ratio (%)']:.1f}% |
                    | ATH | ${row['ATH']:.4f} | if pd.notna(row['ATH']) else 'N/A'
                    | ATL | ${row['ATL']:.6f} | if pd.notna(row['ATL']) else 'N/A'
                    | 유동성 | ${row['Liquidity']:,.0f} |
                    | 24h 거래량 | ${row['24h Volume']:,.0f} |
                    | ICO 날짜 | {row['ICO Date']} |
                    """)
                    
                    # 링크
                    st.markdown(f"[🔗 Solscan](https://solscan.io/token/{row['Mint']}) | [📊 DexScreener](https://dexscreener.com/solana/{row['Mint']})")
                
                st.divider()

def render_roi_chart(df: pd.DataFrame):
    """ROI 비교 차트"""
    st.header("📈 ROI 비교")
    
    # ROI 바 차트
    fig = go.Figure()
    
    # 현재 ROI
    fig.add_trace(go.Bar(
        name="현재 ROI",
        x=df["Symbol"],
        y=df["ROI (x)"],
        marker_color=df["ROI (x)"].apply(
            lambda x: "#00C853" if x >= 1 else "#FF5252"
        ),
        text=df["ROI (x)"].apply(lambda x: f"{x:.2f}x"),
        textposition="outside"
    ))
    
    # ATH ROI (있는 경우)
    if df["ATH ROI (x)"].notna().any():
        fig.add_trace(go.Bar(
            name="ATH ROI",
            x=df["Symbol"],
            y=df["ATH ROI (x)"].fillna(0),
            marker_color="rgba(255, 193, 7, 0.7)",
            text=df["ATH ROI (x)"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else ""),
            textposition="outside"
        ))
    
    fig.add_hline(y=1, line_dash="dash", line_color="white", annotation_text="손익분기점 (1x)")
    
    fig.update_layout(
        title="토큰별 ROI 비교",
        xaxis_title="토큰",
        yaxis_title="ROI (배수)",
        template="plotly_dark",
        barmode="group",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_category_chart(df: pd.DataFrame):
    """카테고리별 분석 차트"""
    col1, col2 = st.columns(2)
    
    with col1:
        # 카테고리별 평균 ROI
        cat_roi = df.groupby("Category")["ROI (x)"].mean().reset_index()
        fig = px.bar(
            cat_roi,
            x="Category",
            y="ROI (x)",
            title="카테고리별 평균 ROI",
            color="ROI (x)",
            color_continuous_scale=["red", "yellow", "green"]
        )
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 카테고리별 유동성 분포
        fig = px.pie(
            df,
            values="Liquidity",
            names="Category",
            title="카테고리별 유동성 분포"
        )
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

def render_timeline_chart(df: pd.DataFrame):
    """ICO 타임라인 차트"""
    st.header("📅 ICO 타임라인")
    
    df_sorted = df.sort_values("ICO Date")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_sorted["ICO Date"],
        y=df_sorted["ROI (x)"],
        mode="markers+text",
        marker=dict(
            size=df_sorted["ICO Raise (USD)"] / 100000 + 10,  # 크기 = 모금액 비례
            color=df_sorted["ROI (x)"],
            colorscale="RdYlGn",
            showscale=True,
            colorbar=dict(title="ROI (x)")
        ),
        text=df_sorted["Symbol"],
        textposition="top center",
        hovertemplate="<b>%{text}</b><br>ICO: %{x}<br>ROI: %{y:.2f}x<extra></extra>"
    ))
    
    fig.add_hline(y=1, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title="ICO 시기별 ROI (버블 크기 = 모금액)",
        xaxis_title="ICO 날짜",
        yaxis_title="현재 ROI (x)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_profit_simulation(df: pd.DataFrame):
    """가상 수익 시뮬레이션"""
    st.header("💵 투자 시뮬레이션")
    
    investment = st.slider("투자금액 (USD)", 100, 10000, 1000, 100)
    
    sim_data = []
    for _, row in df.iterrows():
        if row["Current Price"] and row["ICO Price"]:
            tokens_bought = investment / row["ICO Price"]
            current_value = tokens_bought * row["Current Price"]
            profit = current_value - investment
            
            sim_data.append({
                "Token": row["Symbol"],
                "투자금": investment,
                "토큰 수량": tokens_bought,
                "현재 가치": current_value,
                "수익": profit,
                "수익률": (profit / investment) * 100
            })
    
    sim_df = pd.DataFrame(sim_data)
    
    # 바 차트
    fig = px.bar(
        sim_df,
        x="Token",
        y="수익",
        color="수익",
        color_continuous_scale=["red", "yellow", "green"],
        title=f"${investment} 투자 시 각 토큰별 수익"
    )
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    # 테이블
    st.dataframe(
        sim_df.style.format({
            "투자금": "${:,.0f}",
            "토큰 수량": "{:,.2f}",
            "현재 가치": "${:,.2f}",
            "수익": "${:+,.2f}",
            "수익률": "{:+.1f}%"
        }),
        use_container_width=True
    )

def render_raw_data(df: pd.DataFrame):
    """원본 데이터 다운로드"""
    with st.expander("📥 원본 데이터 다운로드"):
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="CSV 다운로드",
            data=csv,
            file_name=f"metadao_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# ============================================
# 메인 함수
# ============================================

def main():
    st.title("🚀 MetaDAO ICO 토큰 분석 대시보드 v2")
    st.markdown("MetaDAO 런치패드에서 ICO한 8개 토큰의 상세 분석")
    
    # 사이드바
    selected_category, (sort_col, sort_asc) = render_sidebar()
    
    # 데이터 로딩
    with st.spinner("데이터를 불러오는 중..."):
        df = get_all_token_data()
    
    # API 연결 실패 시 데모 데이터
    if df["Current Price"].sum() == 0:
        st.warning("⚠️ API에서 실시간 데이터를 가져올 수 없습니다. 데모 데이터를 표시합니다.")
        # 데모 데이터 설정
        demo_prices = {
            "MTNC": 0.15, "OMFG": 0.88, "UMBRA": 1.71, "AVICI": 5.68,
            "LOYAL": 0.35, "ZKLSOL": 0.08, "PAYSTREAM": 0.06, "SOLO": 1.23
        }
        for idx, row in df.iterrows():
            symbol = row["Symbol"]
            if symbol in demo_prices:
                df.at[idx, "Current Price"] = demo_prices[symbol]
                df.at[idx, "ROI (x)"], df.at[idx, "ROI (%)"] = calculate_roi(
                    demo_prices[symbol], row["ICO Price"]
                )
    
    # 필터링
    if selected_category != "All":
        df = df[df["Category"] == selected_category]
    
    # 정렬
    df = df.sort_values(sort_col, ascending=sort_asc)
    
    # 렌더링
    render_overview(df)
    st.divider()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 요약 테이블", "💰 토큰 카드", "📈 차트", "💵 시뮬레이션", "📥 데이터"
    ])
    
    with tab1:
        render_summary_table(df)
    
    with tab2:
        render_token_cards(df)
    
    with tab3:
        render_roi_chart(df)
        render_category_chart(df)
        render_timeline_chart(df)
    
    with tab4:
        render_profit_simulation(df)
    
    with tab5:
        render_raw_data(df)
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
    Built with Streamlit | Data: Jupiter API, DexScreener API<br>
    ⚠️ 투자 조언이 아닙니다. DYOR!
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
