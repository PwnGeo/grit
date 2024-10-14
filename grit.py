import streamlit as st
from graphviz import Digraph
import sqlite3
from streamlit_option_menu import option_menu


# Tạo kết nối đến cơ sở dữ liệu SQLite
def get_db_connection():
    conn = sqlite3.connect('goals.db')
    c = conn.cursor()
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='goals' ''')
    if c.fetchone()[0] == 0:
        c.execute('''CREATE TABLE goals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      level TEXT,
                      content TEXT,
                      parent_id INTEGER)''')
        conn.commit()
    return conn


def create_goal_tree(low_goals, mid_goals, high_goal):
    # Initialize a Digraph
    dot = Digraph()

    # Add the high-level goal
    dot.node('H', high_goal)

    # Add mid-level goals
    for i, mid_goal in enumerate(mid_goals):
        mid_node_id = f'M{i}'
        dot.node(mid_node_id, mid_goal)
        dot.edge(mid_node_id, 'H')

        # Add low-level goals linking to each mid-level goal
        for j, low_goal in enumerate(low_goals.get(i, [])):
            low_node_id = f'L{i}{j}'
            dot.node(low_node_id, low_goal)
            dot.edge(low_node_id, mid_node_id)
    
    return dot

def save_goals(high_goal, mid_goals, low_goals_mapping):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Xóa tất cả mục tiêu cũ
    c.execute("DELETE FROM goals")
    
    # Lưu mục tiêu cấp cao
    c.execute("INSERT INTO goals (level, content) VALUES (?, ?)", ('high', high_goal))
    high_id = c.lastrowid
    
    # Lưu mục tiêu cấp trung và cấp thấp
    for i, mid_goal in enumerate(mid_goals):
        c.execute("INSERT INTO goals (level, content, parent_id) VALUES (?, ?, ?)", ('mid', mid_goal, high_id))
        mid_id = c.lastrowid
        
        # Lưu mục tiêu cấp thấp
        for low_goal in low_goals_mapping.get(i, []):
            c.execute("INSERT INTO goals (level, content, parent_id) VALUES (?, ?, ?)", ('low', low_goal, mid_id))
    
    conn.commit()
    conn.close()


def load_goals():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM goals WHERE level='high'")
    high_goal_row = c.fetchone()
    high_goal = high_goal_row[2] if high_goal_row else ""
    
    c.execute("SELECT * FROM goals WHERE level='mid'")
    mid_goals = [row[2] for row in c.fetchall()]
    
    low_goals_mapping = {}
    for i, mid_goal in enumerate(mid_goals):
        c.execute("SELECT * FROM goals WHERE level='low' AND parent_id=(SELECT id FROM goals WHERE level='mid' AND content=?)", (mid_goal,))
        low_goals_mapping[i] = [row[2] for row in c.fetchall()]
    
    conn.close()
    return high_goal, mid_goals, low_goals_mapping

def set_page_style():
    st.set_page_config(
        page_title="Grit Platform",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .stApp {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #ffffff;
        color: #000000;
        border-radius: 5px;
    }
    .css-1d391kg {
        padding-top: 3rem;
    }
    </style>
    """, unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        # st.image("https://your-logo-url.com/logo.png", width=200)
        st.markdown('<p class="big-font">Grit Platform</p>', unsafe_allow_html=True)
        menu = option_menu(
            menu_title=None,
            options=["Home", "Goals", "Analytics", "Settings"],
            icons=["house", "bullseye", "graph-up", "gear"],
            menu_icon="cast",
            default_index=0,
        )
    return menu

def home_page():
    st.write(
        """
        ## Welcome to Grit Platform
        Grit Platform helps you manage and track your personal goals effectively. 
        Our hierarchical goal-setting approach allows you to align your daily tasks 
        with your long-term aspirations.

        ### How it works:
        1. **High-level Goal:** Set your overarching life objective.
        2. **Mid-level Goals:** Define long-term milestones.
        3. **Low-level Goals:** Plan daily tasks that contribute to your mid-level goals.

        Get started by navigating to the Goals section!
        """
    )

def goals_page():
    # Load existing goals
    high_goal, mid_goals, low_goals_mapping = load_goals()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Goal Input")
        
        high_level_goal = st.text_input("Your High-level Goal:", value=high_goal, placeholder="Enter your life objective")
        
        mid_level_inputs = st.text_area("Your Mid-level Goals:", value="\n".join(mid_goals), placeholder="Enter one goal per line")
        mid_level_goals = [goal for goal in mid_level_inputs.split("\n") if goal]
        
        all_low_goals = [item for sublist in low_goals_mapping.values() for item in sublist]
        low_level_inputs = st.text_area("Your Low-level Goals:", value="\n".join(all_low_goals), placeholder="Enter one task per line")
        low_level_goals = [goal for goal in low_level_inputs.split("\n") if goal]

        if mid_level_goals:
            st.subheader("Link Low-level Goals to Mid-level Goals")
            for i, mid_goal in enumerate(mid_level_goals):
                selected_low_goals = st.multiselect(
                    f"Select low-level goals for: {mid_goal}",
                    options=low_level_goals,
                    default=low_goals_mapping.get(i, []),
                    key=f"low_for_mid_{i}"
                )
                low_goals_mapping[i] = selected_low_goals

        if st.button("Save Goals", key="save_goals"):
            save_goals(high_level_goal, mid_level_goals, low_goals_mapping)
            st.success("Goals saved successfully!")

    with col2:
        st.subheader("Goal Tree Visualization")
        if high_level_goal and mid_level_goals:
            dot = create_goal_tree(low_goals_mapping, mid_level_goals, high_level_goal)
            st.graphviz_chart(dot, use_container_width=True)
        else:
            st.info("Enter a high-level goal and at least one mid-level goal to see the goal tree.")

def analytics_page():
    st.subheader("Goal Analytics")
    st.write("This feature is coming soon. It will provide insights into your goal progress and achievements.")

def settings_page():
    st.subheader("Settings")
    st.write("Customize your Grit Platform experience here. More options will be available in future updates.")

def main():
    set_page_style()
    menu = sidebar()

    if menu == "Home":
        home_page()
    elif menu == "Goals":
        goals_page()
    # elif menu == "Analytics":
        # analytics_page()
    # elif menu == "Settings":
        # settings_page()


if __name__ == "__main__":
    main()


