import { useState, useEffect } from "react";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [userId, setUserId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState("");
const[description, setDescription] = useState("none");

  // LOGIN
  const login = async () => {
    const res = await fetch("https://task-manager-p3ln.onrender.com/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (data.user_id) {
      setUserId(data.user_id);
    } else {
      alert("Invalid login");
    }
  };

  // FETCH TASKS
  useEffect(() => {
    if (userId) {
      fetch(`https://task-manager-p3ln.onrender.com/tasks/${userId}`)
        .then((res) => res.json())
        .then((data) => setTasks(data));
    }
  }, [userId]);

  const toggleStatus = async (task) => {
  const newStatus =
    task.status === "pending" ? "completed" : "pending";

  await fetch(`https://task-manager-p3ln.onrender.com/tasks/${task.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: newStatus }),
  });

  // Refresh tasks
  fetch(`https://task-manager-p3ln.onrender.com/tasks/${userId}`)
    .then((res) => res.json())
    .then((data) => setTasks(data));
};
  // ADD TASK
  const addTask = async () => {
    await fetch("https://task-manager-p3ln.onrender.com/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTask, description: description,user_id: userId }),
    });

    setNewTask("");
    setDescription("");
    fetch(`https://task-manager-p3ln.onrender.com/tasks/${userId}`)
      .then((res) => res.json())
      .then((data) => setTasks(data));
  };

  // LOGIN UI
  if (!userId) {
    return (
      <div>
        <h2>Login</h2>
        <input
          placeholder="Username"
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          placeholder="Password"
          type="password"
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={login}>Login</button>
      </div>
    );
  }

  // TASK UI
  return (
    <div>
      <h2>Task Manager</h2>
      <input
        placeholder="New Task"
        value={newTask}
        onChange={(e) => setNewTask(e.target.value)}
      />
      <input
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
      />
      <button onClick={addTask}>Add</button>

      <ul>
  {tasks.map((task) => (
    <li key={task.id}>
      <strong
        style={{
          textDecoration:
            task.status === "completed"
              ? "line-through"
              : "none",
        }}
      >
        {task.title}
      </strong>
      <br />
      <small>{task.description}</small>
      <br />

      <button onClick={() => toggleStatus(task)}>
        {task.status === "pending"
          ? "Mark Completed"
          : "Mark Pending"}
      </button>
    </li>
  ))}
</ul>
    </div>
  );
}

export default App;