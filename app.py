import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, Optional
from functools import wraps

# -----------------------------------------------------------
# 1. アプリケーションとデータベースの初期設定
# -----------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_change_in_production')

# データベース設定（環境に応じて切り替え）
if os.environ.get('DATABASE_URL'):
    # 本番環境: PostgreSQL（Render.com等）
    database_url = os.environ.get('DATABASE_URL')
    # PostgreSQLドライバーの指定（psycopg3を使用）
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # 開発環境: SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# -----------------------------------------------------------
# 2. データベースモデルの定義
# -----------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='staff')
    is_first_login = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    skills = db.relationship('UserSkill', backref='user', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    order_index = db.Column(db.Integer, default=0)

class UserSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    can_do = db.Column(db.Boolean, default=False)
    task = db.relationship('Task')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------------------------------------
# 3. フォームの定義
# -----------------------------------------------------------
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

class AddUserForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    confirm_password = PasswordField('パスワード(確認)', validators=[DataRequired(), EqualTo('password', message='パスワードが一致しません。')])
    role = SelectField('権限', choices=[('staff', 'スタッフ'), ('admin', '管理者')])
    submit = SubmitField('ユーザーを追加')

# ★★★ ここから新しいフォームを追加 ★★★
class EditUserForm(FlaskForm):
    username = StringField('ユーザー名', render_kw={'readonly': True})
    # Optional() を使うことで、パスワード欄が空でもOKになる
    password = PasswordField('新しいパスワード (変更する場合のみ入力)', validators=[Optional(), EqualTo('confirm_password', message='パスワードが一致しません。')])
    confirm_password = PasswordField('新しいパスワード(確認)')
    role = SelectField('権限', choices=[('staff', 'スタッフ'), ('admin', '管理者')], validators=[DataRequired()])
    submit = SubmitField('更新する')
# ★★★ ここまで ★★★

class TaskForm(FlaskForm):
    name = StringField('仕事内容', validators=[DataRequired(), Length(max=120)])
    submit = SubmitField('保存する')

class SettingsForm(FlaskForm):
    skill_visibility = SelectField('スキル表示設定', 
                                   choices=[('restricted', 'スタッフは自分のスキルのみ表示'), 
                                           ('all', '全スタッフが互いのスキルを表示')],
                                   validators=[DataRequired()])
    submit = SubmitField('設定を保存')


# -----------------------------------------------------------
# 4. ルーティング (URLと関数の紐付け)
# -----------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.is_first_login:
                return redirect(url_for('initial_setup'))
            return redirect(url_for('dashboard'))
        else:
            flash('ユーザー名またはパスワードが正しくありません。')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。')
    return redirect(url_for('login'))

@app.route('/initial_setup', methods=['GET', 'POST'])
@login_required
def initial_setup():
    if not current_user.is_first_login:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        tasks = Task.query.order_by(Task.order_index, Task.id).all()
        for task in tasks:
            can_do = request.form.get(f'task_{task.id}') == 'on'
            skill = UserSkill(user_id=current_user.id, task_id=task.id, can_do=can_do)
            db.session.add(skill)
        current_user.is_first_login = False
        db.session.commit()
        flash('スキルを登録しました！')
        return redirect(url_for('dashboard'))
    tasks = Task.query.order_by(Task.order_index, Task.id).all()
    return render_template('initial_setup.html', tasks=tasks)

@app.route('/dashboard')
@login_required
def dashboard():
    # スキル表示設定を取得
    skill_visibility_setting = Settings.query.filter_by(key='skill_visibility').first()
    is_restricted = skill_visibility_setting and skill_visibility_setting.value == 'restricted'
    
    # ユーザー一覧を取得
    users = User.query.filter(User.username != 'admin').order_by(User.order_index, User.id).all()
    
    # スキル表示制限がある場合、スタッフは自分のみ表示
    if is_restricted and current_user.role != 'admin':
        users = [user for user in users if user.id == current_user.id]
    
    tasks = Task.query.order_by(Task.order_index, Task.id).all()
    skill_data = {}
    for user in users:
        skill_data[user.id] = {skill.task_id: skill.can_do for skill in user.skills}
    
    return render_template('dashboard.html', users=users, tasks=tasks, skill_data=skill_data, is_restricted=is_restricted)

# -----------------------------------------------------------
# 5. 管理者用ページ
# -----------------------------------------------------------
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('このページにアクセスする権限がありません。')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    form = AddUserForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('そのユーザー名は既に使用されています。')
        else:
            # 新しいユーザーのorder_indexを最大値+1に設定
            max_order = db.session.query(db.func.max(User.order_index)).scalar() or 0
            new_user = User(username=form.username.data, role=form.role.data, order_index=max_order + 1)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash(f'ユーザー「{new_user.username}」を追加しました。')
            return redirect(url_for('manage_users'))
    users = User.query.order_by(User.order_index, User.id).all()
    return render_template('admin_users.html', users=users, form=form)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('自分自身を削除することはできません。')
        return redirect(url_for('manage_users'))
    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f'ユーザー「{user_to_delete.username}」を削除しました。')
    return redirect(url_for('manage_users'))

