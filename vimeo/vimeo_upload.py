from dotenv import load_dotenv
import vimeo
import os


# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
access_token = os.getenv('VIMEO_UPLOAD_API_KEY')
client_id = os.getenv('VIMEO_CLIENT_ID')
client_secret = os.getenv('VIMEO_CLIENT_SECRET')

uri = '/videos/10695948153223'
client = vimeo.VimeoClient(
    token=access_token,
    key=client_id,
    secret=client_secret
)

print(f"Attempting to update video: {uri}")
print(f"{'='*60}")

try:
    response = client.patch(uri, data={
      'description': """Learn about the multiple methods of Nicotine Replacement Therapy to help you curb smoking urges and withdrawal symptoms.
        \n
        \n☑ Nicotine Replacement Therapy Awareness
        \n☑ Enhanced Respiratory Health
        \n☑ Reduced Smoking Urges
        \n
        \n✎ Learn The Science: NRT is not safe for pregnant women, breastfeeding women, and teenagers. If you have had a history of heart attacks or heart problems, please speak with your doctor before beginning NRT.
        \n
        \n*The program is intended for general information purposes only. It is not intended to be relied upon and is not a substitute for professional medical advice based on your individual conditions and circumstances. Your use of Caravan services is subject to additional terms and conditions."""
    })

    # Check response status
    print(f"\n✓ SUCCESS!")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("Video description updated successfully!")

        # Try to parse response body
        try:
            response_data = response.json()
            print(f"\nResponse Data:")
            print(f"  - Video Name: {response_data.get('name', 'N/A')}")
            print(f"  - Video URI: {response_data.get('uri', 'N/A')}")
            print(f"  - Description: {response_data.get('description', 'N/A')[:100]}...")
        except:
            print(f"\nRaw Response: {response.text[:200]}")
    elif response.status_code == 204:
        print("Video updated successfully (No content returned)")
    else:
        print(f"Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n✗ FAILED!")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")

    # Check if it's an HTTP error with response details
    if hasattr(e, 'response'):
        print(f"\nHTTP Status Code: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")

print(f"\n{'='*60}")