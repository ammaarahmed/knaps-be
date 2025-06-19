import pytest
from decimal import Decimal
from datetime import date

@pytest.mark.asyncio
async def test_product_crud(client):
    product = {
        "distributor_name": "dist",
        "brand_name": "brand",
        "product_code": "P1",
        "product_name": "Prod1",
        "category_name": "Cat",
        "trade": 10.0,
        "rrp": 12.0
    }
    resp = await client.post("/products", json=product)
    assert resp.status_code == 201
    created = resp.json()
    pid = created["id"]

    resp = await client.get("/products")
    assert resp.status_code == 200
    assert any(p["id"] == pid for p in resp.json())

    resp = await client.get(f"/products/{pid}")
    assert resp.status_code == 200
    assert resp.json()["product_name"] == "Prod1"

    resp = await client.get("/products/search", params={"q": "Pro"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp = await client.put(f"/products/{pid}", json={"product_name": "New"})
    assert resp.status_code == 200
    assert resp.json()["product_name"] == "New"

    resp = await client.delete(f"/products/{pid}")
    assert resp.status_code == 204

    resp = await client.get(f"/products/{pid}")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_search_short_query(client):
    resp = await client.get("/products/search", params={"q": "x"})
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.asyncio
async def test_bulk_and_related(client):
    base = {
        "distributor_name": "d",
        "brand_name": "b",
        "category_name": "c",
        "trade": 5.0,
        "rrp": 6.0,
    }
    # bulk create two products, second has duplicate code
    data = [
        {**base, "product_code": "B1", "product_name": "Bulk1"},
        {**base, "product_code": "B1", "product_name": "BulkDup"},
    ]
    resp = await client.post("/products/bulk", json=data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] == 1
    assert body["errors"] == 1

    pid = body["created"][0]["id"]

    # sell-in and sell-through
    sell_in = {
        "product_id": pid,
        "quantity": 10,
        "unit_cost": 1.0,
        "total_cost": 10.0,
        "transaction_date": str(date.today()),
        "month_partition": date.today().strftime("%Y-%m"),
    }
    resp = await client.post("/api/sell-ins", json=sell_in)
    assert resp.status_code == 201

    sell_through = {
        "product_id": pid,
        "quantity": 4,
        "unit_price": 2.0,
        "total_revenue": 8.0,
        "transaction_date": str(date.today()),
        "month_partition": date.today().strftime("%Y-%m"),
    }
    resp = await client.post("/api/sell-throughs", json=sell_through)
    assert resp.status_code == 201

    resp = await client.get("/api/sell-ins", params={"product_id": pid})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/api/sell-throughs", params={"product_id": pid})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    month = date.today().strftime("%Y-%m")
    resp = await client.get("/analytics/products", params={"product_id": pid, "month": month})
    assert resp.status_code == 200
    data = resp.json()[0]
    assert data["sell_in_quantity"] == 10
    assert data["sell_through_quantity"] == 4

    resp = await client.get("/analytics/overall", params={"month": month})
    assert resp.status_code == 200
    overall = resp.json()
    assert overall["total_sell_in"] >= 10
    assert overall["total_sell_through"] >= 4
