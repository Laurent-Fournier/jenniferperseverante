import os
import smtplib
from html import escape

import joblib
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory, LangDetectException

from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .models import Message


load_dotenv()

DetectorFactory.seed = 0

BLOCKED_LANGUAGES = {"ru", "hu", "et", "pl", "id"}


# ----------------------
# Add contact message
# ----------------------
@ratelimit(key="ip", rate="3/m", method="POST", block=True)
def add_contact(request, lg):

    if request.method != "POST":
        return redirect(
            reverse(
                "article_detail",
                kwargs={"lg": lg, "slug": ""},
            )
        )

    # URL de la page depuis laquelle le formulaire a été envoyé
    url = request.build_absolute_uri()

    # Read parameters
    user_agent = request.headers.get("User-Agent", "")
    msg_name = request.POST.get("name", "").strip()
    msg_email = request.POST.get("email", "").strip()
    msg_subject = request.POST.get("subject", "").strip()
    msg_text = request.POST.get("message", "").strip()

    article_id = request.POST.get("art_id")
    article_slug = request.POST.get("art_slug", "").strip()

    # -----------------------------------------
    # Predict spam status
    # -----------------------------------------
    models, vectorizers = load_models_and_vectorizers()

    full_text = f"{msg_name} {msg_email} {msg_subject} {msg_text}"
    lang = detect_language(full_text)

    calc_spam = False

    if lang in BLOCKED_LANGUAGES:
        calc_spam = True

    elif lang in models and lang in vectorizers:
        vec = vectorizers[lang]
        X_new = vec.transform([full_text])
        prediction = models[lang].predict(X_new)
        calc_spam = bool(prediction[0])

    elif models:
        # Fallback vers le premier modèle disponible
        fallback_lang = next(iter(models.keys()))

        if fallback_lang in vectorizers:
            vec = vectorizers[fallback_lang]
            X_new = vec.transform([full_text])
            prediction = models[fallback_lang].predict(X_new)
            calc_spam = bool(prediction[0])

    # -----------------------------------------
    # Envoi de l'e-mail uniquement si non spam
    # -----------------------------------------
    response_status = "not_sent"
    response_message = ""

    if not calc_spam:
        now = timezone.now()

        # Échappement des données utilisateur pour le HTML
        html_content = get_html_content(
            url, user_agent, now, lg, lang, msg_name, msg_email, msg_subject, msg_text
        )

        text_content = (
            f"URL : {url}\n"
            f"User agent : {user_agent}\n"
            f"Date : {now}\n"
            f"Langue : {lg}\n"
            f"Langue détectée : {lang}\n"
            f"Nom : {msg_name}\n"
            f"Email : {msg_email}\n"
            f"Sujet : {msg_subject}\n"
            "\n"
            "----------------------------------------\n"
            f"Message :\n{msg_text}"
        )

        email_subject = (
            "Formulaire de contact du site Transbeauté "
            f"[{os.getenv('ENVIRONMENT', 'unknown')}]"
        )

        email_from = os.getenv("CONTACT_FROM", "")

        email_to = [
            email.strip()
            for email in os.getenv("CONTACT_RECIPIENTS", "").split(",")
            if email.strip()
        ]

        try:
            send_email(
                email_subject=email_subject,
                email_from=email_from,
                email_to=email_to,
                text_content=text_content,
                html_content=html_content,
            )

            response_status = "sent"
            response_message = "Email envoyé avec succès."

        except Exception as exc:
            response_status = "error"
            response_message = str(exc)

    else:
        response_status = "spam"
        response_message = "Message détecté comme spam."

    # -----------------------------------------
    # Save message in database
    # -----------------------------------------
    contact_message = Message(
        datetime=timezone.now(),
        calc_spam=calc_spam,
        calc_lg=lang,
        msg_name=msg_name,
        msg_email=msg_email,
        msg_subject=msg_subject,
        msg_text=msg_text,
        language_code=lg,
        msg_url=url,
        response_status=response_status,
        response_message=response_message,
        user_agent=user_agent,
    )

    contact_message.save()

    # -----------------------------------------
    # Redirect
    # -----------------------------------------
    url = reverse(
        "article_detail",
        kwargs={
            "lg": lg,
            "slug": article_slug,
        },
    )

    return redirect(f"{url}?message=contact_added")


