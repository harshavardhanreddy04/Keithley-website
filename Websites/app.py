import streamlit as st
import waveform  # Import waveform.py
import sweep  # Import I-V Sweep.py

st.sidebar.title("Navigation")
app_selection = st.sidebar.radio("Choose an Application", ["Waveform Analysis", "I-V Sweep"])

# Display the selected app
if app_selection == "Waveform Analysis":
    waveform.main()  # Calls the main function in waveform.py
elif app_selection == "I-V Sweep":
    sweep.main()  # Calls the main function in I-V Sweep.py
