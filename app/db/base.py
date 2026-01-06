from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Note: Models are imported in migrations/env.py for Alembic
# This prevents circular import issues during model discovery
