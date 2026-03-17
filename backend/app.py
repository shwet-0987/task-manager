from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
CORS(app)
MYSQL_USER = os.getenv('MYSQLUSER')
MYSQL_PASSWORD = os.getenv('MYSQLPASSWORD')
MYSQL_HOST = os.getenv('MYSQLHOST')
MYSQL_PORT = os.getenv('MYSQLPORT', '3306')
MYSQL_DB = os.getenv('MYSQLDATABASE')

# ---------------- DB CONFIG ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = \
f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?ssl=true"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    tasks = db.relationship("Task", backref="user", cascade="all, delete")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

# ---------------- FORCE TABLE CREATION (IMPORTANT) ----------------
@app.route("/init-db")
def init_db():
    try:
        db.create_all()
        return "Database initialized successfully ✅"
    except Exception as e:
        return str(e)

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return "Task Manager API is running 🚀"


@app.route("/debug")
def debug():
    try:
        users = User.query.all()
        return jsonify({"users_count": len(users)})
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------- AUTH ----------------

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON"}), 400

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON"}), 400

        hashed_pw = bcrypt.hashpw(
            data["password"].encode("utf-8"),
            bcrypt.gensalt()
        )

        user = User(
            username=data["username"],
            email=data["email"],
            password=hashed_pw.decode("utf-8")
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)

        user = User.query.filter_by(username=data["username"]).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if bcrypt.checkpw(
            data["password"].encode("utf-8"),
            user.password.encode("utf-8")
        ):
            return jsonify({
                "message": "Login successful",
                "user_id": user.id
            })

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ---------------- TASK CRUD ----------------

@app.route("/tasks/<int:user_id>", methods=["GET"])
def get_tasks(user_id):
    try:
        tasks = Task.query.filter_by(user_id=user_id).all()

        return jsonify([
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status
            }
            for t in tasks
        ])
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/tasks", methods=["POST"])
def add_task():
    try:
        data = request.get_json(force=True)

        task = Task(
            title=data["title"],
            description=data.get("description"),
            user_id=data["user_id"]
        )

        db.session.add(task)
        db.session.commit()

        return jsonify({"message": "Task added"}), 201

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    try:
        task = Task.query.get(task_id)

        if not task:
            return jsonify({"error": "Task not found"}), 404

        data = request.get_json(force=True)

        task.title = data.get("title", task.title)
        task.description = data.get("description", task.description)
        task.status = data.get("status", task.status)

        db.session.commit()

        return jsonify({"message": "Task updated"})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    try:
        task = Task.query.get(task_id)

        if not task:
            return jsonify({"error": "Task not found"}), 404

        db.session.delete(task)
        db.session.commit()

        return jsonify({"message": "Task deleted"})

    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run()