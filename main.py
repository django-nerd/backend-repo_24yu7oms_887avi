import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Restaurant, Menuitem, Order

app = FastAPI(title="Food Ordering API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Food Ordering Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# Seed data model
class SeedRequest(BaseModel):
    reset: bool = False

@app.post("/seed")
def seed_database(body: SeedRequest):
    # Optionally reset collections
    if body.reset:
        db["restaurant"].drop()
        db["menuitem"].drop()

    # Only seed if empty
    if db["restaurant"].count_documents({}) > 0:
        return {"status": "ok", "message": "Already seeded"}

    restaurants = [
        {
            "name": "Panda Wok",
            "cuisine": "Chinese",
            "rating": 4.6,
            "delivery_fee": 1.99,
            "image": "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "name": "Bombay Bites",
            "cuisine": "Indian",
            "rating": 4.7,
            "delivery_fee": 2.49,
            "image": "https://images.unsplash.com/photo-1604328698692-f76ea9498e76?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "name": "Roma Pizza",
            "cuisine": "Italian",
            "rating": 4.5,
            "delivery_fee": 1.49,
            "image": "https://images.unsplash.com/photo-1541745537413-b804db0d7ce6?q=80&w=1200&auto=format&fit=crop"
        },
    ]

    # Insert restaurants and capture ids
    ids = []
    for r in restaurants:
        rid = db["restaurant"].insert_one({**r}).inserted_id
        ids.append(str(rid))

    # Seed menu items
    chinese_items = [
        {"restaurant_id": ids[0], "name": "Kung Pao Chicken", "price": 11.99, "description": "Spicy stir fry with peanuts", "image": "https://images.unsplash.com/photo-1604908554033-51e6fba73cd1?q=80&w=1200&auto=format&fit=crop"},
        {"restaurant_id": ids[0], "name": "Veg Fried Rice", "price": 8.99, "description": "Classic fried rice", "image": "https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?q=80&w=1200&auto=format&fit=crop"}
    ]
    indian_items = [
        {"restaurant_id": ids[1], "name": "Butter Chicken", "price": 12.99, "description": "Creamy tomato gravy", "image": "https://images.unsplash.com/photo-1604908435709-4c5c1d6a1762?q=80&w=1200&auto=format&fit=crop"},
        {"restaurant_id": ids[1], "name": "Paneer Tikka", "price": 10.49, "description": "Grilled cottage cheese", "image": "https://images.unsplash.com/photo-1628294895950-980f4e0078bf?q=80&w=1200&auto=format&fit=crop"}
    ]
    italian_items = [
        {"restaurant_id": ids[2], "name": "Margherita Pizza", "price": 9.99, "description": "Fresh basil and mozzarella", "image": "https://images.unsplash.com/photo-1548365328-9bdbb02f661d?q=80&w=1200&auto=format&fit=crop"},
        {"restaurant_id": ids[2], "name": "Pasta Alfredo", "price": 11.49, "description": "Creamy alfredo sauce", "image": "https://images.unsplash.com/photo-1525755662778-989d0524087e?q=80&w=1200&auto=format&fit=crop"}
    ]

    for item in chinese_items + indian_items + italian_items:
        db["menuitem"].insert_one(item)

    return {"status": "ok", "restaurants": ids}

@app.get("/restaurants", response_model=List[Restaurant])
def list_restaurants():
    docs = get_documents("restaurant")
    # Map _id to string
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs

@app.get("/restaurants/{restaurant_id}/menu", response_model=List[Menuitem])
def restaurant_menu(restaurant_id: str):
    docs = get_documents("menuitem", {"restaurant_id": restaurant_id})
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs

@app.post("/orders")
def create_order(order: Order):
    # Basic totals calculation on backend
    subtotal = sum(i.price * i.qty for i in order.items)
    delivery_fee = order.delivery_fee if order.delivery_fee else 0
    total = subtotal + delivery_fee

    data = order.model_dump()
    data.update({"subtotal": subtotal, "total": total})

    inserted_id = create_document("order", data)
    return {"status": "ok", "order_id": inserted_id, "total": total}

@app.get("/orders")
def list_orders(email: str):
    docs = get_documents("order", {"email": email})
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
    return docs

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
