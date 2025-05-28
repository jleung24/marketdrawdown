from locust import HttpUser, TaskSet, task, between
import json

class MarketDrawdownTasks(TaskSet):
    wait_time = between(1, 3)  # Simulate user think time

    @task(1)
    def get_data(self):
        # Extract CSRF token from the TaskSet's user instance
        csrftoken = self.user.csrf_token
        if not csrftoken:
            print("CSRF token is missing; ensure the index task has run!")
            return  # Skip task if CSRF token is not available

        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "X-CSRFToken": csrftoken} # Include header for AJAX requests
        payload = {
            "csrfmiddlewaretoken": csrftoken,  # Use the extracted token
            "index-dropdown": "SPY",
            "drawdown_range_min": "15",
            "drawdown_range_max": "30",
            "duration_range_min": "0",
            "duration_range_max": "1000",
            "recovery_target": "85"
        }

        with self.client.post("/get_data/", data=payload, catch_response=True, headers=headers) as response:
            if response.status_code == 200:
                # Check for certain content if needed
                if "dashboard" in response.text:
                    response.success()
            else:
                response.failure(f"Status code {response.status_code}")


    @task(2) # Weighting for different tasks
    def index(self):
        response = self.client.get("/")
        csrftoken = response.cookies.get('csrftoken')
        if not csrftoken:
            print("CSRF token not found")
            return

        # Pass the csrfmiddlewaretoken
        self.user.csrf_token = csrftoken # Store CSRF token to the HttpUser instance


class WebsiteUser(HttpUser):
    host = "http://localhost:8000" # Replace with your server's URL
    wait_time = between(2, 5) # Time between task execution
    tasks = [MarketDrawdownTasks]

    def on_start(self):
        # Initialize CSRF token
        self.csrf_token = None
        # Get CSRF token on start
        response = self.client.get("/")
        csrftoken = response.cookies.get('csrftoken')
        if not csrftoken:
            print("CSRF token not found, login might fail")
        # Pass the csrfmiddlewaretoken
        self.csrf_token = csrftoken
