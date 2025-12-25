"""
Database Layer Module
Handles PostgreSQL connection and queries for the E-Shop Chatbot.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class ConfigurationError(Exception):
    """Raised when required environment variables are missing."""
    pass


class Database:
    """
    Database layer for PostgreSQL connection and queries.
    Uses environment variables for configuration.
    """
    
    def __init__(self):
        """Initialize database connection using environment variables."""
        self.connection = None
        self._load_config()
    
    def _load_config(self):
        """Load database configuration from environment variables."""
        self.host = os.getenv('DB_HOST')
        self.port = os.getenv('DB_PORT')
        self.dbname = os.getenv('DB_NAME')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        
        # Validate required configuration
        missing = []
        if not self.host:
            missing.append('DB_HOST')
        if not self.port:
            missing.append('DB_PORT')
        if not self.dbname:
            missing.append('DB_NAME')
        if not self.user:
            missing.append('DB_USER')
        if not self.password:
            missing.append('DB_PASSWORD')
        
        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    def connect(self):
        """
        Establish database connection.
        
        Raises:
            DatabaseConnectionError: If connection fails.
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connected to database {self.dbname} at {self.host}:{self.port}")
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
    
    def disconnect(self):
        """Close database connection gracefully."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except psycopg2.Error as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.connection = None
    
    def execute_query(self, query, params=None):
        """
        Execute SELECT query and return results.
        
        Args:
            query: SQL query string.
            params: Optional tuple of query parameters.
            
        Returns:
            List of dictionaries representing rows.
        """
        if not self.connection:
            logger.error("No database connection")
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def execute_write(self, query, params=None):
        """
        Execute INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string.
            params: Optional tuple of query parameters.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.connection:
            logger.error("No database connection")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return True
        except psycopg2.Error as e:
            logger.error(f"Write operation failed: {e}")
            self.connection.rollback()
            return False
    
    def is_connected(self):
        """Check if database connection is active."""
        if not self.connection:
            return False
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except psycopg2.Error:
            return False
    
    # User management methods
    
    def create_user(self, email, password_hash, name, role='customer'):
        """
        Create a new user in the database.
        
        Args:
            email: User's email address.
            password_hash: bcrypt hashed password.
            name: User's display name.
            role: User role (default: 'customer').
            
        Returns:
            User dict if successful, None otherwise.
        """
        if not self.connection:
            logger.error("No database connection")
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash, name, role, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id, email, name, role, created_at
                    """,
                    (email, password_hash, name, role)
                )
                self.connection.commit()
                result = cursor.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            logger.error(f"Failed to create user: {e}")
            self.connection.rollback()
            return None
    
    def get_user_by_email(self, email):
        """
        Get user by email address.
        
        Args:
            email: User's email address.
            
        Returns:
            User dict if found, None otherwise.
        """
        if not self.connection:
            logger.error("No database connection")
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password_hash, name, role, created_at, last_login
                    FROM users WHERE email = %s
                    """,
                    (email,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """
        Get user by ID.
        
        Args:
            user_id: User's ID.
            
        Returns:
            User dict if found, None otherwise.
        """
        if not self.connection:
            logger.error("No database connection")
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, email, name, role, created_at, last_login
                    FROM users WHERE id = %s
                    """,
                    (user_id,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            logger.error(f"Failed to get user by id: {e}")
            return None
    
    def update_last_login(self, user_id):
        """
        Update user's last_login timestamp.
        
        Args:
            user_id: User's ID.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.connection:
            logger.error("No database connection")
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users SET last_login = NOW() WHERE id = %s
                    """,
                    (user_id,)
                )
                self.connection.commit()
                return cursor.rowcount > 0
        except psycopg2.Error as e:
            logger.error(f"Failed to update last login: {e}")
            self.connection.rollback()
            return False
    
    # Chat history methods
    
    def save_chat_message(self, user_id, message, is_bot):
        """
        Save a chat message to the database.
        
        Args:
            user_id: User's ID.
            message: Message content.
            is_bot: True if message is from bot, False if from user.
            
        Returns:
            Message dict if successful, None otherwise.
        """
        if not self.connection:
            logger.error("No database connection")
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_messages (user_id, message, is_bot, created_at)
                    VALUES (%s, %s, %s, NOW())
                    RETURNING id, user_id, message, is_bot, created_at
                    """,
                    (user_id, message, is_bot)
                )
                self.connection.commit()
                result = cursor.fetchone()
                return dict(result) if result else None
        except psycopg2.Error as e:
            logger.error(f"Failed to save chat message: {e}")
            self.connection.rollback()
            return None
    
    def get_chat_history(self, user_id, limit=50):
        """
        Get chat history for a user.
        
        Args:
            user_id: User's ID.
            limit: Maximum number of messages to return (default: 50).
            
        Returns:
            List of message dicts ordered by creation time.
        """
        if not self.connection:
            logger.error("No database connection")
            return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, user_id, message, is_bot, created_at
                    FROM chat_messages
                    WHERE user_id = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (user_id, limit)
                )
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    def __enter__(self):
        """Context manager entry - connect to database."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect from database."""
        self.disconnect()
        return False
