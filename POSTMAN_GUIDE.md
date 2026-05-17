# 🚀 ARABIAN COMMERCE - POSTMAN TESTING GUIDE

I have generated the ultimate, premium Postman collection covering **100% of the active endpoints** in the Arabian Commerce project! 

The collection has been generated and saved directly to your workspace:
📁 **File Path**: `file:///home/r4fi/Documents/arabiancommerce/ArabianCommerce_API.postman_collection.json`

---

## 🌟 KEY PREMIUM FEATURES

1. **Perfect Hierarchical Structure**: Divided into `1. Admin Panel` (auth-required dashboard controls) and `2. Customer App` (OTP registration, addresses, shopping cart, checkout) for an intuitive test flow.
2. **Auto-Populating Variables**: Custom **Postman Test Scripts** are attached to key requests. They capture values from JSON responses and dynamically update variables so you **never have to copy-paste tokens or IDs manually**!
3. **Pre-configured Environment/Collection Variables**: Pre-loaded with variables like `base_url`, tokens, `product_id`, `address_id`, `cart_item_id`, and `order_id` with high-quality mock data ready to send.

---

## 🛠️ HOW TO IMPORT & TEST

### Step 1: Import to Postman
1. Open Postman.
2. Click the **Import** button in the top left.
3. Drag & drop or browse to selection:
   `/home/r4fi/Documents/arabiancommerce/ArabianCommerce_API.postman_collection.json`
4. Click **Import** to load the collection.

### Step 2: Running the Testing Flow

#### 1. Admin Workflow (Management & Catalog Setup)
* **Login**: Go to `1. Admin Panel` → `Auth` → `Admin Login` and click **Send**. 
  * *Magic*: The test script automatically saves the `access` token directly into your `admin_token` variable!
* **Create Zones**: Run `Create Delivery Zone`. It will create a zone and automatically save the `delivery_zone_id` variable.
* **Create Products / Categories**: Run `Create Category` followed by `Create Product`. The collection automatically grabs the created `category_id` and `product_id` for downstream requests!

#### 2. Customer Workflow (Ordering & Location Pricing)
* **Register/Login OTP**: 
  1. Trigger `2. Customer App` → `Authentication` → `Login - Send OTP` or `Register - Send OTP`.
  2. Read the dev-only `otp_code` returned in the response (or check server logs).
  3. Send `Verify OTP` using that code.
  * *Magic*: Your `customer_token` is automatically captured and assigned!
* **Location & Address**:
  * Send `Create Address` to villa coordinates in Dubai Marina (`latitude: 25.0780`, `longitude: 55.1400`).
  * *Magic*: The address is saved and gets assigned to the delivery zone automatically! The generated `address_id` is saved.
* **Cart Operations**:
  * Send `Add Item to Cart`. It uses the `product_id` captured from active products.
  * Send `Get Cart` to see the dynamic location-based delivery fee (e.g., 25.00 AED) and grand total dynamically applied based on your default address!
* **Checkout & Tracking**:
  * Trigger `Checkout Cart`. It automatically generates an order, saves the `order_id`, and clears the customer's cart.
  * Go back to `1. Admin Panel` → `Orders (Admin)` → `Update Order Status` to cycle the tracking from `order_confirmed` to `processing` / `in_transit` / `delivered`.

---

## 💎 DYNAMIC VARIABLE REGISTRY
The collection defines and maintains the following variables under Collection Variables:
* `{{base_url}}`: `http://127.0.0.1:8000` (Defaults to local Django server)
* `{{admin_token}}`: Dynamically updated on Admin Login.
* `{{customer_token}}`: Dynamically updated on Customer OTP Verification.
* `{{delivery_zone_id}}`, `{{product_id}}`, `{{category_id}}`, `{{subcategory_id}}`, `{{packaging_type_id}}`, `{{address_id}}`, `{{cart_item_id}}`, `{{order_id}}`, `{{banner_id}}`: All dynamically updated during test runs!
