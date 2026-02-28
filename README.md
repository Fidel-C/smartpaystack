```markdown
# SmartPaystack 

A smart, framework-agnostic, strategy-based Paystack integration for Python. 

Stop writing manual math logic to calculate Paystack fees. Just declare your strategy (`ABSORB`, `PASS`, `SPLIT`) and let the package do the rest. Works seamlessly with **FastAPI, Flask, Django, Tornado, or plain Python scripts.**

## ✨ Features
* **Zero-Math API:** No more Kobo/Cents conversions. Pass native amounts (e.g., `5000` NGN).
* **Smart Fee Strategies:** Easily absorb fees, pass them to the customer, or split them.
* **Multi-Currency Routing:** Automatically applies the correct fee caps and percentages for NGN, GHS, ZAR, KES, and USD.
* **Framework Agnostic Webhooks:** Built-in HMAC SHA512 verifier that works with any web framework.
* **Fully Typed:** Sweet IDE auto-completion.

---

## 📦 Installation

```bash
pip install smartpaystack

```

---

## 🚀 Quickstart

### 1. Initialization

You can either pass your secret key directly or set it as an environment variable (`PAYSTACK_SECRET_KEY`).

```python
import os
from smartpaystack import SmartPaystack

# Option A: Uses the PAYSTACK_SECRET_KEY environment variable
os.environ["PAYSTACK_SECRET_KEY"] = "sk_live_xxxxxx"
client = SmartPaystack()

# Option B: Pass it explicitly
client = SmartPaystack(secret_key="sk_live_xxxxxx")

```

### 2. Collecting Money (Charges)

Stop worrying about fee math. Tell the client how much you want, and who pays the fee.

```python
from smartpaystack import ChargeStrategy, Currency

# Scenario A: You want exactly ₦50,000. Customer pays the Paystack fee.
response = client.create_charge(
    email="customer@email.com", 
    amount=50000, 
    currency=Currency.NGN,
    charge_strategy=ChargeStrategy.PASS 
)
print(response["authorization_url"])

# Scenario B: You absorb the fee for a Ghana Cedi transaction.
response = client.create_charge(
    email="ghana@email.com",
    amount=1000,
    currency=Currency.GHS,
    charge_strategy=ChargeStrategy.ABSORB
)

# Scenario C: You split the Paystack fee 50/50 with the customer.
# If the fee is ₦150, the customer is charged ₦10,075 and you receive ₦9,925.
response = client.create_charge(
    email="split@email.com",
    amount=10000,
    currency=Currency.NGN,
    charge_strategy=ChargeStrategy.SPLIT,
    split_ratio=0.5  # The percentage of the fee the customer pays (0.5 = 50%)
)
print(response["authorization_url"])

```

### 3. Passing Custom Metadata

You can easily attach your own custom data (like order IDs or user IDs) to a charge. The package will safely merge your custom dictionary with its own internal fee calculations so you can access both later in your webhook!

```python
response = client.create_charge(
    email="buyer@email.com",
    amount=15000,
    charge_strategy=ChargeStrategy.PASS,
    metadata={
        "custom_order_id": "ORD-88291",
        "cart_items": 3
    }
)

```

*When this transaction succeeds, your webhook will receive your custom fields alongside `smartpaystack_strategy`, `merchant_expected`, and `customer_amount`.*

### 4. Sending Money (Transfers)

Sending money is a two-step process: create a recipient, then initiate the transfer.

```python
# 1. Resolve the account (Optional but recommended)
account = client.resolve_account_number(account_number="0123456789", bank_code="033")
print(f"Resolved Name: {account['account_name']}")

# 2. Create the recipient (You can pass metadata here, too!)
recipient = client.create_transfer_recipient(
    name=account["account_name"],
    account_number="0123456789",
    bank_code="033",
    metadata={"internal_worker_id": "W-990"}
)
recipient_code = recipient["recipient_code"]

# 3. Send the money (e.g., Send ₦10,500)
transfer = client.initiate_transfer(
    amount=10500,
    recipient_code=recipient_code,
    reason="Monthly Payout"
)
print(f"Transfer Status: {transfer['status']}")

```

---

### 5. Recurring Subscriptions 📅
Easily manage billing cycles. Create a plan once, then subscribe your customers to it. 

```python
from smartpaystack import Interval

