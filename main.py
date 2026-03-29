from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI(title="FreshMart Grocery Delivery API")

# ─────────────────────────────────────────────
# DATA STORE
# ─────────────────────────────────────────────

items = [
    {"id": 1, "name": "Tomato",       "price": 30,  "unit": "kg",     "category": "Vegetable", "in_stock": True},
    {"id": 2, "name": "Banana",       "price": 50,  "unit": "dozen",  "category": "Fruit",     "in_stock": True},
    {"id": 3, "name": "Milk",         "price": 60,  "unit": "litre",  "category": "Dairy",     "in_stock": True},
    {"id": 4, "name": "Rice",         "price": 80,  "unit": "kg",     "category": "Grain",     "in_stock": True},
    {"id": 5, "name": "Spinach",      "price": 20,  "unit": "kg",     "category": "Vegetable", "in_stock": False},
    {"id": 6, "name": "Apple",        "price": 150, "unit": "kg",     "category": "Fruit",     "in_stock": True},
    {"id": 7, "name": "Paneer",       "price": 90,  "unit": "kg",     "category": "Dairy",     "in_stock": True},
    {"id": 8, "name": "Wheat Flour",  "price": 45,  "unit": "kg",     "category": "Grain",     "in_stock": True},
]
item_counter = 9

orders = []
order_counter = 1

cart = []


# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)
    delivery_address: str = Field(..., min_length=10)
    delivery_slot: str = Field(default="Morning")
    bulk_order: bool = Field(default=False)   # Q9


class NewItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    unit: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    in_stock: bool = Field(default=True)


class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)
    delivery_slot: str = Field(default="Morning")


# ─────────────────────────────────────────────
# HELPER FUNCTIONS  (Q7)
# ─────────────────────────────────────────────

def find_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    return None


def calculate_order_total(price: int, quantity: int, delivery_slot: str,
                          bulk_order: bool = False):
    subtotal = price * quantity
    original_subtotal = subtotal

    discount_applied = False
    discount_amount = 0

    # Q9 — bulk discount
    if bulk_order and quantity >= 10:
        discount_amount = round(subtotal * 0.08)
        subtotal -= discount_amount
        discount_applied = True

    # delivery charge
    slot = delivery_slot.lower()
    if slot == "morning":
        delivery_charge = 40
    elif slot == "evening":
        delivery_charge = 60
    elif slot == "self-pickup":
        delivery_charge = 0
    else:
        delivery_charge = 40   # default

    total = subtotal + delivery_charge

    return {
        "original_subtotal": original_subtotal,
        "discount_applied": discount_applied,
        "discount_amount": discount_amount,
        "subtotal_after_discount": subtotal,
        "delivery_charge": delivery_charge,
        "total_cost": total,
    }


def filter_items_logic(items_list, category=None, max_price=None,
                       unit=None, in_stock=None):
    result = items_list[:]
    if category is not None:
        result = [i for i in result if i["category"].lower() == category.lower()]
    if max_price is not None:
        result = [i for i in result if i["price"] <= max_price]
    if unit is not None:
        result = [i for i in result if i["unit"].lower() == unit.lower()]
    if in_stock is not None:
        result = [i for i in result if i["in_stock"] == in_stock]
    return result


# ─────────────────────────────────────────────
# Q1 — HOME ROUTE
# ─────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Welcome to FreshMart Grocery"}


# ─────────────────────────────────────────────
# FIXED ITEM ROUTES  (must come before /{item_id})
# ─────────────────────────────────────────────

# Q5 — summary
@app.get("/items/summary")
def items_summary():
    total = len(items)
    in_stock_count = sum(1 for i in items if i["in_stock"])
    out_of_stock_count = total - in_stock_count

    category_breakdown = {}
    for item in items:
        cat = item["category"]
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    return {
        "total_items": total,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "category_breakdown": category_breakdown,
    }


# Q10 — filter
@app.get("/items/filter")
def filter_items(
    category: Optional[str] = Query(default=None),
    max_price: Optional[int] = Query(default=None),
    unit: Optional[str] = Query(default=None),
    in_stock: Optional[bool] = Query(default=None),
):
    result = filter_items_logic(items, category, max_price, unit, in_stock)
    return {"total": len(result), "items": result}


