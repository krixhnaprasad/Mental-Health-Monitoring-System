import os
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Set the required Google Fit API scopes for heart rate and sleep data
SCOPES = [
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read'
]

# Authenticate with Google Fit API
def authenticate_google_fit():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

# Fetch data from Google Fit API
def fetch_data(service, start_time, end_time, data_source_id, data_type):
    body = {
        "aggregateBy": [
            {
                "dataTypeName": data_type,
                "dataSourceId": data_source_id
            }
        ],
        "bucketByTime": { "durationMillis": 86400000 },  # 1 day in milliseconds
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }
    
    try:
        response = service.users().dataset().aggregate(userId="me", body=body).execute()
        return response
    except Exception as e:
        if "403" in str(e):  # Check if the error is 403 (Forbidden)
            print("Error: Unable to access sleep data source. Data may not be available or accessible.")
        else:
            print(f"Error fetching {data_type} data: {e}")
        return None

# Calculate the average heart rate from the data points
def calculate_average_heart_rate(response):
    total_heart_rate = 0
    count = 0

    for bucket in response.get('bucket', []):
        for dataset in bucket.get('dataset', []):
            for point in dataset.get('point', []):
                for value in point.get('value', []):
                    total_heart_rate += value.get('fpVal')
                    count += 1

    if count == 0:
        return None

    return total_heart_rate / count

# Calculate total sleep time in hours
def calculate_total_sleep_hours(response):
    total_sleep_duration_nanos = 0  # Total sleep duration in nanoseconds

    if response and response.get('bucket'):
        for bucket in response.get('bucket', []):
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    start_time_nanos = int(point.get('startTimeNanos'))
                    end_time_nanos = int(point.get('endTimeNanos'))
                    
                    # Calculate duration for this sleep segment
                    duration_nanos = end_time_nanos - start_time_nanos
                    total_sleep_duration_nanos += duration_nanos

    # Convert total duration from nanoseconds to hours
    total_sleep_hours = total_sleep_duration_nanos / 1e9 / 3600  # nanoseconds to hours
    return total_sleep_hours

# Function to assess mental health based on input values
def assess_mental_health(heart_rate_var, sleep_hours, noise_level, light_level):
    stress_score = 0

    # Physiological Factors
    if heart_rate_var < 50 or heart_rate_var > 95:
        stress_score += 1

    if sleep_hours < 6 or sleep_hours > 15:
        stress_score += 1

    # Environmental Factors
    if noise_level > 70:
        stress_score += 1

    if light_level < 30 or light_level > 200:
        stress_score += 1

    return stress_score

# Function to provide recommendations based on stress score
def provide_recommendation(stress_score):
    if stress_score == 0:
        return "You are doing well! Keep up your current routine."
    elif stress_score == 1:
        return "Slight stress detected. Try to relax and take breaks."
    elif stress_score == 2:
        return "Moderate stress detected. Ensure you have enough sleep and reduce exposure to noise."
    elif stress_score == 3:
        return "High stress detected. Consider reducing environmental stressors and practice mindfulness."
    else:
        return "Critical stress levels detected! Please reach out to a mental health professional."

# Function to automatically fetch data from Google Fit and display results
def fetch_and_display_data():
    try:
        # Fetch heart rate and sleep data from Google Fit
        creds = authenticate_google_fit()
        service = build('fitness', 'v1', credentials=creds)

        # Define the time period (example: last 1 day)
        now = datetime.now(timezone.utc)
        start_time = int((now - timedelta(days=1)).timestamp() * 1000)
        end_time = int(now.timestamp() * 1000)

        # Data source IDs
        heart_rate_data_source = "raw:com.google.heart_rate.bpm:com.boAt.wristgear:GoogleFitSync - HR count"
        sleep_data_source = "derived:com.google.sleep.segment:com.google.android.gms:merge_sleep_segments"

        # Fetch heart rate data
        heart_rate_response = fetch_data(service, start_time, end_time, heart_rate_data_source, "com.google.heart_rate.bpm")

        # Fetch sleep data
        sleep_response = fetch_data(service, start_time, end_time, sleep_data_source, "com.google.sleep.segment")

        # Calculate average heart rate
        if heart_rate_response:
            avg_heart_rate = calculate_average_heart_rate(heart_rate_response)
        else:
            avg_heart_rate = 0  # Set to 0 if no data is available

        # Calculate total sleep hours
        if sleep_response:
            total_sleep_hours = calculate_total_sleep_hours(sleep_response)
        else:
            total_sleep_hours = 0  # Set sleep hours to 0 if data is not available

        # Set the values in the entry fields
        hrv_entry.delete(0, tk.END)
        hrv_entry.insert(0, str(avg_heart_rate))

        sleep_entry.delete(0, tk.END)
        sleep_entry.insert(0, str(total_sleep_hours))

    except Exception as e:
        print(f"Error fetching data from Google Fit: {e}")

