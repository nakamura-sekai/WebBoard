from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret-key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bbs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# モデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # ユーザー情報にアクセスできるようにする
    user = db.relationship('User', backref='posts')
with app.app_context():
    db.create_all()

# ルート
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/index')  # ログイン成功後は /index へ
        else:
            return "ログイン失敗"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')
    content = request.form['content']
    new_post = Post(content=content, user_id=session['user_id'])
    db.session.add(new_post)
    db.session.commit()
    return redirect('/')

@app.route('/')
def root():
    # ログイン済みなら /index に、未ログインなら /login にリダイレクト
    if 'user_id' in session:
        return redirect('/index')
    return redirect('/login')

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    post = Post.query.get(post_id)
    if post and post.user_id == session['user_id']:  # 自分の投稿だけ削除可能
        db.session.delete(post)
        db.session.commit()
    
    return redirect('/index')


if __name__ == '__main__':
    app.run(debug=True)
    