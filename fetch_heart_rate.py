import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Define the scope for heart rate data access
SCOPES = ['https://www.googleapis.com/auth/fitness.heart_rate.read']

def authenticate():
    """Authenticate the user and create a token file."""
    creds = None
    # Check if token.json file exists, if yes load the credentials from it
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use the OAuth client secrets to authorize
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
    
    return creds

def fetch_heart_rate_data(service):
    """Fetch heart rate data from the Google Fit API."""
    # Get today's date and convert it to milliseconds
    today = datetime.datetime.now(datetime.timezone.utc)
    start_of_day = datetime.datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=datetime.timezone.utc)
    end_of_day = datetime.datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=datetime.timezone.utc)
    
    start_time = int(start_of_day.timestamp() * 1000)  # Start of today (milliseconds)
    end_time = int(end_of_day.timestamp() * 1000)  # End of today (milliseconds)

    # Use the specific Data Source ID for the heart rate data
    data_source_id = 'raw:com.google.heart_rate.bpm:com.boAt.wristgear:GoogleFitSync - HR count'
    dataset = f"{start_time}-{end_time}"

    try:
        # Fetch heart rate data from Google Fit API
        response = service.users().dataSources().datasets().get(
            userId='me', dataSourceId=data_source_id, datasetId=dataset).execute()

        heart_rate_data = response.get('point', [])
        if heart_rate_data:
            heart_rate_values = []
            for point in heart_rate_data:
                # Access heart rate value (assuming it is in bpm, like 'fpVal')
                value = point['value'][0].get('fpVal')
                if value is not None:
                    heart_rate_values.append(value)

            if heart_rate_values:
                average_heart_rate = sum(heart_rate_values) / len(heart_rate_values)
                print(f"Average Heart Rate for Today: {average_heart_rate:.2f} BPM")
            else:
                print("No heart rate data available for today.")
        else:
            print("No heart rate data found for today.")
    except Exception as e:
        print(f"An error occurred while fetching heart rate data: {e}")

def main():
    """Main function to authenticate and check the average heart rate data for today."""
    creds = authenticate()  # Ensure this function is defined above main()
    service = build('fitness', 'v1', credentials=creds)

    # Fetch heart rate data for today
    fetch_heart_rate_data(service)

if __name__ == '__main__':
    main()
