import os
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request
import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from dotenv import load_dotenv


load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    # 🔹 Read Railway DATABASE_URL
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        url = urlparse(database_url)

        app.config["DB_CONFIG"] = {
            "host": url.hostname,
            "port": url.port or 3306,
            "user": url.username,
            "password": url.password,
            "database": url.path.lstrip("/"),
        }
    else:
        # fallback for local development
        app.config["DB_CONFIG"] = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", ""),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", ""),
        }

    app.db_pool = None

    def get_db_pool():
        nonlocal app
        if app.db_pool is None:
            try:
                app.db_pool = pooling.MySQLConnectionPool(
                    pool_name="contacts_pool",
                    pool_size=5,
                    pool_reset_session=True,
                    **app.config["DB_CONFIG"],
                )
            except MySQLError as e:
                app.logger.error(f"Error creating DB pool: {e}")
                raise
        return app.db_pool

    def init_db():
        """
        Ensure the contacts table exists.
        Safe to call multiple times (uses IF NOT EXISTS).
        """
        pool = get_db_pool()
        conn = pool.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        mobile_number VARCHAR(15) NOT NULL,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.commit()
        finally:
            conn.close()

    @app.before_request
    def ensure_db():
        """
        Lazily initialize the database on first request.
        """
        try:
            init_db()
        except MySQLError:
            # Error will be surfaced when attempting to use the DB.
            pass

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/services")
    def services():
        return render_template("services.html")

    @app.route("/contact")
    def contact():
        return render_template("contact.html")

    @app.route("/api/contact", methods=["POST"])
    def api_contact():
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        mobile_number = (data.get("mobile_number") or "").strip()

        errors = {}
        if not name:
            errors["name"] = "Name is required."
        if not mobile_number:
            errors["mobile_number"] = "Mobile number is required."
        elif not mobile_number.isdigit() or len(mobile_number) != 10:
            errors["mobile_number"] = "Mobile number must be exactly 10 digits."

        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        try:
            pool = get_db_pool()
            conn = pool.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO contacts (name, mobile_number, submitted_at) VALUES (%s, %s, %s)",
                    (name, mobile_number, datetime.utcnow()),
                )
                conn.commit()
        except MySQLError as e:
            app.logger.error(f"Database error while inserting contact: {e}")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "There was a problem saving your inquiry. Please try again later.",
                    }
                ),
                500,
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass

        return jsonify({"success": True, "message": "Thank you! We will contact you soon."})

    return app


app = create_app()


if __name__ == "__main__":
    # For local development only; Railway will use gunicorn via Procfile.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)