# Q16 — search items
@app.get("/items/search")
def search_items(keyword: str = Query(...)):
    kw = keyword.lower()
    result = [
        i for i in items
        if kw in i["name"].lower() or kw in i["category"].lower()
    ]
    if not result:
        return {"total_found": 0, "items": [], "message": f"No items found for '{keyword}'"}
    return {"total_found": len(result), "items": result}


# Q17 — sort items
@app.get("/items/sort")
def sort_items(
    sort_by: str = Query(default="price"),
    order: str = Query(default="asc"),
):
    valid_sort = ["price", "name", "category"]
    valid_order = ["asc", "desc"]

    if sort_by not in valid_sort:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort}")
    if order not in valid_order:
        raise HTTPException(status_code=400, detail=f"order must be one of {valid_order}")

    reverse = order == "desc"
    sorted_items = sorted(items, key=lambda i: i[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order": order,
        "total": len(sorted_items),
        "items": sorted_items,
    }


# Q18 — paginate items
@app.get("/items/page")
def paginate_items(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=4, ge=1),
):
    total = len(items)
    total_pages = math.ceil(total / limit)
    start = (page - 1) * limit
    end = start + limit
    page_items = items[start:end]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "items": page_items,
    }


# Q20 — browse (combined)
@app.get("/items/browse")
def browse_items(
    keyword: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    in_stock: Optional[bool] = Query(default=None),
    sort_by: str = Query(default="price"),
    order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=4, ge=1),
):
    valid_sort = ["price", "name", "category"]
    valid_order = ["asc", "desc"]
    if sort_by not in valid_sort:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort}")
    if order not in valid_order:
        raise HTTPException(status_code=400, detail=f"order must be one of {valid_order}")

    result = items[:]

    # 1. keyword search
    if keyword is not None:
        kw = keyword.lower()
        result = [i for i in result if kw in i["name"].lower() or kw in i["category"].lower()]

    # 2. category filter
    if category is not None:
        result = [i for i in result if i["category"].lower() == category.lower()]

    # 3. in_stock filter
    if in_stock is not None:
        result = [i for i in result if i["in_stock"] == in_stock]

    # 4. sort
    reverse = order == "desc"
    result = sorted(result, key=lambda i: i[sort_by], reverse=reverse)

    # 5. paginate
    total = len(result)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    result = result[start: start + limit]

    return {
        "keyword": keyword,
        "category": category,
        "in_stock": in_stock,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_results": total,
        "total_pages": total_pages,
        "items": result,
    }


# Q2 — GET all items
@app.get("/items")
def get_items():
    in_stock_count = sum(1 for i in items if i["in_stock"])
    return {"total": len(items), "in_stock_count": in_stock_count, "items": items}


# Q11 — POST /items
@app.post("/items", status_code=201)
def create_item(new_item: NewItem):
    global item_counter
    for item in items:
        if item["name"].lower() == new_item.name.lower():
            raise HTTPException(status_code=400, detail=f"Item '{new_item.name}' already exists")
    item_dict = {
        "id": item_counter,
        **new_item.model_dump(),
    }
    items.append(item_dict)
    item_counter += 1
    return {"message": "Item added successfully", "item": item_dict}


# Q3 — GET /items/{item_id}
@app.get("/items/{item_id}")
def get_item(item_id: int):
    item = find_item(item_id)
    if not item:
        return {"error": f"Item with id {item_id} not found"}
    return item


# Q12 — PUT /items/{item_id}
@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    price: Optional[int] = Query(default=None),
    in_stock: Optional[bool] = Query(default=None),
):
    item = find_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")
    if price is not None:
        item["price"] = price
    if in_stock is not None:
        item["in_stock"] = in_stock
    return {"message": "Item updated", "item": item}


# Q13 — DELETE /items/{item_id}
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    item = find_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")

    # check for active orders
    active = [o for o in orders if o["item_id"] == item_id and o["status"] == "confirmed"]
    if active:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete '{item['name']}' — it has {len(active)} active order(s)"
        )

    items.remove(item)
    return {"message": f"Item '{item['name']}' deleted successfully"}


# ─────────────────────────────────────────────
# ORDERS  (fixed routes first)
# ─────────────────────────────────────────────

# Q19 — search orders (FIXED — must be above /{} if we had one)
@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    result = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]
    if not result:
        return {"total_found": 0, "orders": [], "message": f"No orders found for '{customer_name}'"}
    return {"total_found": len(result), "orders": result}


