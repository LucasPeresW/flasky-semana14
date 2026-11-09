from flask import (
    render_template, redirect, url_for, flash, current_app
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)

from . import auth
from .forms import (
    LoginForm,
    RegistrationForm,
    PasswordResetRequestForm,
    PasswordResetForm,
    ChangePasswordForm,
    ChangeEmailForm
)

from app import db
from app.models import User
from itsdangerous import (
    URLSafeTimedSerializer, BadSignature, SignatureExpired
)

from app.email import send_password_reset_email


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            username=form.username.data.strip()
        )

        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        flash('Cadastro realizado com sucesso. Agora você pode entrar.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.index'))

        flash('E-mail ou senha incorretos.')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.')
    return redirect(url_for('main.index'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if form.email.data.lower().strip() != current_user.email:
            flash('O e-mail informado não corresponde à sua conta.')

        elif not current_user.verify_password(form.old_password.data):
            flash('A senha atual está incorreta.')

        else:
            current_user.password = form.password.data
            db.session.commit()

            flash('Senha alterada com sucesso.')
            return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()

    if form.validate_on_submit():
        novo_email = form.email.data.lower().strip()

        if not current_user.verify_password(form.password.data):
            flash('A senha atual está incorreta.')

        elif User.query.filter_by(email=novo_email).first():
            flash('Este e-mail já está cadastrado.')

        else:
            current_user.email = novo_email
            db.session.commit()

            flash('E-mail alterado com sucesso.')
            return redirect(url_for('main.index'))

    return render_template('auth/change_email.html', form=form)

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    form = PasswordResetRequestForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        user = User.query.filter_by(email=email).first()

        if user is not None:
            token = user.generate_reset_token()

            reset_url = url_for(
                'auth.password_reset',
                token=token,
                _external=True
            )

            send_password_reset_email(user.email, reset_url)

        flash(
            'Se esse e-mail estiver cadastrado, '
            'você receberá um link para redefinir sua senha.'
        )

        return redirect(url_for('auth.login'))

    return render_template(
        'auth/password_reset_request.html',
        form=form
    )


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    serializer = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY']
    )

    try:
        data = serializer.loads(
            token,
            salt='password-reset',
            max_age=3600
        )

    except (BadSignature, SignatureExpired):
        flash('O link de recuperação é inválido ou expirou.')
        return redirect(url_for('auth.password_reset_request'))

    user = db.session.get(User, data.get('reset'))

    if user is None:
        flash('Não foi possível localizar essa conta.')
        return redirect(url_for('auth.password_reset_request'))

    form = PasswordResetForm()

    if form.validate_on_submit():
        if user.reset_password(token, form.password.data):
            db.session.commit()

            flash('Sua senha foi redefinida com sucesso.')
            return redirect(url_for('auth.login'))

        flash('Não foi possível redefinir sua senha.')

    return render_template(
        'auth/password_reset.html',
        form=form
    )