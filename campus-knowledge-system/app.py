import streamlit as st
import networkx as nx
import json
import os
import re
from difflib import get_close_matches
from pyvis.network import Network
import tempfile

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
st.markdown("> **交互式智能版**：支持自然语言查询、动态图谱、人物/关系管理 | 基于图遍历推理")

# ---------- 默认数据（JSON格式，可外部化）----------
DEFAULT_DATA = {
    "persons": {
        "李教授": {"type": "教师", "dept": "计算机学院", "title": "教授", "office": "信息楼301"},
        "张教授": {"type": "教师", "dept": "计算机学院", "title": "教授", "office": "信息楼302"},
        "王教授": {"type": "教师", "dept": "数学学院", "title": "教授", "office": "数学楼201"},
        "张三": {"type": "学生", "dept": "计算机学院", "major": "计算机科学与技术", "year": 2022},
        "李四": {"type": "学生", "dept": "计算机学院", "major": "软件工程", "year": 2023},
        "王芳": {"type": "学生", "dept": "计算机学院", "major": "人工智能", "year": 2021},
        "赵强": {"type": "学生", "dept": "计算机学院", "major": "计算机科学与技术", "year": 2022},
        "孙丽": {"type": "学生", "dept": "计算机学院", "major": "网络工程", "year": 2023},
        "刘伟": {"type": "学生", "dept": "数学学院", "major": "应用数学", "year": 2022},
        "陈晨": {"type": "学生", "dept": "数学学院", "major": "统计学", "year": 2023}
    },
    "relations": {
        "指导": [
            ("李教授", "张三"), ("李教授", "李四"), ("李教授", "王芳"),
            ("张教授", "赵强"), ("张教授", "孙丽"),
            ("王教授", "刘伟"), ("王教授", "陈晨")
        ],
        "同事": [
            ("李教授", "张教授"), ("李教授", "王教授"),
            ("张教授", "李教授"), ("张教授", "王教授"),
            ("王教授", "李教授"), ("王教授", "张教授")
        ]
    },
    "dept_info": {
        "计算机学院": {"location": "信息楼", "dean": "李教授"},
        "数学学院": {"location": "数学楼", "dean": "王教授"}
    }
}

DATA_FILE = "campus_data.json"

