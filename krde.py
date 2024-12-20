import os
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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

def main():
    # Step 1: Authenticate
    creds = authenticate_google_fit()

    # Step 2: Build the Google Fit API service
    service = build('fitness', 'v1', credentials=creds)

    # Step 3: Define the time period (example: last 1 day)
    now = datetime.now(timezone.utc)
    start_time = int((now - timedelta(days=1)).timestamp() * 1000)
    end_time = int(now.timestamp() * 1000)

    # Data source IDs
    heart_rate_data_source = "raw:com.google.heart_rate.bpm:com.boAt.wristgear:GoogleFitSync - HR count"
    sleep_data_source = "derived:com.google.sleep.segment:com.google.android.gms:merge_sleep_segments"
    
    print(f"Querying heart rate and sleep data sources...")

    # Step 4: Fetch heart rate data
    heart_rate_response = fetch_data(service, start_time, end_time, heart_rate_data_source, "com.google.heart_rate.bpm")
    
    # Step 5: Fetch sleep data
    sleep_response = fetch_data(service, start_time, end_time, sleep_data_source, "com.google.sleep.segment")

    # Step 6: Calculate and print average heart rate
    if heart_rate_response:
        avg_heart_rate = calculate_average_heart_rate(heart_rate_response)
    
        if avg_heart_rate:
            print(f"Average Heart Rate: {avg_heart_rate:.2f} bpm")
        else:
            print("No heart rate data available.")
    else:
        print(f"Failed to retrieve heart rate data.")

    # Step 7: Calculate and print total sleep hours
    if sleep_response:
        total_sleep_hours = calculate_total_sleep_hours(sleep_response)
    else:
        total_sleep_hours = 0  # Set sleep hours to 0 if data is not available

    print(f"Total Sleep Time: {total_sleep_hours:.2f} hours")

if __name__ == '__main__':
    main()
