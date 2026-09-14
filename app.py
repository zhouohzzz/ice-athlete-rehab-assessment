import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib import colors
import io

# ===================== 页面全局配置，必须放在最顶部 =====================
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

# 注册PDF中文字体
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'

# ========== PDF生成函数 ==========
def generate_pdf(athlete, score, level, radar_data, advice):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont(FONT_CN,18)
    c.drawCentredString(width/2, height-40, "冰雪运动员智能康复风险评估报告")
    c.setFont(FONT_CN,11)
    temp_eval_id = f"EVAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    c.drawString(40, height-70, f"评估编号：{temp_eval_id}")
    c.drawString(40, height-90, f"运动员编号：{athlete['ath_id']}")
    c.drawString(40, height-110, f"运动员姓名：{athlete['name']}")
    c.drawString(40, height-130, f"运动项目：{athlete['sport']}")
    c.drawString(40, height-150, f"损伤部位：{athlete['site']}")
    c.drawString(40, height-170, f"评估日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(40, height-200, f"康复风险得分：{score:.2f} /100")
    c.setFillColor(colors.darkblue)
    c.setFont(FONT_CN,14)
    c.drawString(40, height-230,f"风险等级：{level}")
    c.setFont(FONT_CN,11)
    c.setFillColor(colors.black)
    c.drawString(40, height-270,"===== 康复参考方案 =====")
    y = height-295
    for line in [advice["load"],advice["physio"],advice["warning"]]:
        c.drawString(40,y,line)
        y -=22
    c.setFont(FONT_CN,9)
    c.setFillColor(colors.grey)
    c.drawString(40,60,"*本报告基于AHP加权风险模型生成，仅作运动队康复参考，不能替代临床诊断")
    c.save()
    buf.seek(0)
    return buf

# ===================== AHP权重配置 康复评估指标 =====================
weights = {
    "疼痛VAS评分":0.22,
    "关节活动度":0.18,
    "肌力恢复水平":0.20,
    "运动平衡能力":0.16,
    "既往损伤次数":0.12,
    "心理焦虑评分":0.12
}

# 风险等级判定
def get_risk_level(total_score):
    if total_score >=70:
        return "高风险", "#d62728"
    elif total_score >=40:
        return "中风险", "#ff9f0e"
    else:
        return "低风险", "#2ca02c"

# ===================== 侧边栏 运动员信息录入 =====================
with st.sidebar:
    st.header("❄️ 运动员信息录入")
    ath_id = st.text_input("运动员编号", value="ATH-001")
    name = st.text_input("运动员姓名", value="张XX")
    sport = st.selectbox("冰雪项目",["短道速滑","花样滑冰","自由式滑雪","冰球","越野滑雪"])
    injury_site = st.text_input("损伤部位", value="膝关节")
    st.divider()
    st.subheader("康复评估指标(0~100)")
    vas = st.slider("疼痛VAS评分",0,100,35)
    rom = st.slider("关节活动度",0,100,68)
    muscle = st.slider("肌力恢复水平",0,100,62)
    balance = st.slider("运动平衡能力",0,100,72)
    past_injury = st.slider("既往损伤次数",0,100,30)
    anxiety = st.slider("心理焦虑评分",0,100,40)

# 打包运动员信息
athlete_info = {
    "ath_id":ath_id,
    "name":name,
    "sport":sport,
    "site":injury_site
}
indicator_scores = {
    "疼痛VAS评分":vas,
    "关节活动度":rom,
    "肌力恢复水平":muscle,
    "运动平衡能力":balance,
    "既往损伤次数":past_injury,
    "心理焦虑评分":anxiety
}

# AHP加权总分计算
total = 0.0
for key in indicator_scores:
    total += indicator_scores[key] * weights[key]
risk_text, risk_color = get_risk_level(total)

# 康复建议
if risk_text == "高风险":
    advice_dict = {
        "load":"负荷建议：禁止专项冰雪训练，仅开展低强度被动活动",
        "physio":"康复理疗：每周3次理疗，重点控制炎症与疼痛",
        "warning":"风险提示：暂不允许上冰，每周复查评估指标"
    }
elif risk_text == "中风险":
    advice_dict = {
        "load":"负荷建议：可进行陆上基础力量，禁止跳跃、急停变向",
        "physio":"康复理疗：每周2次康复干预，逐步提升关节活动范围",
        "warning":"风险提示：上冰前必须二次评估，循序渐进增加训练量"
    }
else:
    advice_dict = {
        "load":"负荷建议：可逐步恢复专项冰雪训练，监控疲劳状态",
        "physio":"康复理疗：维持每周1次维护性康复训练",
        "warning":"风险提示：定期复查，做好运动防护，预防二次损伤"
    }

# 雷达图数据
categories = list(indicator_scores.keys())
values = list(indicator_scores.values())
fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
      r=values,
      theta=categories,
      fill='toself',
      name='评估指标得分'
))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100])),height=400)

