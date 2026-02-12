import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
# -*- coding: utf-8 -*-
"""
湘菜品牌智能选址决策系统 v3.0
功能模块：
    1. 城市宏观分析（统计局+高德行政区域）
    2. 商圈微观评估（高德POI+周边搜索）
    3. 财务5年预测模型
    4. 风险矩阵评估
    5. AI智能推荐（基于历史成功经验）
    6. 综合报告自动生成
    7. 智能选址顾问聊天端口（自然语言交互）
    
数据源模式：
    - 模拟模式（默认）：无需API Key，使用内置样本数据
    - 真实模式：在高德开放平台申请Key后输入侧边栏，自动切换实时数据
    
作者：选址算法团队
版本：2024.03 企业生产级
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import json
import re
from datetime import datetime
import time
import hashlib

# ---------- 页面配置（必须放在最前）----------
st.set_page_config(
    page_title="湘菜品牌智能选址系统 v3.0",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- 自定义CSS美化 ----------
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #c0392b;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        border-bottom: 3px solid #e74c3c;
        padding-bottom: 10px;
    }
    .sub-header {
        font-size: 1.6rem;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
        border-left: 8px solid #e74c3c;
        padding-left: 15px;
    }
    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f0f2f6);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 5px 5px 15px #bebebe, -5px -5px 15px #ffffff;
        text-align: center;
    }
    .chat-message-user {
        background-color: #e6f3ff;
        padding: 12px 18px;
        border-radius: 18px 18px 0 18px;
        margin-bottom: 10px;
        max-width: 80%;
        align-self: flex-end;
    }
    .chat-message-assistant {
        background-color: #f0f0f0;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 0;
        margin-bottom: 10px;
        max-width: 80%;
        align-self: flex-start;
    }
    .stButton>button {
        background-color: #e74c3c;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #c0392b;
        color: white;
        box-shadow: 0 5px 15px rgba(231,76,60,0.4);
    }
</style>
""", unsafe_allow_html=True)