def load_models_and_vectorizers():
    models = {}
    vectorizers = {}

    output_dir = os.getenv("OUTPUT_DIR")

    if not output_dir or not os.path.isdir(output_dir):
        return models, vectorizers

    for file in os.listdir(output_dir):
        if file.startswith("spam_classifier_") and file.endswith(".joblib"):
            lang = file[len("spam_classifier_") : -len(".joblib")]

            model_path = os.path.join(output_dir, file)

            vectorizer_path = os.path.join(
                output_dir,
                f"tfidf_vectorizer_{lang}.joblib",
            )

            if not os.path.isfile(vectorizer_path):
                continue

            models[lang] = joblib.load(model_path)
            vectorizers[lang] = joblib.load(vectorizer_path)

    return models, vectorizers


def detect_language(text: str) -> str:
    text = text.strip()

    if not text:
        return "en"

    try:
        return detect(text)

    except LangDetectException:
        return "en"


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def send_email(
    email_subject,
    email_from,
    email_to,
    text_content,
    html_content,
):
    """
    Construit et envoie un email avec une version texte
    et une version HTML.

    La connexion SMTP utilise SMTP_SERVER et SMTP_PORT
    définis dans le fichier .env.
    """

    if not email_from:
        raise ValueError("CONTACT_FROM n'est pas configuré.")

    if not email_to:
        raise ValueError("CONTACT_RECIPIENTS n'est pas configuré.")

    # -----------------------------------------
    # Récupération de la configuration SMTP
    # -----------------------------------------
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")

    if not smtp_server:
        raise ValueError("SMTP_SERVER n'est pas configuré.")

    if not smtp_port:
        raise ValueError("SMTP_PORT n'est pas configuré.")

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        raise ValueError("SMTP_PORT doit être un nombre entier.")

    # -----------------------------------------
    # Construction du message
    # -----------------------------------------
    email = EmailMultiAlternatives(
        subject=email_subject,
        body=text_content,
        from_email=email_from,
        to=email_to,
    )

    email.attach_alternative(
        html_content,
        "text/html",
    )

    # -----------------------------------------
    # Connexion SMTP
    # -----------------------------------------
    with smtplib.SMTP(
        smtp_server,
        smtp_port,
        timeout=30,
    ) as server:
        # STARTTLS
        server.starttls()

        # Envoi du message
        server.send_message(email.message())


def get_html_content(
    url, user_agent, now, lg, lang, msg_name, msg_email, msg_subject, msg_text
):
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
    margin: 0;
    padding: 20px;
    background-color: #f5f7f9;
    font-family: Arial, Helvetica, sans-serif;
    color: #333333;
