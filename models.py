from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Создаём объект db здесь, а не импортируем
db = SQLAlchemy()

# ========== МОДЕЛИ ДЛЯ БАЗЫ ДАННЫХ ==========

class User(db.Model):
    """Пользователи системы"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='editor')
    full_name = db.Column(db.String(200))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    """Категории контента"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)


class Content(db.Model):
    """Контент (новости, статьи)"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    is_published = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    image_filename = db.Column(db.String(255))  # Имя файла картинки
    image_path = db.Column(db.String(500))  # Путь к картинке

    # Связи
    author = db.relationship('User', backref=db.backref('contents', lazy=True))
    category = db.relationship('Category', backref=db.backref('contents', lazy=True))


class Faculty(db.Model):
    """Факультеты/институты"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    short_name = db.Column(db.String(50))
    description = db.Column(db.Text)
    dean_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(100))
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

    dean = db.relationship('User', backref=db.backref('faculties', lazy=True))


class EducationalProgram(db.Model):
    """Образовательные программы"""
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(300), nullable=False)
    level = db.Column(db.String(50))
    form = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    description = db.Column(db.Text)
    study_plan_path = db.Column(db.String(500))
    curriculum_path = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    faculty = db.relationship('Faculty', backref=db.backref('programs', lazy=True))


class FeedbackMessage(db.Model):
    """Сообщения обратной связи"""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_processed = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)


class AdmissionApplication(db.Model):
    """Заявки на поступление"""
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(200), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    program_code = db.Column(db.String(20), nullable=False)
    program_name = db.Column(db.String(200))
    form_education = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='new')
    notes = db.Column(db.Text)
    consent_data = db.Column(db.Boolean, default=False)
    consent_rules = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)


class OrganizationSection(db.Model):
    """Разделы сведений (ГОСТ)"""
    id = db.Column(db.Integer, primary_key=True)
    order_num = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_required = db.Column(db.Boolean, default=True)
    icon = db.Column(db.String(50))


class OrganizationItem(db.Model):
    """Пункты разделов (ГОСТ)"""
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('organization_section.id'), nullable=False)
    order_num = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    file_name = db.Column(db.String(200))
    file_size = db.Column(db.Integer)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    section = db.relationship('OrganizationSection', backref=db.backref('items', lazy=True))