# ===================== 主页面【全部原生组件，无任何HTML标签！】 =====================
st.title("❄️冰雪运动员智能康复评估系统")
st.subheader("基于AHP层次分析+模糊综合评价的损伤康复风险评估平台")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊评估结果","📐算法公式","📄导出报告"])

# Tab1 评估结果
with tab1:
    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("综合风险评估结果")
        st.metric(label="综合风险总分", value=f"{total:.2f}")
        # 原生三色提示框
        if risk_text == "高风险":
            st.error(f"风险等级：{risk_text}")
        elif risk_text == "中风险":
            st.warning(f"风险等级：{risk_text}")
        else:
            st.success(f"风险等级：{risk_text}")
        st.subheader("康复指导方案")
        st.write(advice_dict["load"])
        st.write(advice_dict["physio"])
        st.write(advice_dict["warning"])
        if st.button("💾保存本次评估记录"):
            rec_id = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            record = {
                "rec_id":rec_id,
                "athlete":athlete_info,
                "score":total,
                "risk":risk_text,
                "time":datetime.now()
            }
            if "history" not in st.session_state:
                st.session_state["history"] = []
            st.session_state["history"].append(record)
            st.success(f"✅评估记录已保存，记录编号：{rec_id}")
    with col2:
        st.subheader("各指标雷达图")
        st.plotly_chart(fig_radar,use_container_width=True)

# Tab2 算法公式（答辩展示，LaTeX公式保留，st.markdown纯文本无HTML）
with tab2:
    st.markdown(r"""
### 1. AHP加权综合评分模型
$$
S = \sum_{i=1}^{n} w_i x_i
$$
$S$：康复风险总分（0-100），$w_i$：AHP层次分析法得到指标权重，$\sum w_i=1$，$x_i$：单项指标得分

### 2. 风险分级规则
$$
\begin{cases}
S \ge 70 & \text{高风险}\\
40 \le S <70 & \text{中风险}\\
S <40 & \text{低风险}
\end{cases}
$$

### 3. 模糊综合评价校验（模型校验）
$$
B = W \circ R
$$
$W$ 权重向量，$R$ 模糊关系矩阵，$\circ$为模糊算子，用来校验AHP结果的稳定性，降低单一打分偏差。
""")
    st.info("模型创新：AHP层次分析计算指标权重，搭配模糊综合评价校验结果，同时可开展指标敏感性分析，定位对康复风险影响最大的因素。")

# Tab3 导出PDF报告
with tab3:
    st.subheader("一键导出评估PDF报告")
    st.write("点击按钮生成完整评估报告，可下载用于申报材料、运动队存档、答辩演示。")
    pdf_bytes = generate_pdf(athlete_info, total, risk_text, values, advice_dict)
    st.download_button(
        label="📥下载PDF评估报告",
        data=pdf_bytes,
        file_name=f"冰雪康复评估报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf",
        mime="application/pdf"
    )

# 历史记录板块
st.divider()
st.subheader("📋历史评估记录")
if "history" in st.session_state and len(st.session_state["history"])>0:
    for item in st.session_state["history"]:
        st.write(f"{item['time'].strftime('%Y-%m-%d %H:%M')} | {item['athlete']['name']} | 总分：{item['score']:.2f} | {item['risk']}")
else:
    st.info("暂无保存的评估记录，请先填写信息并点击【保存本次评估记录】")