# ★★★ この関数をapp.pyに追加してください ★★★
@app.route('/admin/edit_skills/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_skills(user_id):
    user_to_edit = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # 全てのタスクを取得
        tasks = Task.query.order_by(Task.order_index, Task.id).all()
        
        # ユーザーがまだスキル登録していない場合、新規作成
        if not user_to_edit.skills:
            for task in tasks:
                can_do = request.form.get(f'task_{task.id}') == 'on'
                skill = UserSkill(user_id=user_id, task_id=task.id, can_do=can_do)
                db.session.add(skill)
        else:
            # 既存のスキルIDを取得
            existing_task_ids = {skill.task_id for skill in user_to_edit.skills}
            
            # 既存のスキル情報を更新
            for skill in user_to_edit.skills:
                can_do = request.form.get(f'task_{skill.task_id}') == 'on'
                skill.can_do = can_do
            
            # 新しく追加されたタスクがあれば、新規スキルエントリを作成
            for task in tasks:
                if task.id not in existing_task_ids:
                    can_do = request.form.get(f'task_{task.id}') == 'on'
                    skill = UserSkill(user_id=user_id, task_id=task.id, can_do=can_do)
                    db.session.add(skill)
        
        db.session.commit()
        flash(f'「{user_to_edit.username}」さんのスキルを更新しました。')
        return redirect(url_for('dashboard'))

    # 全てのタスクを取得
    all_tasks = Task.query.order_by(Task.order_index, Task.id).all()
    
    # ユーザーの既存スキルを辞書形式で取得
    existing_skills = {skill.task_id: skill for skill in user_to_edit.skills}
    
    # 表示用のスキル一覧を作成（既存スキル + 新規タスク）
    skills_to_edit = []
    for task in all_tasks:
        if task.id in existing_skills:
            skills_to_edit.append(existing_skills[task.id])
        else:
            # 新規タスクの場合、仮のスキルデータを作成
            skills_to_edit.append(UserSkill(user_id=user_id, task_id=task.id, can_do=False, task=task))

    return render_template('edit_skills.html', user_to_edit=user_to_edit, skills_to_edit=skills_to_edit)

@app.route('/my_skills', methods=['GET', 'POST'])
@login_required
def my_skills():
    if request.method == 'POST':
        # 全てのタスクを取得
        tasks = Task.query.order_by(Task.order_index, Task.id).all()
        
        # ユーザーがまだスキル登録していない場合、新規作成
        if not current_user.skills:
            for task in tasks:
                can_do = request.form.get(f'task_{task.id}') == 'on'
                skill = UserSkill(user_id=current_user.id, task_id=task.id, can_do=can_do)
                db.session.add(skill)
        else:
            # 既存のスキルIDを取得
            existing_task_ids = {skill.task_id for skill in current_user.skills}
            
            # 既存のスキル情報を更新
            for skill in current_user.skills:
                can_do = request.form.get(f'task_{skill.task_id}') == 'on'
                skill.can_do = can_do
            
            # 新しく追加されたタスクがあれば、新規スキルエントリを作成
            for task in tasks:
                if task.id not in existing_task_ids:
                    can_do = request.form.get(f'task_{task.id}') == 'on'
                    skill = UserSkill(user_id=current_user.id, task_id=task.id, can_do=can_do)
                    db.session.add(skill)
        
        db.session.commit()
        flash(f'スキル情報を更新しました。')
        return redirect(url_for('dashboard'))

    # 全てのタスクを取得
    all_tasks = Task.query.order_by(Task.order_index, Task.id).all()
    
    # ユーザーの既存スキルを辞書形式で取得
    existing_skills = {skill.task_id: skill for skill in current_user.skills}
    
    # 表示用のスキル一覧を作成（既存スキル + 新規タスク）
    skills_to_edit = []
    for task in all_tasks:
        if task.id in existing_skills:
            skills_to_edit.append(existing_skills[task.id])
        else:
            # 新規タスクの場合、仮のスキルデータを作成
            skills_to_edit.append(UserSkill(user_id=current_user.id, task_id=task.id, can_do=False, task=task))

    return render_template('my_skills.html', user_to_edit=current_user, skills_to_edit=skills_to_edit)

# ★★★ ここから新しい関数を追加 ★★★
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    # フォームにユーザーの既存データを渡して表示する
    form = EditUserForm(obj=user_to_edit)

    if form.validate_on_submit():
        # 最後の管理者をスタッフに変更しようとしていないかチェック
        if user_to_edit.role == 'admin' and form.role.data == 'staff':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                flash('最後の管理者をスタッフに変更することはできません。')
                return redirect(url_for('manage_users'))
        
        # 権限を更新
        user_to_edit.role = form.role.data
        
        # パスワード欄に入力があった場合のみ、パスワードを更新
        if form.password.data:
            user_to_edit.set_password(form.password.data)
        
        db.session.commit()
        flash(f'ユーザー「{user_to_edit.username}」の情報を更新しました。')
        return redirect(url_for('manage_users'))

    # GETリクエストのとき、フォームのパスワード欄はクリアしておく
    form.password.data = ""
    form.confirm_password.data = ""
    
    return render_template('admin_edit_user.html', form=form, user_to_edit=user_to_edit)
# ★★★ ここまで ★★★

@app.route('/admin/reorder_users', methods=['POST'])
@admin_required
def reorder_users():
    user_ids = request.json.get('user_ids', [])
    
    if not user_ids:
        return jsonify({'success': False, 'message': 'ユーザーIDが提供されていません。'})
    
    try:
        for index, user_id in enumerate(user_ids):
            user = User.query.get(user_id)
            if user:
                user.order_index = index
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'ユーザーの順序を更新しました。'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'エラーが発生しました: {str(e)}'})

