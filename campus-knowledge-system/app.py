import streamlit as st

# 页面配置
st.set_page_config(
    page_title="校内人员图谱",
    page_icon="🏫",
    layout="wide"
)

# 标题区域
st.title("🏫 校内人员图谱构建与信息查询")
st.markdown("> 基于知识图谱 + 规则推理 | 支持人员关系查询、指导关系、院系归属等")

# ==================== 人员图谱数据（模拟图结构）====================
PERSONS = {
    # 教师
    "李教授": {
        "type": "教师",
        "dept": "计算机学院",
        "title": "教授",
        "office": "信息楼 301",
        "students": ["张三", "李四", "王芳"],
        "colleagues": ["张教授", "王教授"]
    },
    "张教授": {
        "type": "教师",
        "dept": "计算机学院",
        "title": "教授",
        "office": "信息楼 302",
        "students": ["赵强", "孙丽"],
        "colleagues": ["李教授", "王教授"]
    },
    "王教授": {
        "type": "教师",
        "dept": "数学学院",
        "title": "教授",
        "office": "数学楼 201",
        "students": ["刘伟", "陈晨"],
        "colleagues": ["李教授", "张教授"]
    },
    # 学生
    "张三": {
        "type": "学生",
        "dept": "计算机学院",
        "major": "计算机科学与技术",
        "advisor": "李教授",
        "year": 2022
    },
    "李四": {
        "type": "学生",
        "dept": "计算机学院",
        "major": "软件工程",
        "advisor": "李教授",
        "year": 2023
    },
    "王芳": {
        "type": "学生",
        "dept": "计算机学院",
        "major": "人工智能",
        "advisor": "李教授",
        "year": 2021
    },
    "赵强": {
        "type": "学生",
        "dept": "计算机学院",
        "major": "计算机科学与技术",
        "advisor": "张教授",
        "year": 2022
    },
    "刘伟": {
        "type": "学生",
        "dept": "数学学院",
        "major": "应用数学",
        "advisor": "王教授",
        "year": 2023
    }
}

DEPT_INFO = {
    "计算机学院": {"location": "信息楼", "dean": "李教授"},
    "数学学院": {"location": "数学楼", "dean": "王教授"}
}

# 缓存推理函数（提高性能）
@st.cache_data
def get_all_teachers():
    return [name for name, info in PERSONS.items() if info["type"] == "教师"]

@st.cache_data
def get_all_students():
    return [name for name, info in PERSONS.items() if info["type"] == "学生"]

def reason(question: str) -> str:
    """核心推理引擎，根据自然语言问句返回答案"""
    q = question.lower().strip()

    # 1. 查询教师的学生
    if "学生" in q or "指导" in q:
        for name, info in PERSONS.items():
            if name in question and info["type"] == "教师":
                students = info.get("students", [])
                if students:
                    return f"👨‍🏫 **{name}** 指导的学生有：{', '.join(students)}。"
                return f"👨‍🏫 **{name}** 目前没有指导学生。"
        # 如果没有匹配教师，尝试寻找是否是问某个学生的同学？（暂不实现）
    
    # 2. 查询学生的导师
    if "导师" in q or "指导老师" in q:
        for name, info in PERSONS.items():
            if name in question and info["type"] == "学生":
                advisor = info.get("advisor")
                if advisor:
                    return f"🎓 **{name}** 的导师是：**{advisor}**。"
                return f"🎓 未找到 {name} 的导师信息。"
    
    # 3. 查询同事关系
    if "同事" in q:
        for name, info in PERSONS.items():
            if name in question and info["type"] == "教师":
                colleagues = info.get("colleagues", [])
                if colleagues:
                    return f"🤝 **{name}** 的同事有：{', '.join(colleagues)}。"
                return f"🤝 **{name}** 暂无同事信息。"
    
    # 4. 查询院系归属
    if "院系" in q or "哪个学院" in q:
        for name, info in PERSONS.items():
            if name in question:
                dept = info.get("dept")
                if dept:
                    return f"🏛️ **{name}** 属于 **{dept}**。"
                return f"🏛️ 未找到 {name} 的院系信息。"
    
    # 5. 查询教师办公室
    if "办公室" in q or "在哪" in q:
        for name, info in PERSONS.items():
            if name in question and info["type"] == "教师":
                office = info.get("office")
                if office:
                    return f"📌 **{name}** 的办公室在：**{office}**。"
    
    # 6. 查询院系信息
    for dept, info in DEPT_INFO.items():
        if dept in question:
            return f"🏢 **{dept}** 位于 **{info['location']}**，院长是 **{info['dean']}**。"
    
    # 7. 所有教师列表
    if "所有教师" in q or "教师列表" in q:
        teachers = get_all_teachers()
        return f"👨‍🏫 校内教师共 {len(teachers)} 位：{', '.join(teachers)}。"
    
    # 8. 所有学生列表
    if "所有学生" in q or "学生列表" in q:
        students = get_all_students()
        return f"🎓 在校学生共 {len(students)} 位：{', '.join(students)}。"
    
    # 默认帮助信息
    return (
        "💡 **试试问这些问题：**\n"
        "- 李教授的学生有哪些？\n"
        "- 张三的导师是谁？\n"
        "- 张教授的同事有哪些？\n"
        "- 计算机学院在哪里？\n"
        "- 所有教师列表"
    )

