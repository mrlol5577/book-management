import os
from flask import Flask, render_template, url_for, request, redirect, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy import func
import json
import io

# Створюємо папку instance
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB максимум для upload

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Будь ласка, увійдіть для доступу до цієї сторінки.'

# Модель користувача
class Reader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ====== ЕКСПОРТ БАЗИ ДАНИХ У JSON (DOWNLOAD) ======
@app.route('/download-db-secret-12345')
@login_required
def download_database():
    if current_user.role != 'superadmin': 
        flash('❌ У вас немає прав для завантаження бази даних!', 'danger') 
        return redirect('/books')
    
    try:
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'books': [],
            'readers': [],
            'users': []
        }
        
        for book in Book.query.all():
            backup_data['books'].append({
                'id': book.id,
                'name_book': book.name_book,
                'author': book.author,
                'surname': book.surname,
                'ean': book.ean,
                'buyer': book.buyer,
                'phone': book.phone,
                'stat': book.stat,
                'date': book.date.isoformat() if book.date else None,
                'enddate': book.enddate.isoformat() if book.enddate else None,
                'history': book.history
            })
        
        for reader in Reader.query.all():
            backup_data['readers'].append({
                'id': reader.id,
                'name': reader.name,
                'surname': reader.surname,
                'phone': reader.phone
            })
        
        for user in User.query.all():
            backup_data['users'].append({
                'id': user.id,
                'username': user.username,
                'password_hash': user.password_hash,
                'role': user.role
            })
        
        json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
        buffer = io.BytesIO()
        buffer.write(json_data.encode('utf-8'))
        buffer.seek(0)
        
        filename = f'library_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        flash(f'❌ Помилка при завантаженні: {str(e)}', 'danger')
        return redirect('/books')

