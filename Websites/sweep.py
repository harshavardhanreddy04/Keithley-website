import streamlit as st
import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
import csv
from io import StringIO
import pandas as pd

def main():
    
    # Streamlit app title
    st.title("Keithley I-V Measurement Interface")

    # Input parameters
    ip_address = st.text_input("Enter Keithley IP Address", "169.254.105.180")
    csv_filename = st.text_input("Enter CSV Filename", "IV_measurements.csv")  # User-specified filename

    # Sliders for input parameters
    start_voltage = st.slider("Start Voltage (V)", min_value=-10.0, max_value=10.0, value=-1.0, step=0.1)
    stop_voltage = st.slider("Stop Voltage (V)", min_value=-10.0, max_value=10.0, value=1.0, step=0.1)
    points = st.slider("Number of Points in Sweep", min_value=1, max_value=150, value=20)
    source_limit = st.slider("Current Limit (A)", min_value=0.01, max_value=2.0, value=1.5, step=0.01)
    cycles = st.slider("Number of Cycles", min_value=1, max_value=150, value=3)

    # Initialize lists for storing data if "Start Measurement" button is pressed
    if st.button("Start Measurement"):
        # Set up the connection to the Keithley
        rm = pyvisa.ResourceManager()
        try:
            # Use the user-provided IP address to connect
            multimeter = rm.open_resource(f"TCPIP::{ip_address}::INSTR", open_timeout=5000)
            multimeter.write("*RST")
            time.sleep(1)

            # Configure instrument settings
            multimeter.write("ROUT:TERM REAR")
            multimeter.write(":SOUR:FUNC VOLT")
            multimeter.write(":SOUR:VOLT:MODE FIXED")
            multimeter.write(":SENS:FUNC 'CURR'")
            multimeter.write(f":SENS:CURR:PROT {source_limit}")
            
            # Set the best fixed range for source measurements
            multimeter.write(":SENS:CURR:RANG 0.1")       # Fixed current range
            multimeter.write(":SOUR:RANG:AUTO OFF")        # Disable auto-ranging for the source

            # Power On the Keithley output
            multimeter.write(":OUTP ON")
            st.write("Instrument output turned ON. Beginning I-V sweep...")

            # Initialize data lists
            voltage_readings = []
            current_readings = []
            relative_times = []
            start_time = time.time()
            total_measurements = cycles * points * 2  # Total forward and reverse points across cycles

            # Initialize progress bar
            progress_bar = st.progress(0)
            progress_count = 0

            # Loop over cycles
            for cycle in range(cycles):
                # Generate forward and backward voltages
                voltages = np.concatenate([np.linspace(start_voltage, stop_voltage, points),
                                        np.linspace(stop_voltage, start_voltage, points)])

                # Measure at each voltage without any delay
                for voltage in voltages:
                    multimeter.write(f":SOUR:VOLT {voltage}")
                    try:
                        current = float(multimeter.query(":READ?"))
                        relative_time = time.time() - start_time
                        voltage_readings.append(voltage)
                        current_readings.append(current)
                        relative_times.append(relative_time)

                        # Update progress
                        progress_count += 1
                        progress_bar.progress(progress_count / total_measurements)

                    except ValueError:
                        st.write(f"Measurement failed at voltage: {voltage}")

            # Power off after measurements
            multimeter.write(":OUTP OFF")
            st.write("Instrument output turned OFF.")

            # Save data to CSV
            csv_data = StringIO()
            writer = csv.writer(csv_data)
            writer.writerow(["Voltage (V)", "Current (A)", "Relative Time (s)"])
            for v, i, t in zip(voltage_readings, current_readings, relative_times):
                writer.writerow([v, i, t])

            # Create CSV download link
            st.download_button(
                label="Download CSV Data",
                data=csv_data.getvalue(),
                file_name=csv_filename,
                mime="text/csv",
            )

            # Display I-V plot
            fig, ax = plt.subplots()
            ax.plot(voltage_readings, current_readings, marker='o', linestyle='-')
            ax.set_title("I-V Characteristics")
            ax.set_xlabel("Voltage (V)")
            ax.set_ylabel("Current (A)")
            ax.grid(True)
            st.pyplot(fig)

        except pyvisa.VisaIOError as e:
            st.write(f"Connection error: {e}")

        finally:
            if 'multimeter' in locals():
                multimeter.close()

if __name__ == "__main__":
    main()
