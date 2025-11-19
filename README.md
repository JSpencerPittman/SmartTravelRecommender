# Smart Travel Recommender
## Team Members
1. Jason Pittman
2. Rex Berry
3. Jeffin Joseph

## Project Description
The Smart Travel Recommender uses AI to create personalized travel itineraries tailored to your needs. Planning a budget trip to Europe? 
Looking for highly-rated attractions near your current location? Our application does the heavy lifting for you.
Powered by a large language model and real-time web data, the Smart Travel Recommender generates custom itineraries that match your preferences, 
budget, and travel style—whether you're planning ahead or exploring on the go.

## Development Setup
*We are in the development stage so usage of this application requires locally running it.*

Once you've cloned the repository and created a virtual environment,
```bash
pip install -r requirements.txt
cd smart_travel
```

This is a Django-based application so all commands will be run as `python manage.py <command>`.
```bash
# Load sample data (Optional)
python manage.py load_sample_data

# Run development server
python manage.py runserver
```