@app.route('/admin/move_user/<int:user_id>/<direction>')
@admin_required
def move_user(user_id, direction):
    user = User.query.get_or_404(user_id)
    users = User.query.order_by(User.order_index, User.id).all()
    
    current_index = next(i for i, u in enumerate(users) if u.id == user_id)
    
    if direction == 'up' and current_index > 0:
        # 上に移動
        users[current_index], users[current_index - 1] = users[current_index - 1], users[current_index]
    elif direction == 'down' and current_index < len(users) - 1:
        # 下に移動
        users[current_index], users[current_index + 1] = users[current_index + 1], users[current_index]
    
    # 新しい順序を保存
    for index, user in enumerate(users):
        user.order_index = index
    
    db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/admin/tasks', methods=['GET', 'POST'])
@app.route('/admin/tasks/<int:task_id>', methods=['GET', 'POST'])
@admin_required
def manage_tasks(task_id=None):
    task_to_edit = Task.query.get(task_id) if task_id else None
    form = TaskForm(obj=task_to_edit)
    if form.validate_on_submit():
        existing_task = Task.query.filter(Task.name == form.name.data, Task.id != task_id).first()
        if existing_task:
            flash('その仕事は既に存在します。')
        else:
            if task_to_edit:
                task_to_edit.name = form.name.data
                flash(f'仕事「{task_to_edit.name}」を更新しました。')
            else:
                # 新しいタスクのorder_indexを最大値+1に設定
                max_order = db.session.query(db.func.max(Task.order_index)).scalar() or 0
                new_task = Task(name=form.name.data, order_index=max_order + 1)
                db.session.add(new_task)
                db.session.flush()  # new_taskのIDを取得するため
                
                # 新しいタスクを既存の全ユーザーに追加
                users = User.query.all()
                for user in users:
                    skill = UserSkill(user_id=user.id, task_id=new_task.id, can_do=False)
                    db.session.add(skill)
                
                flash(f'仕事「{new_task.name}」を追加しました。')
            db.session.commit()
            return redirect(url_for('manage_tasks'))
    tasks = Task.query.order_by(Task.order_index, Task.id).all()
    return render_template('admin_tasks.html', tasks=tasks, form=form)