def load_data():
    """从JSON文件加载数据，如果文件不存在则使用默认数据并保存"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)
        return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- 图谱构建（基于有向图）----------
@st.cache_resource
def build_graph(data):
    """从数据构建有向图：指导边有方向，同事边双向"""
    G = nx.DiGraph()
    # 添加节点及属性
    for name, attrs in data["persons"].items():
        G.add_node(name, **attrs)
    # 添加指导边（有向）
    for u, v in data["relations"].get("指导", []):
        G.add_edge(u, v, relation="指导")
    # 添加同事边（无向 -> 双向有向）
    for u, v in data["relations"].get("同事", []):
        G.add_edge(u, v, relation="同事")
        G.add_edge(v, u, relation="同事")
    return G

# 加载数据并构建图
if "campus_data" not in st.session_state:
    st.session_state.campus_data = load_data()
if "G" not in st.session_state:
    st.session_state.G = build_graph(st.session_state.campus_data)

# ---------- 辅助函数 ----------
def get_person_attrs(name):
    return st.session_state.campus_data["persons"].get(name, {})

def get_dept_info(dept_name):
    return st.session_state.campus_data["dept_info"].get(dept_name, {})

def extract_entities_from_question(question):
    """增强实体提取：精确匹配 + 模糊匹配 + 别名映射"""
    candidates = list(st.session_state.campus_data["persons"].keys())
    # 别名映射
    alias_map = {"李老师": "李教授", "张老师": "张教授", "王老师": "王教授"}
    for alias, real in alias_map.items():
        if alias in question:
            return [real]
    # 精确匹配
    found = [name for name in candidates if name in question]
    if found:
        return found
    # 模糊匹配
    words = re.findall(r'[\u4e00-\u9fa5]{2,}', question)
    for w in words:
        match = get_close_matches(w, candidates, n=1, cutoff=0.7)
        if match:
            return [match[0]]
    return []

# ---------- 查询引擎（基于图遍历 + 模式映射）----------
def query_teacher_students(teacher_name):
    """查询教师的学生"""
    students = [v for u,v,d in st.session_state.G.out_edges(teacher_name, data=True) if d.get('relation')=='指导']
    if students:
        return f"👨‍🏫 **{teacher_name}** 指导的学生：{', '.join(students)}。"
    else:
        return f"👨‍🏫 **{teacher_name}** 暂无学生。"

def query_student_advisor(student_name):
    """查询学生的导师"""
    advisors = [u for u,v,d in st.session_state.G.in_edges(student_name, data=True) if d.get('relation')=='指导']
    if advisors:
        return f"🎓 **{student_name}** 的导师是 **{advisors[0]}**。"
    else:
        return f"🎓 未找到 {student_name} 的导师。"

def query_colleagues(person1, person2):
    """查询两人是否为同事"""
    if st.session_state.G.has_edge(person1, person2) and st.session_state.G[person1][person2].get('relation')=='同事':
        return f"🤝 **{person1}** 和 **{person2}** 是同事。"
    else:
        return f"❌ **{person1}** 和 **{person2}** 不是同事。"

def query_dept(person):
    attrs = get_person_attrs(person)
    dept = attrs.get("dept")
    if dept:
        return f"🏛️ **{person}** 属于 **{dept}**。"
    return f"未找到 {person} 的院系信息。"

def query_office(person):
    attrs = get_person_attrs(person)
    if attrs.get("type") == "教师":
        office = attrs.get("office")
        if office:
            return f"📌 **{person}** 的办公室在 **{office}**。"
    return f"未找到 {person} 的办公室信息。"

def query_dept_info(dept_name):
    info = get_dept_info(dept_name)
    if info:
        return f"🏢 **{dept_name}** 位于 **{info['location']}**，院长是 **{info['dean']}**。"
    return f"未找到 {dept_name} 的信息。"

def query_all_teachers():
    teachers = [n for n,attr in st.session_state.campus_data["persons"].items() if attr.get("type")=="教师"]
    return f"👨‍🏫 教师名单（{len(teachers)}人）：{', '.join(teachers)}"

def query_all_students():
    students = [n for n,attr in st.session_state.campus_data["persons"].items() if attr.get("type")=="学生"]
    return f"🎓 学生名单（{len(students)}人）：{', '.join(students)}"

def query_students_of_advisor(student_name):
    """多跳：学生的导师的学生"""
    advisors = [u for u,v,d in st.session_state.G.in_edges(student_name, data=True) if d.get('relation')=='指导']
    if not advisors:
        return f"未找到 {student_name} 的导师。"
    advisor = advisors[0]
    students = [v for u,v,d in st.session_state.G.out_edges(advisor, data=True) if d.get('relation')=='指导']
    return f"🔗 {student_name} 的导师是 {advisor}，{advisor} 还指导了：{', '.join(students)}"

def query_attribute(person, attr_name):
    """通用属性查询"""
    attrs = get_person_attrs(person)
    if attr_name in attrs:
        return f"📋 **{person}** 的 {attr_name} 是 **{attrs[attr_name]}**。"
    return f"未找到 {person} 的 {attr_name} 信息。"

def query_relation_path(person1, person2):
    """查询两人之间的最短路径（解释关系）"""
    try:
        path = nx.shortest_path(st.session_state.G.to_undirected(), source=person1, target=person2)
        if len(path) == 2:
            edge_type = st.session_state.G[person1][person2].get('relation', '未知')
            return f"🔗 **{person1}** 和 **{person2}** 直接相连，关系：{edge_type}。"
        else:
            steps = " → ".join(path)
            return f"🔗 **{person1}** 到 **{person2}** 的路径：{steps}"
    except nx.NetworkXNoPath:
        return f"❌ 未找到 {person1} 与 {person2} 之间的路径。"

def query_count_by_dept(dept_name, person_type=None):
    """统计某院系下的教师/学生数量"""
    persons = [n for n,attr in st.session_state.campus_data["persons"].items() if attr.get("dept")==dept_name]
    if person_type:
        persons = [p for p in persons if get_person_attrs(p).get("type")==person_type]
    return f"📊 {dept_name} 共有 {len(persons)} 人" + (f"（{person_type}）" if person_type else "") + f"：{', '.join(persons)}"

# ---------- 模式匹配与分发 ----------
def answer_question(question):
    q = question.lower()
    entities = extract_entities_from_question(question)
    
    # 1. 教师的学生
    if ("学生" in q) and entities and get_person_attrs(entities[0]).get("type")=="教师":
        return query_teacher_students(entities[0])
    # 2. 学生的导师
    if ("导师" in q or "指导老师" in q) and entities and get_person_attrs(entities[0]).get("type")=="学生":
        return query_student_advisor(entities[0])
    # 3. 同事关系
    if "是同事吗" in q and len(entities) >= 2:
        return query_colleagues(entities[0], entities[1])
    # 4. 院系归属
    if ("院系" in q or "哪个学院" in q) and entities:
        return query_dept(entities[0])
    # 5. 办公室
    if ("办公室" in q or "在哪" in q) and entities:
        return query_office(entities[0])
    # 6. 院系信息
    for dept in st.session_state.campus_data["dept_info"]:
        if dept in question:
            return query_dept_info(dept)
    # 7. 列表查询
    if "所有教师" in q:
        return query_all_teachers()
    if "所有学生" in q:
        return query_all_students()
    # 8. 多跳：导师的学生
    if "导师的学生" in q and entities:
        return query_students_of_advisor(entities[0])
    # 9. 属性查询（职称、年级、专业等）
    attr_keywords = {"职称": "title", "专业": "major", "年级": "year", "类型": "type"}
    for kw, attr in attr_keywords.items():
        if kw in q and entities:
            return query_attribute(entities[0], attr)
    # 10. 关系路径查询
    if "关系" in q and len(entities) >= 2:
        return query_relation_path(entities[0], entities[1])
    # 11. 统计查询：某学院的学生/教师
    for dept in st.session_state.campus_data["dept_info"]:
        if dept in q:
            if "学生" in q:
                return query_count_by_dept(dept, "学生")
            elif "教师" in q:
                return query_count_by_dept(dept, "教师")
            else:
                return query_count_by_dept(dept)
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
    - 属性查询：`李教授的职称是什么？`、`张三的专业？`
    - 关系路径：`李教授和张三是什么关系？`
    - 统计查询：`计算机学院有多少学生？`
    """

