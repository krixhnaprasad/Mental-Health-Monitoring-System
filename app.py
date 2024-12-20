import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

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
entry_fg = '#003366'  # Dark blue text

# Create input fields with labels and better color scheme
fields = [
    ("Heart Rate Variability:", 1),
    ("Sleep Hours:", 2),
    ("Noise Level (dB):", 3),
    ("Light Level (lumens):", 4),
]

for field, row in fields:
    tk.Label(app, text=field, bg='#e6f2ff', fg=label_fg, font=('Arial', 10, 'bold')).grid(row=row, column=0, padx=10, pady=5, sticky='e')

hrv_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg, font=('Arial', 10))
hrv_entry.grid(row=1, column=1, padx=10, pady=5, ipadx=5, ipady=3)

sleep_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg, font=('Arial', 10))
sleep_entry.grid(row=2, column=1, padx=10, pady=5, ipadx=5, ipady=3)

noise_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg, font=('Arial', 10))
noise_entry.grid(row=3, column=1, padx=10, pady=5, ipadx=5, ipady=3)

light_entry = tk.Entry(app, bg=entry_bg, fg=entry_fg, font=('Arial', 10))
light_entry.grid(row=4, column=1, padx=10, pady=5, ipadx=5, ipady=3)

# Create a submit button with an accent color
submit_button = tk.Button(app, text="Submit", command=on_submit, bg='#0059b3', fg='white', font=('Arial', 10, 'bold'))
submit_button.grid(row=5, columnspan=2, pady=20)

# Create result display fields with colors for better readability
result_var = tk.StringVar()
result_label = tk.Label(app, textvariable=result_var, bg='#e6f2ff', fg='#007BFF', font=('Arial', 12, 'bold'))
result_label.grid(row=6, columnspan=2, pady=10)

recommendation_var = tk.StringVar()
tk.Label(app, textvariable=recommendation_var, bg='#e6f2ff', fg='#FF5733', font=('Arial', 12, 'italic')).grid(row=7, columnspan=2, pady=10)

# Make the layout more responsive to window size
for row in range(8):
    app.grid_rowconfigure(row, weight=1)
    app.grid_columnconfigure(1, weight=1)

# Start the main event loop
app.mainloop()
