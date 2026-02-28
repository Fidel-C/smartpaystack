import pytest
import responses
from smartpaystack import SmartPaystack, Interval, Currency

# We'll create a reusable client for these tests
@pytest.fixture
def client():
    return SmartPaystack(secret_key="sk_test_fake_secret_key")

@responses.activate
def test_create_plan(client):
    # 1. Mock the API endpoint
    responses.add(
        responses.POST,
        "https://api.paystack.co/plan",
        json={
            "status": True, 
            "message": "Plan created", 
            "data": {
                "name": "Pro Tier Monthly", 
                "plan_code": "PLN_gx2wn530m0i3w3m", 
                "interval": "monthly", 
                "amount": 1000000 # 10,000 NGN in kobo
            }
        },
        status=201
    )

    # 2. Call your method
    response = client.create_plan(
        name="Pro Tier Monthly",
        amount=10000,
        interval=Interval.MONTHLY
    )
    
    # 3. Assert the package handled it correctly
    assert response["plan_code"] == "PLN_gx2wn530m0i3w3m"
    assert response["amount"] == 1000000

@responses.activate
def test_create_subscription(client):
    responses.add(
        responses.POST,
        "https://api.paystack.co/subscription",
        json={
            "status": True, 
            "message": "Subscription successfully created", 
            "data": {
                "customer": 1173, 
                "plan": 28, 
                "status": "active", 
                "subscription_code": "SUB_vsy1egv220"
            }
        },
        status=200
    )

    response = client.create_subscription(
        customer_email="user@email.com", 
        plan_code="PLN_gx2wn530m0i3w3m"
    )
    
    assert response["status"] == "active"
    assert response["subscription_code"] == "SUB_vsy1egv220"

@responses.activate
def test_enable_subscription(client):
    responses.add(
        responses.POST,
        "https://api.paystack.co/subscription/enable",
        json={
            "status": True, 
            "message": "Subscription enabled successfully",
            # Paystack sometimes omits the data dictionary on simple state toggles,
            # so we test our client's ability to gracefully fall back to returning the whole response.
        },
        status=200
    )

    response = client.enable_subscription(
        subscription_code="SUB_vsy1egv220", 
        email_token="e7x1bejv"
    )
    
    assert response["status"] is True
    assert response["message"] == "Subscription enabled successfully"

@responses.activate
def test_disable_subscription(client):
    responses.add(
        responses.POST,
        "https://api.paystack.co/subscription/disable",
        json={
            "status": True, 
            "message": "Subscription disabled successfully",
        },
        status=200
    )

    response = client.disable_subscription(
        subscription_code="SUB_vsy1egv220", 
        email_token="e7x1bejv"
    )
    
    assert response["status"] is True
    assert response["message"] == "Subscription disabled successfully"