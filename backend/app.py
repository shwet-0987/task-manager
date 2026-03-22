from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
from flask_jwt_extended import(
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity   
)
from datetime import timedelta

app = Flask(__name__)
CORS(app)
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:fdbXASyqhZsQhfnwyjMUyunAiyWPpWij@yamanote.proxy.rlwy.net:13608/railway"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    tasks = db.relationship("Task", backref="user", cascade="all, delete")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum("pending", "completed"), default="pending")

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        onupdate=db.func.now()
    )

@app.route("/register", methods=["POST"])
def register():
    data = request.json

    # hash password
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


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(username=data["username"]).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if bcrypt.checkpw(
        data["password"].encode("utf-8"),
        user.password.encode("utf-8")
    ):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "access_token": access_token
        })

    return jsonify({"error": "Invalid credentials"}), 401


# ---------------- TASK CRUD ----------------

@app.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    current_user = int(get_jwt_identity())
    tasks = Task.query.filter_by(user_id=current_user).all()
    
    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status
        }
        for t in tasks
    ])


@app.route("/tasks", methods=["POST"])
@jwt_required()
def add_task():
    data = request.json
    if not data.get("title"):
        return jsonify({"error": "Title is required"}), 400 
    current_user_id = int(get_jwt_identity())
    task = Task(
        title=data["title"],
        description=data.get("description"),
        user_id=current_user_id
    )
   

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task added"}), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    current_user_id = int(get_jwt_identity())
    
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    if task.user_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)

    db.session.commit()

    return jsonify({"message": "Task updated"})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    current_user_id = int(get_jwt_identity())
    
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    if task.user_id != current_user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"})


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=False)