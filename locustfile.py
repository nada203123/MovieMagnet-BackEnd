from locust import HttpUser, task, between

class MovieAppUser(HttpUser):
    wait_time = between(1, 3)  # Simulates a wait time of 1 to 3 seconds between requests

    def on_start(self):
        """Executed when a user starts a session."""
        self.login()

    def login(self):
        """Logs in the user and stores the authentication token."""
        response = self.client.post("/api/auth/signin/", json={
            "email": "nada.ghribi13@gmail.com",
            "password": "nada.ghribi13@gmail.com"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            self.token = None
            print(f"Login failed: {response.text}")

    @task(2)
    def home_page(self):
        """Test the home page endpoint."""
        self.client.get("/api/auth/home/")

    @task(1)
    def search_movies(self):
        """Test the search movies endpoint."""
        query = "Th"
        self.client.get(f"/api/auth/search/?q={query}")

    @task(3)
    def get_recommendations(self):
        """Test the recommend movies endpoint."""
        
        self.client.post("/api/auth/recommend/", json={"movie_name": "Inception"})

   
