
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Article(models.Model):
    art_date = models.DateField(blank=True, null=True)
    art_family = models.CharField(max_length=45, blank=True, null=True)
    is_page = models.PositiveIntegerField(blank=True, null=True)
    art_cover = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    wp_id = models.PositiveBigIntegerField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'article'


class ArticleLg(models.Model):
    pk = models.CompositePrimaryKey('id', 'language_code')
    id = models.PositiveIntegerField()
    language_code = models.CharField(max_length=2)
    active = models.CharField(max_length=10, blank=True, null=True)
    nav = models.CharField(max_length=25, blank=True, null=True)
    art_slug = models.CharField(max_length=255, blank=True, null=True)
    hero_title = models.CharField(max_length=255, blank=True, null=True)
    hero_subtitle = models.TextField(blank=True, null=True)
    art_title = models.CharField(max_length=255, blank=True, null=True)
    art_description = models.CharField(max_length=255, blank=True, null=True)
    art_text = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'article_lg'




class Message(models.Model):
    datetime = models.DateTimeField(blank=True, null=True, db_comment='Placer dans models.py: datetime = models.DateTimeField(auto_now_add=True)')
    language_code = models.CharField(max_length=2, blank=True, null=True)
    msg_url = models.CharField(max_length=255, blank=True, null=True)
    contact_type = models.CharField(max_length=45, blank=True, null=True)
    msg_name = models.CharField(max_length=255, blank=True, null=True)
    msg_email = models.CharField(max_length=255, blank=True, null=True)
    msg_subject = models.CharField(max_length=255, blank=True, null=True)
    msg_address = models.CharField(max_length=255, blank=True, null=True, db_comment='Adresse exacte')
    msg_event = models.CharField(max_length=255, blank=True, null=True, db_comment='Pour quel événement ?')
    msg_date = models.CharField(max_length=45, blank=True, null=True, db_comment='Date de la séance')
    msg_time = models.CharField(max_length=45, blank=True, null=True, db_comment='Horaire')
    msg_people = models.CharField(max_length=45, blank=True, null=True, db_comment='Nb de personnes à maquiller')
    msg_makeup = models.CharField(max_length=45, blank=True, null=True, db_comment='Maquillage souhaité')
    msg_text = models.TextField(blank=True, null=True, db_comment='Votre message... ou Plus de détails...')
    response_status = models.CharField(max_length=45, blank=True, null=True)
    response_message = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'message'