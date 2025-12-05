"""
MetaDAO ICO 토큰 분석 대시보드 v3
==================================
DexScreener API를 사용하여 MetaDAO 런치패드 ICO 토큰 상세 분석
- TGE 기준 5분/15분/30분/1시간 가상 매도 수익률
- ATH/ATL 계산
- 세일 할당량 분석
- 투자 시뮬레이션

실행: streamlit run metadao_dashboard.py
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import time

# ============================================
# 페이지 설정
# ============================================
st.set_page_config(
    page_title="MetaDAO ICO 분석",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 색상 팔레트 (MetaDAO 레드/핑크 테마)
# ============================================
COLORS = {
    # 배경 (보라-네이비 그라데이션 느낌)
    "bg_primary": "#0D0D1A",
    "bg_secondary": "#12121F",
    "bg_card": "#1A1A2E",
    "bg_card_hover": "#252540",
    "border": "#2D2D4A",
    
    # 텍스트
    "text_primary": "#FFFFFF",
    "text_secondary": "#A0A0B8",
    "text_muted": "#6B6B80",
    
    # 포인트 (핑크/마젠타 계열 - MetaDAO 느낌)
    "accent_primary": "#E91E8C",      # 핫핑크
    "accent_secondary": "#FF6B9D",    # 연한 핑크
    "accent_gradient_start": "#E91E8C",
    "accent_gradient_end": "#FF6B9D",
    
    # 보조 포인트
    "accent_cyan": "#06B6D4",
    "accent_purple": "#A855F7",
    "accent_warning": "#FACC15",
    
    # 상태
    "positive": "#22C55E",
    "positive_light": "#4ADE80",
    "positive_bg": "#0D2818",
    "negative": "#EF4444",
    "negative_light": "#FCA5A5",
    "negative_bg": "#2D1215",
    "neutral_bg": "#1E3A5F",
    
    # 차트용
    "chart_current_roi": "#22C55E",
    "chart_launch_roi": "#E91E8C",     # 핑크
    "chart_ath_roi": "#FACC15",
    "chart_atl_roi": "#EF4444",
    "chart_featured": "#06B6D4",
    "chart_permissionless": "#FF6B9D",
    
    # 프로그레스/강조
    "highlight": "#E91E8C",
    "highlight_glow": "rgba(233, 30, 140, 0.3)",
}

# 연속 색 스케일 (ROI 등)
COLOR_SCALE_ROI = ["#EF4444", "#FACC15", "#22C55E"]

# ============================================
# 커스텀 CSS 주입
# ============================================
def inject_custom_css():
    st.markdown(f"""
    <style>
    /* 전체 배경 - 그라데이션 */
    .stApp {{
        background: linear-gradient(180deg, {COLORS["bg_primary"]} 0%, #1a0a1a 50%, {COLORS["bg_primary"]} 100%);
        background-attachment: fixed;
    }}
    
    /* 사이드바 */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS["bg_secondary"]} 0%, #1a0a1a 100%);
        border-right: 1px solid {COLORS["border"]};
    }}
    
    /* 메트릭 카드 - 글로우 효과 */
    [data-testid="stMetricValue"] {{
        color: {COLORS["text_primary"]};
        font-weight: 700;
    }}
    [data-testid="stMetricLabel"] {{
        color: {COLORS["text_secondary"]};
    }}
    [data-testid="stMetricDelta"] svg {{
        stroke: {COLORS["accent_primary"]};
    }}
    
    /* 헤더 - 핑크 그라데이션 */
    h1 {{
        background: linear-gradient(90deg, {COLORS["accent_primary"]}, {COLORS["accent_secondary"]});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    h2, h3 {{
        color: {COLORS["text_primary"]} !important;
    }}
    
    /* 캡션 */
    .stCaption {{
        color: {COLORS["text_secondary"]} !important;
    }}
    
    /* 탭 - 핑크 테마 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS["bg_card"]};
        border-radius: 12px;
        padding: 6px;
        border: 1px solid {COLORS["border"]};
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {COLORS["text_secondary"]};
        border-radius: 8px;
        padding: 8px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {COLORS["accent_primary"]}40, {COLORS["accent_secondary"]}20);
        color: {COLORS["accent_secondary"]};
        border: 1px solid {COLORS["accent_primary"]}60;
    }}
    
    /* 버튼 - 핑크 그라데이션 */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS["accent_primary"]}, {COLORS["accent_secondary"]});
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px {COLORS["highlight_glow"]};
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px {COLORS["highlight_glow"]};
    }}
    
    /* 데이터프레임 */
    .stDataFrame {{
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        overflow: hidden;
    }}
    
    /* 익스팬더 */
    .streamlit-expanderHeader {{
        background-color: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
    }}
    
    /* 카드 스타일 */
    .custom-card {{
        background: linear-gradient(135deg, {COLORS["bg_card"]} 0%, {COLORS["bg_card_hover"]} 100%);
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}
    
    /* 구분선 */
    hr {{
        border-color: {COLORS["border"]};
        opacity: 0.5;
    }}
    
    /* 셀렉트박스/인풋 */
    .stSelectbox > div > div {{
        background-color: {COLORS["bg_card"]};
        border-color: {COLORS["border"]};
    }}
    
    /* 정보 박스 */
    .stAlert {{
        background-color: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
    }}
    
    /* 숫자 입력 */
    .stNumberInput > div > div > input {{
        background-color: {COLORS["bg_card"]};
        border-color: {COLORS["border"]};
        color: {COLORS["text_primary"]};
    }}
    
    /* 체크박스 */
    .stCheckbox > label > span {{
        color: {COLORS["text_primary"]};
    }}
    
    /* 라디오 버튼 */
    .stRadio > label {{
        color: {COLORS["text_primary"]};
    }}
    
    /* 메트릭 컨테이너 글로우 */
    [data-testid="metric-container"] {{
        background: linear-gradient(135deg, {COLORS["bg_card"]} 0%, {COLORS["bg_card_hover"]} 100%);
        border: 1px solid {COLORS["border"]};
        border-radius: 12px;
        padding: 1rem;
    }}
    
    /* 다운로드 버튼 */
    .stDownloadButton > button {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["accent_primary"]};
        color: {COLORS["accent_primary"]};
    }}
    .stDownloadButton > button:hover {{
        background: {COLORS["accent_primary"]}20;
    }}
    </style>
    """, unsafe_allow_html=True)

# CSS 주입 실행
inject_custom_css()


# ============================================
# Plotly 차트 공통 레이아웃 함수
# ============================================
def apply_dark_layout(fig, height: int = 400):
    """모든 Plotly 차트에 공통 다크 레이아웃 적용"""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(13,13,26,0)",
        plot_bgcolor="rgba(26,26,46,0.5)",
        font=dict(color=COLORS["text_primary"], family="sans-serif"),
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            bgcolor="rgba(26,26,46,0.8)",
            bordercolor=COLORS["border"],
            borderwidth=1,
            font=dict(color=COLORS["text_primary"])
        ),
        xaxis=dict(
            gridcolor=COLORS["border"],
            zerolinecolor=COLORS["border"],
            tickfont=dict(color=COLORS["text_secondary"])
        ),
        yaxis=dict(
            gridcolor=COLORS["border"],
            zerolinecolor=COLORS["border"],
            tickfont=dict(color=COLORS["text_secondary"])
        ),
        title_font=dict(color=COLORS["accent_secondary"], size=16)
    )
    return fig


# ============================================
# ROI 스타일링 함수 (통일)
# ============================================
def style_roi(val):
    """ROI 컬럼 스타일링 (통일된 색상)"""
    if pd.isna(val) or val is None:
        return f"background-color: {COLORS['bg_card']}; color: {COLORS['text_muted']}"
    if val >= 2:
        return f"background-color: {COLORS['positive_bg']}; color: {COLORS['positive_light']}"
    elif val >= 1:
        return f"background-color: {COLORS['neutral_bg']}; color: #93C5FD"
    else:
        return f"background-color: {COLORS['negative_bg']}; color: {COLORS['negative_light']}"


# ============================================
# MetaDAO ICO 토큰 데이터 (공식 크롤링 데이터 기준)
# 
# 필드 설명:
# - committed_usd: 총 청약액 (커밋된 금액)
# - ico_raise_usd: 실제 모금액 (팀이 수령한 금액)
# - min_raise_usd: 최소 모금 목표
# - allowance_usd: 월 허용 예산
# - contributors: 참여 지갑 수
# - oversubscription: 청약배수 (committed / min_raise)
# - is_permissionless: Permissionless Launch 여부
# - tge_timestamp: TGE 시점 (Unix timestamp)
# - launch_price: 상장가 (ICO가 아님)
# ============================================
METADAO_TOKENS = {
    "MTNC": {
        "name": "mtnCapital",
        "mint": "mtnc7NNSpAJuvYNmayXU63WhWZGgFzwQ2yeYWqemeta",
        "ico_price": 0.576,  # $5,758,964 / 10M tokens
        "launch_price": 0.576,
        "committed_usd": 5758964,
        "ico_raise_usd": 5758964,
        "min_raise_usd": 0,  # 이미지 기준 $0.00
        "allowance_usd": None,
        "sale_tokens": 10000000,
        "total_supply": 25000000,
        "ico_date": "2025-04-09",
        "tge_timestamp": None,
        "contributors": 1931,
        "oversubscription": 1.0,
        "is_permissionless": False,
        "description": "First futarchy-governed investment fund",
        "category": "Investment Fund"
    },
    "OMFG": {
        "name": "Omnipair",
        "mint": "omfgRBnxHsNJh6YeGbGAmWenNkenzsXyBXm3WDhmeta",
        "ico_price": 0.112,  # 이미지 Launch Price
        "launch_price": 0.112,
        "committed_usd": 1118102,
        "ico_raise_usd": 1118102,
        "min_raise_usd": 300000,
        "allowance_usd": None,
        "sale_tokens": 10000000,
        "total_supply": 12000000,
        "ico_date": "2025-07-28",
        "tge_timestamp": None,
        "contributors": 321,
        "oversubscription": 3.73,  # 1,118,102 / 300,000
        "is_permissionless": False,
        "description": "Permissionless borrowing and leverage on Solana",
        "category": "DeFi"
    },
    "UMBRA": {
        "name": "Umbra",
        "mint": "PRVT6TB7uss3FrUd2D9xs2zqDBsa3GbMJMwCQsgmeta",
        "ico_price": 0.30,  # 이미지 Launch Price (ICO 가격과 동일하게 설정)
        "launch_price": 0.30,
        "committed_usd": 154943746,
        "ico_raise_usd": 3000000,  # 이미지 기준 $3,000,000
        "min_raise_usd": 750000,
        "allowance_usd": 34091,
        "sale_tokens": 10000000,
        "total_supply": 28500000,
        "ico_date": "2025-10-06",
        "tge_timestamp": None,
        "contributors": 10519,
        "oversubscription": 206.59,  # 154,943,746 / 750,000
        "is_permissionless": False,
        "description": "Privacy for swaps and transfers, built on Arcium",
        "category": "Privacy"
    },
    "AVICI": {
        "name": "Avici",
        "mint": "BANKJmvhT8tiJRsBSS1n2HryMBPvT5Ze4HU95DUAmeta",
        "ico_price": 0.35,  # 이미지 Launch Price
        "launch_price": 0.35,
        "committed_usd": 34230976,
        "ico_raise_usd": 3500000,  # 이미지 기준 $3,500,000
        "min_raise_usd": 2000000,
        "allowance_usd": 100000,
        "sale_tokens": 10000000,
        "total_supply": 100000000,
        "ico_date": "2025-10-14",
        "tge_timestamp": None,
        "contributors": 7352,
        "oversubscription": 17.12,  # 34,230,976 / 2,000,000
        "is_permissionless": False,
        "description": "Distributed Internet banking infrastructure",
        "category": "Payments"
    },
    "LOYAL": {
        "name": "Loyal",
        "mint": "LYLikzBQtpa9ZgVrJsqYGQpR3cC1WMJrBHaXGrQmeta",
        "ico_price": 0.25,  # 이미지 Launch Price
        "launch_price": 0.25,
        "committed_usd": 75898233,
        "ico_raise_usd": 2500000,  # 이미지 기준 $2,500,000
        "min_raise_usd": 500000,
        "allowance_usd": 60000,
        "sale_tokens": 10000000,
        "total_supply": 20976923,
        "ico_date": "2025-10-18",
        "tge_timestamp": None,
        "contributors": 5058,
        "oversubscription": 151.80,  # 75,898,233 / 500,000
        "is_permissionless": True,  # Permissionless Launch
        "description": "Solana-based private decentralized intelligence",
        "category": "AI/Privacy"
    },
    "ZKLSOL": {
        "name": "ZKLSOL",
        "mint": "ZKFHiLAfAFMTcDAuCtjNW54VzpERvoe7PBF9mYgmeta",
        "ico_price": 0.097,  # 이미지 Launch Price
        "launch_price": 0.097,
        "committed_usd": 14886359,
        "ico_raise_usd": 969420,  # 이미지 기준 $969,420
        "min_raise_usd": 300000,
        "allowance_usd": 50000,
        "sale_tokens": 10000000,
        "total_supply": 100000000,
        "ico_date": "2025-10-19",
        "tge_timestamp": None,
        "contributors": 2290,
        "oversubscription": 49.62,  # 14,886,359 / 300,000
        "is_permissionless": True,  # Permissionless Launch
        "description": "Permissionless yield generating privacy protocol",
        "category": "Privacy/LST"
    },
    "PAYSTREAM": {
        "name": "Paystream",
        "mint": "PAYZP1W3UmdEsNLJwmH61TNqACYJTvhXy8SCN4Tmeta",
        "ico_price": 0.075,  # 이미지 Launch Price
        "launch_price": 0.075,
        "committed_usd": 6149247,
        "ico_raise_usd": 750000,  # 이미지 기준 $750,000
        "min_raise_usd": 550000,
        "allowance_usd": 33500,
        "sale_tokens": 10000000,
        "total_supply": 30000000,
        "ico_date": "2025-10-27",
        "tge_timestamp": None,
        "contributors": 1837,
        "oversubscription": 11.18,  # 6,149,247 / 550,000
        "is_permissionless": True,  # Permissionless Launch
        "description": "Liquidity Optimizer For Solana",
        "category": "DeFi/Lending"
    },
    "SOLO": {
        "name": "Solomon",
        "mint": "SoLo9oxzLDpcq1dpqAgMwgce5WqkRDtNXK7EPnbmeta",
        "ico_price": 0.80,  # 이미지 Launch Price
        "launch_price": 0.80,
        "committed_usd": 102932673,
        "ico_raise_usd": 8000000,  # 이미지 기준 $8,000,000
        "min_raise_usd": 2000000,
        "allowance_usd": 100000,
        "sale_tokens": 10000000,
        "total_supply": 25800000,
        "ico_date": "2025-11-18",
        "tge_timestamp": None,
        "contributors": 6604,
        "oversubscription": 51.47,  # 102,932,673 / 2,000,000
        "is_permissionless": False,
        "description": "The composable dollar that always earns",
        "category": "Stablecoin/Yield"
    }
}

# ============================================
# API 함수들
# ============================================

@st.cache_data(ttl=90, show_spinner=False)
def fetch_dexscreener_token(mint_address: str) -> Dict:
    """DexScreener API로 토큰 데이터 조회"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            return {}
        
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
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_dexscreener_pair_candles(pair_address: str) -> List[Dict]:
    """
    DexScreener 페어의 OHLCV 캔들 데이터 가져오기
    (1분봉 기준, 최근 데이터)
    """
    try:
        # DexScreener Pairs 엔드포인트에서 차트 데이터
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # DexScreener는 직접 캔들 데이터를 제공하지 않음
            # pair 정보만 반환
            return data.get("pair", {})
        return {}
    except Exception:
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_geckoterminal_ohlcv(pool_address: str, timeframe: str = "minute", aggregate: int = 5) -> List[Dict]:
    """
    GeckoTerminal API로 OHLCV 데이터 가져오기 (무료)
    timeframe: minute, hour, day
    aggregate: 1, 5, 15 (분봉일 경우)
    """
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool_address}/ohlcv/{timeframe}"
        params = {
            "aggregate": aggregate,
            "limit": 1000,
            "currency": "usd"
        }
        headers = {"Accept": "application/json"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            ohlcv_list = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
            # 형식: [[timestamp, open, high, low, close, volume], ...]
            return ohlcv_list
        return []
    except Exception:
        return []


def get_price_at_timestamp(ohlcv_data: List, target_timestamp: int, tolerance_seconds: int = 300) -> Optional[float]:
    """
    OHLCV 데이터에서 특정 타임스탬프에 가장 가까운 캔들의 종가 반환
    ohlcv_data: [[timestamp, open, high, low, close, volume], ...]
    """
    if not ohlcv_data or not target_timestamp:
        return None
    
    closest_candle = None
    min_diff = float('inf')
    
    for candle in ohlcv_data:
        if len(candle) >= 5:
            candle_ts = candle[0]
            diff = abs(candle_ts - target_timestamp)
            if diff < min_diff and diff <= tolerance_seconds:
                min_diff = diff
                closest_candle = candle
    
    if closest_candle:
        return float(closest_candle[4])  # close price
    return None


def calculate_ath_atl_from_ohlcv(ohlcv_data: List) -> Tuple[Optional[float], Optional[float]]:
    """OHLCV 데이터에서 ATH/ATL 계산"""
    if not ohlcv_data:
        return None, None
    
    try:
        highs = [float(candle[2]) for candle in ohlcv_data if len(candle) >= 5 and candle[2]]
        lows = [float(candle[3]) for candle in ohlcv_data if len(candle) >= 5 and candle[3] and candle[3] > 0]
        
        ath = max(highs) if highs else None
        atl = min(lows) if lows else None
        
        return ath, atl
    except Exception:
        return None, None


def calculate_roi(price: Optional[float], ico_price: float) -> Tuple[Optional[float], Optional[float]]:
    """ROI 계산 (배수, 퍼센트)"""
    if price and ico_price and ico_price > 0:
        roi_x = price / ico_price
        roi_pct = (price - ico_price) / ico_price * 100
        return round(roi_x, 2), round(roi_pct, 2)
    return None, None


def safe_float(value: Any, default: float = 0) -> float:
    """안전하게 float 변환"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


# ============================================
# 메인 데이터 수집 함수
# ============================================

def get_all_token_data() -> pd.DataFrame:
    """모든 토큰 데이터 수집 및 DataFrame 생성"""
    records = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_tokens = len(METADAO_TOKENS)
    
    for idx, (symbol, info) in enumerate(METADAO_TOKENS.items()):
        status_text.text(f"📊 데이터 수집 중: {info['name']} ({idx+1}/{total_tokens})")
        progress_bar.progress((idx + 1) / total_tokens)
        
        mint = info["mint"]
        ico_price = info["ico_price"]
        tge_timestamp = info.get("tge_timestamp")
        
        # DexScreener 데이터 가져오기
        dex_data = fetch_dexscreener_token(mint)
        
        # 현재 가격
        current_price = safe_float(dex_data.get("priceUsd"))
        
        # 페어 주소 (OHLCV 조회용)
        pair_address = dex_data.get("pairAddress", "")
        
        # GeckoTerminal에서 OHLCV 데이터 가져오기 (5분봉)
        ohlcv_data = []
        if pair_address:
            ohlcv_data = fetch_geckoterminal_ohlcv(pair_address, "minute", 5)
        
        # ATH/ATL 계산
        ath_all, atl_all = calculate_ath_atl_from_ohlcv(ohlcv_data)
        
        # DexScreener에서 ATH/ATL 추정 (OHLCV 없을 경우 백업)
        if not ath_all and dex_data:
            # 현재가 기준 추정
            ath_all = current_price  # 최소한 현재가
        
        # ROI 계산
        roi_x, roi_pct = calculate_roi(current_price, ico_price)
        ath_roi_x, ath_roi_pct = calculate_roi(ath_all, ico_price)
        atl_roi_x, atl_roi_pct = calculate_roi(atl_all, ico_price)
        
        # TGE 기준 시간대별 ROI (5분, 15분, 30분, 60분)
        roi_5m_x, roi_5m_pct = None, None
        roi_15m_x, roi_15m_pct = None, None
        roi_30m_x, roi_30m_pct = None, None
        roi_60m_x, roi_60m_pct = None, None
        
        price_5m, price_15m, price_30m, price_60m = None, None, None, None
        
        if tge_timestamp and ohlcv_data:
            # TGE + 5분
            price_5m = get_price_at_timestamp(ohlcv_data, tge_timestamp + 300)
            roi_5m_x, roi_5m_pct = calculate_roi(price_5m, ico_price)
            
            # TGE + 15분
            price_15m = get_price_at_timestamp(ohlcv_data, tge_timestamp + 900)
            roi_15m_x, roi_15m_pct = calculate_roi(price_15m, ico_price)
            
            # TGE + 30분
            price_30m = get_price_at_timestamp(ohlcv_data, tge_timestamp + 1800)
            roi_30m_x, roi_30m_pct = calculate_roi(price_30m, ico_price)
            
            # TGE + 60분
            price_60m = get_price_at_timestamp(ohlcv_data, tge_timestamp + 3600)
            roi_60m_x, roi_60m_pct = calculate_roi(price_60m, ico_price)
        
        # 세일 정보
        sale_tokens = info["sale_tokens"]
        total_supply = info["total_supply"]
        sale_ratio = (sale_tokens / total_supply * 100) if total_supply else 0
        
        # 24h 변동
        price_change_24h = safe_float(dex_data.get("priceChange", {}).get("h24"))
        volume_24h = safe_float(dex_data.get("volume", {}).get("h24"))
        liquidity = safe_float(dex_data.get("liquidity", {}).get("usd"))
        
        # FDV & Market Cap
        fdv = current_price * total_supply if current_price and total_supply else 0
        market_cap = safe_float(dex_data.get("marketCap"))
        
        # 세일 물량 현재 가치
        sale_value_now = current_price * sale_tokens if current_price else 0
        ico_raise = info["ico_raise_usd"]
        profit_usd = sale_value_now - ico_raise if ico_raise else 0
        profit_pct = (profit_usd / ico_raise * 100) if ico_raise else 0
        
        # 새로운 크롤링 데이터 필드들
        committed_usd = info.get("committed_usd", ico_raise)
        min_raise_usd = info.get("min_raise_usd", ico_raise)
        allowance_usd = info.get("allowance_usd")
        contributors = info.get("contributors", 0)
        oversubscription = info.get("oversubscription", 1.0)
        is_permissionless = info.get("is_permissionless", False)
        launch_price = info.get("launch_price")
        
        # Launch ROI = 상장가 / ICO가 (5분 후 바로 매도 시 ROI)
        launch_roi_x, launch_roi_pct = None, None
        if launch_price and ico_price:
            launch_roi_x, launch_roi_pct = calculate_roi(launch_price, ico_price)
        
        records.append({
            # 기본 정보
            "심볼": symbol,
            "이름": info["name"],
            "카테고리": info["category"],
            "설명": info["description"],
            "Mint": mint,
            "Pair Address": pair_address,
            "ICO 날짜": info["ico_date"],
            "TGE Timestamp": tge_timestamp,
            "Permissionless": is_permissionless,
            
            # 펀드레이징 데이터
            "ICO 세일가": ico_price,
            "상장가": launch_price,
            "커밋 (USD)": committed_usd,
            "모금액 (USD)": ico_raise,
            "최소 목표 (USD)": min_raise_usd,
            "Allowance (USD)": allowance_usd,
            "참여 지갑": contributors,
            "청약배수": oversubscription,
            
            # 세일 할당량
            "세일 토큰": sale_tokens,
            "총 공급량": total_supply,
            "세일 비율 (%)": round(sale_ratio, 2),
            
            # 현재 시장 데이터
            "현재가": current_price,
            "24h 변동 (%)": price_change_24h,
            "24h 거래량": volume_24h,
            "유동성": liquidity,
            "시가총액": market_cap,
            "FDV": fdv,
            
            # ATH/ATL (전체 기간)
            "ATH": ath_all,
            "ATL": atl_all,
            
            # 현재 ROI (현재가/ICO가)
            "현재 ROI (x)": roi_x,
            "현재 ROI (%)": roi_pct,
            
            # Launch ROI (상장가/ICO가 = 5분 후 매도 시)
            "Launch ROI (x)": launch_roi_x,
            "Launch ROI (%)": launch_roi_pct,
            
            # ATH/ATL 기준 ROI
            "ATH ROI (x)": ath_roi_x,
            "ATH ROI (%)": ath_roi_pct,
            "ATL ROI (x)": atl_roi_x,
            "ATL ROI (%)": atl_roi_pct,
            
            # TGE 시간대별 가격
            "Price @ 5m": price_5m,
            "Price @ 15m": price_15m,
            "Price @ 30m": price_30m,
            "Price @ 60m": price_60m,
            
            # TGE 시간대별 ROI
            "ROI_5m (x)": roi_5m_x,
            "ROI_5m (%)": roi_5m_pct,
            "ROI_15m (x)": roi_15m_x,
            "ROI_15m (%)": roi_15m_pct,
            "ROI_30m (x)": roi_30m_x,
            "ROI_30m (%)": roi_30m_pct,
            "ROI_60m (x)": roi_60m_x,
            "ROI_60m (%)": roi_60m_pct,
            
            # 세일 물량 현재 가치
            "세일 현재 가치": sale_value_now,
            "손익 (USD)": profit_usd,
            "손익 (%)": round(profit_pct, 2)
        })
        
        # Rate limit 방지
        time.sleep(0.4)
    
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(records)


# ============================================
# UI 컴포넌트
# ============================================

def render_sidebar() -> Tuple[str, str, Tuple[str, bool]]:
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("⚙️ 설정")
        
        # 카테고리 필터
        categories = ["All"] + sorted(list(set(info["category"] for info in METADAO_TOKENS.values())))
        selected_category = st.selectbox("카테고리 필터", categories)
        
        # Launch Type 필터
        launch_types = ["All", "Featured (검증)", "Permissionless"]
        selected_launch_type = st.selectbox("런치 타입", launch_types, help="Featured: MetaDAO 팀 검증, Permissionless: 자유 런칭")
        
        # 정렬 옵션 (한글 컬럼명)
        sort_options = {
            "ROI (높은순)": ("현재 ROI (x)", False),
            "ROI (낮은순)": ("현재 ROI (x)", True),
            "Launch ROI (높은순)": ("Launch ROI (x)", False),
            "청약배수 (높은순)": ("청약배수", False),
            "참여자 (많은순)": ("참여 지갑", False),
            "ICO 날짜 (최신순)": ("ICO 날짜", False),
            "ICO 날짜 (오래된순)": ("ICO 날짜", True),
            "유동성 (높은순)": ("유동성", False),
            "거래량 (높은순)": ("24h 거래량", False),
            "모금액 (높은순)": ("모금액 (USD)", False),
            "커밋액 (높은순)": ("커밋 (USD)", False)
        }
        sort_by = st.selectbox("정렬 기준", list(sort_options.keys()))
        
        st.divider()
        
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        st.markdown("""
        ### 🏷️ 런치 타입
        - **Featured**: MetaDAO 검증 프로젝트
        - **Permissionless**: 누구나 런칭 가능
        """)
        
        return selected_category, selected_launch_type, sort_options[sort_by]


def render_overview(df: pd.DataFrame):
    """전체 요약"""
    st.header("📊 전체 요약")
    
    # 첫 번째 행
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_committed = df["커밋 (USD)"].sum()
        st.metric("총 커밋액", f"${total_committed:,.0f}")
    
    with col2:
        total_raised = df["모금액 (USD)"].sum()
        st.metric("총 모금액", f"${total_raised:,.0f}")
    
    with col3:
        valid_roi = df[df["현재 ROI (x)"].notna()]["현재 ROI (x)"]
        avg_roi = valid_roi.mean() if len(valid_roi) > 0 else 0
        st.metric("평균 ROI", f"{avg_roi:.2f}x")
    
    with col4:
        profitable = len(df[df["현재 ROI (x)"].notna() & (df["현재 ROI (x)"] >= 1)])
        total = len(df[df["현재 ROI (x)"].notna()])
        st.metric("수익 토큰", f"{profitable}/{total}")
    
    with col5:
        avg_oversubscription = df["청약배수"].mean()
        st.metric("평균 청약배수", f"{avg_oversubscription:.1f}x")
    
    # 두 번째 행
    col6, col7, col8, col9, col10 = st.columns(5)
    
    with col6:
        max_oversubscription = df.loc[df["청약배수"].idxmax()]
        st.metric("최고 청약배수", f"{max_oversubscription['심볼']} ({max_oversubscription['청약배수']:.0f}x)")
    
    with col7:
        total_volume = df["24h 거래량"].sum()
        st.metric("총 24h 거래량", f"${total_volume:,.0f}")
    
    with col8:
        total_liquidity = df["유동성"].sum()
        st.metric("총 유동성", f"${total_liquidity:,.0f}")
    
    with col9:
        featured = len(df[~df["Permissionless"]])
        permissionless = len(df[df["Permissionless"]])
        st.metric("Featured / Permissionless", f"{featured} / {permissionless}")
    
    with col10:
        # ATH ROI 최고 토큰
        if df["ATH ROI (x)"].notna().any():
            max_ath_roi = df.loc[df["ATH ROI (x)"].idxmax()]
            st.metric("최고 ATH ROI", f"{max_ath_roi['심볼']} ({max_ath_roi['ATH ROI (x)']:.1f}x)")


def format_number_short(val, prefix: str = "") -> str:
    """숫자를 K/M/B 단위로 포맷"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    
    if abs_val >= 1_000_000_000:
        return f"{sign}{prefix}{abs_val / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        return f"{sign}{prefix}{abs_val / 1_000_000:.2f}M"
    elif abs_val >= 1_000:
        return f"{sign}{prefix}{abs_val / 1_000:.2f}K"
    else:
        return f"{sign}{prefix}{abs_val:,.2f}"


def format_value(val, fmt_type: str = "number") -> str:
    """값 포맷팅"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    
    if fmt_type == "price":
        return f"${val:.4f}"
    elif fmt_type == "usd":
        return format_number_short(val, prefix="$")
    elif fmt_type == "roi_x":
        return f"{val:.2f}x"
    elif fmt_type == "pct":
        return f"{val:+.1f}%"
    elif fmt_type == "number":
        return format_number_short(val)
    return str(val)


def render_summary_table(df: pd.DataFrame):
    """요약 테이블"""
    st.header("📋 한눈에 보기")
    
    # 컬럼 순서: 심볼, 이름, ICO날짜, 모금액, 커밋USD, 청약배수, 참여지갑, ICO세일가, 현재가, 현재ROI, ATH ROI, ATL ROI, Liquidity, 카테고리
    display_cols = [
        "심볼", "이름", "ICO 날짜", 
        "모금액 (USD)", "커밋 (USD)", "청약배수", "참여 지갑",
        "ICO 세일가", "현재가", 
        "현재 ROI (x)", "ATH ROI (x)", "ATL ROI (x)",
        "유동성", "카테고리"
    ]
    
    # 존재하는 컬럼만 선택
    available_cols = [col for col in display_cols if col in df.columns]
    display_df = df[available_cols].copy()
    
    # ROI 컬럼에 통일된 스타일 적용
    roi_cols = [col for col in available_cols if "ROI" in col and "(x)" in col]
    styled = display_df.style.applymap(style_roi, subset=roi_cols)
    
    # 숫자 포맷 (K/M/B 단위)
    def fmt_short_usd(x):
        if pd.isna(x):
            return "N/A"
        return format_number_short(x, prefix="$")
    
    def fmt_short_num(x):
        if pd.isna(x):
            return "N/A"
        return format_number_short(x)
    
    format_dict = {
        "ICO 세일가": "${:.4f}",
        "현재가": lambda x: f"${x:.4f}" if pd.notna(x) else "N/A",
        "현재 ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ATH ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ATL ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "커밋 (USD)": fmt_short_usd,
        "모금액 (USD)": fmt_short_usd,
        "유동성": fmt_short_usd,
        "청약배수": "{:.1f}x",
        "참여 지갑": fmt_short_num
    }
    
    styled = styled.format(format_dict, na_rep="N/A")
    
    st.dataframe(styled, use_container_width=True, height=400)


def render_token_cards(df: pd.DataFrame):
    """토큰별 카드"""
    st.header("💰 토큰별 상세")
    
    cols = st.columns(2)
    
    for idx, (_, row) in enumerate(df.iterrows()):
        with cols[idx % 2]:
            # ROI 이모지
            roi_val = row.get("현재 ROI (x)")
            if roi_val and roi_val >= 2:
                emoji = "🚀"
            elif roi_val and roi_val >= 1:
                emoji = "✅"
            elif roi_val:
                emoji = "📉"
            else:
                emoji = "❓"
            
            # Permissionless 배지
            is_permissionless = row.get("Permissionless", False)
            badge = " 🔓" if is_permissionless else ""
            
            st.subheader(f"{emoji} {row['심볼']} - {row['이름']}{badge}")
            st.caption(f"{row['카테고리']} | {row['설명'][:50]}...")
            
            # 주요 메트릭
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                st.metric(
                    "현재가",
                    format_value(row.get("현재가"), "price"),
                    format_value(row.get("24h 변동 (%)"), "pct") if row.get("24h 변동 (%)") else None
                )
            with m2:
                st.metric("ROI", format_value(row.get("현재 ROI (x)"), "roi_x"))
            with m3:
                st.metric("청약배수", f"{row.get('청약배수', 0):.1f}x")
            with m4:
                st.metric("참여자", format_value(row.get("참여 지갑"), "number"))
            
            # 상세 정보 확장
            with st.expander("📊 상세 정보"):
                tab1, tab2, tab3, tab4 = st.tabs(["펀드레이징", "가격 데이터", "TGE 시간대별 ROI", "세일 정보"])
                
                with tab1:
                    is_permissionless = row.get("Permissionless", False)
                    launch_type = "🔓 Permissionless" if is_permissionless else "✅ Featured (검증)"
                    st.markdown(f"""
                    | 항목 | 값 |
                    |------|-----|
                    | 런치 타입 | {launch_type} |
                    | 커밋액 | {format_value(row.get("커밋 (USD)"), "usd")} |
                    | 실제 모금액 | {format_value(row.get("모금액 (USD)"), "usd")} |
                    | 최소 모금 목표 | {format_value(row.get("최소 목표 (USD)"), "usd")} |
                    | 청약배수 | {row.get("청약배수", 0):.1f}x ({row.get("청약배수", 0)*100:.0f}%) |
                    | 참여자 | {format_value(row.get("참여 지갑"), "number")} |
                    | 월 Allowance | {format_value(row.get("Allowance (USD)"), "usd")} |
                    | ICO 가격 | {format_value(row.get("ICO 세일가"), "price")} |
                    | 상장가 | {format_value(row.get("상장가"), "price")} |
                    | Launch ROI | {format_value(row.get("Launch ROI (x)"), "roi_x")} |
                    """)
                
                with tab2:
                    st.markdown(f"""
                    | 항목 | 값 |
                    |------|-----|
                    | 현재가 | {format_value(row.get("현재가"), "price")} |
                    | ATH | {format_value(row.get("ATH"), "price")} |
                    | ATL | {format_value(row.get("ATL"), "price")} |
                    | 현재 ROI | {format_value(row.get("현재 ROI (x)"), "roi_x")} |
                    | Launch ROI | {format_value(row.get("Launch ROI (x)"), "roi_x")} |
                    | ATH ROI | {format_value(row.get("ATH ROI (x)"), "roi_x")} |
                    | ATL ROI | {format_value(row.get("ATL ROI (x)"), "roi_x")} |
                    | 24h 거래량 | {format_value(row.get("24h 거래량"), "usd")} |
                    | 유동성 | {format_value(row.get("유동성"), "usd")} |
                    | FDV | {format_value(row.get("FDV"), "usd")} |
                    """)
                
                with tab3:
                    # Launch Price 기반 ROI (5분 후 매도)
                    launch_roi = row.get("Launch ROI (x)")
                    launch_roi_pct = row.get("Launch ROI (%)")
                    if launch_roi:
                        st.markdown(f"""
                        **🚀 상장 직후 (5분 내) 매도 시 ROI**
                        
                        | 시점 | 가격 | ROI (x) | ROI (%) |
                        |------|------|---------|---------|
                        | 상장가 (5분) | {format_value(row.get("상장가"), "price")} | {format_value(launch_roi, "roi_x")} | {format_value(launch_roi_pct, "pct")} |
                        
                        *상장가 = ICO 세일가로부터의 초기 가격*
                        """)
                    else:
                        st.info("상장가 데이터가 없습니다.")
                    
                    # TGE timestamp 기반 OHLCV ROI (있는 경우)
                    if row.get("TGE Timestamp"):
                        st.markdown(f"""
                        **📊 TGE 시간대별 ROI (OHLCV 기반)**
                        
                        | 시점 | 가격 | ROI (x) | ROI (%) |
                        |------|------|---------|---------|
                        | +5분 | {format_value(row.get("Price @ 5m"), "price")} | {format_value(row.get("ROI_5m (x)"), "roi_x")} | {format_value(row.get("ROI_5m (%)"), "pct")} |
                        | +15분 | {format_value(row.get("Price @ 15m"), "price")} | {format_value(row.get("ROI_15m (x)"), "roi_x")} | {format_value(row.get("ROI_15m (%)"), "pct")} |
                        | +30분 | {format_value(row.get("Price @ 30m"), "price")} | {format_value(row.get("ROI_30m (x)"), "roi_x")} | {format_value(row.get("ROI_30m (%)"), "pct")} |
                        | +60분 | {format_value(row.get("Price @ 60m"), "price")} | {format_value(row.get("ROI_60m (x)"), "roi_x")} | {format_value(row.get("ROI_60m (%)"), "pct")} |
                        """)
                
                with tab4:
                    st.markdown(f"""
                    | 항목 | 값 |
                    |------|-----|
                    | 세일 토큰 수 | {format_value(row.get("세일 토큰"), "number")} |
                    | 총 공급량 | {format_value(row.get("총 공급량"), "number")} |
                    | 세일 비율 | {row.get("세일 비율 (%)", 0):.1f}% |
                    | ICO 날짜 | {row.get("ICO 날짜", "N/A")} |
                    | 현재 세일 가치 | {format_value(row.get("세일 현재 가치"), "usd")} |
                    | 손익 | {format_value(row.get("손익 (USD)"), "usd")} ({row.get("손익 (%)", 0):+.1f}%) |
                    """)
                
                # 링크
                mint = row.get("Mint", "")
                st.markdown(f"[🔗 Solscan](https://solscan.io/token/{mint}) | [📊 DexScreener](https://dexscreener.com/solana/{mint}) | [🦎 GeckoTerminal](https://www.geckoterminal.com/solana/pools/{row.get('Pair Address', '')})")
            
            st.divider()


def render_roi_chart(df: pd.DataFrame):
    """ROI 비교 차트"""
    st.subheader("📈 현재 ROI vs ATH ROI")
    
    fig = go.Figure()
    
    # 현재 ROI
    fig.add_trace(go.Bar(
        name="현재 ROI",
        x=df["심볼"],
        y=df["현재 ROI (x)"].fillna(0),
        marker_color=COLORS["chart_current_roi"],
        text=df["현재 ROI (x)"].apply(lambda x: f"{x:.2f}x" if x else "N/A"),
        textposition="outside"
    ))
    
    # Launch ROI (5분)
    fig.add_trace(go.Bar(
        name="Launch ROI (5분)",
        x=df["심볼"],
        y=df["Launch ROI (x)"].fillna(0),
        marker_color=COLORS["chart_launch_roi"],
        text=df["Launch ROI (x)"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else ""),
        textposition="outside"
    ))
    
    # ATH ROI
    fig.add_trace(go.Bar(
        name="ATH ROI",
        x=df["심볼"],
        y=df["ATH ROI (x)"].fillna(0),
        marker_color=COLORS["chart_ath_roi"],
        text=df["ATH ROI (x)"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else ""),
        textposition="outside"
    ))
    
    fig.add_hline(y=1, line_dash="dash", line_color=COLORS["text_secondary"], 
                  annotation_text="손익분기점", annotation_font_color=COLORS["text_secondary"])
    
    fig.update_layout(
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    fig = apply_dark_layout(fig, height=450)
    st.plotly_chart(fig, use_container_width=True)


def render_tge_roi_chart(df: pd.DataFrame):
    """TGE 시간대별 ROI 비교 차트 - Launch ROI 기반"""
    st.subheader("⏱️ 상장 직후 매도 ROI (Launch ROI)")
    
    # Launch ROI가 있는 토큰
    has_launch = df[df["Launch ROI (x)"].notna()]
    
    if len(has_launch) == 0:
        st.info("상장가 데이터가 없습니다.")
        return
    
    # Launch ROI 차트
    fig = px.bar(
        has_launch.sort_values("Launch ROI (x)", ascending=True),
        x="Launch ROI (x)",
        y="심볼",
        orientation='h',
        color="Launch ROI (x)",
        color_continuous_scale=COLOR_SCALE_ROI,
        title="상장 직후 (5분 내) 매도 시 ROI"
    )
    
    fig.add_vline(x=1, line_dash="dash", line_color=COLORS["text_secondary"], 
                  annotation_text="손익분기점", annotation_font_color=COLORS["text_secondary"])
    
    fig.update_layout(
        xaxis_title="ROI (x)",
        yaxis_title=""
    )
    
    fig = apply_dark_layout(fig, height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_allocation_chart(df: pd.DataFrame):
    """세일 할당량 분석 차트"""
    st.subheader("📊 세일 할당량 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 커밋액 vs 실제 모금액 비교
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='커밋액 (Committed)',
            x=df["심볼"],
            y=df["커밋 (USD)"],
            marker_color=COLORS["chart_ath_roi"]  # 노란색
        ))
        fig.add_trace(go.Bar(
            name='실제 모금액 (Raised)',
            x=df["심볼"],
            y=df["모금액 (USD)"],
            marker_color=COLORS["positive"]  # 초록색
        ))
        fig.update_layout(
            title="커밋액 vs 실제 모금액",
            barmode='group'
        )
        fig = apply_dark_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 세일 비율 비교
        fig = px.bar(
            df,
            x="심볼",
            y="세일 비율 (%)",
            color="현재 ROI (x)",
            color_continuous_scale=COLOR_SCALE_ROI,
            title="세일 물량 비율 (% of Total Supply)"
        )
        fig = apply_dark_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)


def render_oversubscription_chart(df: pd.DataFrame):
    """청약배수 및 참여자 차트"""
    st.subheader("📊 청약배수 & 참여자 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 청약배수 차트 - 숫자 표시
        sorted_df = df.sort_values("청약배수", ascending=True)
        fig = go.Figure()
        
        # Featured vs Permissionless 분리
        for is_perm, color, name in [(False, COLORS["chart_featured"], "Featured"), 
                                      (True, COLORS["chart_permissionless"], "Permissionless")]:
            mask = sorted_df["Permissionless"] == is_perm
            subset = sorted_df[mask]
            if len(subset) > 0:
                fig.add_trace(go.Bar(
                    name=name,
                    y=subset["심볼"],
                    x=subset["청약배수"],
                    orientation='h',
                    marker_color=color,
                    text=subset["청약배수"].apply(lambda x: f"{x:.1f}x"),
                    textposition="outside",
                    textfont=dict(color=COLORS["text_primary"], size=11)
                ))
        
        fig.update_layout(
            title="토큰별 청약배수 (Oversubscription)",
            xaxis_title="청약배수 (x)",
            yaxis_title="",
            barmode='group'
        )
        # 참조선 추가
        fig.add_vline(x=10, line_dash="dash", line_color=COLORS["accent_warning"], 
                      annotation_text="10x", annotation_position="top right",
                      annotation_font_color=COLORS["accent_warning"])
        fig.add_vline(x=50, line_dash="dash", line_color=COLORS["negative"],
                      annotation_text="50x", annotation_position="top right",
                      annotation_font_color=COLORS["negative"])
        fig = apply_dark_layout(fig, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 참여자 수 차트 - 숫자 표시
        sorted_df = df.sort_values("참여 지갑", ascending=True)
        fig = go.Figure()
        
        for is_perm, color, name in [(False, COLORS["chart_featured"], "Featured"), 
                                      (True, COLORS["chart_permissionless"], "Permissionless")]:
            mask = sorted_df["Permissionless"] == is_perm
            subset = sorted_df[mask]
            if len(subset) > 0:
                fig.add_trace(go.Bar(
                    name=name,
                    y=subset["심볼"],
                    x=subset["참여 지갑"],
                    orientation='h',
                    marker_color=color,
                    text=subset["참여 지갑"].apply(lambda x: format_number_short(x)),
                    textposition="outside",
                    textfont=dict(color=COLORS["text_primary"], size=11)
                ))
        
        fig.update_layout(
            title="토큰별 참여자 수 (Contributors)",
            xaxis_title="참여자 수",
            yaxis_title="",
            barmode='group'
        )
        fig = apply_dark_layout(fig, height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_profit_simulation(df: pd.DataFrame):
    """투자 시뮬레이션 (토큰 선택 + 실제 할당률)"""
    st.header("💵 투자 시뮬레이션")
    
    # 두 가지 모드
    mode = st.radio("시뮬레이션 모드", ["개별 토큰 분석", "전체 토큰 비교"], horizontal=True)
    
    if mode == "개별 토큰 분석":
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 토큰 선택
            token_options = df["심볼"].tolist()
            selected_token = st.selectbox("토큰 선택", token_options, help="분석할 토큰을 선택하세요")
            
            # 선택된 토큰 데이터
            token_data = df[df["심볼"] == selected_token].iloc[0]
            
            # 토큰 정보 표시
            st.markdown(f"### {selected_token} - {token_data['이름']}")
            
            # 할당률 계산 (Raised / Committed)
            committed = token_data.get("커밋 (USD)", 0)
            raised = token_data.get("모금액 (USD)", 0)
            if committed > 0:
                actual_allocation_rate = (raised / committed) * 100
            else:
                actual_allocation_rate = 100
            
            st.info(f"""
            **세일 당시 할당률: {actual_allocation_rate:.2f}%**
            - 총 커밋: ${committed:,.0f}
            - 실제 모금: ${raised:,.0f}
            - 참여자: {token_data.get('참여 지갑', 0):,}명
            - 청약배수: {token_data.get('청약배수', 0):.1f}x
            """)
            
            # 투자금 입력
            investment = st.number_input(
                "참여 금액 (USD)",
                min_value=10,
                max_value=1000000,
                value=1000,
                step=100
            )
            
            # 실제 배정 금액
            effective_investment = investment * (actual_allocation_rate / 100)
            st.success(f"**실제 배정: ${effective_investment:,.2f}** (나머지 ${investment - effective_investment:,.2f} 환불)")
        
        with col2:
            ico_price = token_data.get("ICO 세일가", 0)
            current_price = token_data.get("현재가", 0)
            launch_price = token_data.get("상장가")
            
            if ico_price > 0 and effective_investment > 0:
                tokens_received = effective_investment / ico_price
                
                st.markdown("### 📊 수익 분석")
                
                # 가격별 ROI 테이블
                price_data = []
                
                # 현재가 기준
                if current_price:
                    current_value = tokens_received * current_price
                    current_profit = current_value - effective_investment
                    current_roi = (current_price / ico_price - 1) * 100
                    price_data.append({
                        "시점": "🔵 현재",
                        "가격": f"${current_price:.4f}",
                        "가치": f"${current_value:,.2f}",
                        "손익": f"${current_profit:+,.2f}",
                        "ROI": f"{current_roi:+.1f}%"
                    })
                
                # 상장가 기준 (5분 후 매도 가정)
                if launch_price:
                    launch_value = tokens_received * launch_price
                    launch_profit = launch_value - effective_investment
                    launch_roi = (launch_price / ico_price - 1) * 100
                    price_data.append({
                        "시점": "⚡ 상장가 (5분)",
                        "가격": f"${launch_price:.4f}",
                        "가치": f"${launch_value:,.2f}",
                        "손익": f"${launch_profit:+,.2f}",
                        "ROI": f"{launch_roi:+.1f}%"
                    })
                
                # ATH 기준
                ath = token_data.get("ATH")
                if ath:
                    ath_value = tokens_received * ath
                    ath_profit = ath_value - effective_investment
                    ath_roi = (ath / ico_price - 1) * 100
                    price_data.append({
                        "시점": "🚀 ATH",
                        "가격": f"${ath:.4f}",
                        "가치": f"${ath_value:,.2f}",
                        "손익": f"${ath_profit:+,.2f}",
                        "ROI": f"{ath_roi:+.1f}%"
                    })
                
                # ATL 기준
                atl = token_data.get("ATL")
                if atl:
                    atl_value = tokens_received * atl
                    atl_profit = atl_value - effective_investment
                    atl_roi = (atl / ico_price - 1) * 100
                    price_data.append({
                        "시점": "📉 ATL",
                        "가격": f"${atl:.4f}",
                        "가치": f"${atl_value:,.2f}",
                        "손익": f"${atl_profit:+,.2f}",
                        "ROI": f"{atl_roi:+.1f}%"
                    })
                
                if price_data:
                    price_df = pd.DataFrame(price_data)
                    st.dataframe(price_df, use_container_width=True, hide_index=True)
                
                # 요약 메트릭
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("받은 토큰", f"{tokens_received:,.2f} {selected_token}")
                with m2:
                    if current_price:
                        st.metric("현재 가치", f"${current_value:,.2f}", f"{current_roi:+.1f}%")
                with m3:
                    if launch_price:
                        st.metric("5분 매도 시", f"${launch_value:,.2f}", f"{launch_roi:+.1f}%")
    
    else:
        # 전체 토큰 비교 모드 (기존 로직)
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            investment = st.number_input(
                "투자금액 (USD)",
                min_value=10,
                max_value=1000000,
                value=1000,
                step=100,
                help="각 ICO에 참여한 금액"
            )
            
            apply_allocation = st.checkbox("실제 할당률 적용", value=True,
                                           help="청약배수에 따른 실제 할당 비율 적용")
        
        with col2:
            sim_data = []
            for _, row in df.iterrows():
                current_price = row.get("현재가")
                ico_price = row.get("ICO 세일가")
                launch_price = row.get("상장가")
                
                # 할당률 계산
                committed = row.get("커밋 (USD)", 0)
                raised = row.get("모금액 (USD)", 0)
                if apply_allocation and committed > 0:
                    allocation_rate = raised / committed
                else:
                    allocation_rate = 1.0
                
                effective_inv = investment * allocation_rate
                
                if current_price and ico_price and ico_price > 0:
                    tokens_bought = effective_inv / ico_price
                    current_value = tokens_bought * current_price
                    profit = current_value - effective_inv
                    roi_pct = (current_price / ico_price - 1) * 100
                    
                    # 5분 (상장가) ROI
                    launch_roi = None
                    if launch_price:
                        launch_roi = (launch_price / ico_price - 1) * 100
                    
                    sim_data.append({
                        "토큰": row["심볼"],
                        "할당률": f"{allocation_rate*100:.1f}%",
                        "실제 투자": effective_inv,
                        "받은 토큰": tokens_bought,
                        "현재 가치": current_value,
                        "손익": profit,
                        "현재 ROI": roi_pct,
                        "5분 ROI": launch_roi
                    })
            
            if sim_data:
                sim_df = pd.DataFrame(sim_data)
                
                # 바 차트 - 현재 ROI vs 5분 ROI 비교
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='현재 ROI (%)',
                    x=sim_df["토큰"],
                    y=sim_df["현재 ROI"],
                    marker_color=COLORS["chart_current_roi"]
                ))
                fig.add_trace(go.Bar(
                    name='5분 ROI (%)',
                    x=sim_df["토큰"],
                    y=sim_df["5분 ROI"].fillna(0),
                    marker_color=COLORS["chart_launch_roi"]
                ))
                fig.update_layout(
                    title=f"${investment:,.0f} 투자 시 ROI 비교 (현재 vs 상장 5분)",
                    barmode='group'
                )
                fig.add_hline(y=0, line_dash="dash", line_color=COLORS["text_secondary"])
                fig = apply_dark_layout(fig, height=350)
                st.plotly_chart(fig, use_container_width=True)
                
                # 테이블
                st.dataframe(
                    sim_df.style.format({
                        "실제 투자": "${:,.2f}",
                        "받은 토큰": "{:,.2f}",
                        "현재 가치": "${:,.2f}",
                        "손익": "${:+,.2f}",
                        "현재 ROI": "{:+.1f}%",
                        "5분 ROI": lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A"
                    }),
                    use_container_width=True
                )
                
                # 총합
                total_invested = sim_df["실제 투자"].sum()
                total_value = sim_df["현재 가치"].sum()
                total_profit = sim_df["손익"].sum()
                
                st.markdown(f"""
                **전체 토큰 포트폴리오 (할당률 적용):**
                - 총 실제 투자: ${total_invested:,.0f}
                - 현재 총 가치: ${total_value:,.0f}  
                - 총 손익: **${total_profit:+,.0f}** ({total_profit/total_invested*100:+.1f}%)
                """)


def render_raw_data(df: pd.DataFrame):
    """원본 데이터"""
    st.header("📥 원본 데이터")
    
    # 표시할 주요 컬럼 선택 (TGE Timestamp 제외, 세일가로 대체)
    main_cols = [
        "심볼", "이름", "카테고리", "ICO 날짜",
        "ICO 세일가", "현재가", "ATH", "ATL",
        "모금액 (USD)", "커밋 (USD)", "청약배수", "참여 지갑",
        "현재 ROI (x)", "ATH ROI (x)", "ATL ROI (x)",
        "유동성", "시가총액", "FDV", "24h 거래량",
        "세일 토큰", "총 공급량", "세일 비율 (%)"
    ]
    
    # 존재하는 컬럼만 선택
    available_cols = [col for col in main_cols if col in df.columns]
    display_df = df[available_cols].copy()
    
    # K/M/B 포맷 적용
    def fmt_short_usd(x):
        if pd.isna(x):
            return "N/A"
        return format_number_short(x, prefix="$")
    
    def fmt_short_num(x):
        if pd.isna(x):
            return "N/A"
        return format_number_short(x)
    
    format_dict = {
        "ICO 세일가": "${:.4f}",
        "현재가": lambda x: f"${x:.4f}" if pd.notna(x) else "N/A",
        "ATH": lambda x: f"${x:.4f}" if pd.notna(x) else "N/A",
        "ATL": lambda x: f"${x:.4f}" if pd.notna(x) else "N/A",
        "모금액 (USD)": fmt_short_usd,
        "커밋 (USD)": fmt_short_usd,
        "유동성": fmt_short_usd,
        "시가총액": fmt_short_usd,
        "FDV": fmt_short_usd,
        "24h 거래량": fmt_short_usd,
        "세일 토큰": fmt_short_num,
        "총 공급량": fmt_short_num,
        "청약배수": "{:.1f}x",
        "참여 지갑": fmt_short_num,
        "현재 ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ATH ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ATL ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "세일 비율 (%)": "{:.1f}%"
    }
    
    styled = display_df.style.format(format_dict, na_rep="N/A")
    st.dataframe(styled, use_container_width=True, height=400)
    
    # CSV 다운로드 (원본 숫자 포맷)
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 CSV 다운로드",
        data=csv,
        file_name=f"metadao_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


# ============================================
# 메인 함수
# ============================================

def main():
    # 그라데이션 타이틀 (로켓 이모지는 그대로, 글씨만 그라데이션)
    st.markdown("""
    <h1 style='margin-bottom: 0;'>
        <span style='font-size: 1em;'>🚀</span> <span style='background: linear-gradient(90deg, #E91E8C, #FF6B9D, #A855F7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;'>MetaDAO ICO 토큰 분석 대시보드</span>
    </h1>
    """, unsafe_allow_html=True)
    st.caption("MetaDAO 런치패드 ICO 8개 토큰 상세 분석 | MetaDAO.fi + DexScreener + GeckoTerminal API")
    
    # 사이드바
    selected_category, selected_launch_type, (sort_col, sort_asc) = render_sidebar()
    
    # 데이터 로딩
    with st.spinner("데이터를 불러오는 중..."):
        df = get_all_token_data()
    
    # API 실패 시 데모 데이터
    if df["현재가"].isna().all() or df["현재가"].sum() == 0:
        st.warning("⚠️ API에서 실시간 데이터를 가져올 수 없습니다. 데모 데이터를 표시합니다.")
        demo_prices = {
            "MTNC": 0.60, "OMFG": 0.87, "UMBRA": 1.96, "AVICI": 5.43,
            "LOYAL": 0.33, "ZKLSOL": 0.08, "PAYSTREAM": 0.05, "SOLO": 1.21
        }
        for idx, row in df.iterrows():
            symbol = row["심볼"]
            if symbol in demo_prices:
                df.at[idx, "현재가"] = demo_prices[symbol]
                roi_x, roi_pct = calculate_roi(demo_prices[symbol], row["ICO 세일가"])
                df.at[idx, "현재 ROI (x)"] = roi_x
                df.at[idx, "현재 ROI (%)"] = roi_pct
    
    # 카테고리 필터링
    if selected_category != "All":
        df = df[df["카테고리"] == selected_category]
    
    # 런치 타입 필터링
    if selected_launch_type == "Featured (검증)":
        df = df[~df["Permissionless"]]
    elif selected_launch_type == "Permissionless":
        df = df[df["Permissionless"]]
    
    # 정렬
    df = df.sort_values(sort_col, ascending=sort_asc, na_position='last')
    
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
        render_oversubscription_chart(df)
        render_allocation_chart(df)
    
    with tab4:
        render_profit_simulation(df)
    
    with tab5:
        render_raw_data(df)
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.85em;'>
    Built by <a href='https://x.com/alfy' target='_blank' style='color: #E91E8C; text-decoration: none;'>@alfy</a>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
