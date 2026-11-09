
from flask import render_template, session, redirect, url_for, flash, request
from flask_login import login_required

from . import main
from .forms import NameForm

from app.models import (
    inicializar_banco,
    carregar_usuarios,
    adicionar_usuario,
    carregar_emails,
    editar_usuario,
    excluir_usuario
)

from app.email import send_email


inicializar_banco()


@main.route('/')
def index():
    return render_template('home.html')


@main.route('/painel', methods=['GET', 'POST'])
@login_required
def painel():
    form = NameForm()

    if form.validate_on_submit():
        nome = form.name.data
        novo_usuario = adicionar_usuario(nome)

        if novo_usuario:
            send_email(
                subject='Novo usuário',
                new_username=nome,
                additional_email=form.email.data
            )
            session['name'] = nome
            flash('Usuário cadastrado e e-mails enviados com sucesso.')
        else:
            session['name'] = nome
            flash('Esse usuário já está cadastrado.')

        return redirect(url_for('main.painel'))

    usuarios = carregar_usuarios()

    return render_template(
        'index.html',
        form=form,
        name=session.get('name'),
        usuarios=usuarios
    )


@main.route('/emailsEnviados')
@login_required
def emails_enviados():
    emails = carregar_emails()
    return render_template('emailsEnviados.html', emails=emails)


@main.route('/editar/<nome>', methods=['POST'])
@login_required
def editar(nome):
    novo_nome = request.form.get('novo_nome', '').strip()

    if not novo_nome:
        flash('O nome não pode ficar vazio.')
    elif editar_usuario(nome, novo_nome):
        flash('Usuário editado com sucesso.')
    else:
        flash('Não foi possível editar. Verifique o nome ou as permissões.')

    return redirect(url_for('main.painel'))


@main.route('/excluir/<nome>', methods=['POST'])
@login_required
def excluir(nome):
    if excluir_usuario(nome):
        flash('Usuário excluído com sucesso.')
    else:
        flash('Não foi possível excluir esse usuário.')

    return redirect(url_for('main.painel'))
