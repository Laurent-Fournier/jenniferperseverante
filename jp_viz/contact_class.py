# PEP8
# flake8 /home/laurent/projects/django-web-app/jenniferperseverante_dev_site/jp_viz/contact_class.py

from django.core.mail import EmailMessage

from datetime import datetime
from django.utils import timezone

import os
from dotenv import load_dotenv

load_dotenv()  # load variables from .env

from .models import Message

class Contact:
    DEFAULT_LG = 'fr'
    DEFAULT_CONTACT_TYPE = 'generic'

    TEXTS = {
        'fr': {
            'title': "Contactez-moi",
            'chapo': (
                "Mariage, cours de maquillage, EVJF, shooting, maquillage de soirée, maquillage de fête, entreprise, carte cadeau…<br>"
                "N'hésitez pas à me contacter, je me ferai un plaisir de vous répondre au plus vite.<br>"
                "<br>"
                "📞 Par message ou par appel au : <strong><a href=\"tel:+33660648626\">06 60 64 86 26</a></strong><br>"
                "<br>"
                "Ou sélectionnez le sujet pour lequel vous souhaitez prendre contact :<br>"
            ),
            'name_label': "Votre nom",
            'email_label': "E-mail *",
            'subject_label': "Sujet",
            'send_label': "Envoyer",
            'success_text': "Votre message a été envoyé.<br>Merci !",
            'time_label': "Horaire",
            'people_label': "Nombre de personnes à maquiller",
            'address_label': "Adresse exacte",
            'security_text': "Nous ne partagerons jamais votre e-mail avec qui que ce soit d'autre.",

            'generic': {
                'tab': 'Renseignements',
                'header': (
                    "Une question concernant mes prestations ?<br>"
                    "N'hésitez pas à me contacter, je me ferai un plaisir de vous répondre très vite."
                ),
                'message_label': "Message",
            },
            'wedding': {
                'tab': 'Mariage',
                'header': (
                    "Afin de vous délivrer le meilleur service possible pour votre mariage, merci de remplir le formulaire suivant :"
                ),
                'date_label': "Date du mariage",
                'message_label': "Plus de détails...",
            },
            'studio': {
                'tab': 'Studio de maquillage',
                'header': (
                    "Afin de vous délivrer le meilleur service possible pour la séance de maquillage dans mon studio, merci de remplir le formulaire suivant : "
                ),
                'makeup_label': "Type de maquillage : cours solo, duo, trio, groupes",
                'event_label': "Pour quel événement ?",
                'date_label': "Date de la séance",
                'message_label': "Plus de détails...",
            },
            'at_home': {
                'tab': 'Maquillage à domicile',
                'header': (
                    "Afin de vous délivrer le meilleur service possible pour la séance de maquillage à domicile,<br>"
                    "merci de remplir le formulaire suivant :"
                ),
                'address_label': "Adresse exacte",
                'date_label': "Date de la séance",
                'makeup_label': "Maquillage souhaité : maquillage de mariée, invitée mariage, maquillage soirée",
                'message_label': "Plus de détails...",
            }
        },
        'en': {
            'title': "Get In Touch",
            'chapo': (
                "Wedding, makeup classes, bachelorette party, photoshoot, evening makeup, party makeup, corporate events, gift card…<br>"
                "Feel free to contact me; I’ll be happy to get back to you as soon as possible.<br>"
                "<br>"
                "📞 By message or by phone on: <strong><a href=\"tel:+33660648626\">06 60 64 86 26</a></strong><br>"
                "<br>"
                "Or select the reason for your enquiry:<br>"
            ),
            
            'name_label': "Name",
            'email_label': "Email *",
            'subject_label': "Subject",
            'send_label': "Send Message",
            'success_text': "Your message was sent.<br>Thank you!",

            'time_label': "Time",
            'people_label': "Number of people to be made up",
            'address_label': "Exact address",
            'security_text': "We'll never share your email with anyone else.",

            'generic': {
                'tab': 'Information',
                'header': (
                    "Do you have any questions about my services?.<br>"
                    "Don't hesitate to contact me; I'll be happy to answer you as soon as possible."
                ),
                'message_label': "Your message...",
            },
            'wedding': {
                'tab': 'Wedding',
                'header': "In order to provide you with the best possible service for your wedding, please fill out the following form",
                'date_label': "Wedding Date",
                'message_label': "More details...",
            },
            'studio': {
                'tab': 'Makeup Studio',
                'header': "In order to provide you with the best possible service for the makeup session in my studio, please fill out the following form",
                'makeup_label': "Type of Makeup: solo, duo, trio, group lessons",
                'event_label': "For What Event?",
                'date_label': "Workshop Date",
                'message_label': "More details...",
            },
            'at_home': {
                'tab': 'Makeup at home',
                'header': "In order to provide you with the best possible service for your home makeup session, please fill out the following form",
                'date_label': "Date of the session",
                'makeup_label': "Desired makeup: bridal makeup, wedding guest makeup, evening makeup",
                'message_label': "More details...",
            }
        },
        'es': {
            'title': "Contáctame",
            'chapo': (
                "Boda, cursos de maquillaje, despedida de soltera, sesión de fotos, maquillaje de noche, maquillaje de fiesta, empresa, tarjeta regalo…<br>"
                "No dudes en contactarme; será un placer responderte lo antes posible.<br>"
                "<br>"
                "📞 Por mensaje o por llamada al: <strong><a href=\"tel:+33660648626\">06 60 64 86 26</a></strong><br>"
                "<br>"
                "O selecciona el asunto sobre el que deseas ponerte en contacto:<br>"
            ),
                        
            'name_label': "Nombre",
            'email_label': "Correo electrónico",
            'subject_label': "Sujeto *",
            'send_label': "Enviar Mensaje",
            'success_text': "Tu mensaje ha sido enviado.<br>Gracias !",

            'time_label': "Hora",
            'people_label': "Número de personas a formar",
            'address_label': "Dirección exacta",
            'security_text': 'Nunca compartiremos su correo electrónico con nadie más.',

            'generic': {
                'tab': 'Información',
                'header': (
                    "¿Alguna pregunta sobre mis servicios?<br>"
                    "No dudes en contactarme, estaré encantado de responderte muy rápidamente."
                ),
                'message_label': "Tu mensaje...",
            },
            'wedding': {
                'tab': 'Casamiento',
                'header': "Para poder brindarle el mejor servicio posible para su boda, complete el siguiente formulario",
                'date_label': "Fecha de la Boda",
                'message_label': "Más detalles...",
            },
            'studio': {
                'tab': 'Estudio de maquillaje',
                'header': "Para poder brindarte el mejor servicio posible para la sesión de maquillaje en mi taller, por favor completa el siguiente formulario",
                'makeup_label': "Tipo de maquillaje: solo, dúo, trío, clases grupales.",
                'event_label': "¿Para qué evento?",
                'date_label': "Fecha del taller",
                'message_label': "Más detalles...",
            },
            'at_home': {
                'tab': 'Maquillaje en casa',
                'header': "Para poder brindarte el mejor servicio posible para tu sesión de maquillaje a domicilio, por favor completa el siguiente formulario",
                'date_label': "Fecha de la sesión",
                'makeup_label': "Maquillaje deseado: maquillaje de novia, invitada a la boda, maquillaje de noche.",
                'message_label': "Más detalles...",
            }
        }
    }

    # -----------------------------------
    # Constructor
    # -----------------------------------
    def __init__(self, lg=None, contact_type=None, url=None, no_section=0):
        self.lg = lg or self.DEFAULT_LG
        self.contact_type = contact_type.lower() or self.DEFAULT_CONTACT_TYPE
        self.no_section = no_section
        self.url = url

    def __str__(self):
        return "Contact section"

    # ----------------------------------------------
    # Get all texts from language and contact_type
    # ----------------------------------------------
    def get_texts(self):
        if self.lg not in ['fr', 'en', 'es']:
            raise ValueError(f"Unsupported language_code: {self.lg}")

        if self.contact_type not in ['generic', 'wedding', 'studio', 'at_home']:
            raise ValueError(f"Unsupported contact_type: {self.contact_type}")

        texts = self.TEXTS[self.lg].copy()

        texts['lg'] = self.lg
        texts['contact_type'] = self.contact_type
        texts['style'] = 'even' if self.no_section % 2 == 0 else 'odd'
        texts['contact_action'] = self.url

        return texts

    # ---------------------------------
    # Send email and Save in Db
    # ---------------------------------
    def process(self, request):

        if request.method != 'POST':
            return None
        
        # Read parameters
        user_agent = request.headers.get('User-Agent')
        contact_type = request.POST.get('contact_type')
        msg_name = request.POST.get('name')
        msg_email = request.POST.get('email')
        msg_subject = request.POST.get('subject')
        msg_text = request.POST.get('message')
        msg_address = request.POST.get('address')  # Exact address
        msg_event = request.POST.get('event')  # Event
        msg_date = request.POST.get('date')  # Date of the session
        msg_time = request.POST.get('time')  # Time
        msg_people = request.POST.get('people')  # Number of people to be made up
        msg_makeup = request.POST.get('makeup')  # Desired makeup

        # Validations
        #errors = []
        is_spam = None
        if '@mail.ru' in msg_email:
            is_spam = 1
            message = 'identified as spam: Email contains @mail.ru pattern'
        elif 'и' in msg_text:
            is_spam = 1
            message = 'identified as spam: Text contains и character'
        elif 'AI-powered' in msg_text:
            is_spam = 1
            message = 'identified as spam: Text contains AI-powered pattern'
            
        if is_spam != 1:
            # Send email
            msg_text_cleaned = msg_text.replace('\n', '<br>')
            email_body = ''
            email_body += f"<strong>Url :</strong> {self.url}<br>\n"
            email_body += f"<strong>User agent :</strong> {user_agent}<br>\n"
            # email_body += f"<strong>Message:</strong><br>{request.limited}<br>\n"
            email_body += f"<strong>Date :</strong> {timezone.now()}<br>\n"
            email_body += f"<strong>Type :</strong> {contact_type}<br>\n"
            email_body += f"<strong>Langue :</strong> {self.lg}<br>\n"
            email_body += f"<strong>Nom :</strong> {msg_name}<br>\n"
            email_body += f"<strong>Email :</strong> {msg_email}<br>\n"
            email_body += f"<strong>Sujet :</strong> {msg_subject}<br>\n"
            email_body += f"<strong>Adresse exacte :</strong> {msg_address}<br>\n"
            email_body += f"<strong>Pour quel événément ?</strong> {msg_event}<br>\n"
            email_body += f"<strong>Date de la séance :</strong> {msg_date}<br>\n"
            email_body += f"<strong>Horaire :</strong> {msg_time}<br>\n"
            email_body += f"<strong>Nb de personnes à maquiller :</strong> {msg_people}<br>\n"
            email_body += f"<strong>Maquillage souhaité :</strong> {msg_makeup}<br>\n"
            email_body += "<hr>\n"
            email_body += f"<strong>Message:</strong><br>{msg_text_cleaned}"

            try:
                email = EmailMessage(
                    subject = f'Formulaire de contact du site JenniferPerseverante [{os.getenv('ENVIRONMENT')}]',
                    body = email_body,
                    from_email = 'laurent@beautifuldata.fr',
                    to = ['laurent@beautifuldata.fr'],
                )
                email.content_subtype = 'html'
                nb = email.send()
                r = { 'status': 'SUCCESS', 'message': None, 'count': nb}
            except Exception as e:
                r = { 'status': 'ERROR', 'message': str(e), 'count': 0}
        else:
            r = { 'status': 'EMAIL NOT SENT', 'message': message, 'count': 0}
            

        # Save message in Database
        message = Message(
            datetime = timezone.now(),
            is_spam = is_spam,
            msg_name = msg_name,
            msg_email = msg_email,
            msg_subject = msg_subject,
            msg_text = msg_text,
            language_code = self.lg,
            contact_type = contact_type,
            msg_url = self.url,
            msg_address = msg_address,
            msg_event = msg_event,
            msg_date = msg_date,
            msg_time = msg_time,
            msg_people = msg_people,
            msg_makeup = msg_makeup,
            response_status = r['status'],
            response_message = r['message'],
            user_agent = user_agent,
            # request_limited = request.limited,
        )
        message.save()

        return r
