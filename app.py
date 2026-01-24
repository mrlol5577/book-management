
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newflask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'  # Змініть на випадковий ключ!

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Будь ласка, увійдіть для доступу до цієї сторінки.'

# Модель користувача
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False) 
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_book = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100))
    ean = db.Column(db.Text, nullable=False)
    buyer = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    stat = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    enddate = db.Column(db.DateTime, default=datetime.utcnow)
    history = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршрут для логіну
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('books'))
        else:
            flash('Неправильний логін або пароль', 'danger')
    
    return render_template('login.html')

# Маршрут для виходу
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('books'))

# Маршрут для реєстрації (опціонально)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('books'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Користувач з таким іменем вже існує', 'danger')
            return render_template('register.html')
        
        user = User(username=username)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Помилка при реєстрації', 'danger')
    
    return render_template('register.html')

@app.route('/booked')
def booked():
    search_query = request.args.get('search', '')
    search_type = request.args.get('chose', 'назва')

    if search_query:
        if search_type == 'назва':
            booked = Book.query.filter((Book.name_book.ilike(f'%{search_query}%')) & (Book.stat == 'є')).all()
        elif search_type == 'автор':
            booked = Book.query.filter((Book.author.ilike(f'%{search_query}%')) & (Book.stat == 'є')).all()
        elif search_type == 'ean':
            booked = Book.query.filter((Book.ean.ilike(f'%{search_query}%')) & (Book.stat == 'є')).all()
        elif search_type == 'імя':
            booked = Book.query.filter((Book.buyer.ilike(f'%{search_query}%')) & (Book.stat == 'є')).all()
        elif search_type == 'телефон':
            booked = Book.query.filter((Book.phone.ilike(f'%{search_query}%')) & (Book.stat == 'є')).all()
        else:
            booked = Book.query.filter(Book.stat == 'є').all()
    else:
        booked = Book.query.filter(Book.stat == 'є').all()
    
    return render_template('booked.html', booked=booked, search_query=search_query, search_type=search_type)

@app.route('/notbook')
def notbook():
    search_query = request.args.get('search', '')
    search_type = request.args.get('chose', 'назва')

    if search_query:
        if search_type == 'назва':
            notbook = Book.query.filter((Book.name_book.ilike(f'%{search_query}%')) & (Book.stat == 'нема')).all()
        elif search_type == 'автор':
            notbook = Book.query.filter((Book.author.ilike(f'%{search_query}%')) & (Book.stat == 'нема')).all()
        elif search_type == 'ean':
            notbook = Book.query.filter((Book.ean.ilike(f'%{search_query}%')) & (Book.stat == 'нема')).all()
        elif search_type == 'імя':
            notbook = Book.query.filter((Book.buyer.ilike(f'%{search_query}%')) & (Book.stat == 'нема')).all()
        elif search_type == 'телефон':
            notbook = Book.query.filter((Book.phone.ilike(f'%{search_query}%')) & (Book.stat == 'нема')).all()
        else:
            notbook = Book.query.filter(Book.stat == 'нема').all()
    else:
        notbook = Book.query.filter(Book.stat == 'нема').all()
    
    return render_template('notbook.html', notbook=notbook, search_query=search_query, search_type=search_type)
    
@app.route('/')
@app.route('/books')
def books():
    search_query = request.args.get('search', '')
    search_type = request.args.get('chose', 'назва')
    
    if search_query:
        if search_type == 'все':
            books = Book.query.filter(
                (Book.name_book.ilike(f'%{search_query}%')) |
                (Book.author.ilike(f'%{search_query}%')) |
                (Book.ean.ilike(f'%{search_query}%'))
            ).all()
        elif search_type == 'назва':
            books = Book.query.filter(Book.name_book.ilike(f'%{search_query}%')).all()
        elif search_type == 'автор':
            books = Book.query.filter(Book.author.ilike(f'%{search_query}%')).all()
        elif search_type == 'ean':
            books = Book.query.filter(Book.ean.ilike(f'%{search_query}%')).all()
        elif search_type == 'імя':
            books = Book.query.filter(Book.buyer.ilike(f'%{search_query}%')).all()
        elif search_type == 'телефон':
            books = Book.query.filter(Book.phone.ilike(f'%{search_query}%')).all()
        else:
            books = Book.query.all()
    else:
        books = Book.query.all()
    
    return render_template('value_books.html', books=books, search_query=search_query, search_type=search_type)

@app.route('/books/<int:id>')
@login_required
def change(id):
    book = Book.query.get(id)
    return render_template('change.html', book=book)

@app.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    if request.method == 'POST':
        name_book = request.form['name_book']
        author = request.form['author']
        ean = request.form['ean']
        buyer = request.form['buyer']
        phone = request.form['phone']   
        stat = request.form['stat']   

        date_str = request.form.get('date')
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date = datetime.utcnow()

        books = Book(name_book=name_book, author=author, ean=ean, buyer=buyer, phone=phone, stat=stat, date=date)

        try:
            db.session.add(books)
            db.session.commit()
            flash('Книгу успішно додано!', 'success')
            return redirect('/books')
        except Exception as e:
            flash(f'При добавленні статті сталася помилка: {str(e)}', 'danger')
    
    return render_template('create.html')

@app.route('/books/<int:id>/update', methods=['POST', 'GET'])
@login_required
def customer_update(id):
    book = Book.query.get(id)
    if request.method == 'POST':
        enddate_str = request.form.get('enddate')
        if enddate_str:
            enddate = datetime.strptime(enddate_str, '%Y-%m-%d')
        else:
            enddate = datetime.utcnow()
        
        if book.buyer and book.buyer.strip():
            old_buyer = book.buyer
            old_phone = book.phone if book.phone else 'Немає'
            start_date = book.date.strftime('%d.%m.%Y') if book.date else 'Немає'
            end_date_formatted = enddate.strftime('%d.%m.%Y')
            
            new_history_entry = f"{old_buyer} ({old_phone}) - з {start_date} до {end_date_formatted}"
            
            if book.history:
                book.history = new_history_entry + " | " + book.history
            else:
                book.history = new_history_entry
        
        new_stat = request.form['stat']
        
        if new_stat == 'є':
            book.buyer = request.form['buyer']
            book.phone = request.form['phone']
        else:
            book.buyer = ''
            book.phone = ''
        
        book.stat = new_stat
        book.enddate = enddate
        book.date = datetime.utcnow()

        try:
            db.session.commit()
            flash('Дані успішно оновлено!', 'success')
            return redirect('/books')
        except Exception as e:
            db.session.rollback()
            flash(f'При оновленні статті сталася помилка: {str(e)}', 'danger')
    
    return render_template('customer_update.html', book=book)

@app.route('/books/<int:id>/del')
@login_required
def post_delete(id):
    book = Book.query.get_or_404(id)
    try:
        db.session.delete(book)
        db.session.commit()
        flash('Книгу успішно видалено!', 'success')
        return redirect('/books')
    except:
        flash('Сталася помилка при видаленні', 'danger')
        return redirect('/books')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)