"""
Flask To‑Do App using SQLAlchemy (MySQL via XAMPP)

Features:
- Uses Flask + Flask-SQLAlchemy ORM
- Stores Users and Tasks in a MySQL database (XAMPP)
- Simple registration and login (passwords hashed)
- Tasks are scoped per-user (each user sees their own tasks)
- Creates tables automatically with `db.create_all()`
- Responsive UI for phone, tablet, laptop, desktop and large screens (TV)

Setup (on your machine / XAMPP):
1. Make sure MySQL is running in XAMPP and you've created a database, for example `todo_db`.
   - You can create it via phpMyAdmin or using MySQL client: `CREATE DATABASE todo_db CHARACTER SET utf8mb4;`
2. Install required Python packages:
   ```bash
   pip install flask flask_sqlalchemy pymysql werkzeug
   ```
3. Configure the DB URI if needed by setting the environment variable `DATABASE_URL`.
   Default used by this script: `mysql+pymysql://root:@localhost/todo_db`

Run:
    python app.py

Note: This is a simple demo. For production, use strong secret keys, HTTPS, and proper user/account management.
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ---------- Configuration ----------
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-key-change-me')

# By default connect to local XAMPP MySQL. Override with DATABASE_URL env var if needed.
# Example default: 'mysql+pymysql://root:@localhost/todo_db'
DB_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/todo_db')
if DB_URI.startswith("postgres://"):
    DATABASE_URL = DB_URI.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] =DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# ---------- Models ----------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    due_date = db.Column(db.String(50), nullable=True)  # store date as ISO string (YYYY-MM-DD)
    note = db.Column(db.Text, nullable=True)
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

# ---------- Create tables ----------
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        import traceback, sys
        print("Failed to create tables. Check DATABASE_URL and that MySQL is running.")
        traceback.print_exc()
        print("Current DATABASE_URL:", app.config.get('SQLALCHEMY_DATABASE_URI'))
        sys.exit(1)

# ---------- Helpers ----------
from functools import wraps

def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return fn(*a, **kw)
    return wrapper

# ---------- Templates (fully responsive CSS + animations) ----------
LOGIN_HTML = '''
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login</title>
<style>
:root{--bg:#071023;--card:#071827;--accent:#7c3aed;--muted:#94a3b8}
*{box-sizing:border-box}
body{font-family:Inter,system-ui,Segoe UI,Roboto,Arial;background:var(--bg);color:#e6eef8;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;padding:16px}
.box{background:var(--card);padding:28px;border-radius:12px;box-shadow:0 12px 40px rgba(2,6,23,0.7);width:100%;max-width:420px}
h2{margin:0 0 12px;font-size:20px}
input{width:100%;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,0.03);background:transparent;color:inherit;margin-bottom:10px;outline:none}
input:focus{box-shadow:0 6px 18px rgba(124,58,237,0.12)}
button{width:100%;padding:12px;border-radius:10px;border:0;background:linear-gradient(90deg,var(--accent),#4f46e5);color:#fff;font-weight:600;cursor:pointer}
.error{color:#ffb4b4;margin-bottom:8px}
.small{font-size:13px;color:var(--muted);text-align:center;margin-top:10px}
@media (min-width:1200px){body{padding:40px}}
</style>
</head><body>
<div class="box">
  <h2>Login</h2>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="post">
    <input name="username" placeholder="Username" autofocus />
    <input name="password" type="password" placeholder="Password" />
    <button type="submit">Sign in</button>
  </form>
  <div class="small">No account? <a href="/register" style="color:inherit;opacity:0.9">Register</a></div>
</div>
</body></html>
'''

REGISTER_HTML = '''
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Register</title>
<style>
:root{--bg:#071023;--card:#071827;--accent:#7c3aed;--muted:#94a3b8}
*{box-sizing:border-box}
body{font-family:Inter,system-ui,Segoe UI,Roboto,Arial;background:var(--bg);color:#e6eef8;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;padding:16px}
.box{background:var(--card);padding:28px;border-radius:12px;box-shadow:0 12px 40px rgba(2,6,23,0.7);width:100%;max-width:420px}
input{width:100%;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,0.03);background:transparent;color:inherit;margin-bottom:10px}
button{width:100%;padding:12px;border-radius:10px;border:0;background:linear-gradient(90deg,var(--accent),#4f46e5);color:#fff;font-weight:600;cursor:pointer}
.error{color:#ffb4b4;margin-bottom:8px}
.small{font-size:13px;color:var(--muted);text-align:center;margin-top:10px}
</style>
</head><body>
<div class="box">
  <h2>Create account</h2>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="post">
    <input name="username" placeholder="Choose a username" autofocus />
    <input name="password" type="password" placeholder="Choose a password" />
    <button type="submit">Create account</button>
  </form>
  <div class="small">Have an account? <a href="/login" style="color:inherit;opacity:0.9">Sign in</a></div>
</div>
</body></html>
'''

APP_HTML = '''
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ToDo</title>
<style>
:root{
  --bg:#071023; --card:#071827; --accent:#7c3aed; --muted:#94a3b8;
  --max-width:1200px; --gutter:20px;
}
*{box-sizing:border-box}
body{font-family:Inter,system-ui,Segoe UI,Roboto,Arial;background:var(--bg);color:#e6eef8;margin:0;padding:20px;display:flex;justify-content:center}
.container{width:100%;max-width:var(--max-width);padding:0 16px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.top h2{margin:0;font-size:clamp(18px,2.4vw,26px)}
.user-info{color:var(--muted);font-size:clamp(12px,1.2vw,14px)}
.card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));padding:18px;border-radius:12px;box-shadow:0 12px 40px rgba(2,6,23,0.6)}

/* Form layout: responsive columns that adjust to screen size */
.form-grid{display:grid;grid-template-columns:1fr 340px;gap:18px;align-items:start}
.left-col{display:flex;flex-direction:column;gap:12px}
.right-col{display:flex;flex-direction:column;gap:12px;justify-content:center}
label.small{font-size:13px;color:var(--muted)}

input,textarea,button{padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:inherit;outline:none}
input:focus,textarea:focus{box-shadow:0 8px 22px rgba(124,58,237,0.09)}
textarea{resize:none;min-height:96px}
button{background:linear-gradient(90deg,var(--accent),#4f46e5);border:0;color:#fff;font-weight:600;cursor:pointer}

/* Task list: switch between single-column and two-column depending on width */
.task-list{margin-top:16px;display:grid;gap:12px}
@media (min-width:1000px){
  .task-list{grid-template-columns:1fr 1fr;gap:14px}
}

.task{display:flex;justify-content:space-between;align-items:flex-start;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,0.03);background:linear-gradient(180deg, rgba(255,255,255,0.01), transparent);transform-origin:left center;transition:transform .18s ease,box-shadow .18s}
.task:hover{transform:translateY(-6px);box-shadow:0 12px 30px rgba(2,6,23,0.45)}
.left{display:flex;gap:12px;align-items:flex-start}
.checkbox{width:20px;height:20px;border-radius:6px;border:2px solid var(--muted);display:flex;align-items:center;justify-content:center;cursor:pointer}
.checkbox.done{background:linear-gradient(90deg,var(--accent),#4f46e5);border-color:transparent}
.title{font-size:15px}
.title.done{text-decoration:line-through;opacity:0.6}
.meta{font-size:12px;color:var(--muted);margin-top:6px}
.note{font-size:13px;color:#cbd5e1;margin-top:8px}
.delete-btn{background:transparent;border:1px solid rgba(255,255,255,0.04);padding:8px;border-radius:8px;cursor:pointer}

/* Animations */
@keyframes popIn{from{opacity:0; transform:translateY(10px) scale(.995)} to{opacity:1; transform:none}}
.task.new{animation:popIn .36s cubic-bezier(.2,.9,.3,1) both}

/* draw-in underline for title (simulates drawing the task) */
.task .title{position:relative;display:inline-block}
.task .title::after{
  content:'';position:absolute;left:0;bottom:-8px;height:3px;width:0;background:linear-gradient(90deg,var(--accent),#4f46e5);border-radius:4px;opacity:0.95;transform-origin:left center}
@keyframes drawUnderline{from{width:0}to{width:100%}}
.task.new .title::after{animation:drawUnderline .58s cubic-bezier(.2,.9,.3,1) forwards}

/* subtle "sketch" reveal for the whole task: slight skew + fade */
@keyframes drawReveal{0%{opacity:0;transform:translateX(-36px) rotate(-2deg) scale(.98);filter:blur(6px)}60%{opacity:1;transform:translateX(6px) rotate(1deg) scale(1.01);filter:blur(1px)}100%{opacity:1;transform:none;filter:blur(0)} }
.task.new{animation:drawReveal .45s cubic-bezier(.2,.9,.3,1) both}

/* delete animation */
@keyframes deleteOut {
  0% {opacity:1; transform:translateX(0) scale(1); filter:blur(0px);}  
  20% {opacity:0.9; transform:translateX(5px) scale(0.98); filter:blur(1px);} 
  40% {opacity:0.7; transform:translateX(15px) scale(0.96); filter:blur(2px);} 
  60% {opacity:0.4; transform:translateX(20px) scale(0.93); filter:blur(3px);} 
  80% {opacity:0.2; transform:translateX(25px) scale(0.90); filter:blur(4px);} 
  100% {opacity:0; transform:translateX(40px) scale(0.85); filter:blur(6px);}  
}

.task.removing {
  animation: deleteOut .65s cubic-bezier(.4,.01,.2,1) forwards;
  pointer-events:none;
}

.btn-press
/* delete animation */
@keyframes deleteOut {
  0% {opacity:1; transform:translateX(0) scale(1); filter:blur(0px);}  
  20% {opacity:0.9; transform:translateX(5px) scale(0.98); filter:blur(1px);} 
  40% {opacity:0.7; transform:translateX(15px) scale(0.96); filter:blur(2px);} 
  60% {opacity:0.4; transform:translateX(20px) scale(0.93); filter:blur(3px);} 
  80% {opacity:0.2; transform:translateX(25px) scale(0.90); filter:blur(4px);} 
  100% {opacity:0; transform:translateX(40px) scale(0.85); filter:blur(6px);}  
}

.task.removing {
  animation: deleteOut .65s cubic-bezier(.4,.01,.2,1) forwards;
  pointer-events:none;
}

.btn-press{transform:scale(.98)}

/* Responsive tweaks for small devices */
@media (max-width:720px){
  .form-grid{grid-template-columns:1fr;}
  .right-col{order:2}
  .left-col{order:1}
  body{padding:12px}
}
@media (max-width:420px){
  .card{padding:14px}
  input,textarea,button{padding:10px}
  .top{flex-direction:column;align-items:flex-start;gap:8px}
  .user-info{font-size:12px}
}

/* Large screen / TV adjustments */
@media (min-width:1600px){
  :root{--max-width:1500px}
  body{padding:40px}
  .card{padding:26px}
  textarea{min-height:120px}
}
</style>
</head>
<body>
<div class="container">
  <div class="top">
    <h2>Your ToDo</h2>
    <div class="user-info">Hi {{ user.username }} • <a href="/logout" style="color:inherit;opacity:0.9">Logout</a></div>
  </div>

  <div class="card">
    <form id="addForm">
      <div class="form-grid">
        <div class="left-col">
          <input id="title" placeholder="Task name" required />
          <div style="display:flex;gap:10px;align-items:center">
            <label class="small">Due</label>
            <input id="due" type="date" style="flex:1" />
          </div>
          <textarea id="note" placeholder="Note (optional)" rows="4"></textarea>
        </div>

        <div class="right-col">
          <div style="display:flex;justify-content:center;align-items:center;height:100%">
            <button id="addBtn" type="submit" style="width:100%;padding:14px;font-size:16px">Add Task</button>
          </div>
        </div>
      </div>
    </form>

    <div id="list" class="task-list"></div>
  </div>
</div>

<script>
async function api(path, method='GET', body=null){
  const opts={method, headers:{'Accept':'application/json'}};
  if(body){opts.headers['Content-Type']='application/json'; opts.body=JSON.stringify(body)}
  const res = await fetch(path, opts);
  return res.json();
}

function formatDateIso(iso){
  try{ const d = new Date(iso); return d.toLocaleString(); }catch(e){return iso}
}

async function render(){
  const data = await api('/tasks');
  const container = document.getElementById('list'); container.innerHTML='';
  data.forEach(t=>{
    const el = createTaskElement(t);
    container.appendChild(el);
  });
}
function createTaskElement(t){
  const row = document.createElement('div'); row.className='task';
  const left = document.createElement('div'); left.className='left';

  const cb = document.createElement('div'); cb.className='checkbox'+(t.done? ' done':''); cb.onclick = ()=>{ toggle(t.id); };
  cb.innerHTML = t.done? '✓':'';

  const content = document.createElement('div');
  const title = document.createElement('div'); title.className='title'+(t.done? ' done':''); title.textContent = t.title;
  const meta = document.createElement('div'); meta.className='meta'; meta.textContent = 'Created: ' + formatDateIso(t.created_at) + (t.due_date? ' • Due: '+t.due_date:'');
  content.appendChild(title); content.appendChild(meta);
  if(t.note){ const note = document.createElement('div'); note.className='note'; note.textContent = t.note; content.appendChild(note); }

  left.appendChild(cb); left.appendChild(content);

  const del = document.createElement('button'); del.className='delete-btn'; del.textContent='Delete';
  // animate delete: play animation, then call API and remove element on success
  del.onclick = ()=> animateDelete(row, t.id);

  row.appendChild(left); row.appendChild(del);
  return row;
}

async function animateDelete(row, id){
  // add removing class to trigger CSS animation
  if(!row) return;
  row.classList.add('removing');
  // wait for animation to finish
  row.addEventListener('animationend', async function handler(ev){
    row.removeEventListener('animationend', handler);
    try{
      const res = await api('/delete/'+id, 'POST');
      if(res && res.ok){
        // remove from DOM if still present
        if(row.parentNode) row.parentNode.removeChild(row);
      } else {
        alert(res && res.error ? res.error : 'Delete failed');
        // if delete failed, restore visual state
        row.classList.remove('removing');
        // re-render to sync with server
        render();
      }
    }catch(err){
      alert('Network error');
      row.classList.remove('removing');
      render();
    }
  });
}

async function add(e){
  if(e) e.preventDefault();
  const btn = document.getElementById('addBtn');
  btn.classList.add('btn-press');
  setTimeout(()=>btn.classList.remove('btn-press'),120);

  const title = document.getElementById('title').value.trim();
  if(!title) return alert('Please enter a task name');
  const due = document.getElementById('due').value || null;
  const note = document.getElementById('note').value || null;
  const res = await api('/add','POST',{title,due_date:due,note});
  if(res && res.ok){
    // fetch the latest tasks and animate the newly added item
    const data = await api('/tasks');
    const container = document.getElementById('list');
    container.innerHTML='';
    data.forEach((t,i)=>{
      const el = createTaskElement(t);
      // mark the first (most recent) item with .new to animate it
      if(i===0) el.classList.add('new');
      container.appendChild(el);
      el.addEventListener('animationend', ()=> el.classList.remove('new'));
    });
    document.getElementById('title').value=''; document.getElementById('due').value=''; document.getElementById('note').value='';
  } else if(res && res.error){
    alert(res.error);
  }
}

async function toggle(id){ await api('/toggle/'+id,'POST'); render(); }
async function remove(id){ await api('/delete/'+id,'POST'); render(); }

document.getElementById('addForm').addEventListener('submit', add);
// initial load
render();
</script>
</body>
</html>
'''

# ---------- Routes ----------
@app.route('/register', methods=['GET','POST'])
def register():
    error = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '')
        if not username or not password:
            error = 'Enter username and password'
        elif User.query.filter_by(username=username).first():
            error = 'Username already taken'
        else:
            u = User(username=username)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            session['user_id'] = u.id
            return redirect(url_for('index'))
    return render_template_string(REGISTER_HTML, error=error)

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '')
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            error = 'Invalid credentials'
        else:
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    user = db.session.get(User, session['user_id'])
    return render_template_string(APP_HTML, user=user)

# API routes (JSON)
@app.route('/tasks')
@login_required
def tasks_api():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.id.desc()).all()
    out = []
    for t in tasks:
        out.append({'id': t.id, 'title': t.title, 'due_date': t.due_date, 'note': t.note, 'done': t.done, 'created_at': t.created_at.isoformat()})
    return jsonify(out)

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error':'empty'}), 400
    due = data.get('due_date') or None
    note = data.get('note') or None
    user_id = session['user_id']
    t = Task(user_id=user_id, title=title, due_date=due, note=note)
    db.session.add(t)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    user_id = session['user_id']
    t = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not t:
        return jsonify({'error':'not found'}), 404
    db.session.delete(t)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    user_id = session['user_id']
    t = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not t:
        return jsonify({'error':'not found'}), 404
    t.done = not t.done
    db.session.commit()
    return jsonify({'ok':True})

# ---------- Run ----------
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
