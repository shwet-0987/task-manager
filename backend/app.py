from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = \
"mysql+pymysql://root:AptpOMiErXofCllPOpWBUmYCpTIgkRqy@yamanote.proxy.rlwy.net:42589/railway?ssl=true"
# mysql://root:AptpOMiErXofCllPOpWBUmYCpTIgkRqy@yamanote.proxy.rlwy.net:42589/railway
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    tasks = db.relationship("Task", backref="user", cascade="all, delete")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
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


@app.route("/")
def home():
    return "task manager api is running"

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.json

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
        print(traceback.format_exc())  # 👈 shows full error in Render logs
        return jsonify({"error": str(e)}), 500

@app.route("/debug")
def debug():
    try:
        users = User.query.all()
        return jsonify({"users_count": len(users)})
    except Exception as e:
        return jsonify({"error": str(e)})
    

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
        return jsonify({
            "message": "Login successful",
            "user_id": user.id
        })

    return jsonify({"error": "Invalid credentials"}), 401


# ---------------- TASK CRUD ----------------

@app.route("/tasks/<int:user_id>", methods=["GET"])
def get_tasks(user_id):
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


@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.get_json()

    task = Task(
        title=data["title"],
        description=data.get("description"),
        user_id=data["user_id"]
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task added"}), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.json
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)

    db.session.commit()

    return jsonify({"message": "Task updated"})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"})


# ---------------- RUN ----------------

if __name__ == "__main__":
   # creates tables automatically in MySQL
    with app.app_context():
        db.create_all() 
    app.run()