# ---------- 动态图谱绘制（pyvis交互式）----------
def draw_subgraph(question):
    """根据问题提取子图并返回pyvis网络"""
    entities = extract_entities_from_question(question)
    G_full = st.session_state.G
    # 提取子图（包含实体及其1跳邻居）
    if entities:
        nodes_to_keep = set(entities)
        for ent in entities:
            neighbors = list(G_full.successors(ent)) + list(G_full.predecessors(ent))
            nodes_to_keep.update(neighbors)
        subG = G_full.subgraph(nodes_to_keep).copy()
    else:
        subG = G_full.copy()
    
    net = Network(height="500px", width="100%", directed=True, font_color="black")
    # 设置物理布局（可选，提高稳定性）
    net.set_options("""
    var options = {
        "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
        }
    }
    """)
    # 添加节点，根据类型和是否高亮设置颜色
    for node in subG.nodes():
        attrs = get_person_attrs(node)
        node_type = attrs.get("type", "未知")
        title = f"{node}<br>类型: {node_type}<br>院系: {attrs.get('dept','')}<br>" + \
                (f"职称: {attrs.get('title','')}<br>" if node_type=="教师" else f"专业: {attrs.get('major','')}<br>年级: {attrs.get('year','')}")
        color = "#FFD700" if node in entities else ("#FF6B6B" if node_type=="教师" else "#4D9DE0")
        net.add_node(node, label=node, title=title, color=color, font={"size": 14})
    # 添加边，区分指导与同事
    for u, v, data in subG.edges(data=True):
        rel = data.get('relation', '未知')
        title = f"{u} → {v} : {rel}"
        color = "green" if rel == "指导" else "orange"
        arrows = "to" if rel == "指导" else None
        net.add_edge(u, v, title=title, color=color, arrows=arrows, smooth=True)
    return net

