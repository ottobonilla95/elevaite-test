"""
Integration tests for the db-core package.
"""

import pytest
from fastapi import Depends
from sqlalchemy import Column, Integer, String, select, text
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from db_core import Base, get_tenant_db
from db_core.middleware import get_current_tenant_id
from db_core.utils import get_schema_name


# Define a model for integration tests
class TestItem(Base):
    __tablename__ = "test_items"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)


@pytest.mark.db
class TestSchemaBasedMultitenancy:
    """Integration tests for schema-based multitenancy."""

    @pytest.fixture
    def test_app(self, multitenancy_settings, setup_db, init_db_config, fastapi_app):
        """Create a test FastAPI app with multitenancy."""
        # Use the existing FastAPI app from conftest
        app = fastapi_app

        # Add routes
        @app.post("/items/")
        def create_item(
            name: str, description: str = None, db: Session = Depends(get_tenant_db)
        ):
            # Create a new item for the current tenant
            tenant_id = get_current_tenant_id()
            item = TestItem(name=name, description=description, tenant_id=tenant_id)
            db.add(item)
            db.commit()
            db.refresh(item)
            return {"id": item.id, "name": item.name, "description": item.description}

        @app.get("/items/")
        def list_items(db: Session = Depends(get_tenant_db)):
            # List items for the current tenant
            tenant_id = get_current_tenant_id()
            items = (
                db.execute(select(TestItem).where(TestItem.tenant_id == tenant_id))
                .scalars()
                .all()
            )
            return [
                {"id": item.id, "name": item.name, "description": item.description}
                for item in items
            ]

        @app.get("/items/{item_id}")
        def get_item(item_id: int, db: Session = Depends(get_tenant_db)):
            # Get an item by ID for the current tenant
            tenant_id = get_current_tenant_id()
            item = db.execute(
                select(TestItem).where(
                    (TestItem.id == item_id) & (TestItem.tenant_id == tenant_id)
                )
            ).scalar_one_or_none()

            if item is None:
                return {"error": "Item not found"}
            return {"id": item.id, "name": item.name, "description": item.description}

        return app

    def test_schema_isolation(self, test_app, db_engine, multitenancy_settings):
        """Test that data is isolated between tenant schemas."""
        # Create test client
        client = TestClient(test_app)

        # Create tables in tenant schemas
        for tenant_id in ["tenant1", "tenant2"]:
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            with db_engine.connect() as conn:
                conn.execute(text(f'SET search_path TO "{schema_name}"'))
                TestItem.__table__.create(db_engine, checkfirst=True)

        # Add items for tenant1
        response1 = client.post(
            "/items/?name=Item1&description=Description1",
            headers={"X-Tenant-ID": "tenant1"},
        )
        assert response1.status_code == 200
        item1_id = response1.json()["id"]

        response2 = client.post(
            "/items/?name=Item2&description=Description2",
            headers={"X-Tenant-ID": "tenant1"},
        )
        assert response2.status_code == 200

        # Add items for tenant2
        response3 = client.post(
            "/items/?name=Item3&description=Description3",
            headers={"X-Tenant-ID": "tenant2"},
        )
        assert response3.status_code == 200
        item3_id = response3.json()["id"]

        # List items for tenant1
        response4 = client.get("/items/", headers={"X-Tenant-ID": "tenant1"})
        assert response4.status_code == 200
        items_tenant1 = response4.json()
        assert len(items_tenant1) == 2
        assert any(item["name"] == "Item1" for item in items_tenant1)
        assert any(item["name"] == "Item2" for item in items_tenant1)
        assert not any(item["name"] == "Item3" for item in items_tenant1)

        # List items for tenant2
        response5 = client.get("/items/", headers={"X-Tenant-ID": "tenant2"})
        assert response5.status_code == 200
        items_tenant2 = response5.json()
        assert len(items_tenant2) == 1
        assert any(item["name"] == "Item3" for item in items_tenant2)
        assert not any(item["name"] == "Item1" for item in items_tenant2)

        # Get item by ID for tenant1
        response6 = client.get(f"/items/{item1_id}", headers={"X-Tenant-ID": "tenant1"})
        assert response6.status_code == 200
        assert response6.json()["name"] == "Item1"

        # Get item by ID for tenant2
        response7 = client.get(f"/items/{item3_id}", headers={"X-Tenant-ID": "tenant2"})
        assert response7.status_code == 200
        assert response7.json()["name"] == "Item3"

        # Try to get tenant2's item from tenant1 (should fail or return not found)
        response8 = client.get(f"/items/{item3_id}", headers={"X-Tenant-ID": "tenant1"})
        assert response8.status_code == 200
        assert "error" in response8.json()


@pytest.mark.db
class TestPerformance(TestSchemaBasedMultitenancy):
    """Performance tests for the db-core package."""

    @pytest.mark.parametrize("num_items", [10, 100])
    def test_query_performance(
        self, test_app, db_engine, multitenancy_settings, num_items
    ):
        """Test query performance with different numbers of items."""
        import time

        # Create test client
        client = TestClient(test_app)

        # Create tables in tenant schema
        tenant_id = "tenant1"
        schema_name = get_schema_name(tenant_id, multitenancy_settings)
        with db_engine.connect() as conn:
            conn.execute(text(f'SET search_path TO "{schema_name}"'))
            TestItem.__table__.create(db_engine, checkfirst=True)

        # Add items for tenant
        for i in range(num_items):
            response = client.post(
                f"/items/?name=Item{i}&description=Description{i}",
                headers={"X-Tenant-ID": tenant_id},
            )
            assert response.status_code == 200

        # Measure query time
        start_time = time.time()
        response = client.get("/items/", headers={"X-Tenant-ID": tenant_id})
        end_time = time.time()

        # Verify response
        assert response.status_code == 200
        items = response.json()
        assert len(items) == num_items

        # Log query time (for benchmarking)
        query_time = end_time - start_time
        print(f"Query time for {num_items} items: {query_time:.4f} seconds")

        # No hard assertion on performance, but we could add one if needed
        # assert query_time < 0.5  # Example threshold
