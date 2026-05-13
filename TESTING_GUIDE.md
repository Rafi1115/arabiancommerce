# 🧪 ARABIAN COMMERCE - TESTING GUIDE
# Location-Based Delivery E-commerce System

## 📋 SETUP FIRST
```bash
# 1. Run migrations (if not done)
python manage.py makemigrations
python manage.py migrate

# 2. Load test data
python manage.py load_test_data

# 3. Create admin user (if needed)
python manage.py createsuperuser

# 4. Start server
python manage.py runserver
```

---

## 🎯 TESTING FLOW

### PHASE 1: ADMIN SETUP
#### 1. Admin Login
```bash
curl -X POST http://localhost:8000/api/accounts/admin/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "yourpassword"
  }'
```
**Expected:** Get access & refresh tokens

#### 2. Check Delivery Zones (should be loaded)
```bash
curl -X GET http://localhost:8000/api/accounts/admin/delivery-zones/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```
**Expected:** 4 zones (Downtown Dubai, Dubai Marina, etc.)

#### 3. Check Categories & Products
```bash
# Categories
curl -X GET http://localhost:8000/api/admin/categories/

# Products
curl -X GET http://localhost:8000/api/admin/products/
```

---

### PHASE 2: CUSTOMER REGISTRATION & LOGIN
#### 1. Register Customer
```bash
# Send OTP
curl -X POST http://localhost:8000/api/accounts/register/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+971501234567"}'

# Verify OTP (use code from console/logs)
curl -X POST http://localhost:8000/api/accounts/register/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+971501234567", "otp": "123456"}'
```

#### 2. Login Customer
```bash
# Send login OTP
curl -X POST http://localhost:8000/api/accounts/login/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+971501234567"}'

# Verify login OTP
curl -X POST http://localhost:8000/api/accounts/login/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+971501234567", "otp": "123456"}'
```
**Expected:** Get access token for customer

---

### PHASE 3: ADDRESS MANAGEMENT
#### 1. Create Address (with location for delivery zones)
```bash
curl -X POST http://localhost:8000/api/accounts/addresses/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Home",
    "full_address": "Villa 123, Dubai Marina, Dubai, UAE",
    "city": "Dubai",
    "area": "Marina",
    "latitude": 25.0780,
    "longitude": 55.1400,
    "is_default": true
  }'
```
**Expected:** Address created with delivery_zone auto-assigned (Dubai Marina - 25 AED)

#### 2. Check Address with Delivery Info
```bash
curl -X GET http://localhost:8000/api/accounts/addresses/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
```
**Expected:** Address shows delivery_zone_name and delivery_fee

---

### PHASE 4: CART OPERATIONS
#### 1. View Empty Cart
```bash
curl -X GET http://localhost:8000/api/cart/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
```
**Expected:** Empty cart with delivery_fee from default address (25 AED)

#### 2. Add Items to Cart
```bash
# Get product ID first
curl -X GET http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"

# Add chicken (replace PRODUCT_ID)
curl -X POST http://localhost:8000/api/cart/add/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": PRODUCT_ID,
    "quantity": 2
  }'
```

#### 3. View Cart with Items
```bash
curl -X GET http://localhost:8000/api/cart/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
```
**Expected:** Cart with items, dynamic delivery fee (25 AED), grand total

---

### PHASE 5: CHECKOUT WITH NEW FEATURES
#### 1. Checkout with Delivery Options
```bash
curl -X POST http://localhost:8000/api/checkout/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "address_id": YOUR_ADDRESS_ID,
    "payment_method": "cash",
    "receive_method": "home_delivery",
    "delivery_type": "today",
    "notes": "Handle with care"
  }'
```
**Expected:** Order created with location-based delivery fee

#### 2. Check Order Details
```bash
curl -X GET http://localhost:8000/api/orders/YOUR_ORDER_ID/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
```
**Expected:** Order shows receive_method, delivery_type, delivery_fee from zone

---

### PHASE 6: ORDER MANAGEMENT
#### 1. View Customer Orders
```bash
curl -X GET http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
```

#### 2. Admin View All Orders
```bash
curl -X GET http://localhost:8000/api/admin/orders/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### 3. Admin Update Order Status
```bash
curl -X PATCH http://localhost:8000/api/admin/orders/ORDER_ID/update-status/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "processing",
    "note": "Order is being prepared"
  }'
```

#### 4. Customer Cancel Order (if still order_confirmed)
```bash
curl -X POST http://localhost:8000/api/orders/ORDER_ID/cancel/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
```

---

### PHASE 7: TEST DIFFERENT DELIVERY SCENARIOS
#### 1. Test Different Locations
```bash
# Create address in different zone
curl -X POST http://localhost:8000/api/accounts/addresses/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Office",
    "full_address": "Business Bay, Dubai, UAE",
    "city": "Dubai",
    "area": "Business Bay",
    "is_default": false
  }'
```
**Expected:** Auto-assigned to Downtown Dubai zone (15 AED)

#### 2. Checkout with Scheduled Delivery
```bash
curl -X POST http://localhost:8000/api/checkout/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "address_id": NEW_ADDRESS_ID,
    "payment_method": "card",
    "receive_method": "receive_in_market",
    "delivery_type": "scheduled",
    "scheduled_at": "2026-05-14T14:30:00Z",
    "notes": "Scheduled pickup"
  }'
```

---

## 🔍 WHAT TO VERIFY

### ✅ Location-Based Pricing
- Different addresses show different delivery fees
- Cart reflects correct fees based on default address
- Checkout uses address-specific fees

### ✅ New Order Fields
- receive_method: "home_delivery" or "receive_in_market"
- delivery_type: "today" or "scheduled"
- scheduled_at: only when delivery_type is "scheduled"

### ✅ Order Status Flow
- order_confirmed → processing → in_transit → delivered
- Customer can cancel only from "order_confirmed"
- Admin can update status with notes

### ✅ Auto-Zone Assignment
- Addresses automatically get delivery zones
- Manual override possible in admin

---

## 🚨 COMMON ISSUES & FIXES

### Issue: Delivery fee not updating
**Fix:** Check if address has delivery_zone assigned
```bash
curl -X GET http://localhost:8000/api/accounts/addresses/ \
  -H "Authorization: Bearer YOUR_CUSTOMER_TOKEN"
```

### Issue: Zone not auto-assigned
**Fix:** Ensure city/area match exactly with zone data

### Issue: Order cancel fails
**Fix:** Only orders with status "order_confirmed" can be cancelled

---

## 🎉 SUCCESS CHECKLIST

- [ ] Admin can manage delivery zones
- [ ] Addresses auto-assign delivery zones
- [ ] Cart shows location-based delivery fees
- [ ] Checkout supports delivery scheduling
- [ ] Orders have new delivery fields
- [ ] Order status updates work
- [ ] Customer order cancellation works
- [ ] Different locations have different fees

**Ready for payment integration! 💳**

---

## 📱 MOBILE APP TESTING

Use the same endpoints in your mobile app:
- Cart API for dynamic pricing
- Checkout with new fields
- Order tracking with status updates

All APIs are RESTful and return consistent JSON responses! 🎯