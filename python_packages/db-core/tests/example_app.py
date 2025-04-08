# fastapi_app.py
from datetime import datetime, timezone
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session, relationship

# Import the db-core package
from db_core import (
    Base,
    MultitenancySettings,
    TenantMiddleware,
    get_tenant_db,
    init_db,
)
from db_core.middleware import get_current_tenant_id

# Create the FastAPI app
app = FastAPI(
    title="Schema-Based Multitenant FastAPI Example",
    description="An example API demonstrating schema-based multitenancy",
    version="0.1.0",
)

# Define multitenancy settings
settings = MultitenancySettings(
    tenant_id_header="X-Tenant-ID",
    db_url="postgresql://postgres:postgres@localhost:5433/multitenancy",
    auto_create_tenant_schema=True,
    schema_prefix="tenant_",
)

# Initialize the database
db_info = init_db(
    settings=settings,
    create_schemas=True,
    tenant_ids=["tenant1", "tenant2"],  # Pre-create schemas for these tenants
)

# Add tenant middleware to the app with excluded paths for documentation
app.add_middleware(
    TenantMiddleware,
    settings=settings,
    excluded_paths={
        "/docs": {"default_tenant": "tenant1"},
        "/redoc": {"default_tenant": "tenant1"},
        "/openapi.json": {"default_tenant": "tenant1"},
        "/docs/oauth2-redirect": {"default_tenant": "tenant1"},
        "/docs/swagger-ui-bundle.js": {"default_tenant": "tenant1"},
        "/docs/swagger-ui-standalone-preset.js": {"default_tenant": "tenant1"},
        "/docs/swagger-ui.css": {"default_tenant": "tenant1"},
    },
)


# Define regular SQLAlchemy models - no mixin needed for schema-based multitenancy
class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}  # Allow table redefinition during hot-reload

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)  # Price in cents
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Define relationships
    categories = relationship("Category", secondary="product_categories", back_populates="products")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"extend_existing": True}  # Allow table redefinition during hot-reload

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Define relationships
    products = relationship("Product", secondary="product_categories", back_populates="categories")


class ProductCategory(Base):
    __tablename__ = "product_categories"
    __table_args__ = {"extend_existing": True}  # Allow table redefinition during hot-reload

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)


# Define Pydantic models for API
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: int  # Price in cents


class ProductCreate(ProductBase):
    category_ids: List[int] = []


class ProductResponse(ProductBase):
    id: int
    categories: List[CategoryResponse] = []

    class Config:
        orm_mode = True


# Function to add the tenant header to the OpenAPI documentation
# Store the original openapi function
original_openapi = app.openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = original_openapi()

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "parameters" not in openapi_schema["components"]:
        openapi_schema["components"]["parameters"] = {}

    # Define the tenant header parameter
    openapi_schema["components"]["parameters"]["tenant_header"] = {
        "name": settings.tenant_id_header,
        "in": "header",
        "required": True,
        "schema": {
            "title": "Tenant ID",
            "type": "string",
            "default": "tenant1",
            "example": "tenant1",
        },
        "description": "The tenant identifier used for schema-based multitenancy",
    }

    # Add the tenant header parameter to all paths except docs and openapi
    for path_name, path_item in openapi_schema["paths"].items():
        # Skip documentation paths
        if path_name.startswith("/docs") or path_name.startswith("/redoc") or path_name == "/openapi.json":
            continue

        for operation in path_item.values():
            if "parameters" not in operation:
                operation["parameters"] = []
            operation["parameters"].append({"$ref": "#/components/parameters/tenant_header"})

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Override the openapi function
app.openapi = custom_openapi


# Define API endpoints
@app.get("/")
def read_root():
    tenant_id = get_current_tenant_id()
    return {"message": f"Welcome to the schema-based multitenant API! Current tenant: {tenant_id}"}


@app.get("/categories/", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_tenant_db)):
    return db.query(Category).all()


@app.post("/categories/", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_tenant_db)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/products/", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_tenant_db)):
    return db.query(Product).all()


@app.post("/products/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_tenant_db)):
    # Extract category IDs and remove from the dictionary
    category_ids = product.category_ids
    product_data = product.dict(exclude={"category_ids"})

    # Create the product
    db_product = Product(**product_data)
    db.add(db_product)
    db.flush()

    # Add categories
    if category_ids:
        categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
        db_product.categories = categories

    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/tenant/")
def get_tenant():
    tenant_id = get_current_tenant_id()
    return {"tenant_id": tenant_id}


if __name__ == "__main__":
    uvicorn.run("example_app:app", host="0.0.0.0", port=8000, reload=True)
