import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import re
from difflib import get_close_matches

# ---------- 页面配置 ----------
st.set_page_config(page_title="校内人员图谱", page_icon="🏫", layout="wide")

# 自定义CSS（更美观的卡片效果）
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
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .info-card {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏫 校内人员图谱构建与信息查询")
st.markdown("> **升级版**：基于知识图谱 + 规则推理 | 支持可视化、模糊匹配、多跳推理")

# ---------- 数据（知识图谱）----------
# 使用字典模拟图，同时为了可视化，我们再维护一个 NetworkX 图
@st.cache_resource
def get_graph():
    G = nx.Graph()
    # 添加节点和边（关系）
    # 人员节点
    persons = [
        "李教授", "张教授", "王教授",
        "张三", "李四", "王芳", "赵强", "孙丽", "刘伟", "陈晨"
    ]
    G.add_nodes_from(persons, type="person")
    
    # 关系边
    # 指导关系 (导师->学生)
    edges = [
        ("李教授", "张三"), ("李教授", "李四"), ("李教授", "王芳"),
        ("张教授", "赵强"), ("张教授", "孙丽"),
        ("王教授", "刘伟"), ("王教授", "陈晨")
    ]
    G.add_edges_from(edges, relation="指导")
    # 同事关系
    colleagues = [("李教授", "张教授"), ("李教授", "王教授"), ("张教授", "王教授")]
    G.add_edges_from(colleagues, relation="同事")
    
    return G

G = get_graph()

# 详细的人员信息字典（用于属性查询）
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

# ---------- 辅助函数 ----------
def fuzzy_match(name, candidates):
    """模糊匹配人名，支持拼音首字母？这里简单用 difflib"""
    matches = get_close_matches(name, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_all_names():
    return list(PERSONS.keys())

def get_teachers():
    return [n for n, info in PERSONS.items() if info["type"] == "教师"]

def get_students():
    return [n for n, info in PERSONS.items() if info["type"] == "学生"]

# ---------- 核心推理引擎（支持多跳）----------
def reason(question):
    q = question.lower()
    original = question
    # 提取所有可能出现的人名（先精确匹配，再模糊）
    all_names = get_all_names()
    mentioned_names = []
    for name in all_names:
        if name in original:
            mentioned_names.append(name)
    # 如果没匹配到，尝试模糊匹配
    if not mentioned_names:
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', original)  # 提取中文词
        for w in words:
            matched = fuzzy_match(w, all_names)
            if matched:
                mentioned_names.append(matched)
    mentioned_names = list(set(mentioned_names))  # 去重
    
    # 1. 单跳查询：教师的学生
    if "学生" in q and any(name in original for name in get_teachers()):
        for teacher in get_teachers():
            if teacher in original or (mentioned_names and teacher == mentioned_names[0]):
                students = PERSONS[teacher].get("students", [])
                if students:
                    return f"👨‍🏫 **{teacher}** 指导的学生：{', '.join(students)}。"
                return f"👨‍🏫 **{teacher}** 暂无学生。"
    
    # 2. 学生的导师
    if ("导师" in q or "指导老师" in q) and any(name in original for name in get_students()):
        for student in get_students():
            if student in original or (mentioned_names and student == mentioned_names[0]):
                advisor = PERSONS[student].get("advisor")
                if advisor:
                    return f"🎓 **{student}** 的导师是 **{advisor}**。"
                return f"🎓 未找到 {student} 的导师。"
    
    # 3. 同事关系查询（是否是同事）
    if "是同事吗" in q or "和" in q and "同事" in q:
        # 提取两个名字
        if len(mentioned_names) >= 2:
            a, b = mentioned_names[0], mentioned_names[1]
            if (b in PERSONS[a].get("colleagues", [])) or (a in PERSONS[b].get("colleagues", [])):
                return f"🤝 **{a}** 和 **{b}** 是同事。"
            else:
                return f"❌ **{a}** 和 **{b}** 不是同事。"
    
    # 4. 查询院系
    if "院系" in q or "哪个学院" in q:
        for name in mentioned_names:
            dept = PERSONS[name].get("dept")
            if dept:
                return f"🏛️ **{name}** 属于 **{dept}**。"
    
    # 5. 办公室位置
    if "办公室" in q or "在哪" in q:
        for name in mentioned_names:
            if PERSONS[name]["type"] == "教师":
                office = PERSONS[name].get("office")
                if office:
                    return f"📌 **{name}** 的办公室在 **{office}**。"
    
    # 6. 院系信息查询
    for dept, info in DEPT_INFO.items():
        if dept in original:
            return f"🏢 **{dept}** 位于 **{info['location']}**，院长是 **{info['dean']}**。"
    
    # 7. 全校列表
    if "所有教师" in q:
        return f"👨‍🏫 教师名单（{len(get_teachers())}人）：{', '.join(get_teachers())}"
    if "所有学生" in q:
        return f"🎓 学生名单（{len(get_students())}人）：{', '.join(get_students())}"
    
    # 8. 多跳推理示例：学生的导师的学生（二层）
    if "导师的学生" in q and any(name in original for name in get_students()):
        for student in get_students():
            if student in original:
                advisor = PERSONS[student].get("advisor")
                if advisor:
                    students_of_advisor = PERSONS[advisor].get("students", [])
                    return f"🔗 {student} 的导师是 {advisor}，{advisor} 还指导了：{', '.join(students_of_advisor)}"
                break
    
    # 9. 关系路径（例如：李教授-张三-? 可扩展）
    if "路径" in q and len(mentioned_names) >= 2:
        try:
            path = nx.shortest_path(G, source=mentioned_names[0], target=mentioned_names[1])
            edge_labels = []
            for i in range(len(path)-1):
                edge_data = G.get_edge_data(path[i], path[i+1])
                relation = edge_data.get('relation', '未知')
                edge_labels.append(f"{path[i]} -{relation}-> {path[i+1]}")
            return " → ".join(edge_labels)
        except nx.NetworkXNoPath:
            return f"❌ 未找到 {mentioned_names[0]} 到 {mentioned_names[1]} 的路径。"
    
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
    - 路径查询：`李教授 到 刘伟 的关系路径`
    """

# ---------- 可视化图谱（使用 matplotlib） ----------
def draw_graph():
    fig, ax = plt.subplots(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42, k=1.5)
    # 节点颜色：教师红色，学生蓝色
    node_colors = []
    for node in G.nodes():
        if PERSONS[node]["type"] == "教师":
            node_colors.append("#FF6B6B")
        else:
            node_colors.append("#4D9DE0")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=1200, alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight="bold")
    # 边：指导关系实线，同事关系虚线
    edges_advise = [(u,v) for u,v,d in G.edges(data=True) if d.get('relation')=='指导']
    edges_colleague = [(u,v) for u,v,d in G.edges(data=True) if d.get('relation')=='同事']
    nx.draw_networkx_edges(G, pos, edgelist=edges_advise, ax=ax, edge_color="green", width=2, arrows=True, arrowstyle='->', arrowsize=15)
    nx.draw_networkx_edges(G, pos, edgelist=edges_colleague, ax=ax, edge_color="orange", width=2, style='dashed')
    ax.set_title("校内人员知识图谱", fontsize=16)
    ax.axis('off')
    return fig

# ---------- 侧边栏：数据管理（动态添加临时人员）----------
with st.sidebar:
    st.header("📊 图谱概览")
    st.metric("👨‍🏫 教师", len(get_teachers()))
    st.metric("🎓 学生", len(get_students()))
    st.divider()
    
    # 动态添加人员（仅会话内有效，演示扩展性）
    st.subheader("➕ 临时添加人员")
    new_name = st.text_input("姓名")
    new_type = st.selectbox("类型", ["教师", "学生"])
    if st.button("添加", use_container_width=True):
        if new_name and new_name not in PERSONS:
            if new_type == "教师":
                PERSONS[new_name] = {"type": "教师", "dept": "未知", "title": "讲师", "office": "待定", "students": [], "colleagues": []}
                G.add_node(new_name, type="person")
            else:
                PERSONS[new_name] = {"type": "学生", "dept": "未知", "major": "未知", "advisor": "待定", "year": 2024}
                G.add_node(new_name, type="person")
            st.success(f"已添加 {new_name}（{new_type}）")
            st.cache_resource.clear()
            st.rerun()
        elif new_name in PERSONS:
            st.warning("人员已存在")
    
    st.divider()
    st.caption("💡 提示：添加的人员仅在当前会话有效，刷新页面即恢复。")

# ---------- 主界面布局 ----------
# 两列：左侧问答，右侧图谱
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("✨ 智能问答")
    # 快速示例按钮（使用 grid 布局）
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
            with st.expander("📐 查看推理路径"):
                st.markdown("""
                **推理步骤：**
                1. **实体识别**：从问句中提取人名、关系词。
                2. **模糊匹配**：若精确匹配失败，尝试相似度匹配。
                3. **图谱遍历**：根据关系（指导、同事、院系）进行单跳或多跳查询。
                4. **结果生成**：组装自然语言答案。
                """)
                # 显示推理中涉及到的实体
                if answer != help_message():
                    st.markdown("**涉及实体：**")
                    for name in get_all_names():
                        if name in answer:
                            st.write(f"- {name}（{PERSONS[name]['type']}）")
        else:
            st.warning("请输入问题")

with col_right:
    st.subheader("🗺️ 知识图谱可视化")
    fig = draw_graph()
    st.pyplot(fig)
    st.caption("绿色箭头：指导关系 | 橙色虚线：同事关系")

# 页脚
st.divider()
st.caption("🏫 校内人员图谱 | 支持模糊匹配、多跳推理 | 数据可编辑（临时）")