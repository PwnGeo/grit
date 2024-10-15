import streamlit as st
from streamlit_option_menu import option_menu
import networkx as nx
import matplotlib.pyplot as plt
import io

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
            node_size=3000, node_color='lightblue', 
            font_size=10, font_weight='bold', edge_color='gray')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def goals_page():
    if "high_goal" not in st.session_state:
        st.session_state.high_goal = ""
    if "mid_goals" not in st.session_state:
        st.session_state.mid_goals = []
    if "low_goals_mapping" not in st.session_state:
        st.session_state.low_goals_mapping = {}
    if "all_low_goals" not in st.session_state:
        st.session_state.all_low_goals = []

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Goal Input")
        
        high_level_goal = st.text_input(
            "Your High-level Goal:",
            value=st.session_state.high_goal,
            placeholder="Enter your life objective"
        )
        
        mid_level_inputs = st.text_area(
            "Your Mid-level Goals:",
            value="\n".join(st.session_state.mid_goals),
            placeholder="Enter one goal per line"
        )
        mid_level_goals = [goal for goal in mid_level_inputs.split("\n") if goal]
        
        low_level_inputs = st.text_area(
            "Your Low-level Goals:",
            value="\n".join(st.session_state.all_low_goals),
            placeholder="Enter one task per line"
        )
        low_level_goals = [goal for goal in low_level_inputs.split("\n") if goal]

        st.session_state.all_low_goals = low_level_goals

        if mid_level_goals:
            st.subheader("Link Low-level Goals to Mid-level Goals")
            for i, mid_goal in enumerate(mid_level_goals):
                selected_low_goals = st.multiselect(
                    f"Select low-level goals for: {mid_goal}",
                    options=st.session_state.all_low_goals,
                    default=st.session_state.low_goals_mapping.get(i, []),
                    key=f"low_for_mid_{i}"
                )
                st.session_state.low_goals_mapping[i] = selected_low_goals

    with col2:
        st.subheader("Goal Tree Visualization")
        if high_level_goal and mid_level_goals:
            # Create the goal tree
            G = create_goal_tree(st.session_state.low_goals_mapping, mid_level_goals, high_level_goal)
            
            # Plot and get the graph image buffer
            img_buffer = plot_goal_tree(G)

            # Display the goal tree
            st.image(img_buffer, caption='Goal Tree', use_column_width=True)
            
            # Provide a download button for the PNG image of the graph
            st.download_button(
                label="Download Goal Tree as PNG",
                data=img_buffer,
                file_name="goal_tree.png",
                mime="image/png"
            )
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