# Function to display results based on user inputs
def on_update():
    try:
        # Fetch heart rate and sleep data
        fetch_and_display_data()

        # Get user input for noise and light levels
        noise_level = float(noise_entry.get())
        light_level = float(light_entry.get())

        # Fetch the heart rate and sleep data from the entry fields
        heart_rate = float(hrv_entry.get())
        sleep_hours = float(sleep_entry.get())

        # Assess stress based on the values
        stress_score = assess_mental_health(heart_rate, sleep_hours, noise_level, light_level)
        recommendation = provide_recommendation(stress_score)

        # Set the stress score and recommendation
        result_var.set(f"Stress Score: {stress_score}")
        
        # Change font color based on stress score
        if stress_score == 0:
            result_label.config(fg='green')  # Green for good health
        else:
            result_label.config(fg='#007BFF')  # Blue for other levels

        recommendation_var.set(f"Recommendation: {recommendation}")
        
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric values.")

# Create the main application window
app = tk.Tk()
app.title("Mental Health Monitoring System")

# Set background color to a light gradient
app.configure(bg='#e6f2ff')

# Load and display logo (ensure you have an image file 'logo.png' in the same directory)
try:
    logo_image = Image.open("logo.jpeg")
    logo_image = logo_image.resize((400, 200))  # Resize logo to fit desktop size
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(app, image=logo_photo, bg='#e6f2ff')
    logo_label.grid(row=0, column=0, columnspan=2, pady=20)
except Exception as e:
    messagebox.showwarning("Image Load Error", f"Could not load logo: {e}")

# Define styles for the labels and entry fields
label_fg = '#003366'  # Dark blue for text
entry_bg = '#ffffff'  # White background for entry fields
entry_fg = '#000000'  # Black text color for entry fields

# Define the labels and entry fields dynamically
fields = [
    ("Heart Rate Variability (BPM):", 1),
    ("Sleep Hours:", 2),
    ("Noise Level (dB):", 3),
    ("Light Level (lux):", 4)
]

hrv_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg)
sleep_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg)
noise_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg)
light_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg)

# Place the labels and entries dynamically
for label_text, row_num in fields:
    label = tk.Label(app, text=label_text, font=("Helvetica", 12), fg=label_fg, bg="#e6f2ff")
    label.grid(row=row_num, column=0, padx=20, pady=5, sticky='w')

# Place the entry fields in grid
hrv_entry.grid(row=1, column=1, padx=20, pady=5)
sleep_entry.grid(row=2, column=1, padx=20, pady=5)
noise_entry.grid(row=3, column=1, padx=20, pady=5)
light_entry.grid(row=4, column=1, padx=20, pady=5)

# Create the submit button
submit_button = tk.Button(app, text="Update", command=on_update, bg='#007bff', fg='white', font=("Helvetica", 12))
submit_button.grid(row=5, column=0, columnspan=2, pady=20)

# Display result label
result_var = tk.StringVar()
result_label = tk.Label(app, textvariable=result_var, font=("Helvetica", 12), bg='#e6f2ff')
result_label.grid(row=6, column=0, columnspan=2)

# Display recommendation label
recommendation_var = tk.StringVar()
recommendation_label = tk.Label(app, textvariable=recommendation_var, font=("Helvetica", 12), bg='#e6f2ff')
recommendation_label.grid(row=7, column=0, columnspan=2)

# Start the automatic data fetch when the app is launched
fetch_and_display_data()

# Start the GUI event loop
app.mainloop()
