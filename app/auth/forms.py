from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError
)

class LoginForm(FlaskForm):

    email = StringField(
        'E-mail',
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        'Senha',
        validators=[DataRequired()]
    )

    remember_me = BooleanField('Lembrar-me')

    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):

    email = StringField(
        'E-mail',
        validators=[DataRequired(), Email()]
    )

    username = StringField(
        'Nome de usuário',
        validators=[
            DataRequired(),
            Length(1, 64)
        ]
    )

    password = PasswordField(
        'Senha',
        validators=[
            DataRequired(),
            EqualTo('password2', message='As senhas devem ser iguais.')
        ]
    )

    password2 = PasswordField(
        'Confirme sua senha',
        validators=[DataRequired()]
    )

    submit = SubmitField('Cadastrar')

    def validate_email(self, field):
        from app.models import User

        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Este e-mail já está cadastrado.')

    def validate_username(self, field):
        from app.models import User

        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Este nome de usuário já está cadastrado.')

class PasswordResetRequestForm(FlaskForm):

    email = StringField(
        'E-mail',
        validators=[DataRequired(), Email()]
    )

    submit = SubmitField('Recuperar senha')

class PasswordResetForm(FlaskForm):

    password = PasswordField(
        'Nova senha',
        validators=[
            DataRequired(),
            EqualTo('password2', message='As senhas devem ser iguais.')
        ]
    )

    password2 = PasswordField(
        'Confirme a nova senha',
        validators=[DataRequired()]
    )

    submit = SubmitField('Redefinir senha')

class ChangePasswordForm(FlaskForm):

    email = StringField(
        'E-mail',
        validators=[DataRequired(), Email()]
    )

    old_password = PasswordField(
        'Senha atual',
        validators=[DataRequired()]
    )

    password = PasswordField(
        'Nova senha',
        validators=[
            DataRequired(),
            EqualTo('password2', message='As senhas devem ser iguais.')
        ]
    )

    password2 = PasswordField(
        'Confirme a nova senha',
        validators=[DataRequired()]
    )

    submit = SubmitField('Alterar senha')


class ChangeEmailForm(FlaskForm):

    email = StringField(
        'Novo e-mail',
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        'Senha atual',
        validators=[DataRequired()]
    )

    submit = SubmitField('Alterar e-mail')