">

    <table
        role="presentation"
        width="100%"
        cellpadding="0"
        cellspacing="0"
        border="0"
        style="max-width: 700px; margin: 0 auto;"
    >
        <tr>
            <td>

                <!-- Conteneur principal -->
                <table
                    role="presentation"
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    border="0"
                    style="
                        background-color: #ffffff;
                        border: 1px solid #e1e5e8;
                        border-radius: 8px;
                        overflow: hidden;
                    "
                >

                    <!-- En-tête -->
                    <tr>
                        <td style="
                            background-color: #e0a869;
                            padding: 24px 28px;
                            color: #ffffff;
                        ">
                            <div style="
                                font-size: 13px;
                                text-transform: uppercase;
                                letter-spacing: 1px;
                                opacity: 0.9;
                            ">
                                Transbeauté
                            </div>

                            <div style="
                                margin-top: 6px;
                                font-size: 24px;
                                font-weight: bold;
                            ">
                                Nouveau message de contact
                            </div>
                        </td>
                    </tr>

                    <!-- Contenu -->
                    <tr>
                        <td style="padding: 28px;">

                            <!-- Informations -->
                            <table
                                role="presentation"
                                width="100%"
                                cellpadding="0"
                                cellspacing="0"
                                border="0"
                            >
                                <tr>
                                    <td colspan="2" style="
                                        padding-bottom: 15px;
                                        font-size: 17px;
                                        font-weight: bold;
                                        color: #e0a869;
                                    ">
                                        Informations du contact
                                    </td>
                                </tr>

                                <tr>
                                    <td style="
                                        width: 150px;
                                        padding: 9px 0;
                                        color: #777777;
                                        font-size: 14px;
                                    ">
                                        Nom
                                    </td>
                                    <td style="
                                        padding: 9px 0;
                                        font-size: 15px;
                                        font-weight: 600;
                                    ">
                                        {escape(msg_name)}
                                    </td>
                                </tr>

                                <tr>
                                    <td style="
                                        padding: 9px 0;
                                        color: #777777;
                                        font-size: 14px;
                                        border-top: 1px solid #eeeeee;
                                    ">
                                        Email
                                    </td>
                                    <td style="
                                        padding: 9px 0;
                                        border-top: 1px solid #eeeeee;
                                        font-size: 15px;
                                    ">
                                        <a
                                            href="mailto:{escape(msg_email)}"
                                            style="
                                                color: #e0a869;
                                                text-decoration: none;
                                            "
                                        >
                                            {escape(msg_email)}
                                        </a>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="
                                        padding: 9px 0;
                                        color: #777777;
                                        font-size: 14px;
                                        border-top: 1px solid #eeeeee;
                                    ">
                                        Sujet
                                    </td>
                                    <td style="
                                        padding: 9px 0;
                                        border-top: 1px solid #eeeeee;
                                        font-size: 15px;
                                    ">
                                        {escape(msg_subject)}
                                    </td>
                                </tr>

                                <tr>
                                    <td style="
                                        padding: 9px 0;
                                        color: #777777;
                                        font-size: 14px;
                                        border-top: 1px solid #eeeeee;
                                    ">
                                        Langue
                                    </td>
                                    <td style="
                                        padding: 9px 0;
                                        border-top: 1px solid #eeeeee;
                                        font-size: 15px;
                                    ">
                                        {escape(lg)}
                                        <span style="
                                            color: #888888;
                                            font-size: 13px;
                                        ">
                                            (détectée : {escape(lang)})
                                        </span>
                                    </td>
                                </tr>
                            </table>

                            <!-- Séparation -->
                            <div style="
                                height: 1px;
                                background-color: #e5e7eb;
                                margin: 28px 0;
                            "></div>

                            <!-- Message -->
                            <div style="
                                font-size: 17px;
                                font-weight: bold;
                                color: #e0a869;
                                margin-bottom: 12px;
                            ">
                                Message
                            </div>

                            <div style="
                                background-color: #f8faf9;
                                border-left: 4px solid #e0a869;
                                padding: 18px 20px;
                                font-size: 15px;
                                line-height: 1.6;
                                color: #333333;
                            ">
                                {escape(msg_text).replace(chr(10), "<br>")}
                            </div>

                            <!-- Informations techniques -->
                            <div style="
                                margin-top: 28px;
                                padding-top: 20px;
                                border-top: 1px solid #e5e7eb;
                            ">

                                <div style="
                                    font-size: 14px;
                                    font-weight: bold;
                                    color: #666666;
                                    margin-bottom: 10px;
                                ">
                                    Informations techniques
                                </div>

                                <div style="
                                    background-color: #f5f7f9;
                                    padding: 14px 16px;
                                    border-radius: 5px;
                                    font-size: 12px;
                                    line-height: 1.6;
                                    color: #777777;
                                    word-break: break-word;
                                ">
                                    <strong>URL :</strong>
                                    {escape(url)}
                                    <br>

                                    <strong>Date :</strong>
                                    {escape(str(now))}
                                    <br>

                                    <strong>User agent :</strong>
                                    {escape(user_agent)}
                                </div>

                            </div>

                        </td>
                    </tr>

                    <!-- Pied de page -->
                    <tr>
                        <td style="
                            padding: 16px 28px;
                            background-color: #f8faf9;
                            border-top: 1px solid #e5e7eb;
                            text-align: center;
                            font-size: 12px;
                            color: #999999;
                        ">
                            Message envoyé depuis le formulaire de contact
                            de Transbeauté.
                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>

</body>
</html>
"""