# ---------- 数据管理侧边栏 ----------
with st.sidebar:
    st.header("📊 数据管理")
    with st.expander("➕ 添加新人物"):
        new_name = st.text_input("姓名")
        new_type = st.selectbox("类型", ["教师", "学生"])
        new_dept = st.text_input("院系")
        if new_type == "教师":
            new_title = st.text_input("职称")
            new_office = st.text_input("办公室")
        else:
            new_major = st.text_input("专业")
            new_year = st.number_input("入学年份", min_value=2000, max_value=2030, step=1)
        if st.button("添加人物"):
            if new_name and new_dept:
                person_data = {"type": new_type, "dept": new_dept}
                if new_type == "教师":
                    person_data["title"] = new_title or "未知"
                    person_data["office"] = new_office or "未知"
                else:
                    person_data["major"] = new_major or "未知"
                    person_data["year"] = new_year
                st.session_state.campus_data["persons"][new_name] = person_data
                # 重建图
                st.session_state.G = build_graph(st.session_state.campus_data)
                save_data(st.session_state.campus_data)
                st.success(f"已添加 {new_name}")
                st.rerun()
            else:
                st.error("姓名和院系不能为空")
    
    with st.expander("🔗 添加新关系"):
        rel_type = st.selectbox("关系类型", ["指导", "同事"])
        node1 = st.selectbox("第一个人", list(st.session_state.campus_data["persons"].keys()))
        node2 = st.selectbox("第二个人", list(st.session_state.campus_data["persons"].keys()))
        if st.button("添加关系"):
            if node1 == node2:
                st.error("不能添加自己到自己")
            else:
                if rel_type == "指导":
                    # 检查类型合理性：指导应该由教师指向学生
                    if get_person_attrs(node1).get("type") != "教师" or get_person_attrs(node2).get("type") != "学生":
                        st.warning("指导关系通常由教师指向学生，但已强制添加")
                    st.session_state.campus_data["relations"].setdefault("指导", []).append((node1, node2))
                else:
                    st.session_state.campus_data["relations"].setdefault("同事", []).append((node1, node2))
                    st.session_state.campus_data["relations"].setdefault("同事", []).append((node2, node1))
                st.session_state.G = build_graph(st.session_state.campus_data)
                save_data(st.session_state.campus_data)
                st.success(f"已添加 {rel_type} 关系：{node1} → {node2}")
                st.rerun()
    
    if st.button("🗑️ 重置所有数据", use_container_width=True):
        st.session_state.campus_data = DEFAULT_DATA.copy()
        st.session_state.G = build_graph(st.session_state.campus_data)
        save_data(st.session_state.campus_data)
        st.success("已重置为默认数据")
        st.rerun()
    
    st.divider()
    st.caption("💡 提示：点击图谱节点可查看详细信息，支持拖拽缩放。")

# ---------- 主界面 ----------
col_left, col_right = st.columns([1.2, 1.8])

with col_left:
    st.subheader("✨ 智能问答")
    ex_qs = [
        "李教授的学生有哪些？", "张三的导师是谁？", "李教授和张教授是同事吗？",
        "所有教师", "张三属于哪个学院？", "张三的导师的学生有哪些？",
        "李教授的职称是什么？", "计算机学院有多少学生？"
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
                answer = answer_question(question)
            st.success("✅ 推理结果")
            st.info(answer)
            # 展示推理路径（仅多跳展示）
            with st.expander("📐 推理路径"):
                entities = extract_entities_from_question(question)
                if entities:
                    for e in entities:
                        st.write(f"- {e}（{get_person_attrs(e).get('type')}）")
                else:
                    st.write("未识别到具体人物，显示全图")
                if "导师的学生" in question.lower() and entities:
                    # 手动演示步骤
                    student = entities[0]
                    advisor = None
                    for u,v,d in st.session_state.G.in_edges(student, data=True):
                        if d.get('relation')=='指导':
                            advisor = u
                            break
                    if advisor:
                        st.write(f"1️⃣ {student} 的导师 → {advisor}")
                        others = [v for u,v,d in st.session_state.G.out_edges(advisor, data=True) if d.get('relation')=='指导' and v != student]
                        st.write(f"2️⃣ {advisor} 指导的其他学生 → {', '.join(others)}")
            st.session_state["last_question"] = question
        else:
            st.warning("请输入问题")

with col_right:
    st.subheader("🗺️ 动态知识图谱")
    last_q = st.session_state.get("last_question", "")
    if last_q:
        net = draw_subgraph(last_q)
    else:
        net = draw_subgraph("")  # 全图
    # 保存为临时HTML并在Streamlit中显示
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, "r", encoding="utf-8") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=550)
    st.caption("🟢 绿色箭头：指导关系 | 🟠 橙色边：同事关系 | 🟡 黄色节点：问题中涉及的人物")

st.divider()
st.caption("🏫 校内人员图谱 | 交互式动态子图 | 支持图遍历推理、数据管理")