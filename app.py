import os
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy import func

# Створюємо папку instance
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "newflask.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Будь ласка, увійдіть для доступу до цієї сторінки.'

# Модель користувача
class Reader(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ЦЕ ОБОВ'ЯЗКОВО!!!
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False) 
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')  

    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_book = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), default='')
    ean = db.Column(db.Text, nullable=False)
    buyer = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    stat = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    enddate = db.Column(db.DateTime, default=datetime.utcnow)
    history = db.Column(db.String(100), default='')

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршрут для логіну
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books'))

    if request.method == 'POST':
        password = request.form['password']

        # шукаємо будь-якого користувача з правильним паролем
        user_found = None
        for user in User.query.all():
            if user.check_password(password):
                user_found = user
                break

        if user_found:
            login_user(user_found)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('books'))
        else:
            flash('Неправильний пароль', 'danger')

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

    if search_query:
        search_query_lower = search_query.lower()
        booked = []
        # Шукаємо тільки серед виданих книг
        for book in Book.query.filter(Book.stat == 'видана').all():
            if (search_query_lower in book.name_book.lower() or
                search_query_lower in book.author.lower() or
                search_query_lower in book.ean.lower()):
                booked.append(book)
    else:
        booked = Book.query.filter(Book.stat == 'видана').all()
    
    return render_template('booked.html', booked=booked, search_query=search_query)

@app.route('/notbook')
def notbook():
    search_query = request.args.get('search', '')
    
    if search_query:
        search_query_lower = search_query.lower()
        notbook = []
        # Шукаємо тільки серед доступних книг
        for book in Book.query.filter(Book.stat == 'доступна').all():
            if (search_query_lower in book.name_book.lower() or
                search_query_lower in book.author.lower() or
                search_query_lower in book.ean.lower()):
                notbook.append(book)
    else:
        notbook = Book.query.filter(Book.stat == 'доступна').all()
    
    return render_template('notbook.html', notbook=notbook, search_query=search_query)


@app.route('/')
@app.route('/books')
def books():
    search_query = request.args.get('search', '')

    if search_query:
        search_query_lower = search_query.lower()  # перетворюємо запит в нижній регістр
        books = []
        # Перебираємо всі книги і шукаємо збіги в Python
        for book in Book.query.all():
            if (search_query_lower in book.name_book.lower() or
                search_query_lower in book.author.lower() or
                search_query_lower in book.ean.lower()):
                books.append(book)
    else:
        books = Book.query.all()

    return render_template('value_books.html', books=books, search_query=search_query)

    


@app.route('/books/<int:id>', methods=['POST', 'GET'])
@login_required
def change(id):
    book = Book.query.get(id)

    if request.method == 'POST':
        enddate_str = request.form.get('enddate')
        if enddate_str:
            enddate = datetime.strptime(enddate_str, '%Y-%m-%d')
        else:
            enddate = datetime.utcnow()
        
        # Зберігаємо історію ТІЛЬКИ якщо був попередній читач
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
        
        if new_stat == 'видана':
            buyer = request.form.get('buyer', '').strip()
            phone = request.form.get('phone', '').strip()
            surname = request.form.get('surname', '').strip()

            # Перевіряємо заповнення полів
            if not buyer or not phone or not surname:
                flash('⚠️ Заповніть всі поля: ім\'я, прізвище та телефон!', 'warning')
                return render_template('change.html', book=book)

            # Оновлюємо дані книги
            book.buyer = buyer
            book.phone = phone
            book.surname = surname
            book.stat = 'видана'
            book.date = datetime.utcnow()
            book.enddate = enddate

        else:  # stat == 'нема'
            book.buyer = ''
            book.phone = ''
            book.surname = ''
            book.stat = 'доступна'
            book.enddate = enddate
            book.date = datetime.utcnow()

        # Єдиний commit для книги
        try:
            db.session.commit()
            
            # ПІСЛЯ успішного commit книги — додаємо читача
            if new_stat == 'видана':
                existing_reader = Reader.query.filter_by(phone=phone).first()
                if not existing_reader:
                    new_reader = Reader(
                        name=buyer,
                        surname=surname,
                        phone=phone
                    )
                    db.session.add(new_reader)
                    db.session.commit()
            
            flash('✅ Дані успішно оновлено!', 'success')
            return redirect('/books')
            
        except Exception as e:
            db.session.rollback()
            flash(f'⚠️ Помилка: {str(e)}', 'danger')
            return render_template('change.html', book=book)
    
    return render_template('change.html', book=book)
@app.route('/search_books')
@login_required
def search_books():
    q = request.args.get('q', '').lower()

    if not q or len(q) < 2:
        return {'results': []}

    books = []
    for book in Book.query.all():
        if (q in book.name_book.lower() or 
            q in book.author.lower() or 
            q in book.ean.lower()):
            books.append(book)

    results = []
    for book in books[:5]:  # Показуємо максимум 5 результатів
        results.append({
            'name_book': book.name_book,
            'author': book.author,
            'ean': book.ean,
            'stat': book.stat
        })

    return {'results': results}
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

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/reg', methods=['POST', 'GET'])
def reg():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        phone = request.form['phone']

        reader = Reader(name=name,surname=surname,phone=phone)

        try:
            db.session.add(reader)
            db.session.commit()
            return redirect('/books')
        except Exception as e:
            flash(f'При добавленні статті сталася помилка: {str(e)}', 'danger')

    return render_template('reg.html')


@app.route('/books/<int:id>/del')
@login_required
def post_delete(id):
    # Тільки superadmin може видаляти
    if current_user.role != 'superadmin':
        flash('❌ У вас немає прав на видалення!', 'danger')
        return redirect('/books')

    book = Book.query.get_or_404(id)

    try:
        db.session.delete(book)
        db.session.commit()
        flash('✅ Книгу видалено!', 'success')
    except:
        flash('❌ Помилка при видаленні', 'danger')

    return redirect('/books')
    
@app.route('/search_reader')
@login_required
def search_reader():
    q = request.args.get('q', '')

    if not q:
        return {'results': []}

    readers = Reader.query.filter(
        Reader.name.ilike(f'%{q}%')
    ).limit(5).all()

    results = []

    for r in readers:
        results.append({
            'name': r.name,
            'surname': r.surname,
            'phone': r.phone
        })

    return {'results': results}



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)