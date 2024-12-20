import os
import json
from datetime import datetime, timedelta, timezone
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

# Fetch heart rate data from Google Fit API
def fetch_heart_rate_data(service, start_time, end_time, data_source_id):
    body = {
        "aggregateBy": [
            {
                "dataTypeName": "com.google.heart_rate.bpm",
                "dataSourceId": data_source_id
            }
        ],
        "bucketByTime": { "durationMillis": 60000 },  # 1 minute in milliseconds to get detailed data points
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }
    
    try:
        response = service.users().dataset().aggregate(userId="me", body=body).execute()
        return response
    except Exception as e:
        print(f"Error fetching heart rate data: {e}")
        return None

# Extract the last recorded heart rate data point
def extract_last_heart_rate_data(response):
    last_heart_rate = None
    last_time = None

    for bucket in response.get('bucket', []):
        for dataset in bucket.get('dataset', []):
            for point in dataset.get('point', []):
                start_time = datetime.utcfromtimestamp(int(point['startTimeNanos']) / 1e9).strftime('%Y-%m-%d %H:%M:%S')
                for value in point.get('value', []):
                    heart_rate = value.get('fpVal')
                    last_heart_rate = heart_rate
                    last_time = start_time  # Keep updating to get the latest time and heart rate

    return {'time': last_time, 'heart_rate': last_heart_rate} if last_heart_rate else None

def main():
    # Step 1: Authenticate
    creds = authenticate_google_fit()

    # Step 2: Build the Google Fit API service
    service = build('fitness', 'v1', credentials=creds)

    # Step 3: Define the time period (start of today to now)
    now = datetime.now(timezone.utc)
    start_of_today = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
    start_time = int(start_of_today.timestamp() * 1000)  # Start of today in milliseconds
    end_time = int(now.timestamp() * 1000)  # Current time in milliseconds

    # Use derived data source to fetch detailed heart rate data
    data_source_id = "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
    
    # Step 4: Fetch heart rate data for today
    response = fetch_heart_rate_data(service, start_time, end_time, data_source_id)

    # Step 5: Extract and print the last recorded heart rate data point
    if response:
        last_heart_rate_data = extract_last_heart_rate_data(response)

        if last_heart_rate_data:
            print(f"Last recorded heart rate:")
            print(f"Time: {last_heart_rate_data['time']}, Heart Rate: {last_heart_rate_data['heart_rate']:.2f} bpm")
        else:
            print("No heart rate data available for today.")
    else:
        print(f"Failed to retrieve heart rate data from {data_source_id}.")

if __name__ == '__main__':
    main()
