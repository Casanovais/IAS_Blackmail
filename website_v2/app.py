import streamlit as st
import pandas as pd

def intro():
    import streamlit as st

    st.write("# To Be Honest: Catch the LLM in a Lie")
    st.sidebar.success("Select a scenario above.")

    st.markdown(
        """

        This is a proof-of-concept website developed for a university project to explore the boundaries of truth, non-factual generation, and verifiable information when interacting with a Large Language Model (LLM).

        ## Your Mission

        Your goal is simple, but challenging: Can you successfully catch the LLM fabricating information, contradicting itself, or presenting biased/unverifiable statements?

        You will interact directly with the LLM. You are encouraged to use external search tools and your own critical thinking to vet its responses.

        ## How to Begin

        👈 Select a Scenario from the sidebar on the left to begin your challenge.

        Each scenario provides a pre-set context or prompt designed to guide your investigation into a specific type of potential LLM deception (e.g., historical alteration, technical fabrication, self-contradiction, etc.).

        We hope you enjoy the challenge and contribute valuable data to this study!
    """
    )

def scenario(n):
    import streamlit as st
    import pandas as pd

    #load the scenario from the json file
    chosen_scenario = scenarios.iloc[n]

    # Sidebar: always show the scenario metadata/details
    st.sidebar.markdown(f"## {chosen_scenario['title']}")
    st.sidebar.markdown(f" {chosen_scenario['description']}")
    st.sidebar.progress(int(chosen_scenario['difficulty']), text="Difficulty", width="stretch")

    # Ensure global active key exists
    if 'active_scenario' not in st.session_state:
        st.session_state['active_scenario'] = None

    # Sidebar: Load / Unload controls for the selected scenario
    if st.session_state['active_scenario'] == n:
        # show an unload button to deactivate this scenario
        if st.sidebar.button("Unload scenario", key=f"unload_btn_{n}"):
            st.session_state['active_scenario'] = None
            st.session_state['messages'] = None  # clear chat history when unloading
    else:
        # show a load button to activate this scenario (will deactivate any other)
        if st.sidebar.button("Load scenario", key=f"load_btn_{n}"):
            st.session_state['active_scenario'] = n
            st.session_state['messages'] = None  # clear chat history when loading

    # NOTE: Do NOT write the scenario description to the main area here.
    # The main area will display only the currently active scenario (if any),
    # otherwise remain the intro/main page content.

page_names_to_funcs = {
    "About the Project": intro
}

scenarios = pd.read_json('scenarios.json')
for i in range(len(scenarios)):
    title = scenarios.iloc[i]['title']
    page_names_to_funcs[title] = (lambda i=i: scenario(i))

demo_name = st.sidebar.selectbox("Choose a scenario", page_names_to_funcs.keys())
# Render sidebar for selected page (about or scenario metadata + buttons)
page_names_to_funcs[demo_name]()

# Main area: if the user selected "About the Project" we must show only the intro.
# Otherwise, show the active scenario (if any) or fallback to intro.
if demo_name == "About the Project":
    # intro() was already called above by page_names_to_funcs[demo_name]()
    pass
else:
    if 'active_scenario' not in st.session_state or st.session_state['active_scenario'] is None:
        # No active scenario: show fallback main content (intro)
        intro()
    else:
        # Execute the active scenario in the main area
        from llm_interaction import talk_to_ai
        active_idx = st.session_state['active_scenario']
        active_scenario = scenarios.iloc[active_idx]

        # Clear or set a header indicating which scenario is active
        st.header(active_scenario['title'])

        # call talk_to_ai only for the active scenario
        talk_to_ai(
            main_target=active_scenario['main_llm_target'],
            second_target=active_scenario['secondary_conflicting_target'],
            means_to_scheme=active_scenario['means_to_scheme'],
            context=active_scenario['context'],
            scenario_number=active_idx
        )