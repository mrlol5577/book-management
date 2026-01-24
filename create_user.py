from app import app, db, User

def create_admin_user():
    with app.app_context():
        # Створюємо таблиці якщо їх немає
        db.create_all()
        
        # Перевіряємо чи вже існує адмін
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            print('Користувач "admin" вже існує!')
            return
        
        # Створюємо нового адміна
        admin = User(username='admin')
        admin.set_password('admin123')  # Змініть пароль!
        
        db.session.add(admin)
        db.session.commit()
        
        print('Адміністратора успішно створено!')
        print('Логін: admin')
        print('Пароль: admin123')
        print('\nОБОВ\'ЯЗКОВО змініть пароль після першого входу!')

if __name__ == '__main__':
    create_admin_user()