# 1. Create a Plan (e.g., A Pro tier that costs ₦10,000 / month)
plan = client.create_plan(
    name="Pro Tier Monthly",
    amount=10000,
    interval=Interval.MONTHLY
)
plan_code = plan["plan_code"]

# 2. Subscribe a customer to the plan
# Note: If the customer already has an active authorization (saved card), 
# you can pass the authorization_code to charge them immediately.
subscription = client.create_subscription(
    customer_email="user@email.com",
    plan_code=plan_code
)
print(f"Subscription active: {subscription['status']}")

# 3. Disable a subscription (Requires the sub code and email token from Paystack)
client.disable_subscription(
    subscription_code="SUB_vsy1egv220",
    email_token="e7x1bejv"
)

```


## 🛡️ Error Handling

When building fintech applications, you must handle failures gracefully. `smartpaystack` provides specific exceptions so you can catch exactly what went wrong.

```python
from smartpaystack import SmartPaystack
from smartpaystack.exceptions import PaystackAPIError, PaystackError

client = SmartPaystack()

try:
    account = client.resolve_account_number("invalid_number", "033")
except PaystackAPIError as e:
    # Raised when Paystack returns a 400/500 response, or network fails
    print(f"Paystack API failed: {str(e)}")
    # Example Output: Paystack API failed: Could not resolve account name.
except PaystackError as e:
    # A generic fallback for any other package-related error
    print(f"An unexpected error occurred: {str(e)}")

```

**Available Exceptions (from `smartpaystack.exceptions`):**

* `PaystackError`: The base class for all package exceptions.
* `PaystackAPIError`: Raised when the HTTP request to Paystack fails or returns an error message.
* `WebhookVerificationError`: Raised when the HMAC signature on an incoming webhook is invalid or missing.

---

## 📡 Verifying Webhooks

Paystack sends webhooks to your server when events happen (like a successful charge or transfer). `smartpaystack` provides a generic `WebhookVerifier` that works with any framework.

### Example: FastAPI

```python
from fastapi import FastAPI, Request, Header, HTTPException
from smartpaystack import WebhookVerifier
from smartpaystack.exceptions import WebhookVerificationError

app = FastAPI()
verifier = WebhookVerifier(secret_key="sk_live_xxxxxx")

@app.post("/paystack/webhook")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(None)):
    raw_body = await request.body()
    
    try:
        # Verifies the HMAC SHA512 signature and parses the JSON
        event_data = verifier.verify_and_parse(raw_body, x_paystack_signature)
    except WebhookVerificationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event_data["event"] == "charge.success":
        data = event_data["data"]
        # Retrieve the math breakdown and your custom metadata!
        merchant_keeps = data["metadata"]["merchant_expected"]
        order_id = data["metadata"].get("custom_order_id")
        
        print(f"Payment successful for Order {order_id}! Expected payout: {merchant_keeps}")
        
    return {"status": "success"}

```

### Example: Flask

```python
from flask import Flask, request, jsonify
from smartpaystack import WebhookVerifier
from smartpaystack.exceptions import WebhookVerificationError

app = Flask(__name__)
verifier = WebhookVerifier(secret_key="sk_live_xxxxxx")

@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    signature = request.headers.get("x-paystack-signature")
    raw_body = request.get_data()
    
    try:
        event_data = verifier.verify_and_parse(raw_body, signature)
    except WebhookVerificationError as e:
        return jsonify({"error": str(e)}), 400

    if event_data["event"] == "transfer.success":
        print("Transfer successful!")
        
    return jsonify({"status": "success"}), 200

```

### Example: Django

In your `views.py`, use `@csrf_exempt` since Paystack (an external service) cannot send a CSRF token.

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from smartpaystack import WebhookVerifier
from smartpaystack.exceptions import WebhookVerificationError

# Initialize the verifier (ideally load this from environment or settings)
verifier = WebhookVerifier(secret_key=getattr(settings, "PAYSTACK_SECRET_KEY", "sk_live_xxxxxx"))

@csrf_exempt
@require_POST
def paystack_webhook(request):
    signature = request.headers.get("x-paystack-signature", "")
    raw_body = request.body # Django provides the raw bytes here
    
    try:
        event_data = verifier.verify_and_parse(raw_body, signature)
    except WebhookVerificationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # Handle the event
    if event_data["event"] == "charge.success":
        print(f"Payment successful for amount: {event_data['data']['amount']}")
        
    return JsonResponse({"status": "success"}, status=200)



```



