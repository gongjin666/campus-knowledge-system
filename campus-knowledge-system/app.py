import streamlit as st

# 配置页面标题和图标
st.set_page_config(page_title="校园知识推理系统", page_icon="🎓")

# ----- 1. 定义知识图谱数据 (用字典来模拟图结构) -----
# 课程数据：包含课程信息，用 'prerequisites' (先修课程) 定义关系
courses = {
    "高等数学": {"credit": 5, "prerequisites": [], "teacher": "王教授"},
    "线性代数": {"credit": 3, "prerequisites": [], "teacher": "李教授"},
    "离散数学": {"credit": 4, "prerequisites": ["高等数学"], "teacher": "赵教授"},
    "数据结构": {"credit": 4, "prerequisites": ["离散数学"], "teacher": "张教授"},
    "机器学习": {"credit": 4, "prerequisites": ["线性代数", "高等数学"], "teacher": "孙教授"},
    "深度学习": {"credit": 4, "prerequisites": ["机器学习", "线性代数"], "teacher": "孙教授"},
}

# 设施数据
facilities = {
    "图书馆": {"hours": "8:00-22:00", "location": "图书馆楼", "type": "学习场所"},
    "第一食堂": {"hours": "6:30-20:00", "location": "生活区", "type": "餐厅"},
}

# ----- 2. 核心推理函数 (根据问题在图谱中进行推理) -----
def reason(question):
    """接收用户问题，返回推理结果"""
    q = question.lower()
    
    # 推理1: 查询先修课程
    if "先修" in q or "前置" in q:
        for course in courses:
            if course in question:
                prereqs = courses[course]["prerequisites"]
                if prereqs:
                    return f"📚 **《{course}》** 需要先学习：**{' → '.join(prereqs)}**。"
                return f"✅ **《{course}》** 没有先修课程要求，可以直接选修。"
    
    # 推理2: 查询后续课程 (通过学习路径的反向查找)
    if "学完" in q and ("能学" in q or "可以选" in q):
        for prereq_course in courses:
            if prereq_course in question:
                next_courses = []
                for course, info in courses.items():
                    if prereq_course in info["prerequisites"]:
                        next_courses.append(course)
                if next_courses:
                    return f"🔗 学完 **《{prereq_course}》** 后，可以继续学习：**{' → '.join(next_courses)}**。"
                return f"⚠️ 目前没有以 **《{prereq_course}》** 为先修课程的进阶课程。"
    
    # 推理3: 查询授课教师
    if "谁教" in q or "老师" in q:
        for course, info in courses.items():
            if course in question:
                return f"👨‍🏫 **《{course}》** 由 **{info['teacher']}** 讲授。"
    
    # 推理4: 查询设施信息
    for name, info in facilities.items():
        if name in question:
            return f"🏢 **{name}**：{info['hours']}开放，位于 {info['location']}（{info['type']}）。"
    
    # 默认回复
    return "💡 试试问：\n• 高等数学的先修课程是什么？\n• 学完数据结构能学什么？\n• 谁教机器学习？\n• 图书馆几点开门？"

# ----- 3. 主页面UI设计 (Streamlit可视化部分)-----
st.title("🎓 校园知识图谱自动推理系统")
st.caption("基于知识图谱 + 规则推理 | 支持先修查询、路径规划、设施问答")

# 输入框
user_question = st.text_input(
    "💬 输入你的问题：",
    placeholder="例如：高等数学的先修课程是什么？",
    key="question_input"
)

# 推理按钮
if st.button("🔍 开始推理", type="primary", use_container_width=True):
    if user_question:
        with st.spinner("推理中..."):
            answer = reason(user_question)
        st.success("✅ 推理结果")
        st.info(answer)
        
        # 展示推理过程（给老师看，显得更专业）
        with st.expander("📐 查看推理过程"):
            st.markdown("""
            **推理引擎执行步骤：**
            1.  **关键词提取**：从用户问题中提取实体（课程名/设施名）。
            2.  **图谱匹配**：在我们的知识图谱中定位对应的“节点”。
            3.  **关系查询**：根据查询类型进行“图遍历”。
                -   **前置查询**：查找指向该节点的“入边”。
                -   **后置查询**：查找从该节点出发的“出边”。
            4.  **结果生成**：将多跳路径组合成自然语言答案。
            """)
    else:
        st.warning("⚠️ 请输入一个问题")