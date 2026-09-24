import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from io import BytesIO

# ===================== 页面基础配置 =====================
st.set_page_config(
    page_title="冰雪运动员康复评估系统",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注册中文字体（PDF导出中文不乱码）
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_NAME = 'STSong-Light'

# 初始化session_state
if "history" not in st.session_state:
    st.session_state["history"] = []
if "clear_all_flag" not in st.session_state:
    st.session_state["clear_all_flag"] = False

# AHP权重（康复评估指标权重）
weights = np.array([0.25, 0.20, 0.20, 0.15, 0.12, 0.08])
labels = ["疼痛VAS评分", "关节活动度", "肌力恢复水平", "运动失衡评估", "既往损伤程度", "心理焦虑评分"]

# ===================== 侧边栏【兼容旧版本横向滑块】 =====================
with st.sidebar:
    st.header("❄️ 运动员信息录入")

    # 一键清空按钮
    if st.button("🗑️ 一键清空侧边栏全部内容", type="primary"):
        for key in ["ath_id","name","sport","injury_site","vas","rom","muscle","balance","past_injury","anxiety"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["clear_all_flag"] = True
        st.rerun()

    if st.session_state["clear_all_flag"]:
        default_text = ""
        default_slider = 0
        st.session_state["clear_all_flag"] = False
    else:
        default_text = None
        default_slider = None

    ath_id = st.text_input("运动员编号", value=default_text, key="ath_id")
    name = st.text_input("运动员姓名", value=default_text, key="name")
    sport = st.text_input("冰雪项目", value=default_text, key="sport")
    injury_site = st.text_input("损伤部位", value=default_text, key="injury_site")
    st.divider()
    st.subheader("康复评估指标(0~100)")

    # 横向滑块，无 orientation 参数，旧版本streamlit可运行
    col_slide1, col_val1 = st.columns([4,1])
    with col_slide1:
        vas = st.slider("疼痛VAS评分",0,100, value=default_slider, key="vas")
    with col_val1:
        st.markdown(f"**{vas}**")

    col_slide2, col_val2 = st.columns([4,1])
    with col_slide2:
        rom = st.slider("关节活动度",0,100, value=default_slider, key="rom")
    with col_val2:
        st.markdown(f"**{rom}**")

    col_slide3, col_val3 = st.columns([4,1])
    with col_slide3:
        muscle = st.slider("肌力恢复水平",0,100, value=default_slider, key="muscle")
    with col_val3:
        st.markdown(f"**{muscle}**")

    col_slide4, col_val4 = st.columns([4,1])
    with col_slide4:
        balance = st.slider("运动失衡评估",0,100, value=default_slider, key="balance")
    with col_val4:
        st.markdown(f"**{balance}**")

    col_slide5, col_val5 = st.columns([4,1])
    with col_slide5:
        past_injury = st.slider("既往损伤程度",0,100, value=default_slider, key="past_injury")
    with col_val5:
        st.markdown(f"**{past_injury}**")

    col_slide6, col_val6 = st.columns([4,1])
    with col_slide6:
        anxiety = st.slider("心理焦虑评分",0,100, value=default_slider, key="anxiety")
    with col_val6:
        st.markdown(f"**{anxiety}**")

# ===================== 主页面 =====================
st.title("❄️ 冰雪运动员康复评估系统")
st.markdown("基于AHP层次分析法，对冰雪项目运动员损伤康复水平进行综合量化评估")
st.divider()

# ----------------核心改动：负向指标反转----------------
vas_rev = 100 - vas             # 疼痛VAS：输入越高症状越重，转为康复得分越低
past_injury_rev = 100 - past_injury
anxiety_rev = 100 - anxiety

# 送入雷达图与AHP加权计算（全部指标：数值越高，康复状态越好）
score_data = np.array([vas_rev, rom, muscle, balance, past_injury_rev, anxiety_rev])
comprehensive_score = np.sum(score_data * weights)

# 评估等级判定
if comprehensive_score >=80:
    level = "优秀"
    color = "#2ecc71"
    suggestion = "康复状态良好，可逐步恢复专项训练，定期复查"
elif comprehensive_score >=60:
    level = "良好"
    color = "#3498db"
    suggestion = "康复进展平稳，继续维持当前康复方案，控制训练负荷"
elif comprehensive_score >=40:
    level = "一般"
    color = "#f39c12"
    suggestion = "康复存在短板，需要调整康复计划，减少大强度训练"
else:
    level = "较差"
    color = "#e74c3c"
    suggestion = "康复不足，禁止专项训练，优先进行基础康复治疗"

# 布局：左侧雷达图，右侧综合评估
col_main_left, col_main_right = st.columns([3,2])
with col_main_left:
    st.subheader("📊 康复指标雷达图")
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=score_data,
        theta=labels,
        fill='toself',
        name="本次评估",
        line_color='#1f77b4'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        showlegend=True,
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

with col_main_right:
    st.subheader("📋 综合评估结果")
    st.metric(label="综合康复得分", value=f"{comprehensive_score:.2f}")
    st.markdown(f"<h3 style='color:{color}'>评估等级：{level}</h3>", unsafe_allow_html=True)
    st.info(f"康复建议：{suggestion}")
    st.divider()
    st.write("各指标权重(AHP)：")
    weight_df = pd.DataFrame({"评估指标":labels, "权重":weights})
    st.dataframe(weight_df, hide_index=True)

# 保存记录按钮（Excel存储原始输入分数，便于溯源）
if st.button("💾 保存本次评估记录"):
    record = {
        "运动员编号":ath_id,
        "姓名":name,
        "冰雪项目":sport,
        "损伤部位":injury_site,
        "疼痛VAS原始分":vas,
        "关节活动度":rom,
        "肌力恢复水平":muscle,
        "运动失衡评估":balance,
        "既往损伤原始分":past_injury,
        "心理焦虑原始分":anxiety,
        "综合得分":round(comprehensive_score,2),
        "评估等级":level
    }
    st.session_state["history"].append(record)
    st.success("✅ 评估记录已存入历史！")

# 历史记录板块
st.divider()
st.subheader("📜 历史评估记录")
if len(st.session_state["history"]) > 0:
    history_df = pd.DataFrame(st.session_state["history"])
    st.dataframe(history_df, use_container_width=True, hide_index=True)

    # 导出Excel
    buffer_excel = BytesIO()
    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
        history_df.to_excel(writer, index=False, sheet_name="康复记录")
    st.download_button(
        label="📥 导出历史记录Excel",
        data=buffer_excel.getvalue(),
        file_name="冰雪运动员康复评估记录.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 导出PDF评估报告（PDF中同时写入原始评分）
    def create_pdf_report():
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        c.setFont(FONT_NAME, 14)
        c.drawString(120, 800, "冰雪运动员康复评估报告")
        c.setFont(FONT_NAME,11)
        y_pos =760
        c.drawString(80, y_pos, f"运动员编号：{ath_id}")
        y_pos -=25
        c.drawString(80, y_pos, f"姓名：{name}")
        y_pos -=25
        c.drawString(80, y_pos, f"冰雪项目：{sport}")
        y_pos -=25
        c.drawString(80, y_pos, f"损伤部位：{injury_site}")
        y_pos -=35
        c.drawString(80, y_pos, f"疼痛VAS原始评分：{vas}")
        y_pos -=25
        c.drawString(80, y_pos, f"既往损伤原始评分：{past_injury}")
        y_pos -=25
        c.drawString(80, y_pos, f"心理焦虑原始评分：{anxiety}")
        y_pos -=35
        c.drawString(80, y_pos, f"综合康复得分：{comprehensive_score:.2f}")
        y_pos -=25
        c.drawString(80, y_pos, f"评估等级：{level}")
        y_pos -=25
        c.drawString(80, y_pos, f"康复建议：{suggestion}")
        c.save()
        return pdf_buffer.getvalue()

    pdf_data = create_pdf_report()
    st.download_button(
        label="📄 导出本次PDF评估报告",
        data=pdf_data,
        file_name=f"{name}_康复评估报告.pdf",
        mime="application/pdf"
    )
else:
    st.info("暂无历史评估记录，请录入信息后保存")

# 底部系统说明（同步更新文字，消除矛盾）
st.divider()
st.markdown("### 系统说明")
st.markdown("1. 输入评分范围0~100：疼痛、既往损伤、焦虑得分越高代表症状越重；系统内部自动转换后，所有指标用于评估的数值越高代表该项康复状态越好。")
st.markdown("2. 综合得分由AHP层次分析法加权计算得出。")
st.markdown("3. 支持保存历史记录，一键导出Excel档案与PDF评估报告。")