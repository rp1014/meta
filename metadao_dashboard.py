"""
MetaDAO ICO 토큰 분석 대시보드
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
        "ico_price": 0.575,  # $5.75M / 10M tokens
        "launch_price": 0.575,
        "committed_usd": 5750000,
        "ico_raise_usd": 5750000,
        "min_raise_usd": 5750000,
        "allowance_usd": None,
        "sale_tokens": 10000000,
        "total_supply": 25000000,
        "ico_date": "2025-04-09",
        "tge_timestamp": None,
        "contributors": 1931,
        "oversubscription": 1.0,
        "is_permissionless": False,
        "description": "Futarchy 기반 투자 펀드 (첫 번째 MetaDAO 프로젝트)",
        "category": "Investment Fund"
    },
    "OMFG": {
        "name": "Omnipair",
        "mint": "omfgRBnxHsNJh6YeGbGAmWenNkenzsXyBXm3WDhmeta",
        "ico_price": 0.03,  # $300K / 10M tokens
        "launch_price": 0.03,
        "committed_usd": 300000,
        "ico_raise_usd": 300000,
        "min_raise_usd": 300000,
        "allowance_usd": None,
        "sale_tokens": 10000000,
        "total_supply": 12000000,
        "ico_date": "2025-07-28",
        "tge_timestamp": None,
        "contributors": 321,
        "oversubscription": 1.0,
        "is_permissionless": False,
        "description": "탈중앙화 트레이딩 & 렌딩 프로토콜 (Oracle-less)",
        "category": "DeFi"
    },
    "UMBRA": {
        "name": "Umbra",
        "mint": "PRVT6TB7uss3FrUd2D9xs2zqDBsa3GbMJMwCQsgmeta",
        "ico_price": 0.075,
        "launch_price": 0.30,  # 상장가는 ICO 가격의 4배
        "committed_usd": 154943746,
        "ico_raise_usd": 750000,  # 팀이 $750K만 수령
        "min_raise_usd": 750000,
        "allowance_usd": 34091,
        "sale_tokens": 10000000,
        "total_supply": 28500000,
        "ico_date": "2025-10-06",
        "tge_timestamp": None,
        "contributors": 10519,
        "oversubscription": 206.59,  # 20,659%
        "is_permissionless": False,
        "description": "Solana 프라이버시 프로토콜 (Arcium 기반)",
        "category": "Privacy"
    },
    "AVICI": {
        "name": "Avici",
        "mint": "BANKJmvhT8tiJRsBSS1n2HryMBPvT5Ze4HU95DUAmeta",
        "ico_price": 0.35,
        "launch_price": 0.43,  # ICODrops 기준 상장가
        "committed_usd": 34230976,
        "ico_raise_usd": 3500000,  # 팀이 $3.5M만 수령 (89.8% 환불)
        "min_raise_usd": 2000000,
        "allowance_usd": 100000,
        "sale_tokens": 10000000,
        "total_supply": 100000000,
        "ico_date": "2025-10-14",
        "tge_timestamp": None,
        "contributors": 7352,
        "oversubscription": 17.12,  # 1,712%
        "is_permissionless": False,
        "description": "크립토 네오뱅크 (Visa 카드, 자기수탁)",
        "category": "Payments"
    },
    "LOYAL": {
        "name": "Loyal",
        "mint": "LYLikzBQtpa9ZgVrJsqYGQpR3cC1WMJrBHaXGrQmeta",
        "ico_price": 0.05,
        "launch_price": None,
        "committed_usd": 75898233,
        "ico_raise_usd": 2500000,  # 추정 (팀이 적정 금액만 수령)
        "min_raise_usd": 500000,
        "allowance_usd": 60000,
        "sale_tokens": 10000000,
        "total_supply": 20976923,
        "ico_date": "2025-10-18",
        "tge_timestamp": None,
        "contributors": 5058,
        "oversubscription": 151.80,  # 15,180%
        "is_permissionless": True,  # Permissionless Launch
        "description": "탈중앙화 AI 추론 프로토콜 (MagicBlock & Arcium)",
        "category": "AI/Privacy"
    },
    "ZKLSOL": {
        "name": "ZKLSOL",
        "mint": "ZKFHiLAfAFMTcDAuCtjNW54VzpERvoe7PBF9mYgmeta",
        "ico_price": 0.097,  # 상장가 기준 (크롤링)
        "launch_price": 0.097,
        "committed_usd": 14886359,
        "ico_raise_usd": 969420,  # 실제 모금액
        "min_raise_usd": 300000,
        "allowance_usd": 50000,
        "sale_tokens": 10000000,
        "total_supply": 100000000,
        "ico_date": "2025-10-19",
        "tge_timestamp": None,
        "contributors": 2290,
        "oversubscription": 49.62,  # 4,962%
        "is_permissionless": True,  # Permissionless Launch
        "description": "프라이버시 + LST 스테이킹 (Zero-Knowledge)",
        "category": "Privacy/LST"
    },
    "PAYSTREAM": {
        "name": "Paystream",
        "mint": "PAYZP1W3UmdEsNLJwmH61TNqACYJTvhXy8SCN4Tmeta",
        "ico_price": 0.075,  # 상장가 기준 (크롤링)
        "launch_price": 0.075,
        "committed_usd": 6149247,
        "ico_raise_usd": 750000,  # 실제 모금액
        "min_raise_usd": 550000,
        "allowance_usd": 33500,
        "sale_tokens": 10000000,
        "total_supply": 30000000,
        "ico_date": "2025-10-27",
        "tge_timestamp": None,
        "contributors": 1837,
        "oversubscription": 11.18,  # 1,118%
        "is_permissionless": True,  # Permissionless Launch
        "description": "P2P 렌딩 & 유동성 최적화 프로토콜",
        "category": "DeFi/Lending"
    },
    "SOLO": {
        "name": "Solomon",
        "mint": "SoLo9oxzLDpcq1dpqAgMwgce5WqkRDtNXK7EPnbmeta",
        "ico_price": 0.80,  # 크롤링 기준 Launch Price
        "launch_price": 0.80,
        "committed_usd": 102932673,  # $102.9M 커밋
        "ico_raise_usd": 8000000,  # 실제 $8M 모금
        "min_raise_usd": 2000000,
        "allowance_usd": 100000,
        "sale_tokens": 10000000,
        "total_supply": 25800000,
        "ico_date": "2025-11-18",
        "tge_timestamp": None,
        "contributors": 6604,
        "oversubscription": 51.47,  # 5,147%
        "is_permissionless": False,
        "description": "수익형 스테이블코인 (USDv/sUSDv, 베이시스 트레이드)",
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
        
        # 상장가 대비 ROI (있는 경우)
        launch_roi_x, launch_roi_pct = None, None
        if launch_price and current_price:
            launch_roi_x, launch_roi_pct = calculate_roi(current_price, launch_price)
        
        records.append({
            # 기본 정보
            "Symbol": symbol,
            "Name": info["name"],
            "Category": info["category"],
            "Description": info["description"],
            "Mint": mint,
            "Pair Address": pair_address,
            "ICO Date": info["ico_date"],
            "TGE Timestamp": tge_timestamp,
            "Is Permissionless": is_permissionless,
            
            # 펀드레이징 데이터
            "ICO Price": ico_price,
            "Launch Price": launch_price,
            "Committed (USD)": committed_usd,
            "Raised (USD)": ico_raise,
            "Min Raise (USD)": min_raise_usd,
            "Allowance (USD)": allowance_usd,
            "Contributors": contributors,
            "Oversubscription": oversubscription,
            
            # 세일 할당량
            "Sale Tokens": sale_tokens,
            "Total Supply": total_supply,
            "Sale % of Supply": round(sale_ratio, 2),
            
            # 현재 시장 데이터
            "Current Price": current_price,
            "24h Change (%)": price_change_24h,
            "24h Volume": volume_24h,
            "Liquidity": liquidity,
            "Market Cap": market_cap,
            "FDV": fdv,
            
            # ATH/ATL (전체 기간)
            "ATH": ath_all,
            "ATL": atl_all,
            
            # 현재 ROI
            "ROI (x)": roi_x,
            "ROI (%)": roi_pct,
            
            # 상장가 대비 ROI
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
            "Sale Value Now": sale_value_now,
            "Profit (USD)": profit_usd,
            "Profit (%)": round(profit_pct, 2)
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
        
        # 정렬 옵션
        sort_options = {
            "ROI (높은순)": ("ROI (x)", False),
            "ROI (낮은순)": ("ROI (x)", True),
            "청약배수 (높은순)": ("Oversubscription", False),
            "참여자 (많은순)": ("Contributors", False),
            "ICO 날짜 (최신순)": ("ICO Date", False),
            "ICO 날짜 (오래된순)": ("ICO Date", True),
            "유동성 (높은순)": ("Liquidity", False),
            "거래량 (높은순)": ("24h Volume", False),
            "모금액 (높은순)": ("Raised (USD)", False),
            "커밋액 (높은순)": ("Committed (USD)", False)
        }
        sort_by = st.selectbox("정렬 기준", list(sort_options.keys()))
        
        st.divider()
        
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        st.markdown("""
        ### 📊 데이터 소스
        - MetaDAO.fi (크롤링)
        - DexScreener API
        - GeckoTerminal API
        
        ### 🏷️ 런치 타입
        - **Featured**: MetaDAO 검증 프로젝트
        - **Permissionless**: 누구나 런칭 가능
        
        ### 📝 TGE 시간대별 ROI
        토큰 메타데이터에 `tge_timestamp`를  
        입력하면 자동 계산됩니다.
        
        ### ⚠️ 주의
        - 실시간 데이터 지연 가능
        - ATH/ATL은 조회 기간 한정
        - 투자 조언 아님, DYOR!
        """)
        
        return selected_category, selected_launch_type, sort_options[sort_by]


def render_overview(df: pd.DataFrame):
    """전체 요약"""
    st.header("📊 전체 요약")
    
    # 첫 번째 행
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_committed = df["Committed (USD)"].sum()
        st.metric("총 커밋액", f"${total_committed:,.0f}")
    
    with col2:
        total_raised = df["Raised (USD)"].sum()
        st.metric("총 모금액", f"${total_raised:,.0f}")
    
    with col3:
        valid_roi = df[df["ROI (x)"].notna()]["ROI (x)"]
        avg_roi = valid_roi.mean() if len(valid_roi) > 0 else 0
        st.metric("평균 ROI", f"{avg_roi:.2f}x")
    
    with col4:
        profitable = len(df[df["ROI (x)"].notna() & (df["ROI (x)"] >= 1)])
        total = len(df[df["ROI (x)"].notna()])
        st.metric("수익 토큰", f"{profitable}/{total}")
    
    with col5:
        total_contributors = df["Contributors"].sum()
        st.metric("총 참여자", f"{total_contributors:,.0f}")
    
    # 두 번째 행
    col6, col7, col8, col9, col10 = st.columns(5)
    
    with col6:
        avg_oversubscription = df["Oversubscription"].mean()
        st.metric("평균 청약배수", f"{avg_oversubscription:.1f}x")
    
    with col7:
        total_volume = df["24h Volume"].sum()
        st.metric("총 24h 거래량", f"${total_volume:,.0f}")
    
    with col8:
        total_liquidity = df["Liquidity"].sum()
        st.metric("총 유동성", f"${total_liquidity:,.0f}")
    
    with col9:
        featured = len(df[~df["Is Permissionless"]])
        permissionless = len(df[df["Is Permissionless"]])
        st.metric("Featured / Permissionless", f"{featured} / {permissionless}")
    
    with col10:
        max_oversubscription = df.loc[df["Oversubscription"].idxmax()]
        st.metric("최고 청약배수", f"{max_oversubscription['Symbol']} ({max_oversubscription['Oversubscription']:.0f}x)")


def format_value(val, fmt_type: str = "number") -> str:
    """값 포맷팅"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    
    if fmt_type == "price":
        return f"${val:.4f}"
    elif fmt_type == "usd":
        return f"${val:,.0f}"
    elif fmt_type == "roi_x":
        return f"{val:.2f}x"
    elif fmt_type == "pct":
        return f"{val:+.1f}%"
    elif fmt_type == "number":
        return f"{val:,.0f}"
    return str(val)