# ==================== 侧边栏 - 图谱概览 ====================
with st.sidebar:
    st.header("📊 人员图谱概览")
    
    # 统计卡片
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👨‍🏫 教师", len(get_all_teachers()))
    with col2:
        st.metric("🎓 学生", len(get_all_students()))
    
    st.divider()
    
    # 按院系展示
    st.subheader("🏛️ 按院系")
    dept_people = {}
    for name, info in PERSONS.items():
        d = info.get("dept", "未知")
        dept_people.setdefault(d, []).append(name)
    for d, people in dept_people.items():
        with st.expander(f"{d} ({len(people)}人)"):
            st.write("、".join(people))
    
    st.divider()
    st.caption("🔍 支持查询：学生列表、导师、同事、院系、办公室等")

# ==================== 主界面 ====================
# 示例问题按钮行
st.subheader("✨ 快速提问")
example_questions = [
    "李教授的学生有哪些？",
    "张三的导师是谁？",
    "张教授的同事有哪些？",
    "计算机学院在哪里？",
    "所有教师列表"
]
cols = st.columns(len(example_questions))
for i, q in enumerate(example_questions):
    if cols[i].button(q, key=f"ex_{i}", use_container_width=True):
        st.session_state["question"] = q
        st.rerun()

st.divider()

# 输入区域
question = st.text_input(
    "💬 输入你的问题：",
    value=st.session_state.get("question", ""),
    placeholder="例如：李教授的学生有哪些？",
    key="question_input"
)

# 推理按钮
if st.button("🔍 开始推理", type="primary", use_container_width=True):
    if question:
        with st.spinner("正在推理中..."):
            answer = reason(question)
        
        st.success("✅ 推理结果")
        st.info(answer)
        
        # 展示推理过程（增强可解释性）
        with st.expander("📐 查看推理过程"):
            st.markdown("""
            **推理引擎执行步骤：**
            1. **实体识别** → 从问题中提取人名、关系词（如“学生”、“导师”）
            2. **图谱匹配** → 在人员字典中查找匹配的节点
            3. **关系遍历** → 根据关系类型（指导、同事、院系）进行跳转
            4. **结果生成** → 组合自然语言答案并返回
            """)
            
            # 展示匹配到的节点信息（如果有）
            for name in PERSONS.keys():
                if name in question:
                    st.info(f"📌 匹配到实体：**{name}**（{PERSONS[name]['type']}）")
                    break
    else:
        st.warning("⚠️ 请输入一个问题")

# 简单的关系图展示（文字版，无需额外库）
st.divider()
with st.expander("🗺️ 查看图谱关系（文字版）"):
    st.markdown("**指导关系（导师→学生）**")
    for name, info in PERSONS.items():
        if info["type"] == "教师" and info.get("students"):
            for stu in info["students"]:
                st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{name} 👉 {stu}")
    
    st.markdown("**同事关系**")
    for name, info in PERSONS.items():
        if info["type"] == "教师" and info.get("colleagues"):
            for col in info["colleagues"]:
                if name < col:  # 避免重复
                    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{name} 🤝 {col}")

# 页脚
st.markdown("---")
st.caption("🏫 校内人员图谱 | 基于规则推理 | 支持自然语言查询 | 数据可扩展")