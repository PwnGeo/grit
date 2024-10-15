import streamlit as st
import sqlite3
from streamlit_option_menu import option_menu
import networkx as nx
import matplotlib.pyplot as plt

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
    # Initialize a directed graph
    G = nx.DiGraph()

    # Add the high-level goal
    G.add_node('H', label=high_goal)

    # Add mid-level goals
    for i, mid_goal in enumerate(mid_goals):
        mid_node_id = f'M{i}'
        G.add_node(mid_node_id, label=mid_goal)
        G.add_edge(mid_node_id, 'H')

        # Add low-level goals linking to each mid-level goal
        for j, low_goal in enumerate(low_goals.get(i, [])):
            low_node_id = f'L{i}{j}'
            G.add_node(low_node_id, label=low_goal)
            G.add_edge(low_node_id, mid_node_id)

    return G

def plot_goal_tree(G):
    plt.figure(figsize=(10, 6))

    pos = {}
    level_positions = {"H": (0.5, 1)}

    # Number of mid-level goals
    mid_level_nodes = sorted(n for n in G if n.startswith('M'))
    num_mid = len(mid_level_nodes)

    # Allocate positions for mid-level goals
    for i, mid_node in enumerate(mid_level_nodes):
        pos[mid_node] = ((i + 1) / (num_mid + 1), 0.65)

    # Allocate positions for low-level goals
    low_level_nodes = [n for n in G if n.startswith('L')]
    
    # Collect parent-child relationships for calculation
    for mid_index, mid_node in enumerate(mid_level_nodes):
        connected_low_nodes = [n for n in low_level_nodes if G.has_edge(n, mid_node)]
        num_low = len(connected_low_nodes)
        for j, low_node in enumerate(connected_low_nodes):
            # Calculate position to avoid overlap
            if num_low > 1:
                pos[low_node] = ((mid_index + 1 + (j + 1) / (num_low + 1) - 0.5 / (num_low + 1)) / (num_mid + 1), 0.30)
            else:
                pos[low_node] = (pos[mid_node][0], 0.30)
    
    # Set the high-level goal position
    pos['H'] = level_positions["H"]

    labels = nx.get_node_attributes(G, 'label')

    # Draw the nodes and edges
    nx.draw(G, pos, labels=labels, with_labels=True, 
            node_size=3000, node_color='lightblue', font_size=10, 
            font_weight='bold', edge_color='gray')
    
    plt.title("Goal Tree Visualization")
    st.pyplot(plt)





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
        st.image("https://miraway.vn/images/logo.png", width=200)
        st.markdown('<p class="big-font">Grit Platform</p>', unsafe_allow_html=True)
        menu = option_menu(
            menu_title=None,
            options=["Home", "Goals"],
            icons=["house", "bullseye"],            
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
            G = create_goal_tree(low_goals_mapping, mid_level_goals, high_level_goal)
            plot_goal_tree(G)
        else:
            st.info("Enter a high-level goal and at least one mid-level goal to see the goal tree.")

def main():
    set_page_style()
    menu = sidebar()

    if menu == "Home":
        home_page()
    elif menu == "Goals":
        goals_page()

if __name__ == "__main__":
    main()
