import streamlit as st

st.set_page_config(page_title="校内人员图谱", page_icon="🏫")

st.title("🏫 校内人员图谱构建与信息查询")
st.caption("基于知识图谱 + 规则推理 | 支持人员关系查询、指导关系、院系归属等")

# ==================== 校内人员图谱数据 ====================
# 这里用 Python 字典模拟图结构：每个人是一个节点，关系用列表存储

persons = {
    # 教师
    "李教授": {
        "type": "教师",
        "dept": "计算机学院",
        "title": "教授",
        "office": "信息楼 301",
        "students": ["张三", "李四", "王芳"],   # 指导的学生
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

# 院系信息（辅助）
depts = {
    "计算机学院": {"location": "信息楼", "dean": "李教授"},
    "数学学院": {"location": "数学楼", "dean": "王教授"}
}

# ==================== 推理引擎 ====================
def reason(question):
    """根据用户问题，在图谱中查找并推理"""
    q = question.lower()
    
    # 1. 查询某人的学生 / 指导的学生
    if "学生" in q or "指导" in q:
        for name, info in persons.items():
            if name in question and info["type"] == "教师":
                students = info.get("students", [])
                if students:
                    return f"👨‍🏫 {name} 指导的学生有：{', '.join(students)}。"
                else:
                    return f"👨‍🏫 {name} 目前没有指导学生。"
    
    # 2. 查询某学生的导师
    if "导师" in q or "指导老师" in q:
        for name, info in persons.items():
            if name in question and info["type"] == "学生":
                advisor = info.get("advisor")
                if advisor:
                    return f"🎓 {name} 的导师是：{advisor}。"
                else:
                    return f"🎓 未找到 {name} 的导师信息。"
    
    # 3. 查询同事关系
    if "同事" in q:
        for name, info in persons.items():
            if name in question and info["type"] == "教师":
                colleagues = info.get("colleagues", [])
                if colleagues:
                    return f"🤝 {name} 的同事有：{', '.join(colleagues)}。"
                else:
                    return f"🤝 {name} 暂无同事信息。"
    
    # 4. 查询某人的院系
    if "院系" in q or "哪个学院" in q:
        for name, info in persons.items():
            if name in question:
                dept = info.get("dept")
                if dept:
                    return f"🏛️ {name} 属于 {dept}。"
                else:
                    return f"🏛️ 未找到 {name} 的院系信息。"
    
    # 5. 查询教师的办公室
    if "办公室" in q or "在哪" in q:
        for name, info in persons.items():
            if name in question and info["type"] == "教师":
                office = info.get("office")
                if office:
                    return f"📌 {name} 的办公室在：{office}。"
    
    # 6. 查询院系信息
    for dept, info in depts.items():
        if dept in question:
            return f"🏢 {dept} 位于 {info['location']}，院长是 {info['dean']}。"
    
    # 7. 全校人员列表（展示图谱概览）
    if "所有教师" in q or "教师列表" in q:
        teachers = [name for name, info in persons.items() if info["type"] == "教师"]
        return f"👨‍🏫 校内教师：{', '.join(teachers)}。"
    
    if "所有学生" in q or "学生列表" in q:
        students = [name for name, info in persons.items() if info["type"] == "学生"]
        return f"🎓 在校学生：{', '.join(students)}。"
    
    # 默认回复
    return "💡 试试问：\n• 李教授的学生有哪些？\n• 张三的导师是谁？\n• 张教授的同事有哪些？\n• 计算机学院在哪？\n• 所有教师列表"

# ==================== 页面UI ====================
user_question = st.text_input("💬 输入你的问题：", placeholder="例如：李教授的学生有哪些？")

if st.button("🔍 开始推理", type="primary", use_container_width=True):
    if user_question:
        with st.spinner("正在推理中..."):
            answer = reason(user_question)
        st.success("✅ 推理结果")
        st.info(answer)
        
        # 展示推理过程（专业感）
        with st.expander("📐 查看推理过程"):
            st.markdown("""
            **推理步骤：**
            1. **实体识别**：从问题中提取人名、关系词（如“学生”、“导师”）。
            2. **图谱匹配**：在人员字典中查找对应节点的属性。
            3. **关系遍历**：根据关系类型（指导、同院系、同事）进行跳转。
            4. **结果生成**：组合自然语言答案。
            """)
    else:
        st.warning("⚠️ 请输入一个问题")

# 侧边栏显示图谱概览
with st.sidebar:
    st.header("📊 人员图谱概览")
    st.subheader("教师")
    for name, info in persons.items():
        if info["type"] == "教师":
            st.write(f"• **{name}** ({info['dept']})")
    st.subheader("学生")
    for name, info in persons.items():
        if info["type"] == "学生":
            st.write(f"• {name}（导师：{info['advisor']}）")
    
    st.divider()
    st.caption("支持查询：学生列表、导师、同事、院系、办公室等")

st.divider()
st.caption("🏫 校内人员图谱 | 基于规则推理 | 可扩展更多关系")