# ====== ВІДНОВЛЕННЯ БАЗИ ДАНИХ З JSON (UPLOAD) ======
@app.route('/restore-db-secret-54321', methods=['GET', 'POST'])
@login_required
def restore_database():
    if current_user.role != 'superadmin':
        flash('❌ У вас немає прав для відновлення бази даних!', 'danger')
        return redirect('/books')
    
    if request.method == 'POST':
        if 'database' not in request.files:
            flash('❌ Файл не вибрано!', 'danger')
            return redirect(request.url)
        
        file = request.files['database']
        
        if file.filename == '':
            flash('❌ Файл не вибрано!', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.json'):
            try:
                json_data = file.read().decode('utf-8')
                backup_data = json.loads(json_data)
                
                stats = {
                    'books_restored': 0,
                    'readers_restored': 0,
                    'users_restored': 0,
                    'errors': []
                }
                
                if 'books' in backup_data:
                    for book_data in backup_data['books']:
                        try:
                            book = Book(
                                id=book_data.get('id'),
                                name_book=book_data.get('name_book', ''),
                                author=book_data.get('author', ''),
                                surname=book_data.get('surname', ''),
                                ean=book_data.get('ean', ''),
                                buyer=book_data.get('buyer', ''),
                                phone=book_data.get('phone', ''),
                                stat=book_data.get('stat', 'доступна'),
                                date=datetime.fromisoformat(book_data['date']) if book_data.get('date') else datetime.utcnow(),
                                enddate=datetime.fromisoformat(book_data['enddate']) if book_data.get('enddate') else datetime.utcnow(),
                                history=book_data.get('history', '')
                            )
                            db.session.merge(book)
                            stats['books_restored'] += 1
                        except Exception as e:
                            stats['errors'].append(f"Книга {book_data.get('id')}: {str(e)}")
                
                if 'readers' in backup_data:
                    for reader_data in backup_data['readers']:
                        try:
                            reader = Reader(
                                id=reader_data.get('id'),
                                name=reader_data.get('name', ''),
                                surname=reader_data.get('surname', ''),
                                phone=reader_data.get('phone', '')
                            )
                            db.session.merge(reader)
                            stats['readers_restored'] += 1
                        except Exception as e:
                            stats['errors'].append(f"Читач {reader_data.get('id')}: {str(e)}")
                
                if 'users' in backup_data:
                    for user_data in backup_data['users']:
                        try:
                            if user_data.get('id') != current_user.id:
                                user = User(
                                    id=user_data.get('id'),
                                    username=user_data.get('username', ''),
                                    password_hash=user_data.get('password_hash', ''),
                                    role=user_data.get('role', 'admin')
                                )
                                db.session.merge(user)
                                stats['users_restored'] += 1
                        except Exception as e:
                            stats['errors'].append(f"Користувач {user_data.get('id')}: {str(e)}")
                
                db.session.commit()
                
                message = f"✅ Відновлено: Книг: {stats['books_restored']}, Читачів: {stats['readers_restored']}, Користувачів: {stats['users_restored']}"
                if stats['errors']:
                    message += f"\n⚠️ Помилки: {len(stats['errors'])}"
                
                flash(message, 'success')
                return redirect('/books')
                
            except json.JSONDecodeError:
                flash('❌ Невірний формат JSON файлу!', 'danger')
                return redirect(request.url)
            except Exception as e:
                db.session.rollback()
                flash(f'❌ Помилка при відновленні: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('❌ Невірний формат файлу! Потрібен файл .json', 'danger')
            return redirect(request.url)
    
    return render_template('restore_db.html')

# ====== ВИПРАВЛЕННЯ ПОСЛІДОВНОСТЕЙ ID (FIX SEQUENCES) ======
@app.route('/fix-sequences-secret-88888')
@login_required
def fix_sequences():
    if current_user.role != 'superadmin':
        flash('❌ У вас немає прав!', 'danger')
        return redirect('/books')
    
    try:
        db.session.execute(db.text("""
            SELECT setval(pg_get_serial_sequence('book', 'id'), 
                   COALESCE((SELECT MAX(id) FROM book), 0) + 1, false);
        """))
        
        db.session.execute(db.text("""
            SELECT setval(pg_get_serial_sequence('reader', 'id'), 
                   COALESCE((SELECT MAX(id) FROM reader), 0) + 1, false);
        """))
        
        db.session.execute(db.text("""
            SELECT setval(pg_get_serial_sequence('user', 'id'), 
                   COALESCE((SELECT MAX(id) FROM "user"), 0) + 1, false);
        """))
        
        db.session.commit()
        
        flash('✅ Послідовності ID успішно виправлено!', 'success')
        return redirect('/books')
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Помилка: {str(e)}', 'danger')
        return redirect('/books')

# Маршрут для логіну
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books'))

    if request.method == 'POST':
        password = request.form['password']

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('books'))

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
        search_query_lower = search_query.lower()
        books = []
        for book in Book.query.all():
            if (search_query_lower in book.name_book.lower() or
                search_query_lower in book.author.lower() or
                search_query_lower in book.ean.lower()):
                books.append(book)
    else:
        books = Book.query.all()

    return render_template('value_books.html', books=books, search_query=search_query)

@app.route('/readers')
@login_required
def readers():
    search_query = request.args.get('search', '')

    if search_query:
        search_query_lower = search_query.lower()
        readers = []
        for reader in Reader.query.all():
            if (search_query_lower in reader.name.lower() or
                search_query_lower in reader.surname.lower() or
                search_query_lower in reader.phone.lower()):
                readers.append(reader)
    else:
        readers = Reader.query.all()

    return render_template('readers.html', readers=readers, search_query=search_query)

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

            if not buyer or not phone or not surname:
                flash('⚠️ Заповніть всі поля: ім\'я, прізвище та телефон!', 'warning')
                return render_template('change.html', book=book)

            book.buyer = buyer
            book.phone = phone
            book.surname = surname
            book.stat = 'видана'
            book.date = datetime.utcnow()
            book.enddate = enddate

        else:
            book.buyer = ''
            book.phone = ''
            book.surname = ''
            book.stat = 'доступна'
            book.enddate = enddate
            book.date = datetime.utcnow()

        try:
            db.session.commit()
            
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

@app.route('/books/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    
    if request.method == 'POST':
        name_book = request.form.get('name_book', '').strip()
        author = request.form.get('author', '').strip()
        ean = request.form.get('ean', '').strip()
        
        if not name_book or not author:
            flash('⚠️ Назва книги та автор - обов\'язкові поля!', 'warning')
            return render_template('edit_book.html', book=book)
        
        book.name_book = name_book
        book.author = author
        book.ean = ean
        
        try:
            db.session.commit()
            flash('✅ Книгу успішно оновлено!', 'success')
            return redirect(f'/books/{book.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'⚠️ Помилка при оновленні: {str(e)}', 'danger')
            return render_template('edit_book.html', book=book)
    
    return render_template('edit_book.html', book=book)

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
    for book in books[:5]:
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

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)