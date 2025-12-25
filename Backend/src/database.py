

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
    pass


class ConfigurationError(Exception):
    pass


class Database:
    
    def __init__(self):
        self.connection = None
        self._load_config()
    
    def _load_config(self):
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
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except psycopg2.Error as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.connection = None
    
    def execute_query(self, query, params=None):
        
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
    
    def get_chat_history(self, user_id, limit=10):
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
       
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        
        self.disconnect()
        return False