def render_summary_table(df: pd.DataFrame):
    """요약 테이블"""
    st.header("📋 한눈에 보기")
    
    # 표시할 컬럼
    display_cols = [
        "Symbol", "Name", "Is Permissionless",
        "Committed (USD)", "Raised (USD)", "Contributors", "Oversubscription",
        "ICO Price", "Current Price", 
        "ROI (x)", "ATH ROI (x)", "ATL ROI (x)",
        "ROI_5m (x)", "ROI_15m (x)", "ROI_30m (x)", "ROI_60m (x)",
        "24h Change (%)", "Liquidity", "Sale % of Supply"
    ]
    
    # 존재하는 컬럼만 선택
    available_cols = [col for col in display_cols if col in df.columns]
    display_df = df[available_cols].copy()
    
    # 스타일링 함수
    def style_roi(val):
        if pd.isna(val) or val is None:
            return "background-color: #1a1a2e; color: #888"
        if val >= 2:
            return "background-color: #0d4d1a; color: #4ade80"
        elif val >= 1:
            return "background-color: #1a3d1a; color: #86efac"
        else:
            return "background-color: #4d0d0d; color: #f87171"
    
    roi_cols = [col for col in available_cols if "ROI" in col and "(x)" in col]
    
    styled = display_df.style.applymap(style_roi, subset=roi_cols)
    
    # 숫자 포맷
    format_dict = {
        "ICO Price": "${:.4f}",
        "Current Price": "${:.4f}",
        "ROI (x)": "{:.2f}x",
        "ATH ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ATL ROI (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ROI_5m (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ROI_15m (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ROI_30m (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "ROI_60m (x)": lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A",
        "24h Change (%)": "{:+.2f}%",
        "Liquidity": "${:,.0f}",
        "Sale % of Supply": "{:.1f}%"
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
            roi_val = row.get("ROI (x)")
            if roi_val and roi_val >= 2:
                emoji = "🚀"
            elif roi_val and roi_val >= 1:
                emoji = "✅"
            elif roi_val:
                emoji = "📉"
            else:
                emoji = "❓"
            
            # Permissionless 배지
            is_permissionless = row.get("Is Permissionless", False)
            badge = " 🔓" if is_permissionless else ""
            
            st.subheader(f"{emoji} {row['Symbol']} - {row['Name']}{badge}")
            st.caption(f"{row['Category']} | {row['Description'][:50]}...")
            
            # 주요 메트릭
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                st.metric(
                    "현재가",
                    format_value(row.get("Current Price"), "price"),
                    format_value(row.get("24h Change (%)"), "pct") if row.get("24h Change (%)") else None
                )
            with m2:
                st.metric("ROI", format_value(row.get("ROI (x)"), "roi_x"))
            with m3:
                st.metric("청약배수", f"{row.get('Oversubscription', 0):.1f}x")
            with m4:
                st.metric("참여자", format_value(row.get("Contributors"), "number"))
            
            # 상세 정보 확장
            with st.expander("📊 상세 정보"):
                tab1, tab2, tab3, tab4 = st.tabs(["펀드레이징", "가격 데이터", "TGE 시간대별 ROI", "세일 정보"])
                
                with tab1:
                    is_permissionless = row.get("Is Permissionless", False)
                    launch_type = "🔓 Permissionless" if is_permissionless else "✅ Featured (검증)"
                    st.markdown(f"""
                    | 항목 | 값 |
                    |------|-----|
                    | 런치 타입 | {launch_type} |
                    | 커밋액 | {format_value(row.get("Committed (USD)"), "usd")} |
                    | 실제 모금액 | {format_value(row.get("Raised (USD)"), "usd")} |
                    | 최소 모금 목표 | {format_value(row.get("Min Raise (USD)"), "usd")} |
                    | 청약배수 | {row.get("Oversubscription", 0):.1f}x ({row.get("Oversubscription", 0)*100:.0f}%) |
                    | 참여자 | {format_value(row.get("Contributors"), "number")} |
                    | 월 Allowance | {format_value(row.get("Allowance (USD)"), "usd")} |
                    | ICO 가격 | {format_value(row.get("ICO Price"), "price")} |
                    | 상장가 | {format_value(row.get("Launch Price"), "price")} |
                    """)
                
                with tab2:
                    st.markdown(f"""
                    | 항목 | 값 |
                    |------|-----|
                    | 현재가 | {format_value(row.get("Current Price"), "price")} |
                    | ATH | {format_value(row.get("ATH"), "price")} |
                    | ATL | {format_value(row.get("ATL"), "price")} |
                    | 현재 ROI | {format_value(row.get("ROI (x)"), "roi_x")} |
                    | ATH ROI | {format_value(row.get("ATH ROI (x)"), "roi_x")} |
                    | 24h 거래량 | {format_value(row.get("24h Volume"), "usd")} |
                    | 유동성 | {format_value(row.get("Liquidity"), "usd")} |
                    | FDV | {format_value(row.get("FDV"), "usd")} |
                    """)
                
                with tab3:
                    if row.get("TGE Timestamp"):
                        st.markdown(f"""
                        | 시점 | 가격 | ROI (x) | ROI (%) |
                        |------|------|---------|---------|
                        | +5분 | {format_value(row.get("Price @ 5m"), "price")} | {format_value(row.get("ROI_5m (x)"), "roi_x")} | {format_value(row.get("ROI_5m (%)"), "pct")} |
                        | +15분 | {format_value(row.get("Price @ 15m"), "price")} | {format_value(row.get("ROI_15m (x)"), "roi_x")} | {format_value(row.get("ROI_15m (%)"), "pct")} |
                        | +30분 | {format_value(row.get("Price @ 30m"), "price")} | {format_value(row.get("ROI_30m (x)"), "roi_x")} | {format_value(row.get("ROI_30m (%)"), "pct")} |
                        | +60분 | {format_value(row.get("Price @ 60m"), "price")} | {format_value(row.get("ROI_60m (x)"), "roi_x")} | {format_value(row.get("ROI_60m (%)"), "pct")} |
                        """)
                    else:
                        st.info("TGE 타임스탬프가 설정되지 않았습니다.")
                
                with tab4:
                    st.markdown(f"""
                    | 항목 | 값 |
                    |------|-----|
                    | 세일 토큰 수 | {format_value(row.get("Sale Tokens"), "number")} |
                    | 총 공급량 | {format_value(row.get("Total Supply"), "number")} |
                    | 세일 비율 | {row.get("Sale % of Supply", 0):.1f}% |
                    | ICO 날짜 | {row.get("ICO Date", "N/A")} |
                    | 현재 세일 가치 | {format_value(row.get("Sale Value Now"), "usd")} |
                    | 손익 | {format_value(row.get("Profit (USD)"), "usd")} ({row.get("Profit (%)", 0):+.1f}%) |
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
        x=df["Symbol"],
        y=df["ROI (x)"].fillna(0),
        marker_color=df["ROI (x)"].apply(
            lambda x: "#22c55e" if x and x >= 1 else "#ef4444"
        ),
        text=df["ROI (x)"].apply(lambda x: f"{x:.2f}x" if x else "N/A"),
        textposition="outside"
    ))
    
    # ATH ROI
    fig.add_trace(go.Bar(
        name="ATH ROI",
        x=df["Symbol"],
        y=df["ATH ROI (x)"].fillna(0),
        marker_color="rgba(250, 204, 21, 0.7)",
        text=df["ATH ROI (x)"].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else ""),
        textposition="outside"
    ))
    
    fig.add_hline(y=1, line_dash="dash", line_color="white", annotation_text="손익분기점")
    
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_tge_roi_chart(df: pd.DataFrame):
    """TGE 시간대별 ROI 비교 차트"""
    st.subheader("⏱️ TGE 시간대별 가상 매도 ROI")
    
    # TGE 데이터가 있는 토큰만
    has_tge = df[df["TGE Timestamp"].notna()]
    
    if len(has_tge) == 0:
        st.info("TGE 타임스탬프가 설정된 토큰이 없습니다. METADAO_TOKENS에 tge_timestamp를 추가하세요.")
        return
    
    # 데이터 준비
    time_labels = ["5분", "15분", "30분", "60분"]
    roi_cols = ["ROI_5m (x)", "ROI_15m (x)", "ROI_30m (x)", "ROI_60m (x)"]
    
    fig = go.Figure()
    
    for _, row in has_tge.iterrows():
        roi_values = [row.get(col) for col in roi_cols]
        fig.add_trace(go.Bar(
            name=row["Symbol"],
            x=time_labels,
            y=[v if v else 0 for v in roi_values],
            text=[f"{v:.2f}x" if v else "N/A" for v in roi_values],
            textposition="outside"
        ))
    
    fig.add_hline(y=1, line_dash="dash", line_color="white", annotation_text="손익분기점")
    
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        height=450,
        xaxis_title="TGE 이후 시점",
        yaxis_title="ROI (배수)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
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
            x=df["Symbol"],
            y=df["Committed (USD)"],
            marker_color='rgba(255, 165, 0, 0.7)'
        ))
        fig.add_trace(go.Bar(
            name='실제 모금액 (Raised)',
            x=df["Symbol"],
            y=df["Raised (USD)"],
            marker_color='rgba(0, 255, 127, 0.7)'
        ))
        fig.update_layout(
            title="커밋액 vs 실제 모금액",
            template="plotly_dark",
            height=350,
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 세일 비율 비교
        fig = px.bar(
            df,
            x="Symbol",
            y="Sale % of Supply",
            color="ROI (x)",
            color_continuous_scale=["red", "yellow", "green"],
            title="세일 물량 비율 (% of Total Supply)"
        )
        fig.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)


def render_oversubscription_chart(df: pd.DataFrame):
    """청약배수 및 참여자 차트"""
    st.subheader("📊 청약배수 & 참여자 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 청약배수 차트
        fig = px.bar(
            df.sort_values("Oversubscription", ascending=True),
            x="Oversubscription",
            y="Symbol",
            orientation='h',
            color="Is Permissionless",
            color_discrete_map={True: "#ff6b6b", False: "#4ecdc4"},
            title="토큰별 청약배수 (Oversubscription)",
            labels={"Is Permissionless": "Permissionless"}
        )
        fig.update_layout(
            template="plotly_dark", 
            height=400,
            xaxis_title="청약배수 (x)",
            yaxis_title=""
        )
        # 참조선 추가
        fig.add_vline(x=10, line_dash="dash", line_color="yellow", 
                      annotation_text="10x", annotation_position="top right")
        fig.add_vline(x=50, line_dash="dash", line_color="orange",
                      annotation_text="50x", annotation_position="top right")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 참여자 수 차트
        fig = px.bar(
            df.sort_values("Contributors", ascending=True),
            x="Contributors",
            y="Symbol",
            orientation='h',
            color="Is Permissionless",
            color_discrete_map={True: "#ff6b6b", False: "#4ecdc4"},
            title="토큰별 참여자 수 (Contributors)",
            labels={"Is Permissionless": "Permissionless"}
        )
        fig.update_layout(
            template="plotly_dark", 
            height=400,
            xaxis_title="참여자 수",
            yaxis_title=""
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 청약배수 vs ROI 상관관계
    st.subheader("🔗 청약배수 vs ROI 상관관계")
    
    # ROI가 있는 데이터만 필터링
    corr_df = df[df["ROI (x)"].notna()].copy()
    
    if len(corr_df) > 0:
        fig = px.scatter(
            corr_df,
            x="Oversubscription",
            y="ROI (x)",
            size="Contributors",
            color="Is Permissionless",
            color_discrete_map={True: "#ff6b6b", False: "#4ecdc4"},
            hover_data=["Symbol", "Name", "Raised (USD)"],
            title="청약배수와 현재 ROI 관계 (버블 크기 = 참여자 수)",
            labels={"Is Permissionless": "Permissionless"}
        )
        fig.update_layout(template="plotly_dark", height=450)
        
        # 1x ROI 참조선
        fig.add_hline(y=1, line_dash="dash", line_color="white",
                      annotation_text="원금", annotation_position="right")
        
        st.plotly_chart(fig, use_container_width=True)


def render_profit_simulation(df: pd.DataFrame):
    """투자 시뮬레이션 (직접 입력)"""
    st.header("💵 투자 시뮬레이션")
    
    st.markdown("ICO 참여 금액을 입력하면 각 토큰별 현재 가치와 수익을 계산합니다.")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # 금액 직접 입력
        investment = st.number_input(
            "투자금액 (USD)",
            min_value=10,
            max_value=1000000,
            value=1000,
            step=100,
            help="ICO 참여 금액을 입력하세요"
        )
        
        # 할당률 표시 옵션
        show_allocation = st.checkbox("실제 할당 비율 적용", value=False, 
                                       help="과열 ICO의 경우 실제 할당률이 낮을 수 있습니다")
        
        if show_allocation:
            allocation_rate = st.slider("예상 할당률 (%)", 1, 100, 10)
            effective_investment = investment * (allocation_rate / 100)
            st.info(f"실제 배정 금액: ${effective_investment:,.0f}")
        else:
            effective_investment = investment
    
    with col2:
        sim_data = []
        for _, row in df.iterrows():
            current_price = row.get("Current Price")
            ico_price = row.get("ICO Price")
            
            if current_price and ico_price and ico_price > 0:
                tokens_bought = effective_investment / ico_price
                current_value = tokens_bought * current_price
                profit = current_value - effective_investment
                roi_pct = (profit / effective_investment * 100) if effective_investment > 0 else 0
                
                sim_data.append({
                    "토큰": row["Symbol"],
                    "ICO 가격": ico_price,
                    "현재 가격": current_price,
                    "배정 토큰": tokens_bought,
                    "현재 가치": current_value,
                    "손익": profit,
                    "수익률 (%)": roi_pct
                })
        
        if sim_data:
            sim_df = pd.DataFrame(sim_data)
            
            # 바 차트
            fig = px.bar(
                sim_df,
                x="토큰",
                y="손익",
                color="손익",
                color_continuous_scale=["#ef4444", "#facc15", "#22c55e"],
                title=f"${effective_investment:,.0f} 투자 시 토큰별 손익"
            )
            fig.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            # 테이블
            st.dataframe(
                sim_df.style.format({
                    "ICO 가격": "${:.4f}",
                    "현재 가격": "${:.4f}",
                    "배정 토큰": "{:,.2f}",
                    "현재 가치": "${:,.2f}",
                    "손익": "${:+,.2f}",
                    "수익률 (%)": "{:+.1f}%"
                }).applymap(
                    lambda x: "color: #22c55e" if isinstance(x, (int, float)) and x > 0 else "color: #ef4444",
                    subset=["손익", "수익률 (%)"]
                ),
                use_container_width=True
            )
            
            # 총합
            total_profit = sim_df["손익"].sum()
            total_invested = effective_investment * len(sim_df)
            total_value = sim_df["현재 가치"].sum()
            
            st.markdown(f"""
            **전체 토큰 동일 금액 투자 시:**
            - 총 투자금: ${total_invested:,.0f}
            - 현재 총 가치: ${total_value:,.0f}  
            - 총 손익: **${total_profit:+,.0f}** ({total_profit/total_invested*100:+.1f}%)
            """)


def render_raw_data(df: pd.DataFrame):
    """원본 데이터"""
    st.header("📥 원본 데이터")
    
    st.dataframe(df, use_container_width=True, height=400)
    
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
    st.title("🚀 MetaDAO ICO 토큰 분석 대시보드")
    st.caption("MetaDAO 런치패드 ICO 8개 토큰 상세 분석 | MetaDAO.fi + DexScreener + GeckoTerminal API")
    
    # 사이드바
    selected_category, selected_launch_type, (sort_col, sort_asc) = render_sidebar()
    
    # 데이터 로딩
    with st.spinner("데이터를 불러오는 중..."):
        df = get_all_token_data()
    
    # API 실패 시 데모 데이터
    if df["Current Price"].isna().all() or df["Current Price"].sum() == 0:
        st.warning("⚠️ API에서 실시간 데이터를 가져올 수 없습니다. 데모 데이터를 표시합니다.")
        demo_prices = {
            "MTNC": 0.60, "OMFG": 0.87, "UMBRA": 1.96, "AVICI": 5.43,
            "LOYAL": 0.33, "ZKLSOL": 0.08, "PAYSTREAM": 0.05, "SOLO": 1.21
        }
        for idx, row in df.iterrows():
            symbol = row["Symbol"]
            if symbol in demo_prices:
                df.at[idx, "Current Price"] = demo_prices[symbol]
                roi_x, roi_pct = calculate_roi(demo_prices[symbol], row["ICO Price"])
                df.at[idx, "ROI (x)"] = roi_x
                df.at[idx, "ROI (%)"] = roi_pct
    
    # 카테고리 필터링
    if selected_category != "All":
        df = df[df["Category"] == selected_category]
    
    # 런치 타입 필터링
    if selected_launch_type == "Featured (검증)":
        df = df[~df["Is Permissionless"]]
    elif selected_launch_type == "Permissionless":
        df = df[df["Is Permissionless"]]
    
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
        render_oversubscription_chart(df)  # 추가
        render_tge_roi_chart(df)
        render_allocation_chart(df)
    
    with tab4:
        render_profit_simulation(df)
    
    with tab5:
        render_raw_data(df)
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.85em;'>
    Data: MetaDAO.fi, DexScreener API, GeckoTerminal API | Built with Streamlit<br>
    ⚠️ 투자 조언이 아닙니다. DYOR!
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