@app.route('/admin/skill_stats')
@admin_required
def skill_stats():
    """スキル習得率統計ページ（管理者専用）"""
    # 'admin'ユーザー以外のユーザーと全タスクを取得
    users = User.query.filter(User.username != 'admin').all()
    tasks = Task.query.order_by(Task.order_index, Task.id).all()
    
    # スキル習得率を計算
    skill_statistics = []
    total_users = len(users)
    
    for task in tasks:
        if total_users > 0:
            # このタスクができるユーザー数を計算（'admin'ユーザーを除外）
            skilled_users = UserSkill.query.join(User).filter(
                UserSkill.task_id == task.id,
                UserSkill.can_do == True,
                User.username != 'admin'
            ).all()
            skilled_count = len(skilled_users)
            
            # 習得率を計算
            mastery_rate = (skilled_count / total_users) * 100
            
            # 習得者の名前を取得
            skilled_user_names = [User.query.get(skill.user_id).username for skill in skilled_users]
            
            skill_statistics.append({
                'task': task,
                'skilled_count': skilled_count,
                'total_count': total_users,
                'mastery_rate': round(mastery_rate, 1),
                'skilled_users': skilled_user_names
            })
        else:
            skill_statistics.append({
                'task': task,
                'skilled_count': 0,
                'total_count': 0,
                'mastery_rate': 0,
                'skilled_users': []
            })
    
    return render_template('admin_skill_stats.html', 
                         skill_statistics=skill_statistics,
                         total_users=total_users)

@app.route('/admin/reorder_tasks', methods=['POST'])
@admin_required
def reorder_tasks():
    task_ids = request.json.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'success': False, 'message': 'タスクIDが提供されていません。'})
    
    try:
        for index, task_id in enumerate(task_ids):
            task = Task.query.get(task_id)
            if task:
                task.order_index = index
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'タスクの順序を更新しました。'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'エラーが発生しました: {str(e)}'})

