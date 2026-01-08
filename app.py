import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
import time

# Декоратор для увеличения времени загрузки
def delayed_response(delay=5):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Имитируем загрузку
            if app.debug:  # Только в режиме разработки
                time.sleep(delay)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Сначала создаём приложение
app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
# Настройки для загрузки файлов
app.config['UPLOAD_FOLDER'] = 'static/uploads/news'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Создаем папку для загрузок, если её нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Проверяет, можно ли загружать такой файл"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
# Настройки БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Импортируем db из models и инициализируем
from models import db

db.init_app(app)

# Импортируем модели ПОСЛЕ создания db
from models import User, Category, Content, Faculty, EducationalProgram, FeedbackMessage, AdmissionApplication, \
    OrganizationSection, OrganizationItem


# ========== СОЗДАНИЕ БАЗЫ ДАННЫХ ==========
def create_tables():
    """Создаёт все таблицы в базе данных"""
    with app.app_context():

        db.create_all()

        print("=" * 50)
        print("ПРОВЕРКА БАЗЫ ДАННЫХ:")
        print(f"Пользователей: {User.query.count()}")
        print(f"Категорий: {Category.query.count()}")
        print(f"Контента: {Content.query.count()}")
        print("=" * 50)

        # Создаём тестовые данные, если таблицы пустые
        if User.query.count() == 0:
            print("Создаём пользователей...")
            admin = User(username='admin', role='admin', email='admin@university.ru')
            admin.set_password('admin123')
            db.session.add(admin)

            editor = User(username='editor', role='editor', email='editor@university.ru')
            editor.set_password('editor123')
            db.session.add(editor)

            db.session.commit()
            print("✅ Пользователи созданы")

        if Category.query.count() == 0:
            print("Создаём категории...")
            categories = [
                Category(name='Новости', slug='news'),
                Category(name='Объявления', slug='announcements'),
                Category(name='События', slug='events')
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("✅ Категории созданы")

        # Проверяем наличие данных
        news_category = Category.query.filter_by(slug='news').first()
        admin_user = User.query.filter_by(username='admin').first()

        print(f"Категория 'новости': {news_category}")
        print(f"Пользователь 'admin': {admin_user}")
        print(f"Контент в базе: {Content.query.count()} записей")

        # Создаём тестовые новости, если их нет
        if news_category and admin_user and Content.query.count() == 0:
            print("Создаём тестовые новости...")
            contents = [
                Content(
                    title='Добро пожаловать на наш сайт!',
                    content='Это демонстрационная новость. Система успешно работает!\n\nЗдесь вы найдете все актуальные новости университета.',
                    category_id=news_category.id,
                    author_id=admin_user.id,
                    is_published=True
                ),
                Content(
                    title='Начало зимней сессии',
                    content='Расписание экзаменов и зачётов находится во вкладке "Расписание". Удачи!',
                    category_id=news_category.id,
                    author_id=admin_user.id,
                    is_published=True
                )
            ]
            db.session.add_all(contents)
            db.session.commit()
            print("✅ Тестовые новости созданы")

        print("=" * 50)
        print("ФИНАЛЬНАЯ ПРОВЕРКА:")

        # Выводим все категории
        all_categories = Category.query.all()
        print("Категории в базе:")
        for cat in all_categories:
            print(f"  - {cat.name} (slug: {cat.slug}, id: {cat.id})")

        # Выводим все новости
        all_content = Content.query.all()
        print("Контент в базе:")
        for content in all_content:
            print(f"  - '{content.title}' (категория id: {content.category_id}, опубликовано: {content.is_published})")

        print("=" * 50)

# ========== МАРШРУТЫ ==========

@app.route('/')
def home():
    """Главная страница"""
    time.sleep(5)
    # Получаем только опубликованные новости из категории "новости"
    news_category = Category.query.filter_by(slug='news').first()


    if news_category:
        news = Content.query.filter_by(
            category_id=news_category.id,
            is_published=True
        ).order_by(Content.created_at.desc()).limit(5).all()

    return render_template('index.html', news=news, user=session.get('user'), category=news_category)
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового администратора"""
    if 'user' in session:
        flash('Вы уже авторизованы!', 'warning')
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()

        errors = []
        if not username:
            errors.append('Введите имя пользователя')
        if not password:
            errors.append('Введите пароль')
        if password != password_confirm:
            errors.append('Пароли не совпадают')
        if len(password) < 8:
            errors.append('Пароль должен быть не менее 8 символов')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            errors.append('Пользователь с таким именем уже существует')

        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            new_user = User(username=username, role='editor')
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Заполните все поля', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user'] = {'id': user.id, 'username': user.username, 'role': user.role}
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('user', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('home'))

@app.route('/news')
def news_list():
    """Список всех новостей"""
    news_category = Category.query.filter_by(slug='news').first()

    if news_category:
        all_news = Content.query.filter_by(
            category_id=news_category.id,
            is_published=True
        ).order_by(Content.created_at.desc()).all()
    else:
        all_news = []

    return render_template('news_list.html', news=all_news)
@app.route('/news/<int:news_id>')
def news_detail(news_id):
    """Детальная страница новости"""
    news_item = Content.query.get_or_404(news_id)

    # Проверяем, опубликована ли новость
    if not news_item.is_published:
        flash('Эта новость не опубликована', 'error')
        return redirect(url_for('news_list'))

    return render_template('news_detail.html', news=news_item)
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contacts')
def contacts():
    return render_template('contacts.html')


@app.route('/admin/add-news', methods=['GET', 'POST'])
def add_news():
    """Добавление новости (только для админов)"""
    if 'user' not in session:
        flash('Для добавления новостей необходимо войти в систему', 'error')
        return redirect(url_for('login'))

    user_role = session['user'].get('role')
    if user_role != 'admin':
        flash('У вас недостаточно прав для добавления новостей', 'error')
        return redirect(url_for('home'))
    if request.method == 'POST':
        # 1. Получаем данные
        title = request.form['title'].strip()
        content = request.form['content'].strip()

        # 2. Проверяем
        if not title or not content:
            flash('Нужны заголовок и текст!', 'error')
            return render_template('add_news.html')

        # 3. Получаем категорию "новости"
        news_category = Category.query.filter_by(slug='news').first()
        if not news_category:
            news_category = Category(name='Новости', slug='news')
            db.session.add(news_category)
            db.session.commit()

        # 4. Обрабатываем картинку (если есть)
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:  # если файл выбран
                # Простая проверка
                if file.filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    filename = secure_filename(file.filename)
                    file.save('static/uploads/news/' + filename)
                    image_path = 'uploads/news/' + filename

        # 5. Сохраняем
        new_news = Content(
            title=title,
            content=content,
            category_id=news_category.id,
            author_id=session['user']['id'],  # автор = текущий пользователь
            is_published=True,
            image_path=image_path
        )

        db.session.add(new_news)
        db.session.commit()

        flash('Новость добавлена!', 'success')
        return redirect(url_for('news_list'))

    return render_template('add_news.html')

@app.route('/svedeniya')
def svedeniya():
    """Сведения об образовательной организации"""
    return render_template('svedeniya.html')

@app.route('/faculties')
def faculties():
    """Факультеты"""
    return render_template('faculties.html')


@app.route('/education')
def education():
    """Образование"""
    return render_template('education.html')


@app.route('/documents')
def documents():
    """Документы"""
    return render_template('documents.html')


@app.route('/admission')
def admission():
    """Подача заявки на поступление"""
    return render_template('admission.html')


@app.route('/submit_admission', methods=['POST'])
def submit_admission():
    """Обработка заявки на поступление"""
    if request.method == 'POST':
        # Здесь будет обработка формы
        flash('Заявка успешно отправлена!', 'success')
        return redirect(url_for('admission'))

@app.route('/accessibility')
def accessibility():
    """Страница версии для слабовидящих"""
    return render_template('accessibility.html')

@app.route('/search')
def search():
    """Поиск по новостям"""
    # Получаем поисковый запрос
    query = request.args.get('q', '').strip()

    # Если запрос пустой, показываем все новости
    if not query:
        return redirect(url_for('news_list'))

    # Ищем новости, где есть этот текст
    # Ищем и в заголовке, и в тексте новости
    results = Content.query.filter(
        Content.is_published == True,  # только опубликованные
        db.or_(
            Content.title.ilike(f'%{query}%'),  # ищем в заголовке
            Content.content.ilike(f'%{query}%')  # ищем в тексте
        )
    ).order_by(Content.created_at.desc()).all()

    # Показываем результаты
    return render_template('search_results.html',
                           results=results,
                           query=query,
                           results_count=len(results))

# ========== ИНИЦИАЛИЗАЦИЯ ==========
# Создаём таблицы ПРИ ИМПОРТЕ приложения
with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=True, port=5000)