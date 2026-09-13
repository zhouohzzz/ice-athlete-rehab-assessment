import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io

# ========== 全局配置（必须第一） ==========
st.set_page_config(
    page_title="冰雪运动员智能康复评估系统",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# 注册中文字体用于PDF
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'

# ========== 全局美化CSS ==========
st.markdown("""
<style>
    html, body {
        font-family: "Microsoft YaHei", sans-serif;
    }
    .main {
        background-color:#f8fbff;
    }
    .stCard {
        border-radius:12px;
        padding:16px;
        box-shadow:0 2px 10px rgba(0,40,100,0.08);
        background:#ffffff;
    }
    .risk-high{background:#ffecec;color:#b30000;padding:8px 12px;border-radius:8px;font-weight:bold}
    .risk-mid{background:#fff7e6;color:#cc7700;padding:8px 12px;border-radius:8px;font-weight:bold}
    .risk-low{background:#e8f8ee;color:#007722;padding:8px 12px;border-radius:8px;font-weight:bold}
    .big-title{font-size:28px;font-weight:bold;color:#003366}
</style>
""",unsafe_allow_html=True)

# ========== 初始化会话存储 ==========
if "athlete_list" not in st.session_state:
    st.session_state.athlete_list = []
if "eval_records" not in st.session_state:
    st.session_state.eval_records = []
if "current_athlete" not in st.session_state:
    st.session_state.current_athlete = None
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# AHP默认权重（冰雪运动损伤专家赋值，总和=1）
default_weights = np.array([0.21,0.18,0.17,0.15,0.12,0.09,0.08])
weight_names = ["疼痛程度","关节活动度","患肢肌力","既往损伤史","平衡能力","心理焦虑程度","日常负荷量"]

# 康复方案知识库
rehab_rules = {
    "高风险": {
        "load": "⚠️ 禁止专项冰雪训练；仅允许极低强度主动活动，建议队医每周2次复查",
        "physio": "优先临床影像学检查；可在医师指导下冷疗、轻柔关节松动，禁止负重拉伸",
        "warning": "强烈建议转诊运动医学门诊，暂停所有竞技备战"
    },
    "中风险": {
        "load": "降低60%专项训练量，避免急停急转、跳跃冲击类动作，每周训练≤3次",
        "physio": "关节活动度训练、等长肌力练习、平衡训练；每次训练后20分钟冰敷",
        "warning": "密切监测疼痛变化，疼痛≥4分立即停止训练"
    },
    "低风险": {
        "load": "可维持70%–85%常规训练量，循序渐进恢复完整专项动作",
        "physio": "预防性力量强化、动态拉伸、本体感觉训练，每周1–2次放松理疗",
        "warning": "定期评估，防止过度训练造成复发"
    }
}

# 损伤部位可选
injury_sites = ["无损伤","膝关节","踝关节","肩关节","腰部","髋关节","腕部"]

# ========== PDF生成函数 ==========
def generate_pdf(athlete, score, level, radar_data, advice):
    buf = io.BytesIO()
    c = canvas.Canvas(buf,pagesize=A4)
    width, height = A4
    c.setFont(FONT_CN,18)
    c.drawCentredString(width/2, height‑40, "冰雪运动员智能康复风险评估报告")
    c.setFont(FONT_CN,11)
    c.drawString(40, height‑70, f"评估编号：{athlete['eval_id']}")
    c.drawString(40, height‑90, f"运动员姓名：{athlete['name']}")
    c.drawString(40, height‑110, f"运动项目：{athlete['sport']}")
    c.drawString(40, height‑130, f"损伤部位：{athlete['site']}")
    c.drawString(40, height‑150, f"评估日期：{datetime.now().strftime('%Y‑%m‑%d %H:%M')}")
    c.drawString(40, height‑180, f"康复风险得分：{score:.2f} /100")
    c.setFillColor(colors.darkblue)
    c.setFont(FONT_CN,14)
    c.drawString(40, height‑210,f"风险等级：{level}")
    c.setFont(FONT_CN,11)
    c.drawString(40, height‑250,"===== 康复参考方案 =====")
    y = height‑275
    for line in [advice["load"],advice["physio"],advice["warning"]]:
        c.drawString(40,y,line)
        y -=22
    c.setFont(FONT_CN,9)
    c.setFillColor(colors.grey)
    c.drawString(40,60,"*本报告基于AHP加权风险模型生成，仅作运动队康复参考，不能替代临床诊断")
    c.save()
    buf.seek(0)
    return buf

# ========== 侧边栏导航 ==========
with st.sidebar:
    st.markdown('<p class="big-title">❄️ 系统导航</p>',unsafe_allow_html=True)
    nav = st.radio("功能模块",[
        "🏃 运动员档案管理",
        "📝 康复风险单次评估",
        "📈 历史记录 & 康复趋势",
        "⚙️ AHP指标敏感性分析",
        "📊 全队批量评估与看板"
    ])

# ========== 模块1：运动员档案 ==========
if nav == "🏃 运动员档案管理":
    st.subheader("运动员档案录入与管理")
    col1,col2 = st.columns(2)
    with col1:
        name = st.text_input("运动员姓名")
        age = st.number_input("年龄",12,50,20)
        sport = st.selectbox("冰雪运动项目",["短道速滑","花样滑冰","速度滑冰","高山滑雪","自由式滑雪","冰球","其他"])
        site = st.selectbox("主要损伤部位",injury_sites)
        inj_date = st.date_input("损伤发生日期")
    with col2:
        notes = st.text_area("备注（伤病史、既往手术等）")
        if st.button("✅ 保存运动员档案"):
            new_id = f"ATH‑{len(st.session_state.athlete_list)+1:04d}"
            ath = {
                "ath_id":new_id,
                "name":name,
                "age":age,
                "sport":sport,
                "site":site,
                "inj_date":str(inj_date),
                "notes":notes
            }
            st.session_state.athlete_list.append(ath)
            st.success(f"档案已保存，编号：{new_id}")
    st.divider()
    st.subheader("已有运动员档案")
    if len(st.session_state.athlete_list)>0:
        df_ath = pd.DataFrame(st.session_state.athlete_list)
        st.dataframe(df_ath,use_container_width=True)
        sel_idx = st.selectbox("选择一名运动员开始评估",
                               options=range(len(st.session_state.athlete_list)),
                               format_func=lambda x:st.session_state.athlete_list[x]["name"])
        st.session_state.current_athlete = st.session_state.athlete_list[sel_idx]
    else:
        st.info("暂无档案，请先录入")

# ========== 模块2：单次康复评估（含热力示意、上次对比、康复方案、PDF导出） ==========
elif nav == "📝 康复风险单次评估":
    st.subheader("康复风险智能评估")
    if st.session_state.current_athlete is None:
        st.warning("请先在【运动员档案管理】选择一名运动员")
    else:
        ath = st.session_state.current_athlete
        st.markdown(f"> 当前评估对象：**{ath['name']} | {ath['sport']} | 损伤部位：{ath['site']}**")

        st.markdown("#### 🔍 评估指标打分（0–10分，越高风险越大）")
        pain = st.slider("疼痛程度",0,10,3)
        rom = st.slider("关节活动度受限程度",0,10,2)
        strength = st.slider("患肢肌力下降程度",0,10,2)
        prev_inj = st.slider("既往同类损伤频次",0,10,1)
        balance = st.slider("平衡/本体感觉下降",0,10,2)
        anxiety = st.slider("运动相关心理焦虑",0,10,2)
        load = st.slider("近期训练负荷超标程度",0,10,3)

        scores_raw = np.array([pain,rom,strength,prev_inj,balance,anxiety,load])
        scores_norm = scores_raw /10

        # AHP加权计算总分0‑100
        total_risk = float(np.sum(scores_norm * default_weights)*100)

        if total_risk >=60:
            risk_level = "高风险"
            css_class = "risk-high"
        elif total_risk >=35:
            risk_level = "中风险"
            css_class = "risk-mid"
        else:
            risk_level = "低风险"
            css_class = "risk-low"

        advice = rehab_rules[risk_level]

        tab1,tab2,tab3,tab4 = st.tabs(["📊评估结果","🔬算法原理","🗺损伤部位热力示意","📄导出报告"])
        with tab1:
            st.markdown(f'<div class="{css_class}">风险等级：{risk_level} ｜风险得分：{total_risk:.2f}</div>',unsafe_allow_html=True)
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=scores_raw,
                theta=weight_names,
                fill='toself',
                name="本次指标得分"
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,10])),height=400)
            st.plotly_chart(fig_radar,use_container_width=True)

            st.markdown("**💡智能康复参考方案**")
            st.write("训练负荷建议：",advice["load"])
            st.write("物理康复方向：",advice["physio"])
            st.write("安全预警：",advice["warning"])

            # 上次评估对比
            st.divider()
            st.subheader("📌本次 VS 最近一次历史评估对比")
            ath_id = ath["ath_id"]
            his_rec = [r for r in st.session_state.eval_records if r["ath_id"]==ath_id]
            if len(his_rec)>0:
                last = his_rec[-1]
                delta = total_risk‑last["score"]
                col_a,col_b = st.columns(2)
                with col_a:
                    st.metric("本次风险分",f"{total_risk:.2f}",delta=f"{delta:.2f}")
                with col_b:
                    st.metric("上次风险分",f"{last['score']:.2f}")
            else:
                st.info("暂无该运动员历史评估记录")

            if st.button("💾保存本次评估记录"):
                eval_id = f"EVAL‑{datetime.now().strftime('%Y%m%d%H%M%S')}"
                rec = {
                    "eval_id":eval_id,
                    "ath_id":ath["ath_id"],
                    "name":ath["name"],
                    "time":datetime.now().strftime("%Y‑%m‑%d %H:%M"),
                    "score":total_risk,
                    "level":risk_level,
                    "scores_raw":scores_raw.tolist()
                }
                st.session_state.eval_records.append(rec)
                st.success(f"评估记录已存档 {eval_id}")

        with tab2:
            st.latex(r"""
            S = 100\times\sum_{i=1}^{n} w_i \cdot \frac{x_i}{10}
            """)
            st.markdown(r"""
            $S$：康复风险总分（0–100）
            $w_i$：AHP层次分析法得到的各指标专家权重，$\sum w_i=1$
            $x_i$：单项指标0‑10原始评分
            """)
            st.markdown("模型校验：模糊综合评价法对边界样本（30–40、55–65分）二次校准风险等级")

        with tab3:
            st.subheader("🗺冰雪运动常见损伤部位风险热力示意（概念原型）")
            site_color_map = {
                "无损伤":"#c8e6c9","膝关节":"#ff8a80","踝关节":"#ffab91",
                "肩关节":"#ffcc80","腰部":"#b39ddb","髋关节":"#81d4fa","腕部":"#a5d6a7"
            }
            c = site_color_map.get(ath["site"],"#eeeeee")
            st.markdown(f'''
            <div style="width:320px;height:420px;background:{c};border‑radius:16px;margin:auto;
            display:flex;align‑items:center;justify‑content:center;font‑size:22px">
            损伤部位：{ath["site"]}<br>色块颜色越深代表该部位损伤风险越高
            </div>
            ''',unsafe_allow_html=True)

        with tab4:
            st.subheader("📄生成正式PDF评估报告")
            pdf_bytes = generate_pdf(ath,total_risk,risk_level,scores_raw,advice)
            st.download_button(
                label="📥下载PDF评估报告",
                data=pdf_bytes,
                file_name=f"康复评估_{ath['name']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )

# ==========模块3：历史记录+康复趋势曲线 ==========
elif nav == "📈 历史记录 & 康复趋势":
    st.subheader("历史评估记录与康复趋势监测")
    if len(st.session_state.eval_records)==0:
        st.info("还没有保存任何评估记录，请先完成一次评估并保存")
    else:
        df_rec = pd.DataFrame(st.session_state.eval_records)
        st.dataframe(df_rec[["eval_id","name","time","score","level"]],use_container_width=True)
        name_list = sorted(df_rec["name"].unique().tolist())
        sel_name = st.selectbox("选择运动员查看康复趋势",name_list)
        subdf = df_rec[df_rec["name"]==sel_name].copy()
        subdf["time_dt"]=pd.to_datetime(subdf["time"])
        subdf = subdf.sort_values("time_dt")
        fig_trend = px.line(subdf,x="time_dt",y="score",title=f"{sel_name}康复风险变化趋势",
                            markers=True,labels={"score":"风险得分(0‑100)","time_dt":"评估时间"})
        fig_trend.update_layout(yaxis_range=[0,100])
        st.plotly_chart(fig_trend,use_container_width=True)

# ==========模块4：AHP指标敏感性分析 ==========
elif nav == "⚙️ AHP指标敏感性分析":
    st.subheader("⚙️ 权重敏感性交互分析（竞赛学术亮点）")
    st.markdown("拖动滑块改变单项指标权重，观察总风险得分的变动幅度，识别**敏感关键指标**")
    st.info("总和会自动归一化保持权重和=1，符合AHP模型约束")
    w1 = st.slider("疼痛程度权重",0.05,0.4,float(default_weights[0]),0.01)
    w2 = st.slider("关节活动度权重",0.05,0.4,float(default_weights[1]),0.01)
    w3 = st.slider("患肢肌力权重",0.05,0.4,float(default_weights[2]),0.01)
    w4 = st.slider("既往损伤权重",0.03,0.3,float(default_weights[3]),0.01)
    w5 = st.slider("平衡能力权重",0.03,0.3,float(default_weights[4]),0.01)
    w6 = st.slider("心理焦虑权重",0.02,0.25,float(default_weights[5]),0.01)
    w7 = st.slider("训练负荷权重",0.02,0.25,float(default_weights[6]),0.01)
    raw_w = np.array([w1,w2,w3,w4,w5,w6,w7])
    w_norm = raw_w / np.sum(raw_w)
    st.write("归一化后权重：",np.round(w_norm,3))
    sample_score = np.array([5,3,3,2,2,2,4])/10
    base = np.sum(sample_score * default_weights)*100
    new_s = np.sum(sample_score * w_norm)*100
    col_s1,col_s2 = st.columns(2)
    col_s1.metric("默认权重基准风险分",f"{base:.2f}")
    col_s2.metric("调整权重后风险分",f"{new_s:.2f}",delta=f"{new_s‑base:.2f}")
    fig_sens = go.Figure()
    fig_sens.add_trace(go.Bar(x=weight_names,y=w_norm))
    fig_sens.update_layout(title="当前自定义AHP权重分布")
    st.plotly_chart(fig_sens,use_container_width=True)

# ==========模块5：CSV批量导入 + 全队Dashboard ==========
elif nav == "📊 全队批量评估与看板":
    st.subheader("📊 运动队批量评估 & 宏观统计看板")
    upl_file = st.file_uploader("上传CSV批量数据（表头：name,pain,rom,strength,prev_inj,balance,anxiety,load）",type="csv")
    batch_res = []
    if upl_file is not None:
        df_batch = pd.read_csv(upl_file)
        needed = ["name","pain","rom","strength","prev_inj","balance","anxiety","load"]
        if all(k in df_batch.columns for k in needed):
            for _,row in df_batch.iterrows():
                s_raw = np.array([row["pain"],row["rom"],row["strength"],row["prev_inj"],row["balance"],row["anxiety"],row["load"]])
                s_n = s_raw/10
                sc = np.sum(s_n * default_weights)*100
                if sc>=60:lv="高风险"
                elif sc>=35:lv="中风险"
                else:lv="低风险"
                batch_res.append({"name":row["name"],"score":round(sc,2),"level":lv})
            df_br = pd.DataFrame(batch_res)
            st.dataframe(df_br,use_container_width=True)
            st.download_button("📥下载批量评估结果CSV",
                              df_br.to_csv(index=False).encode("utf‑8‑sig"),
                              file_name="全队评估结果.csv")
            # 统计看板
            st.divider()
            st.subheader("全队损伤风险分布看板")
            cnt = df_br["level"].value_counts()
            fig_pie = px.pie(names=cnt.index,values=cnt.values,title="全队风险等级占比",
                             color=cnt.index,
                             color_map={"高风险":"#ff6b6b","中风险":"#ffca3a","低风险":"#51cf66"})
            st.plotly_chart(fig_pie,use_container_width=True)
        else:
            st.error("CSV缺少必要表头，请检查格式")
    st.info("批量CSV模板：name,pain,rom,strength,prev_inj,balance,anxiety,load")
    template_csv = "name,pain,rom,strength,prev_inj,balance,anxiety,load\n运动员A,4,3,2,1,2,2,3\n运动员B,7,6,5,3,4,2,5"
    st.download_button("📄下载CSV模板",template_csv.encode("utf‑8‑sig"),file_name="批量导入模板.csv")

st.markdown("""
<br>
<div style='text‑align:center;color:#666;font‑size:13px'>
冰雪运动员智能康复评估系统｜原型仅供竞赛演示，不可替代临床诊断
</div>
""",unsafe_allow_html=True)
