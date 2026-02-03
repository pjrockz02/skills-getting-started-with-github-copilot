import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_basketball_activity_exists(self):
        """Test that Basketball activity exists"""
        response = client.get("/activities")
        activities = response.json()
        assert "Basketball" in activities

    def test_activities_have_initial_participants(self):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        activities = response.json()
        
        # At least one activity should have participants
        has_participants = any(
            len(activity["participants"]) > 0 
            for activity in activities.values()
        )
        assert has_participants


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_returns_200(self):
        """Test signing up a new participant returns 200"""
        response = client.post(
            "/activities/Basketball/signup?email=test@example.com"
        )
        assert response.status_code == 200

    def test_signup_new_participant_returns_success_message(self):
        """Test signup returns a success message"""
        response = client.post(
            "/activities/Tennis Club/signup?email=newuser@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newuser@example.com" in data["message"]

    def test_signup_duplicate_participant_returns_400(self):
        """Test signing up the same participant twice returns 400"""
        email = "duplicate@example.com"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Art Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Art Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_invalid_activity_returns_404(self):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Invalid Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds the participant"""
        email = "verify@example.com"
        
        # Get initial participants count
        response = client.get("/activities")
        initial_count = len(response.json()["Drama Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        updated_count = len(response.json()["Drama Club"]["participants"])
        assert updated_count == initial_count + 1
        assert email in response.json()["Drama Club"]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_returns_200(self):
        """Test unregistering an existing participant returns 200"""
        email = "unregister@example.com"
        
        # First sign up
        client.post(f"/activities/Basketball/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 200

    def test_unregister_returns_success_message(self):
        """Test unregister returns a success message"""
        email = "unregister2@example.com"
        
        client.post(f"/activities/Tennis Club/signup?email={email}")
        response = client.post(
            f"/activities/Tennis Club/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_nonexistent_participant_returns_400(self):
        """Test unregistering a non-existent participant returns 400"""
        response = client.post(
            "/activities/Math Club/unregister?email=nonexistent@example.com"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_invalid_activity_returns_404(self):
        """Test unregistering from a non-existent activity returns 404"""
        response = client.post(
            "/activities/Invalid Activity/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removetest@example.com"
        activity = "Robotics Club"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_index(self):
        """Test that root redirects to /static/index.html"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
