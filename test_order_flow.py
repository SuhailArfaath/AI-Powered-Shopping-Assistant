import requests
import json

BASE = "http://localhost:8000/api/chat"

print("="*60)
print("TEST 1: Place order with ASIN + qty (missing details)")
print("="*60)
r = requests.post(BASE, json={"message": "I want to order B0CHH6X6H2 5 quantities", "session_id": "testflow1"})
d = r.json()
print(d["reply"][:800])
print(f"\nshow_order_button: {d.get('show_order_button', False)}")
print("\nOutbound guardrails:")
for g in d.get("outbound_guardrails", []):
    status = "PASS" if g["passed"] else "FAIL"
    print(f"  {status} - {g['name']}")
print()

print("="*60)
print("TEST 2: Provide missing details (name, email, address)")
print("="*60)
r = requests.post(BASE, json={"message": "My name is Batman, email batman@wayne.com, address 1 Batcave Lane, Gotham", "session_id": "testflow1"})
d = r.json()
print(d["reply"][:1000])
print(f"\nshow_order_button: {d.get('show_order_button', False)}")
print()

print("="*60)
print("TEST 3: Confirm order (click Place Order)")
print("="*60)
r = requests.post(BASE, json={"message": "confirm order", "session_id": "testflow1"})
d = r.json()
print(d["reply"][:800])
print()

print("="*60)
print("TEST 4: Check orders page")
print("="*60)
r = requests.get("http://localhost:8000/api/orders")
d = r.json()
for o in d.get("orders", []):
    print(f"  #{o['id']} - {o['customer_name']} - {o['product_asin']} - {o['quantity']}x - ${o['total_price']} - {o['status']}")
