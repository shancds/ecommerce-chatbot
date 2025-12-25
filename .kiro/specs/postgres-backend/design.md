# Design Document: PostgreSQL Backend Integration

## Overview

This design transforms the E-Shop Customer Support Chatbot from a JSON file-based system to a PostgreSQL-backed REST API. The architecture maintains the existing agent-based chatbot logic while replacing the data layer and adding HTTP endpoints for frontend integration.

The solution uses:
- **psycopg2**: PostgreSQL adapter for Python
- **Flask**: Lightweight web framework for REST API
- **python-dotenv**: Environment variable management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (External)                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────────┐
│                    Flask REST API                            │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  /api/chat   │  │ /api/health  │                        │
│  └──────────────┘  └──────────────┘                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Customer Support Agent                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Perception  │→ │  Reasoning   │→ │    Action    │      │
│  │ (NLP Process)│  │ (Inference)  │  │  (Execute)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Knowledge Base                             │
│              (PostgreSQL Data Layer)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Database Layer                            │
│              (psycopg2 Connection Pool)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ products │ │  orders  │ │ policies │ │  rules   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Database Layer (`src/database.py`)

Handles PostgreSQL connection and queries.

```python
class Database:
    def __init__(self):
        """Initialize database connection using environment variables"""
        
    def connect(self) -> None:
        """Establish database connection"""
        
    def disconnect(self) -> None:
        """Close database connection"""
        
    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute SELECT query and return results"""
        
    def execute_write(self, query: str, params: tuple = None) -> None:
        """Execute INSERT/UPDATE/DELETE query"""
```

### 2. Updated Knowledge Base (`src/knowledge_base.py`)

Modified to use Database layer instead of JSON files.

```python
class KnowledgeBase:
    def __init__(self, db: Database):
        """Initialize with database connection"""
        
    def get_product(self, product_id: str) -> dict:
        """Query product from database"""
        
    def get_order(self, order_id: str) -> dict:
        """Query order from database"""
        
    def get_rules(self) -> list:
        """Query all rules from database"""
        
    def get_return_policy(self) -> dict:
        """Query return policy from database"""
        
    def get_shipping_policy(self) -> dict:
        """Query shipping policy from database"""
        
    def search_products(self, category: str = None, max_price: float = None) -> list:
        """Search products with filters"""
```

### 3. REST API (`src/api.py`)

Flask application exposing chatbot endpoints.

```python
app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message and return response"""
    
@app.route('/api/health', methods=['GET'])
def health():
    """Return server and database health status"""
```

## Data Models

### Products Table

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(10) PRIMARY KEY | Product ID (e.g., P001) |
| name | VARCHAR(255) | Product name |
| price | DECIMAL(10,2) | Product price |
| category | VARCHAR(100) | Product category |
| features | JSON | Array of feature strings |
| returnable | BOOLEAN | Whether product is returnable |
| return_window | INTEGER | Return window in days |
| stock | INTEGER | Available stock |

### Orders Table

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(10) PRIMARY KEY | Order ID (e.g., ORD12345) |
| product_id | VARCHAR(10) | Foreign key to products |
| customer_id | VARCHAR(10) | Customer identifier |
| status | VARCHAR(50) | Order status |
| order_date | DATE | Order placement date |
| delivery_date | DATE | Expected/actual delivery date |
| tracking_number | VARCHAR(50) | Shipping tracking number |
| quantity | INTEGER | Quantity ordered |
| total | DECIMAL(10,2) | Order total |

### Policies Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Auto-increment ID |
| policy_type | VARCHAR(50) UNIQUE | Policy type (return, shipping, warranty, faq) |
| policy_data | JSON | Policy content as JSON |

### Rules Table

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(10) PRIMARY KEY | Rule ID (e.g., R001) |
| name | VARCHAR(255) | Rule name |
| condition | JSON | Rule conditions |
| action | VARCHAR(100) | Action to execute |
| priority | INTEGER | Rule priority |
| response_template | TEXT | Response template |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Database connection uses environment configuration
*For any* set of environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD), the Database_Layer SHALL use these values when establishing the connection.
**Validates: Requirements 1.1**

### Property 2: Product retrieval consistency
*For any* product ID that exists in the database, querying through Knowledge_Base SHALL return a product dict with all required fields (name, price, category, features, returnable, return_window, stock).
**Validates: Requirements 3.1**

### Property 3: Order retrieval consistency
*For any* order ID that exists in the database, querying through Knowledge_Base SHALL return an order dict with all required fields (product_id, customer_id, status, order_date, delivery_date, tracking_number, quantity, total).
**Validates: Requirements 3.2**

### Property 4: Product search filter correctness
*For any* search with category filter, all returned products SHALL have a category matching the filter. *For any* search with max_price filter, all returned products SHALL have a price less than or equal to max_price.
**Validates: Requirements 3.5**

### Property 5: Chat API response format
*For any* valid message sent to /api/chat, the response SHALL be valid JSON containing a "response" field with the chatbot's reply.
**Validates: Requirements 4.1**

## Error Handling

| Error Scenario | Handling |
|----------------|----------|
| Database connection failure | Log error, raise DatabaseConnectionError |
| Query execution failure | Log error, return None or empty list |
| Invalid API request | Return 400 with error message |
| Missing environment variables | Raise ConfigurationError on startup |

## Testing Strategy

### Unit Tests
- Test Database class connection and query methods
- Test KnowledgeBase methods with mocked database
- Test API endpoints with test client

### Property-Based Testing
Using **Hypothesis** library for Python property-based testing.

Each property test will:
1. Generate random valid inputs
2. Execute the operation
3. Verify the property holds

Property tests will be annotated with:
```python
# **Feature: postgres-backend, Property {number}: {property_text}**
```

Configuration: Minimum 100 iterations per property test.