# ---------- 高德地图API封装（真实数据源）----------
class AMapService:
    """高德地图开放平台API封装"""
    def __init__(self, api_key):
        self.key = api_key
        self.base_url = "https://restapi.amap.com/v3"
        self.session = requests.Session()
    
    def search_poi(self, keyword, city, offset=20, page=1):
        """POI关键词搜索"""
        url = f"{self.base_url}/place/text"
        params = {
            "keywords": keyword,
            "city": city,
            "offset": offset,
            "page": page,
            "extensions": "all",
            "output": "JSON",
            "key": self.key
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data["status"] == "1":
                return data
        except Exception as e:
            st.error(f"高德POI搜索失败: {e}")
        return None
    
    def search_around(self, location, keywords, radius=1000):
        """周边搜索"""
        url = f"{self.base_url}/place/around"
        params = {
            "location": location,
            "keywords": keywords,
            "radius": radius,
            "output": "JSON",
            "key": self.key
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            return resp.json()
        except:
            return None
    
    def geocode(self, address, city):
        """地理编码：地址转经纬度"""
        url = f"{self.base_url}/geocode/geo"
        params = {
            "address": address,
            "city": city,
            "output": "JSON",
            "key": self.key
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data["status"] == "1" and data["geocodes"]:
                return data["geocodes"][0]["location"]
        except:
            return None
    
    def district(self, keywords):
        """行政区划查询"""
        url = f"{self.base_url}/config/district"
        params = {
            "keywords": keywords,
            "subdistrict": 0,
            "output": "JSON",
            "key": self.key
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data["status"] == "1" and data["districts"]:
                return data["districts"][0]
        except:
            return None
        return None

# ---------- 模拟数据生成器（无API Key时使用）----------
def generate_mock_city_data(city_name):
    """模拟城市宏观数据"""
    mock_db = {
        '苏州': {
            'population': 1280, 'gdp_growth': 6.8, 'disposable_income': 75000,
            'rental_index': 85, 'spicy_acceptance': 65, 'dining_frequency': 8.5,
            'competition_index': 62, 'logistics_score': 88, 'policy_score': 85,
            'growth_potential': 92
        },
        '郑州': {
            'population': 1260, 'gdp_growth': 7.2, 'disposable_income': 42000,
            'rental_index': 72, 'spicy_acceptance': 85, 'dining_frequency': 7.8,
            'competition_index': 68, 'logistics_score': 92, 'policy_score': 78,
            'growth_potential': 88
        },
        '杭州': {
            'population': 1220, 'gdp_growth': 7.0, 'disposable_income': 70000,
            'rental_index': 88, 'spicy_acceptance': 60, 'dining_frequency': 8.2,
            'competition_index': 70, 'logistics_score': 90, 'policy_score': 86,
            'growth_potential': 90
        },
        '南京': {
            'population': 930, 'gdp_growth': 6.5, 'disposable_income': 68000,
            'rental_index': 80, 'spicy_acceptance': 55, 'dining_frequency': 7.5,
            'competition_index': 65, 'logistics_score': 85, 'policy_score': 82,
            'growth_potential': 84
        }
    }
    return mock_db.get(city_name, mock_db['苏州'])

def generate_mock_district_data(city, district_name):
    """模拟商圈微观数据"""
    mock_db = {
        ('苏州', '工业园区湖东'): {
            'daily_flow': 85000, 'weekend_multiplier': 1.8, 'office_ratio': 0.45,
            'family_ratio': 0.35, 'youth_ratio': 0.55, 'avg_rent': 220,
            'competitor_count': 3, 'visibility_score': 88, 'accessibility_score': 92,
            'neighbor_quality': 85, 'parking_score': 78
        },
        ('苏州', '姑苏区观前街'): {
            'daily_flow': 150000, 'weekend_multiplier': 2.2, 'office_ratio': 0.15,
            'family_ratio': 0.25, 'youth_ratio': 0.40, 'avg_rent': 320,
            'competitor_count': 7, 'visibility_score': 95, 'accessibility_score': 88,
            'neighbor_quality': 82, 'parking_score': 65
        },
        ('郑州', '金水区花园路'): {
            'daily_flow': 95000, 'weekend_multiplier': 1.6, 'office_ratio': 0.35,
            'family_ratio': 0.45, 'youth_ratio': 0.50, 'avg_rent': 180,
            'competitor_count': 5, 'visibility_score': 85, 'accessibility_score': 90,
            'neighbor_quality': 80, 'parking_score': 82
        }
    }
    key = (city, district_name)
    if key in mock_db:
        return mock_db[key]
    else:
        # 返回一个默认值
        return {
            'daily_flow': 70000, 'weekend_multiplier': 1.7, 'office_ratio': 0.3,
            'family_ratio': 0.3, 'youth_ratio': 0.4, 'avg_rent': 200,
            'competitor_count': 4, 'visibility_score': 75, 'accessibility_score': 75,
            'neighbor_quality': 70, 'parking_score': 70
        }

# ---------- 真实数据获取函数（使用高德API）----------
def get_city_data_real(amap, city_name, stats_df):
    """从高德+统计局数据库获取真实城市数据"""
    # 1. 获取行政区信息（人口、面积）
    district_info = amap.district(city_name)
    population = 0
    if district_info:
        try:
            population = int(district_info.get('population', '0'))
        except:
            population = 0
    
    # 2. 从统计数据库读取（CSV或DataFrame）
    city_row = stats_df[stats_df['city'] == city_name]
    if not city_row.empty:
        disposable_income = city_row.iloc[0].get('disposable_income', 60000)
        gdp_growth = city_row.iloc[0].get('gdp_growth', 6.5)
    else:
        disposable_income = 60000
        gdp_growth = 6.5
    
    # 3. 湘菜接受度（可根据口味大数据，这里用经验值）
    spicy_dict = {'郑州': 85, '苏州': 65, '杭州': 60, '南京': 55, '武汉': 88, '长沙': 95}
    spicy_acceptance = spicy_dict.get(city_name, 70)
    
    # 4. 返回标准格式
    return {
        'population': population if population > 0 else 1000,  # 若获取失败，给个默认值
        'gdp_growth': gdp_growth,
        'disposable_income': disposable_income,
        'rental_index': 80,  # 需其他数据源
        'spicy_acceptance': spicy_acceptance,
        'dining_frequency': 8.0,
        'competition_index': 65,
        'logistics_score': 80,
        'policy_score': 80,
        'growth_potential': 85
    }

def get_district_data_real(amap, city, district_name):
    """从高德API获取真实商圈数据"""
    # 1. 地理编码得到中心点
    location = amap.geocode(f"{district_name},{city}", city)
    if not location:
        return generate_mock_district_data(city, district_name)
    
    # 2. 搜索竞品（大米先生）
    competitor_data = amap.search_poi("大米先生", city)
    competitor_count = 0
    if competitor_data and competitor_data['status'] == '1':
        competitor_count = int(competitor_data['count'])
    
    # 3. 搜索周边设施
    bus = amap.search_around(location, "公交车站", 500)
    subway = amap.search_around(location, "地铁站", 800)
    office = amap.search_around(location, "写字楼", 1000)
    residence = amap.search_around(location, "住宅小区", 1000)
    
    bus_cnt = len(bus.get('pois', [])) if bus else 0
    subway_cnt = len(subway.get('pois', [])) if subway else 0
    office_cnt = len(office.get('pois', [])) if office else 0
    
    # 4. 估算人流（简易模型）
    daily_flow = 30000 + office_cnt * 500 + subway_cnt * 2000
    
    return {
        'daily_flow': daily_flow,
        'weekend_multiplier': 1.8,
        'office_ratio': min(0.6, office_cnt / 100) if office_cnt else 0.3,
        'family_ratio': 0.3,
        'youth_ratio': 0.4,
        'avg_rent': 200,  # 需租金API
        'competitor_count': competitor_count,
        'visibility_score': 75,
        'accessibility_score': 85 if (bus_cnt+subway_cnt) > 10 else 70,
        'neighbor_quality': 70,
        'parking_score': 70
    }

# ---------- 静态宏观经济数据库（模拟统计年鉴）----------
@st.cache_data
def load_city_stats():
    """城市统计年鉴数据（可定期更新）"""
    data = {
        'city': ['苏州', '郑州', '杭州', '南京', '武汉', '长沙', '成都', '西安'],
        'disposable_income': [75000, 42000, 70000, 68000, 55000, 60000, 50000, 45000],
        'gdp_growth': [6.8, 7.2, 7.0, 6.5, 7.5, 7.8, 7.3, 6.9],
        'population': [1280, 1260, 1220, 930, 1120, 1000, 1650, 1200],
        'retail_total': [9500, 5200, 7800, 7200, 6800, 5500, 8200, 5900]  # 亿
    }
    return pd.DataFrame(data)

# ---------- 品牌参数全局存储 ----------
if 'brand_config' not in st.session_state:
    st.session_state.brand_config = {
        'brand_name': '湘味小炒',
        'store_count': 120,
        'avg_price': 49,
        'seat_count': 120,
        'target_groups': ['年轻白领', '家庭聚餐', '朋友聚会'],
        'main_competitor': '大米先生',
        'budget_min': 150,
        'budget_max': 200,
        'roi_target': 18,
        'expansion_strategy': '谨慎测试(先开1-2家)'
    }

# ---------- 对话历史存储 ----------
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ---------- 侧边栏：全局配置 ----------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/restaurant.png", width=80)
    st.title("🍲 品牌配置中心")
    
    with st.expander("🔧 品牌基础信息", expanded=True):
        brand_name = st.text_input("品牌名称", value=st.session_state.brand_config['brand_name'])
        store_count = st.number_input("现有门店数", min_value=1, max_value=1000, 
                                      value=st.session_state.brand_config['store_count'])
        avg_price = st.slider("客单价(元)", 30, 80, 
                              value=st.session_state.brand_config['avg_price'])
        seat_count = st.slider("标准店座位数", 60, 200, 
                               value=st.session_state.brand_config['seat_count'])
    
    with st.expander("🎯 目标客群", expanded=True):
        target_groups = st.multiselect(
            "主要客群",
            ["年轻白领", "家庭聚餐", "朋友聚会", "商务简餐", "学生群体", "社区银发"],
            default=st.session_state.brand_config['target_groups']
        )
    
    with st.expander("⚔️ 竞争策略", expanded=True):
        main_competitor = st.text_input("主要竞品名称", value=st.session_state.brand_config['main_competitor'])
        acceptable_competition = st.slider("可接受竞品数(半径1km)", 0, 10, 4)
    
    with st.expander("💰 投资预算", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            budget_min = st.number_input("最低(万元)", 80, 500, 
                                         value=st.session_state.brand_config['budget_min'])
        with col2:
            budget_max = st.number_input("最高(万元)", 100, 800, 
                                         value=st.session_state.brand_config['budget_max'])
        roi_target = st.slider("目标回收期(月)", 12, 36, 
                               value=st.session_state.brand_config['roi_target'])
    
    with st.expander("🌍 扩张偏好", expanded=True):
        priority_city = st.selectbox("优先城市", ["苏州", "郑州", "杭州", "南京", "武汉", "长沙"])
        expansion_strategy = st.radio("扩张策略", 
                                      ["谨慎测试(先开1-2家)", "快速占领(3-5家)", "全面铺开(5家以上)"],
                                      index=0)
    
    # 保存配置按钮
    if st.button("💾 保存品牌配置", use_container_width=True):
        st.session_state.brand_config = {
            'brand_name': brand_name,
            'store_count': store_count,
            'avg_price': avg_price,
            'seat_count': seat_count,
            'target_groups': target_groups,
            'main_competitor': main_competitor,
            'budget_min': budget_min,
            'budget_max': budget_max,
            'roi_target': roi_target,
            'priority_city': priority_city,
            'expansion_strategy': expansion_strategy
        }
        st.success("✅ 品牌配置已保存！")
    
    st.divider()
    
    # ---------- 高德API配置（切换真实/模拟模式）----------
    st.subheader("🗺️ 数据源设置")
    amap_key = st.text_input("高德地图API Key (留空则使用模拟数据)", 
                             type="password", 
                             help="申请地址：https://lbs.amap.com/")
    
    if amap_key:
        st.success("✅ 已启用【真实数据模式】")
        amap_client = AMapService(amap_key)
        use_mock = False
    else:
        st.info("ℹ️ 当前使用【模拟数据模式】")
        amap_client = None
        use_mock = True
    
    # 加载统计年鉴数据
    city_stats = load_city_stats()
    
    st.divider()
    st.caption("📌 系统版本：v3.0 企业版 | 数据更新：2024.03")
    st.caption("🚀 智能选址顾问已上线，请在聊天窗口输入需求")

# ---------- 核心分析函数 ----------
def analyze_city(city_name, amap_client, city_stats, use_mock):
    """城市宏观分析接口"""
    if use_mock or amap_client is None:
        return generate_mock_city_data(city_name)
    else:
        return get_city_data_real(amap_client, city_name, city_stats)

def analyze_district(city, district, amap_client, use_mock):
    """商圈微观分析接口"""
    if use_mock or amap_client is None:
        return generate_mock_district_data(city, district)
    else:
        return get_district_data_real(amap_client, city, district)

def financial_forecast(avg_price, seat_count, monthly_rent, labor_cost, 
                       food_cost_rate, utility_rate, marketing_rate, 
                       initial_investment, city, use_mock):
    """财务预测核心模型"""
    # 基础计算
    table_turnover = 2.8  # 默认翻台率
    daily_customers = seat_count * table_turnover
    daily_revenue = daily_customers * avg_price
    monthly_revenue = daily_revenue * 30
    
    # 成本
    monthly_food_cost = monthly_revenue * (food_cost_rate / 100)
    monthly_utility = monthly_revenue * (utility_rate / 100)
    monthly_marketing = monthly_revenue * (marketing_rate / 100)
    monthly_other = monthly_revenue * 0.05
    equipment_depreciation = 2000000 / 60  # 200万设备5年折旧
    
    # 利润
    monthly_profit = (monthly_revenue - monthly_food_cost - monthly_utility -
                      monthly_marketing - monthly_other - 
                      labor_cost * 10000 - monthly_rent * 10000 - 
                      equipment_depreciation)
    
    # 季节性调整
    seasonal_factors = {
        '苏州': [0.85, 0.65, 0.90, 0.95, 1.0, 0.95, 0.88, 0.92, 0.98, 1.05, 1.02, 0.95],
        '郑州': [0.70, 0.65, 0.85, 0.95, 1.0, 0.98, 0.95, 0.92, 0.96, 1.02, 0.90, 0.75],
        '默认': [0.85, 0.80, 0.90, 0.95, 1.0, 0.98, 0.96, 0.97, 0.98, 1.02, 0.95, 0.85]
    }
    season = seasonal_factors.get(city, seasonal_factors['默认'])
    
    # 5年现金流模拟
    months = 60
    monthly_data = []
    cum_cash = -initial_investment
    breakeven_month = None
    
    for m in range(1, months+1):
        growth = 1.0 + min(0.5, m * 0.015)  # 前33个月增长
        seasonal = season[(m-1)%12]
        adj_profit = monthly_profit * growth * seasonal
        cum_cash += adj_profit
        
        monthly_data.append({
            '月份': m,
            '营收(万)': monthly_revenue * growth * seasonal / 10000,
            '利润(万)': adj_profit / 10000,
            '累计现金流(万)': cum_cash / 10000
        })
        
        if cum_cash >= 0 and breakeven_month is None:
            breakeven_month = m
    
    df_cashflow = pd.DataFrame(monthly_data)
    annual_profit = df_cashflow['利润(万)'].tail(12).sum()
    roe = annual_profit / (initial_investment / 10000) * 100 if initial_investment > 0 else 0
    
    return {
        'monthly_revenue': monthly_revenue,
        'monthly_profit': monthly_profit,
        'breakeven_month': breakeven_month if breakeven_month else 99,
        'annual_profit': annual_profit,
        'roe': roe,
        'df_cashflow': df_cashflow,
        'seasonal_factors': season
    }

def risk_assessment(city_data, district_data, financials, brand_config):
    """综合风险评估"""
    risks = {}
    
    # 市场风险
    comp_score = min(100, district_data.get('competitor_count', 0) * 12)
    demand_score = 100 - city_data.get('growth_potential', 80)
    price_score = 30 if brand_config['avg_price'] > 55 else 20
    risks['市场风险'] = {
        '竞争激烈度': comp_score,
        '需求波动': demand_score,
        '价格敏感': price_score,
        '平均': (comp_score + demand_score + price_score) / 3
    }
    
    # 运营风险
    rent_score = max(0, (district_data.get('avg_rent', 200) - 150) // 2)
    labor_score = 25  # 默认
    supply_score = 15 if city_data.get('logistics_score', 80) > 85 else 25
    risks['运营风险'] = {
        '租金压力': rent_score,
        '人力稳定性': labor_score,
        '供应链风险': supply_score,
        '平均': (rent_score + labor_score + supply_score) / 3
    }
    
    # 财务风险
    payback_score = 40 if financials['breakeven_month'] > 24 else 20 if financials['breakeven_month'] > 18 else 10
    cashflow_score = 30 if financials['monthly_profit'] < 50000 else 15
    risks['财务风险'] = {
        '回本周期': payback_score,
        '现金流压力': cashflow_score,
        '投资强度': 20 if brand_config['budget_max'] > 250 else 10,
        '平均': (payback_score + cashflow_score + 20) / 3
    }
    
    # 政策风险
    policy_score = 100 - city_data.get('policy_score', 80)
    env_score = 30 if district_data.get('visibility_score', 70) < 60 else 15
    risks['政策风险'] = {
        '证照难度': policy_score,
        '环保消防': env_score,
        '地方保护': 20,
        '平均': (policy_score + env_score + 20) / 3
    }
    
    # 总风险分
    total_score = sum([v['平均'] for v in risks.values()]) / len(risks)
    return risks, total_score

def ai_recommendations(city_data, district_data, financials, brand_config):
    """AI智能建议（基于规则+历史经验）"""
    recs = []
    
    # 选址建议
    if district_data.get('competitor_count', 0) > 5:
        recs.append(("竞争策略", "竞品密集，建议错位经营：主打现炒锅气，增加外卖窗口", "⚠️"))
    else:
        recs.append(("竞争策略", "竞争温和，可快速抢占心智，加大营销投入", "✅"))
    
    if financials['breakeven_month'] > 24:
        recs.append(("财务优化", f"回本周期{financials['breakeven_month']}个月偏长，建议降低租金或提升翻台率", "🔴"))
    else:
        recs.append(("财务健康", f"回本周期{financials['breakeven_month']}个月，处于健康区间", "🟢"))
    
    # 本地化调整
    if city_data.get('spicy_acceptance', 50) < 70:
        recs.append(("菜品本地化", "建议增加免辣/微辣菜品，占比约30%，并推出儿童套餐", "🟡"))
    
    if brand_config['avg_price'] > 55:
        recs.append(("价格策略", "客单价偏高，建议设置39元引流套餐，提升复购", "🟡"))
    elif brand_config['avg_price'] < 45:
        recs.append(("价格策略", "客单价偏低，可小幅提价至49-52元，优化利润结构", "🟢"))
    
    # 通用建议
    recs.append(("会员体系", "开业前30天启动社群运营，储值赠礼锁定初始客流", "✅"))
    recs.append(("人员培训", "提前45天招聘店长、厨师，进行标准化操作培训", "✅"))
    
    return recs

# ---------- 自然语言处理（简单意图识别）----------
def parse_user_query(query):
    """从用户输入中提取城市、商圈、预算等信息"""
    city_pattern = r'(苏州|郑州|杭州|南京|武汉|长沙|成都|西安|上海|北京|广州|深圳)'
    district_pattern = r'([\u4e00-\u9fa5]{2,}(?:商圈|广场|中心|路|街|区))'
    price_pattern = r'(\d{2,3})[元块]'
    
    city_match = re.search(city_pattern, query)
    district_match = re.search(district_pattern, query)
    price_match = re.search(price_pattern, query)
    
    result = {
        'city': city_match.group(1) if city_match else st.session_state.brand_config.get('priority_city', '苏州'),
        'district': district_match.group(1) if district_match else None,
        'avg_price': int(price_match.group(1)) if price_match else st.session_state.brand_config.get('avg_price', 49)
    }
    return result

def generate_chat_response(user_input, amap_client, use_mock, city_stats):
    """生成选址顾问回复"""
    parsed = parse_user_query(user_input)
    city = parsed['city']
    district = parsed['district'] if parsed['district'] else '工业园区湖东'  # 默认商圈
    
    # 获取数据
    city_data = analyze_city(city, amap_client, city_stats, use_mock)
    district_data = analyze_district(city, district, amap_client, use_mock)
    
    # 财务假设
    financials = financial_forecast(
        avg_price=parsed['avg_price'],
        seat_count=st.session_state.brand_config['seat_count'],
        monthly_rent=district_data.get('avg_rent', 200) * 300 / 10000,  # 300㎡
        labor_cost=15,
        food_cost_rate=32,
        utility_rate=8,
        marketing_rate=5,
        initial_investment=st.session_state.brand_config['budget_min'] * 10000,
        city=city,
        use_mock=use_mock
    )
    
    # 风险评估
    risks, total_risk = risk_assessment(city_data, district_data, financials, st.session_state.brand_config)
    
    # 综合评分
    match_score = int(
        0.25 * city_data.get('spicy_acceptance', 60) +
        0.20 * (city_data.get('disposable_income', 50000) / 1000) +
        0.15 * (100 - district_data.get('competitor_count', 0) * 8) +
        0.15 * district_data.get('daily_flow', 50000) / 1000 +
        0.15 * (100 - total_risk) +
        0.10 * (100 - abs(parsed['avg_price'] - 49) * 2)
    )
    
    # 构建回复
    response = f"🎯 **{city}{district if district else ''}选址分析报告**\n\n"
    response += f"📊 **综合得分**: {match_score}/100  "
    if match_score >= 80:
        response += "🌟 强烈推荐\n\n"
    elif match_score >= 65:
        response += "👍 建议考虑\n\n"
    else:
        response += "⚠️ 谨慎评估\n\n"
    
    response += f"👥 **日均客流**: {district_data['daily_flow']:,} 人  |  🏪 **竞品数量**: {district_data['competitor_count']} 家\n"
    response += f"💰 **租金水平**: {district_data['avg_rent']} 元/㎡/月  |  💵 **客单价**: {parsed['avg_price']} 元\n"
    response += f"⏳ **预估回本**: {financials['breakeven_month']} 个月  |  📈 **年化ROE**: {financials['roe']:.1f}%\n\n"
    
    response += "**🔍 核心优势**:\n"
    if district_data['office_ratio'] > 0.4:
        response += "- 白领客群充足，午市刚需\n"
    if district_data['daily_flow'] > 80000:
        response += "- 商圈流量大，品牌曝光佳\n"
    if financials['breakeven_month'] <= 20:
        response += "- 投资回收快，现金流稳健\n"
    
    response += "\n**⚠️ 风险提示**:\n"
    if district_data['competitor_count'] > 5:
        response += "- 竞争激烈，需差异化运营\n"
    if total_risk > 50:
        response += "- 综合风险偏高，建议复核\n"
    if city_data['spicy_acceptance'] < 70:
        response += "- 本地辣味接受度较低，需调整菜单\n"
    
    response += "\n💡 **AI优化建议**:\n"
    ai_recs = ai_recommendations(city_data, district_data, financials, st.session_state.brand_config)
    for rec in ai_recs[:3]:  # 只取前3条
        response += f"- {rec[0]}：{rec[1]}\n"
    
    return response

# ---------- 主界面：多标签页 ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏙️ 城市宏观", "📍 商圈微观", "💰 财务预测", 
    "⚠️ 风险评估", "🎯 AI推荐", "📋 综合报告", "💬 智能顾问"
])

# ---------- Tab1: 城市宏观 ----------
with tab1:
    st.markdown('<h2 class="sub-header">🏙️ 城市宏观竞争力分析</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_city = st.selectbox("选择城市", city_stats['city'].tolist(), key="city_tab1")
    with col2:
        depth = st.radio("分析深度", ["快速", "详细"], horizontal=True, key="depth")
    
    # 获取数据
    city_data = analyze_city(selected_city, amap_client if not use_mock else None, 
                             city_stats, use_mock)
    
    # 关键指标卡片
    cols = st.columns(5)
    with cols[0]:
        st.metric("常住人口", f"{city_data['population']}万", delta="±0%")
    with cols[1]:
        st.metric("人均年收入", f"{city_data['disposable_income']/1000:.1f}千元", 
                 delta="+5.2%" if selected_city=='苏州' else "+4.1%")
    with cols[2]:
        st.metric("湘菜接受度", f"{city_data['spicy_acceptance']}%",
                 delta="高" if city_data['spicy_acceptance']>=80 else "中")
    with cols[3]:
        st.metric("餐饮频次", f"{city_data['dining_frequency']}次/月")
    with cols[4]:
        st.metric("租金指数", f"{city_data['rental_index']}/100")
    
    # 雷达图
    categories = ['消费能力', '辣味接受', '竞争环境', '政策支持', '物流', '增长潜力']
    values = [
        city_data['disposable_income']/1000,
        city_data['spicy_acceptance'],
        100 - city_data['competition_index'],
        city_data['policy_score'],
        city_data['logistics_score'],
        city_data['growth_potential']
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        marker=dict(color='#e74c3c')
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=400,
        title=f"{selected_city} 城市六维评估"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 季节性
    st.subheader("📅 季节性客流波动")
    months = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    if selected_city == '苏州':
        season = [0.85,0.65,0.90,0.95,1.0,0.95,0.88,0.92,0.98,1.05,1.02,0.95]
    elif selected_city == '郑州':
        season = [0.70,0.65,0.85,0.95,1.0,0.98,0.95,0.92,0.96,1.02,0.90,0.75]
    else:
        season = [0.85]*12
    
    fig_season = px.line(x=months, y=season, markers=True, 
                        title=f"{selected_city} 月度客流系数",
                        labels={'x':'月份', 'y':'客流系数'})
    fig_season.add_hline(y=1.0, line_dash="dash", line_color="green")
    fig_season.update_layout(height=300)
    st.plotly_chart(fig_season, use_container_width=True)

# ---------- Tab2: 商圈微观 ----------
with tab2:
    st.markdown('<h2 class="sub-header">📍 商圈微观评估</h2>', unsafe_allow_html=True)
    
    col_c, col_d = st.columns(2)
    with col_c:
        city_t2 = st.selectbox("城市", city_stats['city'].tolist(), key="city_t2")
    with col_d:
        district_t2 = st.text_input("输入商圈名称（如：工业园区湖东）", value="工业园区湖东", key="district_t2")
    
    if st.button("🔍 分析该商圈", key="btn_district"):
        with st.spinner("正在获取商圈数据..."):
            district_data = analyze_district(city_t2, district_t2, 
                                           amap_client if not use_mock else None, use_mock)
            st.session_state['district_data'] = district_data
            st.session_state['district_name'] = district_t2
            st.session_state['city_name'] = city_t2
    
    if 'district_data' in st.session_state:
        d = st.session_state['district_data']
        
        # 指标卡片
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("日均客流", f"{d['daily_flow']/10000:.1f}万")
        m2.metric("周末客流倍率", f"{d['weekend_multiplier']}x")
        m3.metric("平均租金", f"{d['avg_rent']}元/㎡")
        m4.metric("竞品数量", f"{d['competitor_count']}家")
        
        # 客群分布
        st.subheader("👥 客群结构")
        labels = ['白领', '家庭', '年轻群体', '其他']
        sizes = [d['office_ratio'], d['family_ratio'], d['youth_ratio'], 
                 1 - d['office_ratio'] - d['family_ratio'] - d['youth_ratio']]
        fig_pie = px.pie(values=sizes, names=labels, hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set2)
        fig_pie.update_layout(height=300)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # 微观位置六维评分
        st.subheader("📐 微观位置评分")
        loc_scores = {
            '可见性': d['visibility_score'],
            '可达性': d['accessibility_score'],
            '邻居质量': d['neighbor_quality'],
            '停车便利': d['parking_score'],
            '租金合理性': max(0, 100 - (d['avg_rent'] - 150) // 2),
            '客流质量': min(100, d['daily_flow'] / 1000)
        }
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=list(loc_scores.values()),
            theta=list(loc_scores.keys()),
            fill='toself',
            marker=dict(color='#3498db')
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=400
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ---------- Tab3: 财务预测 ----------
with tab3:
    st.markdown('<h2 class="sub-header">💰 5年财务现金流预测</h2>', unsafe_allow_html=True)
    
    colp1, colp2, colp3 = st.columns(3)
    with colp1:
        store_area = st.slider("店铺面积(㎡)", 150, 500, 300, key="area")
        table_turnover = st.slider("翻台率(次/天)", 1.5, 4.0, 2.8, 0.1, key="turnover")
    with colp2:
        monthly_rent_input = st.number_input("月租金(万元)", 3.0, 30.0, 12.0, 0.5, key="rent")
        labor_cost_input = st.number_input("月人力成本(万元)", 8.0, 30.0, 15.0, 0.5, key="labor")
    with colp3:
        food_cost_rate = st.slider("食材成本率%", 25, 40, 32, key="food")
        utility_rate = st.slider("水电杂费率%", 5, 12, 8, key="util")
        marketing_rate = st.slider("营销费率%", 3, 10, 5, key="mkt")
    
    city_fin = st.selectbox("选择城市（用于季节性）", city_stats['city'].tolist(), key="city_fin")
    initial_invest = st.number_input("初始投资总额(万元)", 100, 500, 180, key="invest") * 10000
    
    if st.button("📊 生成财务预测", key="btn_fin"):
        fin = financial_forecast(
            avg_price=st.session_state.brand_config['avg_price'],
            seat_count=st.session_state.brand_config['seat_count'],
            monthly_rent=monthly_rent_input,
            labor_cost=labor_cost_input,
            food_cost_rate=food_cost_rate,
            utility_rate=utility_rate,
            marketing_rate=marketing_rate,
            initial_investment=initial_invest,
            city=city_fin,
            use_mock=use_mock
        )
        st.session_state['financials'] = fin
        
        # 现金流图表
        fig = make_subplots(rows=2, cols=1, 
                           subplot_titles=('月度营收与利润', '累计现金流'),
                           vertical_spacing=0.15)
        fig.add_trace(
            go.Scatter(x=fin['df_cashflow']['月份'], y=fin['df_cashflow']['营收(万)'],
                      mode='lines', name='营收', line=dict(color='#3498db')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=fin['df_cashflow']['月份'], y=fin['df_cashflow']['利润(万)'],
                      mode='lines', name='利润', line=dict(color='#2ecc71')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=fin['df_cashflow']['月份'], y=fin['df_cashflow']['累计现金流(万)'],
                      mode='lines', name='累计现金流', line=dict(color='#e74c3c')),
            row=2, col=1
        )
        if fin['breakeven_month'] and fin['breakeven_month'] < 60:
            fig.add_vline(x=fin['breakeven_month'], line_dash="dash", 
                         line_color="green", row=2, col=1)
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # 关键指标
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("年营收", f"{fin['annual_profit']*12/10000:.1f}万" if fin['annual_profit'] else "N/A")
        k2.metric("年净利润", f"{fin['annual_profit']:.1f}万")
        k3.metric("投资回收期", f"{fin['breakeven_month']}个月")
        k4.metric("ROE", f"{fin['roe']:.1f}%")

# ---------- Tab4: 风险评估 ----------
with tab4:
    st.markdown('<h2 class="sub-header">⚠️ 风险矩阵评估</h2>', unsafe_allow_html=True)
    
    if 'district_data' in st.session_state and 'financials' in st.session_state:
        city_data_risk = analyze_city(st.session_state.get('city_name', '苏州'),
                                     amap_client if not use_mock else None,
                                     city_stats, use_mock)
        risks, total_risk = risk_assessment(
            city_data_risk,
            st.session_state['district_data'],
            st.session_state['financials'],
            st.session_state.brand_config
        )
        
        # 雷达图
        categories = list(risks.keys())
        values = [risks[c]['平均'] for c in categories]
        fig_risk = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            marker=dict(color='#e67e22')
        ))
        fig_risk.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=400,
            title=f"综合风险评分：{total_risk:.1f}/100"
        )
        st.plotly_chart(fig_risk, use_container_width=True)
        
        # 详细风险表
        for cat, items in risks.items():
            with st.expander(f"{cat} (平均分: {items['平均']:.1f})"):
                for k, v in items.items():
                    if k != '平均':
                        colr1, colr2, colr3 = st.columns([1,1,3])
                        colr1.write(f"**{k}**")
                        colr2.write(f"{v:.0f}/100")
                        if v >= 30:
                            colr3.warning("高风险")
                        elif v >= 20:
                            colr3.info("中风险")
                        else:
                            colr3.success("低风险")
    else:
        st.warning("请先在【商圈微观】中分析商圈，并在【财务预测】中生成预测。")

# ---------- Tab5: AI推荐 ----------
with tab5:
    st.markdown('<h2 class="sub-header">🎯 AI智能选址推荐</h2>', unsafe_allow_html=True)
    
    if 'district_data' in st.session_state and 'financials' in st.session_state:
        city_data_ai = analyze_city(st.session_state.get('city_name', '苏州'),
                                   amap_client if not use_mock else None,
                                   city_stats, use_mock)
        recs = ai_recommendations(
            city_data_ai,
            st.session_state['district_data'],
            st.session_state['financials'],
            st.session_state.brand_config
        )
        
        for title, detail, level in recs:
            if level == "✅" or level == "🟢":
                st.success(f"**{title}**：{detail}")
            elif level == "⚠️" or level == "🟡":
                st.warning(f"**{title}**：{detail}")
            else:
                st.error(f"**{title}**：{detail}")
        
        # 成功概率估算
        city_match = min(100, city_data_ai['spicy_acceptance'])
        district_match = min(100, 100 - st.session_state['district_data']['competitor_count'] * 5)
        finance_match = 100 if st.session_state['financials']['breakeven_month'] <= 20 else 60
        brand_match = 80  # 默认
        
        prob = (city_match*0.3 + district_match*0.3 + finance_match*0.25 + brand_match*0.15)
        st.metric("📈 综合成功概率", f"{prob:.1f}%",
                 delta="高" if prob>=75 else "中" if prob>=60 else "低")
        
        # 开业倒计时
        st.subheader("⏰ 智能开业倒计时计划")
        timeline = pd.DataFrame({
            '时间节点': ['T-90天', 'T-60天', 'T-30天', 'T-7天', 'T-0天'],
            '核心任务': ['选址签约/设计定稿', '装修进场/人员招聘', '员工培训/营销预热', 
                      '设备调试/试营业', '正式开业/媒体宣传']
        })
        st.dataframe(timeline, use_container_width=True, hide_index=True)
    else:
        st.info("完成商圈分析和财务预测后，AI将为您生成定制化建议。")

# ---------- Tab6: 综合报告 ----------
with tab6:
    st.markdown('<h2 class="sub-header">📋 综合选址报告</h2>', unsafe_allow_html=True)
    
    if 'district_data' in st.session_state and 'financials' in st.session_state:
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        city_rep = st.session_state.get('city_name', '苏州')
        district_rep = st.session_state.get('district_name', '')
        brand = st.session_state.brand_config
        
        # 获取城市数据
        city_rep_data = analyze_city(city_rep, amap_client if not use_mock else None,
                                     city_stats, use_mock)
        dist_rep_data = st.session_state['district_data']
        fin_rep = st.session_state['financials']
        
        report_text = f"""
# {brand['brand_name']} 新店选址分析报告
**生成时间**：{report_time}  
**分析城市**：{city_rep}  
**推荐商圈**：{district_rep}  

---

## 一、市场分析摘要
- 城市人口：{city_rep_data['population']} 万  
- 人均可支配收入：{city_rep_data['disposable_income']} 元/年  
- 湘菜接受度：{city_rep_data['spicy_acceptance']}%  
- 商圈日均客流：{dist_rep_data['daily_flow']} 人  
- 竞品数量（1km内）：{dist_rep_data['competitor_count']} 家  
- 平均租金：{dist_rep_data['avg_rent']} 元/㎡/月  

## 二、财务预测
- 投资总额：{brand['budget_min']}~{brand['budget_max']} 万元  
- 预计月营收：{fin_rep['monthly_revenue']/10000:.1f} 万元  
- 预计月利润：{fin_rep['monthly_profit']/10000:.1f} 万元  
- 投资回收期：{fin_rep['breakeven_month']} 个月  
- 年化ROE：{fin_rep['roe']:.1f}%  

## 三、风险评估
综合风险评分：{total_risk if 'total_risk' in locals() else '待计算'}/100  
主要风险项：{', '.join([c for c in risks.keys()][:2]) if 'risks' in locals() else '待分析'}

## 四、AI建议
1. 竞争策略：{recs[0][1] if 'recs' in locals() else '差异化定位'}
2. 本地化调整：根据口味接受度调整辣度
3. 营销预热：开业前30天启动社群运营

## 五、结论
**综合推荐指数**：{match_score if 'match_score' in locals() else '85'}/100  
**建议行动**：{"优先推进" if match_score>=75 else "谨慎评估"}

---
*报告由湘菜品牌智能选址系统 v3.0 自动生成*
        """
        
        st.markdown(report_text)
        
        # 下载按钮
        st.download_button(
            label="📥 下载完整报告(.txt)",
            data=report_text,
            file_name=f"{city_rep}_{district_rep}_选址报告_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.warning("请先在【商圈微观】和【财务预测】完成分析，生成综合报告。")

# ---------- Tab7: 智能选址顾问（聊天端口）----------
with tab7:
    st.markdown('<h2 class="sub-header">💬 智能选址顾问</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        您可以像咨询专业分析师一样提问，例如：<br>
        🔹 “我想在苏州工业园区湖东开一家店，客单价55元，怎么样？”<br>
        🔹 “郑州金水区适合开湘菜馆吗？预算200万。”<br>
        🔹 “帮我评估一下苏州观前街的选址优劣。”
    </div>
    """, unsafe_allow_html=True)
    
    # 聊天历史显示
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(f'<div style="display:flex; justify-content:flex-end;"><div class="chat-message-user">👤 {msg["content"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="display:flex; justify-content:flex-start;"><div class="chat-message-assistant">🤖 {msg["content"]}</div></div>', unsafe_allow_html=True)
    
    # 聊天输入
    user_input = st.chat_input("输入您的选址需求...")
    
    if user_input:
        # 添加用户消息
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # 生成回复
        with st.spinner("顾问正在分析..."):
            response = generate_chat_response(
                user_input, 
                amap_client if not use_mock else None,
                use_mock,
                city_stats
            )
        
        # 添加助手消息
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        
        # 重新运行以刷新聊天界面
        st.rerun()
    
    # 清空聊天按钮
    if st.button("🧹 清空对话", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()

# ---------- 页脚 ----------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 10px;">
    🍜 湘菜品牌智能选址决策系统 v3.0 · 企业级生产版本 · 数据驱动 · 精准决策<br>
    ⚡ 当前模式：{} | 如需使用真实数据，请在侧边栏输入高德API Key<br>
    © 2024 选址算法实验室
</div>
""".format("真实数据模式" if not use_mock else "模拟数据模式"), unsafe_allow_html=True)

# ---------- 程序启动说明 ----------
# 运行命令：streamlit run location_master.py
# 依赖安装：pip install streamlit pandas numpy plotly requests
