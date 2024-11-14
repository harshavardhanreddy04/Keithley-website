
import streamlit as st
import pyvisa
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def main():
    
# Streamlit app title
    st.title("Keithley Sweep Voltage Pulse Interface with Precise Time Capture")

# Input parameters
    ip_address = st.text_input("Enter Keithley IP Address", "169.254.105.180")
    start_voltage = st.number_input("Start Voltage (V)", min_value=-10.0, max_value=10.0, value=-4.0)
    end_voltage = st.number_input("End Voltage (V)", min_value=-10.0, max_value=10.0, value=4.0)
    points_per_cycle = st.number_input("Points per Cycle", min_value=10, max_value=500, value=100)
    cycles = st.slider("Number of Cycles", min_value=1, max_value=200, value=3)
    file_name = st.text_input("Enter filename to save data (e.g., data.csv)", "data.csv")

    # Initialize lists for storing pulse data if "Start Sweep Pulse Measurement" button is pressed
    if st.button("Start Sweep Pulse Measurement"):
        # Set up the connection to the Keithley
        rm = pyvisa.ResourceManager()
        try:
            # Use the user-provided IP address to connect
            multimeter = rm.open_resource(f"TCPIP::{ip_address}::INSTR", open_timeout=5000)
            multimeter.write("*RST")
            time.sleep(1)

            # Configure the instrument for voltage sweeping
            multimeter.write("ROUT:TERM REAR")
            multimeter.write(":SOUR:FUNC VOLT")
            multimeter.write(":SOUR:VOLT:MODE FIXED")
            multimeter.write(":SENS:FUNC 'CURR'")  # Set measurement mode to current
            multimeter.write(":OUTP ON")
            st.write("Instrument output turned ON. Beginning voltage sweep sequence...")

            # Initialize data lists for plotting and saving
            keithley_times = []
            voltage_levels = []
            current_levels = []

            # Capture start time with respect to the first measurement
            start_time = None

            # Initialize progress bar
            total_points = cycles * points_per_cycle
            progress_bar = st.progress(0)
            point_counter = 0  # To track progress

            # Generate the sweep sequence
            for cycle in range(cycles):
                # Sweep up from start_voltage to end_voltage
                for t in range(points_per_cycle // 2):
                    voltage = start_voltage + (end_voltage - start_voltage) * (t / (points_per_cycle / 2))
                    multimeter.write(f":SOUR:VOLT {voltage}")

                    # Read current and capture time from the instrument if possible
                    try:
                        current = float(multimeter.query(":READ?"))
                        current_time = time.time()
                        if start_time is None:
                            start_time = current_time  # Set initial reference time
                        keithley_times.append(current_time - start_time)  # Capture relative time
                        voltage_levels.append(voltage)
                        current_levels.append(current)
                    except ValueError:
                        st.write(f"Measurement failed at voltage: {voltage}")

                    # Update progress
                    point_counter += 1
                    progress_bar.progress(point_counter / total_points)

                # Sweep down from end_voltage to start_voltage
                for t in range(points_per_cycle // 2):
                    voltage = end_voltage - (end_voltage - start_voltage) * (t / (points_per_cycle / 2))
                    multimeter.write(f":SOUR:VOLT {voltage}")

                    # Read current and capture time from the instrument if possible
                    try:
                        current = float(multimeter.query(":READ?"))
                        current_time = time.time()
                        keithley_times.append(current_time - start_time)
                        voltage_levels.append(voltage)
                        current_levels.append(current)
                    except ValueError:
                        st.write(f"Measurement failed at voltage: {voltage}")

                    # Update progress
                    point_counter += 1
                    progress_bar.progress(point_counter / total_points)

            # Power off after sweep sequence
            multimeter.write(":OUTP OFF")
            st.write("Instrument output turned OFF.")

            # Save data to CSV
            data = pd.DataFrame({"Keithley Time (s)": keithley_times, "Voltage (V)": voltage_levels, "Current (A)": current_levels})
            data.to_csv(file_name, index=False)
            st.write(f"Data saved to {file_name}")

            # Display voltage-time plot
            fig1, ax1 = plt.subplots()
            ax1.plot(keithley_times, voltage_levels, drawstyle='steps-post')
            ax1.set_title("Voltage Sweep Sequence")
            ax1.set_xlabel("Keithley Time (s)")
            ax1.set_ylabel("Voltage (V)")
            ax1.grid(True)
            st.pyplot(fig1)

            # Display Voltage-Current plot
            fig2, ax2 = plt.subplots()
            ax2.plot(voltage_levels, current_levels, marker='o', linestyle='-')
            ax2.set_title("Voltage vs. Current")
            ax2.set_xlabel("Voltage (V)")
            ax2.set_ylabel("Current (A)")
            ax2.grid(True)
            st.pyplot(fig2)

            # Display Current-Time plot
            fig3, ax3 = plt.subplots()
            ax3.plot(keithley_times, current_levels, drawstyle='steps-post')
            ax3.set_title("Current vs. Keithley Time")
            ax3.set_xlabel("Keithley Time (s)")
            ax3.set_ylabel("Current (A)")
            ax3.grid(True)
            st.pyplot(fig3)

        except pyvisa.VisaIOError as e:
            st.write(f"Connection error: {e}")

        finally:
            if 'multimeter' in locals():
                multimeter.close()
                
if __name__ == "__main__":
    main()

