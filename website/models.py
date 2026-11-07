import logging
import os

import psycopg
from flask_login import UserMixin
from psycopg.rows import dict_row


logger = logging.getLogger(__name__)


def create_connection():
    return psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    )


class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = str(user_id)
        self.username = username
        self.email = email


def create_table():
    with create_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_name VARCHAR(100) NOT NULL,
                email VARCHAR(250) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                note_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id)
                    ON DELETE CASCADE,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_user_by_email(email):
    try:
        with create_connection() as connection:
            return connection.execute("""
                SELECT user_id, user_name, email, password
                FROM users
                WHERE email = %s
            """, (email,)).fetchone()
    except psycopg.Error:
        logger.exception("Find user error")
        return None


def get_user_by_id(user_id):
    try:
        with create_connection() as connection:
            row = connection.execute("""
                SELECT user_id, user_name, email
                FROM users
                WHERE user_id = %s
            """, (user_id,)).fetchone()
            if row:
                return User(row["user_id"], row["user_name"], row["email"])
            return None
    except psycopg.Error:
        logger.exception("Find user by ID error")
        return None


def create_note(user_id, title, content):
    try:
        with create_connection() as connection:
            connection.execute("""
                INSERT INTO notes (user_id, title, content)
                VALUES (%s, %s, %s)
            """, (user_id, title, content))
        return True
    except psycopg.Error:
        logger.exception("Error creating note")
        return False


def get_notes(user_id):
    try:
        with create_connection() as connection:
            return connection.execute("""
                SELECT note_id, title, content, created_at
                FROM notes
                WHERE user_id = %s
                ORDER BY created_at DESC, note_id DESC
            """, (user_id,)).fetchall()
    except psycopg.Error:
        logger.exception("Error retrieving notes")
        return None


def get_note(user_id, note_id):
    try:
        with create_connection() as connection:
            return connection.execute("""
                SELECT note_id, title, content, created_at
                FROM notes
                WHERE user_id = %s AND note_id = %s
            """, (user_id, note_id)).fetchone()
    except psycopg.Error:
        logger.exception("Error retrieving note")
        return None


def update_note(user_id, note_id, title, content):
    try:
        with create_connection() as connection:
            cursor = connection.execute("""
                UPDATE notes
                SET title = %s, content = %s
                WHERE user_id = %s AND note_id = %s
            """, (title, content, user_id, note_id))
            if cursor.rowcount > 0:
                return True

            row = connection.execute("""
                SELECT note_id
                FROM notes
                WHERE user_id = %s AND note_id = %s
            """, (user_id, note_id)).fetchone()
            return row is not None
    except psycopg.Error:
        logger.exception("Error updating note")
        return False


def delete_note(user_id, note_id):
    try:
        with create_connection() as connection:
            cursor = connection.execute("""
                DELETE FROM notes
                WHERE user_id = %s AND note_id = %s
            """, (user_id, note_id))
            return cursor.rowcount > 0
    except psycopg.Error:
        logger.exception("Error deleting note")
        return False