@app.get("/orders/sort")
def sort_orders(order: str = Query(default="asc")):
    valid_order = ["asc", "desc"]
    if order not in valid_order:
        raise HTTPException(status_code=400, detail=f"order must be one of {valid_order}")
    reverse = order == "desc"
    sorted_orders = sorted(orders, key=lambda o: o["total_cost"], reverse=reverse)
    return {"order": order, "total": len(sorted_orders), "orders": sorted_orders}


@app.get("/orders/page")
def paginate_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=4, ge=1),
):
    total = len(orders)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    page_orders = orders[start: start + limit]
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "orders": page_orders,
    }


# Q4 — GET all orders
@app.get("/orders")
def get_orders():
    return {"total": len(orders), "orders": orders}


# Q8 — POST /orders
@app.post("/orders", status_code=201)
def create_order(order_req: OrderRequest):
    global order_counter

    item = find_item(order_req.item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with id {order_req.item_id} not found")
    if not item["in_stock"]:
        raise HTTPException(status_code=400, detail=f"'{item['name']}' is currently out of stock")

    cost_info = calculate_order_total(
        price=item["price"],
        quantity=order_req.quantity,
        delivery_slot=order_req.delivery_slot,
        bulk_order=order_req.bulk_order,
    )

    order = {
        "order_id": order_counter,
        "customer_name": order_req.customer_name,
        "item_id": item["id"],
        "item_name": item["name"],
        "quantity": order_req.quantity,
        "unit": item["unit"],
        "delivery_slot": order_req.delivery_slot,
        "delivery_address": order_req.delivery_address,
        "bulk_order": order_req.bulk_order,
        **cost_info,
        "status": "confirmed",
    }

    orders.append(order)
    order_counter += 1
    return {"message": "Order placed successfully", "order": order}


# ─────────────────────────────────────────────
# CART  (Q14 & Q15)
# ─────────────────────────────────────────────

@app.post("/cart/add")
def add_to_cart(
    item_id: int = Query(...),
    quantity: int = Query(default=1, ge=1),
):
    item = find_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")
    if not item["in_stock"]:
        raise HTTPException(status_code=400, detail=f"'{item['name']}' is out of stock")

    # merge if already in cart
    for entry in cart:
        if entry["item_id"] == item_id:
            entry["quantity"] += quantity
            entry["subtotal"] = entry["quantity"] * item["price"]
            return {"message": "Cart updated", "cart_entry": entry}

    entry = {
        "item_id": item_id,
        "item_name": item["name"],
        "unit": item["unit"],
        "price_per_unit": item["price"],
        "quantity": quantity,
        "subtotal": quantity * item["price"],
    }
    cart.append(entry)
    return {"message": "Item added to cart", "cart_entry": entry}


@app.get("/cart")
def get_cart():
    grand_total = sum(e["subtotal"] for e in cart)
    return {"total_items": len(cart), "grand_total": grand_total, "cart": cart}


@app.delete("/cart/{item_id}")
def remove_from_cart(item_id: int):
    for entry in cart:
        if entry["item_id"] == item_id:
            cart.remove(entry)
            return {"message": f"Item '{entry['item_name']}' removed from cart"}
    raise HTTPException(status_code=404, detail=f"Item with id {item_id} not in cart")


@app.post("/cart/checkout", status_code=201)
def checkout(checkout_req: CheckoutRequest):
    global order_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — add items before checkout")

    placed_orders = []

    for entry in cart:
        item = find_item(entry["item_id"])
        if not item:
            continue

        cost_info = calculate_order_total(
            price=item["price"],
            quantity=entry["quantity"],
            delivery_slot=checkout_req.delivery_slot,
        )

        order = {
            "order_id": order_counter,
            "customer_name": checkout_req.customer_name,
            "item_id": item["id"],
            "item_name": item["name"],
            "quantity": entry["quantity"],
            "unit": item["unit"],
            "delivery_slot": checkout_req.delivery_slot,
            "delivery_address": checkout_req.delivery_address,
            "bulk_order": False,
            **cost_info,
            "status": "confirmed",
        }

        orders.append(order)
        order_counter += 1
        placed_orders.append(order)

    grand_total = sum(o["total_cost"] for o in placed_orders)
    cart.clear()

    return {
        "message": "Checkout successful",
        "total_orders_placed": len(placed_orders),
        "grand_total": grand_total,
        "orders": placed_orders,
    }
