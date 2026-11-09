import os
import json
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from . import db
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


BASEDIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')
)

USERS_FILE = os.path.join(BASEDIR, 'usuarios.json')
DATABASE_FILE = os.path.join(BASEDIR, 'emails.db')


def inicializar_banco():
    conexao = sqlite3.connect(DATABASE_FILE)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            de TEXT NOT NULL,
            para TEXT NOT NULL,
            assunto TEXT NOT NULL,
            texto TEXT NOT NULL,
            data_hora TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


def salvar_email(de, destinatarios, assunto, texto):
    conexao = sqlite3.connect(DATABASE_FILE)
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO emails
        (de, para, assunto, texto, data_hora)
        VALUES (?, ?, ?, ?, ?)
    """, (
        de,
        '\n'.join(destinatarios),
        assunto,
        texto,
        datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    ))

    conexao.commit()
    conexao.close()


def carregar_emails():
    conexao = sqlite3.connect(DATABASE_FILE)
    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()
    cursor.execute("""
        SELECT *
        FROM emails
        ORDER BY id DESC
    """)

    emails = cursor.fetchall()
    conexao.close()

    return emails


def carregar_usuarios():
    if not os.path.exists(USERS_FILE):
        usuarios = [
            {
                "nome": "john",
                "funcao": "Administrator"
            }
        ]

        salvar_usuarios(usuarios)
        return usuarios

    with open(USERS_FILE, 'r', encoding='utf-8') as arquivo:
        return json.load(arquivo)


def salvar_usuarios(usuarios):
    with open(USERS_FILE, 'w', encoding='utf-8') as arquivo:
        json.dump(
            usuarios,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def adicionar_usuario(nome):
    usuarios = carregar_usuarios()

    for usuario in usuarios:
        if usuario['nome'].lower() == nome.lower():
            return False

    usuarios.append({
        "nome": nome,
        "funcao": "User"
    })

    salvar_usuarios(usuarios)

    return True

def editar_usuario(nome_atual, novo_nome):
    usuarios = carregar_usuarios()

    # Não permite editar o administrador
    for usuario in usuarios:
        if usuario['nome'].lower() == nome_atual.lower():
            if usuario['funcao'] == 'Administrator':
                return False

    # Verifica se o novo nome já existe
    for usuario in usuarios:
        if usuario['nome'].lower() == novo_nome.lower():
            return False

    # Altera o nome do usuário
    for usuario in usuarios:
        if usuario['nome'].lower() == nome_atual.lower():
            usuario['nome'] = novo_nome
            salvar_usuarios(usuarios)
            return True

    return False


def excluir_usuario(nome):
    usuarios = carregar_usuarios()

    for usuario in usuarios:
        if usuario['nome'].lower() == nome.lower():

            # Não permite excluir o administrador
            if usuario['funcao'] == 'Administrator':
                return False

            usuarios.remove(usuario)
            salvar_usuarios(usuarios)
            return True

    return False

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    users = db.relationship('User', backref='role', lazy='dynamic')


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    @property
    def password(self):
        raise AttributeError('A senha não pode ser lida diretamente.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        serializer = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY']
        )

        return serializer.dumps(
            {'confirm': self.id},
            salt='account-confirm'
        )

    def confirm(self, token, expiration=3600):
        serializer = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY']
        )

        try:
            data = serializer.loads(
                token,
                salt='account-confirm',
                max_age=expiration
            )
        except (BadSignature, SignatureExpired):
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)

        return True

    def generate_reset_token(self, expiration=3600):
        serializer = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY']
        )

        return serializer.dumps(
            {'reset': self.id},
            salt='password-reset'
        )

    def reset_password(self, token, new_password, expiration=3600):
        serializer = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY']
        )

        try:
            data = serializer.loads(
                token,
                salt='password-reset',
                max_age=expiration
            )
        except (BadSignature, SignatureExpired):
            return False

        if data.get('reset') != self.id:
            return False

        self.password = new_password
        db.session.add(self)

        return True