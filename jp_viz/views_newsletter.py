from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.template.loader import get_template, render_to_string
from django.db import connection
from .models import PixelTracking, Subscriber

import smtplib
from email.message import EmailMessage

from io import BytesIO
from PIL import Image, ImageDraw


signer = TimestampSigner()


@require_GET
def tracking_pixel(request, token):
    # Récupère l'envoi d'email correspondant
    # try:
    #     # email_sent = Envoi.objects.get(
    #     #     email_destinataire__iexact=subscriber_id,
    #     #     id_article=article_id
    #     # )
    # except Envoi.DoesNotExist:
    #     # Si l'envoi n'existe pas, retourne une image vide
    #     return HttpResponse(status=404)

    data = signer.unsign(token)
    subscriber_id, article_id = data.split("|")

    # Crée une nouvelle entrée dans la table pixel_tracking
    PixelTracking.objects.create(
        subscriber_id=subscriber_id, article_id=article_id, tracking_date=timezone.now()
    )

    # Génère une image transparente de 1x1 pixel
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)

    return HttpResponse(output, content_type="image/png")


def subscribe(request, lg):
    article_slug = request.POST.get("art_slug", "")
    email = request.POST.get("email")

    base_url = f"{request.scheme}://{request.get_host()}"

    # return HttpResponse(f"[DEBUG] l'email' est : /{lg}/{email}")

    if not email:
        return HttpResponse("Email manquant", status=400)

    sql = "SELECT id, sub_email, is_active FROM subscriber WHERE sub_email= %s"

    with connection.cursor() as cursor:
        cursor.execute(sql, [email])  # ✅ Protection contre injection SQL
        row = cursor.fetchone()

    if row:
        # The subscriber exists
        subscriber_id = row[0]  # The id
    else:
        # Create the subscriber
        subscriber = Subscriber.objects.create(
            language_code=lg,
            is_active=0,
            sub_email=email,
            subscription_date=timezone.now(),
        )
        subscriber_id = subscriber.id  # Récupère l'ID généré

    # return HttpResponse(f"[DEBUG] le subscriber_id est : {subscriber_id}")

    token = signer.sign(subscriber_id)

    confirmation_url = f"{base_url}/{lg}/confirm/{token}/"

    # Read HTML template
    filename = get_template(f"emails/subscription_template_{lg}.htm").origin.name
    with open(filename, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Read PLAIN TEXT template
    filename = get_template(f"emails/subscription_template_{lg}.txt").origin.name
    with open(filename, "r", encoding="utf-8") as f:
        text_content = f.read()

    html_content = html_content.replace("{{ confirmation_url }}", confirmation_url)
    text_content = text_content.replace("{{ confirmation_url }}", confirmation_url)

    SMTP_SERVER = "smtp-beautifuldata.alwaysdata.net"
    SMTP_PORT = 587

    # Crée le message
    # msg = MIMEMultipart('alternative')  # que Html et plain text, pas de pièce jointe.
    subject = {
        "fr": "Confirmez votre inscription à la Newsletter Transbeauté",
        "en": "Confirm your subscription to the Transbeauté newsletter",
        "es": "Confirme su suscripción al boletín de Transbeauté",
    }

    msg = EmailMessage()
    msg["Subject"] = subject[lg]
    msg["From"] = "donotreply@transbeaute.fr"
    msg["To"] = email
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    # Send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            # server.starttls()  # Activer TLS
            # server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            # server.quit()
            # print(f"#{i} Email envoyé à {email}")
    except smtplib.SMTPConnectError as e:
        print(f"Erreur de connexion SMTP pour {email}: {e}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"Erreur d'authentification pour {email}: {e}")
    except smtplib.SMTPException as e:
        print(f"Erreur SMTP générale pour {email}: {e}")
    except Exception as e:
        print(f"Erreur inattendue pour {email}: {e}")

    if article_slug == "":
        return redirect(f"/{lg}/?message=subscription_email_sent")
    else:
        url = reverse("article_detail", kwargs={"lg": lg, "slug": article_slug})
        return redirect(f"{url}?message=subscription_email_sent")
    # return HttpResponse(f"[DEBUG] email sent to : {email}")


def confirm_subscription(request, lg, token):
    try:
        subscriber_id = signer.unsign(token, max_age=60 * 60 * 24)

        subscriber = Subscriber.objects.get(id=subscriber_id)

        subscriber.is_active = True
        subscriber.save()

        return redirect(f"/{lg}/?message=subscription_confirmed")
        # return HttpResponse("Votre inscription est confirmée.")

    except SignatureExpired:
        return HttpResponse("Lien expiré.")

    except BadSignature:
        return HttpResponse("Lien invalide.")


def unsubscribe(request, lg, token):
    try:
        subscriber_id = signer.unsign(token, max_age=60 * 60 * 24)

        subscriber = Subscriber.objects.get(id=subscriber_id)

        subscriber.is_active = False
        subscriber.save()

        return HttpResponse("Votre désinscription est confirmée.")

    except SignatureExpired:
        return HttpResponse("Lien expiré.")

    except BadSignature:
        return HttpResponse("Lien invalide.")
