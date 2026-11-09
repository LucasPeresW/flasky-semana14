import requests
from threading import Thread

from flask import current_app

from .models import salvar_email


def send_async_email(
    app,
    recipients,
    subject,
    html_content
):
    with app.app_context():

        api_key = app.config['API_KEY']
        api_url = app.config['API_URL']
        api_from = app.config['API_FROM']

        for recipient in recipients:

            if not recipient:
                continue

            try:
                response = requests.post(
                    api_url,
                    auth=('api', api_key),
                    data={
                        'from': api_from,
                        'to': [recipient],
                        'subject': subject,
                        'html': html_content
                    }
                )

                print(
                    f'[Mailgun] Envio para {recipient} - '
                    f'Status: {response.status_code}'
                )

                if response.status_code < 400:
                    print(
                        f'[Mailgun] E-mail enviado para {recipient}'
                    )
                else:
                    print(
                        f'[Mailgun] Resposta: {response.text}'
                    )

            except Exception as e:
                print(
                    f'[Mailgun] Erro ao enviar para '
                    f'{recipient}: {e}'
                )


def send_email(
    subject,
    new_username,
    additional_email
):
    app = current_app._get_current_object()

    recipients = [
        app.config['FLASKY_ADMIN'],
        app.config['MY_INSTITUTIONAL_EMAIL'],
        additional_email
    ]

    full_subject = (
        app.config['FLASKY_MAIL_SUBJECT_PREFIX']
        + ' '
        + subject
    )

    email_text = (
        'Novo usuário cadastrado: '
        + new_username
    )

    html_content = f"""
    <h3>Novo Usuário Cadastrado</h3>

    <p>
        <b>Prontuário:</b>
        {app.config['STUDENT_ID']}
    </p>

    <p>
        <b>Nome do aluno:</b>
        {app.config['STUDENT_NAME']}
    </p>

    <p>
        <b>Novo usuário cadastrado:</b>
        {new_username}
    </p>
    """

    salvar_email(
        de=new_username,
        destinatarios=recipients,
        assunto=full_subject,
        texto=email_text
    )

    thread = Thread(
        target=send_async_email,
        args=[
            app,
            recipients,
            full_subject,
            html_content
        ]
    )

    thread.start()

    return thread

def send_password_reset_email(recipient, reset_url):
    app = current_app._get_current_object()

    subject = (
        app.config['FLASKY_MAIL_SUBJECT_PREFIX']
        + ' Recuperação de senha'
    )

    html_content = f"""
    <h3>Recuperação de senha</h3>

    <p>Recebemos uma solicitação para redefinir sua senha.</p>

    <p>Para cadastrar uma nova senha, acesse:</p>

    <p>
        <a href="{reset_url}">
            Redefinir minha senha
        </a>
    </p>

    <p>Se o botão não funcionar, copie este endereço:</p>

    <p>{reset_url}</p>

    <p>Este link expira em uma hora.</p>

    <p>Se você não solicitou essa alteração, ignore este e-mail.</p>
    """

    salvar_email(
        de='Flasky',
        destinatarios=[recipient],
        assunto=subject,
        texto=f'Link para redefinir a senha: {reset_url}'
    )

    thread = Thread(
        target=send_async_email,
        args=[
            app,
            [recipient],
            subject,
            html_content
        ]
    )

    thread.start()

    return thread