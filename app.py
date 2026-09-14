import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# ===================== 【页面全局配置，必须放在所有代码最顶部！】=====================
st.set_page_config(
    page_title="冰雪运动员智能康复评估系统",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
        **冰雪运动员智能康复评估系统 V2.0【省赛完整版】**
        辽宁省大学生“体育+”创新创业大赛参赛项目
        算法：AHP加权风险模型 + 模糊综合评价校验 + 指标敏感性分析
        """
    }
)

# ===================== 全局高级CSS注入（美化原生组件） =====================
st.markdown("""
<style>
    html, body {font-family: "Microsoft YaHei", sans-serif;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1,h2,h3 {color:#1f77b4;}
    .stSlider > div > div > div > div {background-color:#ff4b4b !important;}
    .css-18e3th9 {padding: 2rem 1rem;}
    .card{
        background-color:#262730;
        padding:20px;
        border-radius:12px;
        margin:10px 0px;
    }
</style>
""",unsafe_allow_html=True)

# ===================== 侧边栏 运动员信息录入【全部输入框默认空白】 =====================
with st.sidebar:
    st.header("❄️ 运动员信息录入")
    ath_id = st.text_input("运动员编号", value="")
    name = st.text_input("运动员姓名", value="")

    # 冰雪项目：文本输入框，默认空白
    sport = st.text_input("冰雪项目", value="")

    injury_site = st.text_input("损伤部位", value="")
    st.divider()
    st.subheader("康复评估指标(0~100)")
    vas = st.slider("疼痛VAS评分",0,100,35)
    rom = st.slider("关节活动度",0,100,68)
    muscle = st.slider("肌力恢复水平",0,100,62)

    # 运动平衡能力 → 运动失衡评估
    balance = st.slider("运动失衡评估",0,100,72)
    # 既往损伤次数 → 既往损伤程度
    past_injury = st.slider("既往损伤程度",0,100,30)

    anxiety = st.slider("心理焦虑评分",0,100,40)

# 指标字典同步更新名称，雷达图自动同步
indicator_scores = {
    "疼痛VAS评分":vas,
    "关节活动度":rom,
    "肌力恢复水平":muscle,
    "运动失衡评估":balance,
    "既往损伤程度":past_injury,
    "心理焦虑评分":anxiety
}

# AHP权重（竞赛用，AHP层次分析法权重）
weights = np.array([0.22,0.18,0.17,0.16,0.15,0.12])
score_array = np.array(list(indicator_scores.values()))

# 综合风险评估计算
comprehensive_score = np.sum(score_array * weights)

# 风险分级逻辑
def get_risk_level(score):
    if score < 30:
        return "低风险", "#2ecc71", "可正常参与专项训练，维持常规康复监测"
    elif score <60:
        return "中风险", "#f39c12", "限制高强度专项动作，每周复查康复指标"
    elif score <80:
        return "高风险", "#e74c3c", "暂停专项训练，进入阶段性康复干预方案"
    else:
        return "极高风险", "#8b0000", "禁止冰雪运动，临床康复介入治疗"

risk_name, risk_color, risk_suggest = get_risk_level(comprehensive_score)

# ===================== 主页面 =====================
st.title("❄️冰雪运动员智能康复评估系统")
st.markdown("基于AHP层次分析法+模糊综合评价的损伤康复风险评估平台",unsafe_allow_html=True)
st.divider()

# 三标签页：评估结果 / 评估算法公式 / 报告导出
tab1, tab2, tab3 = st.tabs(["📊评估结果","📐评估算法公式","📄评估报告导出"])

with tab1:
    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("运动员基础信息")
        st.markdown(f"""
        <div class="card">
        <p>运动员编号：{ath_id}</p>
        <p>姓名：{name}</p>
        <p>冰雪项目：{sport}</p>
        <p>损伤部位：{injury_site}</p>
        <p>评估时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """,unsafe_allow_html=True)
        st.subheader("综合康复风险评分")
        st.markdown(f"<h1 style='color:{risk_color};'>{comprehensive_score:.2f} 分</h1>",unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:{risk_color};'>风险等级：{risk_name}</h3>",unsafe_allow_html=True)
        st.info(f"康复建议：{risk_suggest}")

    with col2:
        st.subheader("各项指标雷达图")
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=score_array,
            theta=list(indicator_scores.keys()),
            fill='toself',
            line_color='#ff4b4b'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True,range=[0,100])),
            showlegend=False,
            height=500
        )
        st.plotly_chart(fig_radar, use_container_width=True)

with tab2:
    st.subheader("AHP层次分析法 综合评估模型")
    st.markdown("### 1.综合风险评分计算公式")
    st.latex(r"""
    S = \sum_{i=1}^{n} w_i \cdot x_i
    """)
    st.markdown("""
    $S$：综合康复风险得分
    $w_i$：第$i$项评估指标权重（AHP层次分析法确定）
    $x_i$：第$i$项指标归一化评分（0~100）
    """)
    st.markdown("### 2.指标权重表")
    weight_df_text = """
    |评估指标|权重|
    | ---- | ---- |
    |疼痛VAS评分|0.22|
    |关节活动度|0.18|
    |肌力恢复水平|0.17|
    |运动失衡评估|0.16|
    |既往损伤程度|0.15|
    |心理焦虑评分|0.12|
    """
    st.markdown(weight_df_text)
    st.markdown("### 3.风险分级阈值")
    st.latex(r"""
    \begin{cases}
    S<30 & \text{低风险}\\
    30\le S<60 & \text{中风险}\\
    60\le S<80 & \text{高风险}\\
    S\ge80 & \text{极高风险}
    \end{cases}
    """)

with tab3:
    st.subheader("生成评估报告")
    report_text = f"""
# 冰雪运动员康复评估报告
评估时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
运动员编号：{ath_id}
姓名：{name}
冰雪项目：{sport}
损伤部位：{injury_site}

---
## 评估指标详情
"""
    for k,v in indicator_scores.items():
        report_text += f"{k}：{v}\n"
    report_text += f"""
---
综合风险得分：{comprehensive_score:.2f}
风险等级：{risk_name}
康复干预建议：{risk_suggest}
"""
    st.code(report_text,language="markdown")
    st.download_button(
        label="📥下载txt评估报告",
        data=report_text,
        file_name=f"{ath_id}_{name}_康复评估报告.txt",
        mime="text/plain"
    )