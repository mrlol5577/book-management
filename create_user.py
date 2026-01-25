from app import app, db, User


def create_users():
    with app.app_context():
        db.create_all()

        # SUPER ADMIN
        if not User.query.filter_by(username='superadmin').first():
            super_admin = User(username='superadmin', role='superadmin')
            super_admin.set_password('super123')
            db.session.add(super_admin)
            print('SuperAdmin створений')

        # SIMPLE ADMIN
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print('Admin створений')

        db.session.commit()
        print('Готово!')


if __name__ == '__main__':
    create_users()