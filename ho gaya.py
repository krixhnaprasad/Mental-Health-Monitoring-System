import os
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Set the required Google Fit API scopes
SCOPES = ['https://www.googleapis.com/auth/fitness.heart_rate.read']

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

# Fetch the last recorded heart rate data from Google Fit API
def fetch_last_heart_rate_data():
    creds = authenticate_google_fit()
    service = build('fitness', 'v1', credentials=creds)

    now = datetime.now(timezone.utc)
    start_of_today = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
    start_time = int(start_of_today.timestamp() * 1000)  # Start of today in milliseconds
    end_time = int(now.timestamp() * 1000)  # Current time in milliseconds

    data_source_id = "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"

    body = {
        "aggregateBy": [
            {
                "dataTypeName": "com.google.heart_rate.bpm",
                "dataSourceId": data_source_id
            }
        ],
        "bucketByTime": { "durationMillis": 60000 },
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }
    
    try:
        response = service.users().dataset().aggregate(userId="me", body=body).execute()
        last_heart_rate = None
        for bucket in response.get('bucket', []):
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        last_heart_rate = value.get('fpVal')
        return last_heart_rate
    except Exception as e:
        print(f"Error fetching heart rate data: {e}")
        return None

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

# Function to collect sensor data from user input and assess mental health
def on_submit():
    try:
        heart_rate_var = int(hrv_entry.get())
        sleep_hours = float(sleep_entry.get())
        noise_level = float(noise_entry.get())
        light_level = float(light_entry.get())

        stress_score = assess_mental_health(heart_rate_var, sleep_hours, noise_level, light_level)
        recommendation = provide_recommendation(stress_score)

        # Set the stress score text
        result_var.set(f"Stress Score: {stress_score}")
        
        # Change font color based on stress score
        if stress_score == 0:
            result_label.config(fg='green')  # Green for good health
        else:
            result_label.config(fg='#007BFF')  # Blue for other levels

        # Set the recommendation text
        recommendation_var.set(f"Recommendation: {recommendation}")
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric values.")

# Function to auto-fill heart rate value from Google Fit API
def auto_fill_heart_rate():
    last_heart_rate = fetch_last_heart_rate_data()
    if last_heart_rate:
        hrv_entry.delete(0, tk.END)  # Clear the entry field first
        hrv_entry.insert(0, str(int(last_heart_rate)))  # Insert the fetched heart rate value

# Create the main application window
app = tk.Tk()
app.title("Mental Health Monitoring System")
app.configure(bg='#e6f2ff')

# Load and display logo (ensure you have an image file 'logo.png' in the same directory)
try:
    logo_image = Image.open("logo.jpeg")
    logo_image = logo_image.resize((400, 200))
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(app, image=logo_photo, bg='#e6f2ff')
    logo_label.grid(row=0, column=0, columnspan=2, pady=20)
except Exception as e:
    messagebox.showwarning("Image Load Error", f"Could not load logo: {e}")

# Create input fields
fields = [
    ("Heart Rate Variability:", 1),
    ("Sleep Hours:", 2),
    ("Noise Level (dB):", 3),
    ("Light Level (lumens):", 4),
]

for field, row in fields:
    tk.Label(app, text=field, bg='#e6f2ff', fg='#003366', font=('Arial', 10, 'bold')).grid(row=row, column=0, padx=10, pady=5, sticky='e')

hrv_entry = tk.Entry(app, bg='#ffffff', fg='#003366', font=('Arial', 10))
hrv_entry.grid(row=1, column=1, padx=10, pady=5, ipadx=5, ipady=3)

sleep_entry = tk.Entry(app, bg='#ffffff', fg='#003366', font=('Arial', 10))
sleep_entry.grid(row=2, column=1, padx=10, pady=5, ipadx=5, ipady=3)

noise_entry = tk.Entry(app, bg='#ffffff', fg='#003366', font=('Arial', 10))
noise_entry.grid(row=3, column=1, padx=10, pady=5, ipadx=5, ipady=3)

light_entry = tk.Entry(app, bg='#ffffff', fg='#003366', font=('Arial', 10))
light_entry.grid(row=4, column=1, padx=10, pady=5, ipadx=5, ipady=3)

# Create a submit button
submit_button = tk.Button(app, text="Submit", command=on_submit, bg='#0059b3', fg='white', font=('Arial', 10, 'bold'))
submit_button.grid(row=5, columnspan=2, pady=20)

# Create result display fields
result_var = tk.StringVar()
result_label = tk.Label(app, textvariable=result_var, bg='#e6f2ff', fg='#007BFF', font=('Arial', 12, 'bold'))
result_label.grid(row=6, columnspan=2, pady=10)

recommendation_var = tk.StringVar()
tk.Label(app, textvariable=recommendation_var, bg='#e6f2ff', fg='#FF5733', font=('Arial', 12, 'italic')).grid(row=7, columnspan=2, pady=10)

# Automatically fill heart rate when app starts
auto_fill_heart_rate()

# Start the main event loop
app.mainloop()
