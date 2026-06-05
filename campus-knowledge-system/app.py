import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from difflib import get_close_matches
import re

# ---------- 页面配置 ----------
st.set_page_config(page_title="校内人员图谱", page_icon="🏫", layout="wide")

st.markdown("""
<style>
    .stButton button {
        border-radius: 20px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.02);
        background-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏫 校内人员图谱构建与信息查询")
st.markdown("> **动态子图版**：根据您的问题自动生成对应的知识图谱子图 | 支持模糊匹配、多跳推理")

# ---------- 全局数据 ----------
PERSONS = {
    "李教授": {"type": "教师", "dept": "计算机学院", "title": "教授", "office": "信息楼301", "students": ["张三","李四","王芳"], "colleagues": ["张教授","王教授"]},
    "张教授": {"type": "教师", "dept": "计算机学院", "title": "教授", "office": "信息楼302", "students": ["赵强","孙丽"], "colleagues": ["李教授","王教授"]},
    "王教授": {"type": "教师", "dept": "数学学院", "title": "教授", "office": "数学楼201", "students": ["刘伟","陈晨"], "colleagues": ["李教授","张教授"]},
    "张三": {"type": "学生", "dept": "计算机学院", "major": "计算机科学与技术", "advisor": "李教授", "year": 2022},
    "李四": {"type": "学生", "dept": "计算机学院", "major": "软件工程", "advisor": "李教授", "year": 2023},
    "王芳": {"type": "学生", "dept": "计算机学院", "major": "人工智能", "advisor": "李教授", "year": 2021},
    "赵强": {"type": "学生", "dept": "计算机学院", "major": "计算机科学与技术", "advisor": "张教授", "year": 2022},
    "孙丽": {"type": "学生", "dept": "计算机学院", "major": "网络工程", "advisor": "张教授", "year": 2023},
    "刘伟": {"type": "学生", "dept": "数学学院", "major": "应用数学", "advisor": "王教授", "year": 2022},
    "陈晨": {"type": "学生", "dept": "数学学院", "major": "统计学", "advisor": "王教授", "year": 2023}
}

DEPT_INFO = {
    "计算机学院": {"location": "信息楼", "dean": "李教授"},
    "数学学院": {"location": "数学楼", "dean": "王教授"}
}

@st.cache_resource
def build_full_graph():
    """构建完整的NetworkX图（指导关系 + 同事关系）"""
    G = nx.Graph()
    # 添加所有人员节点
    for name in PERSONS:
        G.add_node(name, type=PERSONS[name]["type"])
    # 指导关系（有向，但绘图时用无向边+箭头样式，这里仍存为无向边并标记relation）
    for teacher, info in PERSONS.items():
        if info["type"] == "教师":
            for student in info.get("students", []):
                G.add_edge(teacher, student, relation="指导")
    # 同事关系
    for teacher, info in PERSONS.items():
        if info["type"] == "教师":
            for col in info.get("colleagues", []):
                G.add_edge(teacher, col, relation="同事")
    return G

G_full = build_full_graph()

def extract_entities_from_question(question):
    """从问题中提取人名（精确匹配 + 模糊匹配）"""
    candidates = list(PERSONS.keys())
    # 精确匹配
    found = [name for name in candidates if name in question]
    # 模糊匹配（如果精确匹配为0，则尝试模糊）
    if not found:
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', question)
        for w in words:
            match = get_close_matches(w, candidates, n=1, cutoff=0.6)
            if match:
                found.append(match[0])
    return list(set(found))

def get_subgraph(entities, G, hops=1):
    """根据实体列表提取子图：包含这些实体及其hops跳邻居"""
    if not entities:
        return G  # 返回全图
    nodes_to_keep = set(entities)
    for ent in entities:
        neighbors = list(nx.single_source_shortest_path_length(G, ent, cutoff=hops).keys())
        nodes_to_keep.update(neighbors)
    return G.subgraph(nodes_to_keep).copy()

def draw_subgraph(question, G_full):
    """根据问题绘制子图，高亮问题中涉及的实体"""
    entities = extract_entities_from_question(question)
    subG = get_subgraph(entities, G_full, hops=1)
    fig, ax = plt.subplots(figsize=(8, 6))
    pos = nx.spring_layout(subG, seed=42, k=1.5)
    
    # 节点颜色：教师红色，学生蓝色，高亮实体黄色
    node_colors = []
    for node in subG.nodes():
        if node in entities:
            node_colors.append("#FFD700")  # 金黄色高亮
        elif PERSONS[node]["type"] == "教师":
            node_colors.append("#FF6B6B")
        else:
            node_colors.append("#4D9DE0")
    nx.draw_networkx_nodes(subG, pos, ax=ax, node_color=node_colors, node_size=1200, alpha=0.9)
    nx.draw_networkx_labels(subG, pos, ax=ax, font_size=10, font_weight="bold")
    
    # 边：指导关系用绿色实线箭头，同事关系橙色虚线
    edges_advise = [(u,v) for u,v,d in subG.edges(data=True) if d.get('relation')=='指导']
    edges_colleague = [(u,v) for u,v,d in subG.edges(data=True) if d.get('relation')=='同事']
    if edges_advise:
        nx.draw_networkx_edges(subG, pos, edgelist=edges_advise, ax=ax, edge_color="green", width=2, arrows=True, arrowstyle='->', arrowsize=15)
    if edges_colleague:
        nx.draw_networkx_edges(subG, pos, edgelist=edges_colleague, ax=ax, edge_color="orange", width=2, style='dashed')
    ax.set_title(f"动态知识图谱（涉及：{', '.join(entities) if entities else '全部节点'}）", fontsize=12)
    ax.axis('off')
    return fig

# ---------- 推理引擎（与原版类似，加入多跳）----------
def reason(question):
    q = question.lower()
    original = question
    entities = extract_entities_from_question(original)
    
    # 1. 教师的学生
    if "学生" in q and any(name in original for name, info in PERSONS.items() if info["type"]=="教师"):
        for teacher in [n for n,info in PERSONS.items() if info["type"]=="教师"]:
            if teacher in original or (entities and teacher == entities[0]):
                students = PERSONS[teacher].get("students", [])
                if students:
                    return f"👨‍🏫 **{teacher}** 指导的学生：{', '.join(students)}。"
                return f"👨‍🏫 **{teacher}** 暂无学生。"
    
    # 2. 学生的导师
    if ("导师" in q or "指导老师" in q) and any(name in original for name, info in PERSONS.items() if info["type"]=="学生"):
        for student in [n for n,info in PERSONS.items() if info["type"]=="学生"]:
            if student in original or (entities and student == entities[0]):
                advisor = PERSONS[student].get("advisor")
                if advisor:
                    return f"🎓 **{student}** 的导师是 **{advisor}**。"
                return f"🎓 未找到 {student} 的导师。"
    
    # 3. 同事关系查询
    if "是同事吗" in q and len(entities) >= 2:
        a,b = entities[0], entities[1]
        if (b in PERSONS[a].get("colleagues", [])) or (a in PERSONS[b].get("colleagues", [])):
            return f"🤝 **{a}** 和 **{b}** 是同事。"
        else:
            return f"❌ **{a}** 和 **{b}** 不是同事。"
    
    # 4. 院系归属
    if "院系" in q or "哪个学院" in q:
        for name in entities:
            dept = PERSONS[name].get("dept")
            if dept:
                return f"🏛️ **{name}** 属于 **{dept}**。"
    
    # 5. 办公室
    if "办公室" in q or "在哪" in q:
        for name in entities:
            if PERSONS[name]["type"] == "教师":
                office = PERSONS[name].get("office")
                if office:
                    return f"📌 **{name}** 的办公室在 **{office}**。"
    
    # 6. 院系信息
    for dept, info in DEPT_INFO.items():
        if dept in original:
            return f"🏢 **{dept}** 位于 **{info['location']}**，院长是 **{info['dean']}**。"
    
    # 7. 列表查询
    if "所有教师" in q:
        teachers = [n for n,info in PERSONS.items() if info["type"]=="教师"]
        return f"👨‍🏫 教师名单（{len(teachers)}人）：{', '.join(teachers)}"
    if "所有学生" in q:
        students = [n for n,info in PERSONS.items() if info["type"]=="学生"]
        return f"🎓 学生名单（{len(students)}人）：{', '.join(students)}"
    
    # 8. 多跳：学生的导师的学生
    if "导师的学生" in q and entities:
        for student in [n for n,info in PERSONS.items() if info["type"]=="学生"]:
            if student in original or (entities and student == entities[0]):
                advisor = PERSONS[student].get("advisor")
                if advisor:
                    students_of_advisor = PERSONS[advisor].get("students", [])
                    return f"🔗 {student} 的导师是 {advisor}，{advisor} 还指导了：{', '.join(students_of_advisor)}"
                break
    
    # 默认帮助
    return help_message()

def help_message():
    return """
    💡 **支持的问题类型：**
    - 教师的学生：`李教授的学生有哪些？`
    - 学生的导师：`张三的导师是谁？`
    - 同事关系：`李教授和张教授是同事吗？`
    - 院系归属：`张三属于哪个学院？`
    - 办公室：`李教授的办公室在哪？`
    - 院系信息：`计算机学院在哪？`
    - 列表查询：`所有教师`、`所有学生`
    - 多跳推理：`张三的导师的学生有哪些？`
    """

# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("📊 快速统计")
    st.metric("教师", len([n for n,info in PERSONS.items() if info["type"]=="教师"]))
    st.metric("学生", len([n for n,info in PERSONS.items() if info["type"]=="学生"]))
    st.divider()
    st.caption("💡 右侧图谱会根据您的问题动态变化，高亮涉及的人物。")

# ---------- 主界面布局 ----------
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("✨ 智能问答")
    # 示例问题按钮
    ex_qs = [
        "李教授的学生有哪些？", "张三的导师是谁？", "李教授和张教授是同事吗？",
        "所有教师", "张三属于哪个学院？", "张三的导师的学生有哪些？"
    ]
    for i in range(0, len(ex_qs), 2):
        cols = st.columns(2)
        for j in range(2):
            if i+j < len(ex_qs):
                if cols[j].button(ex_qs[i+j], key=f"ex_{i+j}", use_container_width=True):
                    st.session_state["question"] = ex_qs[i+j]
                    st.rerun()
    st.divider()
    
    question = st.text_input("💬 输入你的问题：", value=st.session_state.get("question", ""), key="question_input")
    if st.button("🔍 开始推理", type="primary", use_container_width=True):
        if question:
            with st.spinner("推理中..."):
                answer = reason(question)
            st.success("✅ 推理结果")
            st.info(answer)
            # 推理过程（简单展示）
            with st.expander("📐 推理路径"):
                st.markdown("**涉及实体：**")
                entities = extract_entities_from_question(question)
                if entities:
                    for e in entities:
                        st.write(f"- {e}（{PERSONS[e]['type']}）")
                else:
                    st.write("未识别到具体人物，显示全图")
            # 将问题暂存，用于右侧绘图
            st.session_state["last_question"] = question
        else:
            st.warning("请输入问题")

# 右侧动态图谱（根据最近一次推理的问题）
with col_right:
    st.subheader("🗺️ 动态知识图谱")
    last_q = st.session_state.get("last_question", "")
    if last_q:
        fig = draw_subgraph(last_q, G_full)
        st.pyplot(fig)
    else:
        # 默认显示全图（或欢迎图）
        fig = draw_subgraph("", G_full)  # 空字符串会显示全图
        st.pyplot(fig)
    st.caption("绿色箭头：指导关系 | 橙色虚线：同事关系 | 黄色节点：问题中涉及的人物")

st.divider()
st.caption("🏫 校内人员图谱 | 动态子图 | 支持模糊匹配、多跳推理")