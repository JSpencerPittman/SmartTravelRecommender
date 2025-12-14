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

## Setup
Once you've cloned the repository and created a virtual environment,
```bash
pip install -r requirements.txt
cd smart_travel
```
Before we start up the server you will need to get an API key for the OpenAI repository. Then you will need to set the `OPENAI_API_KEY` environment variable.
```bash
export OPENAI_API_KEY=...
```
Then we will need to establish the models in sqlite.
```bash
python manage.py makemigrations
python manage.py migrate
```
Now we can bootup the Django server.
```bash
python manage.py runserver
```
You will be able to find the application being hosted at `http://127.0.0.1:8000`.
## Testing
For unit & integration testing django offers us the ability to test using the `manage.py` script.
```bash
python manage.py test accounts chat integration_tests
```

To get coverage reports as well you can use the `coverage` library with the following sequence of commands.
```bash
coverage run --source='.' manage.py test accounts chat integration_tests
coverage report
coverage html
```

## Admin
To access administrator pages you will need to create a new user using the following command.
```bash
python manage.py createsuperuser
```
For access to the usage statistics pages navigate to `http://127.0.0.1:8000/admin/usage-statistics`.