@app.route('/admin/delete_task/<int:task_id>', methods=['POST'])
@admin_required
def delete_task(task_id):
    task_to_delete = Task.query.get_or_404(task_id)
    
    # 関連するUserSkillエントリを削除
    UserSkill.query.filter_by(task_id=task_id).delete()
    
    db.session.delete(task_to_delete)
    db.session.commit()
    flash(f'仕事「{task_to_delete.name}」を削除しました。')
    return redirect(url_for('manage_tasks'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    form = SettingsForm()
    
    if form.validate_on_submit():
        # スキル表示設定を更新
        skill_visibility_setting = Settings.query.filter_by(key='skill_visibility').first()
        if skill_visibility_setting:
            skill_visibility_setting.value = form.skill_visibility.data
        else:
            skill_visibility_setting = Settings(key='skill_visibility', value=form.skill_visibility.data)
            db.session.add(skill_visibility_setting)
        
        db.session.commit()
        flash('設定を更新しました。')
        return redirect(url_for('admin_settings'))
    
    # 現在の設定を取得してフォームに反映
    skill_visibility_setting = Settings.query.filter_by(key='skill_visibility').first()
    if skill_visibility_setting:
        form.skill_visibility.data = skill_visibility_setting.value
    else:
        form.skill_visibility.data = 'restricted'  # デフォルト値
    
    return render_template('admin_settings.html', form=form)

@app.route('/admin/migrate_data', methods=['POST'])
@admin_required
def migrate_data():
    """データ移行エンドポイント"""
    try:
        # データベースからデータを取得
        import json
        
        # 全データを取得
        users_data = []
        for user in User.query.all():
            users_data.append({
                'id': user.id,
                'username': user.username,
                'password_hash': user.password_hash,
                'role': user.role,
                'is_first_login': user.is_first_login,
                'order_index': user.order_index
            })
        
        tasks_data = []
        for task in Task.query.all():
            tasks_data.append({
                'id': task.id,
                'name': task.name,
                'order_index': task.order_index
            })
        
        user_skills_data = []
        for skill in UserSkill.query.all():
            user_skills_data.append({
                'id': skill.id,
                'user_id': skill.user_id,
                'task_id': skill.task_id,
                'can_do': skill.can_do
            })
        
        settings_data = []
        for setting in Settings.query.all():
            settings_data.append({
                'id': setting.id,
                'key': setting.key,
                'value': setting.value
            })
        
        # JSONデータを作成
        migration_data = {
            'users': users_data,
            'tasks': tasks_data,
            'user_skills': user_skills_data,
            'settings': settings_data
        }
        
        # Supabaseに移行（この部分は実際のSupabase設定に応じて調整）
        if os.environ.get('DATABASE_URL') and 'supabase.com' in os.environ.get('DATABASE_URL', ''):
            # 既にSupabase環境の場合
            flash('現在のデータベースは既にSupabaseです。移行は不要です。')
        else:
            # 移行データをJSONファイルとして保存（手動移行用）
            with open('migration_data.json', 'w', encoding='utf-8') as f:
                json.dump(migration_data, f, ensure_ascii=False, indent=2)
            
            flash(f'データ移行の準備が完了しました。移行データ: ユーザー {len(users_data)}件、タスク {len(tasks_data)}件、スキル {len(user_skills_data)}件')
        
        return redirect(url_for('admin_settings'))
        
    except Exception as e:
        flash(f'データ移行エラー: {str(e)}')
        return redirect(url_for('admin_settings'))


# -----------------------------------------------------------
# 6. アプリケーションの実行と初期設定
# -----------------------------------------------------------
def init_database():
    """データベースを初期化する関数"""
    try:
        # データベーステーブルを作成（既存テーブルは保持）
        db.create_all()
        
        # 管理者ユーザーを作成（存在しない場合のみ）
        if not User.query.filter_by(username='admin').first():
            print("Creating admin user...")
            admin_user = User(username='admin', role='admin', is_first_login=False)
            admin_user.set_password('password')
            db.session.add(admin_user)
        
        # 既存タスクのorder_indexを修正（NULLの場合）
        try:
            tasks_without_order = Task.query.filter((Task.order_index.is_(None)) | (Task.order_index == 0)).all()
            if tasks_without_order:
                print(f"Updating order_index for {len(tasks_without_order)} tasks...")
                for index, task in enumerate(tasks_without_order):
                    task.order_index = index + 1
        except Exception as e:
            print(f"Note: order_index update skipped: {e}")
        
        
        # 設定を初期化（存在しない場合のみ）
        if not Settings.query.filter_by(key='skill_visibility').first():
            print("Creating initial settings...")
            skill_visibility_setting = Settings(key='skill_visibility', value='restricted')
            db.session.add(skill_visibility_setting)
        
        db.session.commit()
        print("Database initialized.")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        db.session.rollback()

def create_sample_data():
    """サンプルデータを作成する関数"""
    if Task.query.count() == 0:
        print("Creating sample tasks...")
        sample_tasks = ['レジ打ち', '品出し', '清掃', '発注作業', 'クレーム対応', '在庫管理', '接客']
        for index, task_name in enumerate(sample_tasks):
            task = Task(name=task_name, order_index=index)
            db.session.add(task)
        
        # サンプルスタッフユーザーを作成
        if User.query.filter_by(role='staff').count() == 0:
            print("Creating sample staff users...")
            sample_users = [
                {'username': 'yamada', 'role': 'staff'},
                {'username': 'sato', 'role': 'staff'},
                {'username': 'tanaka', 'role': 'staff'}
            ]
            
            for user_data in sample_users:
                user = User(
                    username=user_data['username'], 
                    role=user_data['role'],
                    is_first_login=False,
                    order_index=User.query.count()
                )
                user.set_password('password123')  # サンプル用パスワード
                db.session.add(user)
        
        db.session.commit()
        print("Sample data created.")

if __name__ == '__main__':
    print("🚀 アプリケーションを起動しています...")
    
    try:
        with app.app_context():
            # 環境変数でサンプルデータ作成を制御
            if os.environ.get('SKIP_DB_INIT') != 'true':
                print("📊 データベース初期化中...")
                init_database()
                
                # Supabase接続テスト（簡素化）
                if os.environ.get('DATABASE_URL') and 'supabase.com' in os.environ.get('DATABASE_URL', ''):
                    print("✅ Supabase環境を検出しました")
                    try:
                        user_count = User.query.count()
                        print(f"✅ Supabase接続成功！ユーザー: {user_count}件")
                    except Exception as e:
                        print(f"⚠️ Supabase接続テストをスキップ: {e}")
                
                # 開発環境でサンプルデータを作成
                if os.environ.get('CREATE_SAMPLE_DATA') == 'true' or not os.environ.get('DATABASE_URL'):
                    create_sample_data()
            else:
                print("Database initialization skipped.")
    except Exception as e:
        print(f"⚠️ 初期化エラー（続行します）: {e}")
            
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    print(f"🌐 サーバーを起動中... ポート: {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)