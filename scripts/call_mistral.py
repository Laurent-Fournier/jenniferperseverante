#!/usr/bin/env python
"""
Description : Génération des redirections 301 entre Wordpress et Django
Usage : python scripts/call_mistral.py
"""

# cd ~/www/jpdev_site/
# source env/bin/activate
# python scripts/call_mistral.py

import mysql.connector
import requests

import os
from dotenv import load_dotenv

from mistral_class import MistralAPI

def main():
    load_dotenv()  # load variables from .env
        
    connexion = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    cursor = connexion.cursor(dictionary=True)

    id = 10159
    sql = f"""SELECT language_code, art_slug FROM beautifuldata_transbeaute.article_lg WHERE id={id} """
    cursor.execute(sql)
    rows = cursor.fetchall()
    slug = {'fr': None, 'en': None, 'es': None}
    for row in rows:
        if row['language_code']=='fr':
            slug['fr'] = row['art_slug']
        if row['language_code']=='en':
            slug['en'] = row['art_slug']
        if row['language_code']=='es':
            slug['es'] = row['art_slug']

    print(slug)

    api = MistralAPI(api_key=os.getenv('MISTRAL_API_KEY'))
    slug_en = api.call(api.PROMPT_URL_TRANLSATION_EN, slug['fr'])
    slug_es = api.call(api.PROMPT_URL_TRANLSATION_ES, slug['fr'])
    print('-------------------')
    print(slug_en)
    print('-------------------')
    print(slug_es)
    print('-------------------')


    quit()
    
    # sql = """
    #     SELECT
    #         article.id,
    #         article_lg.art_slug,
    #         wor5635_posts.ID, wor5635_posts.post_name
    #     FROM article
    #     LEFT OUTER JOIN article_lg ON
    #         article.id = article_lg.id AND article_lg.language_code='fr'
    #     LEFT OUTER JOIN wor5635_posts ON
	#         article.wp_id = wor5635_posts.ID
    #     WHERE wor5635_posts.post_name IS NOT NULL
    #     """
    # cursor.execute(sql)
    
    # rows = cursor.fetchall()

    # text = ''
    # for row in rows:
    #     print( f'/{row['post_name']} -> /fr/{row['art_slug']}' )
    #     # print( f"path('{row['post_name']}', RedirectView.as_view(url='/fr/{row['art_slug']}', permanent=True))," )
    #     print()
    #     # text += f"    path('{row['post_name']}', RedirectView.as_view(url='/fr/{row['art_slug']}', permanent=True)),\n"
    #     text += f"    re_path(r'^{row['post_name']}/?$', RedirectView.as_view(url='/fr/{row['art_slug']}', permanent=True)),\n"
        
    # with open("scripts/redirections301.txt", "w", encoding="utf-8") as fichier:
    #     fichier.write(text)        
    
    cursor.close()
    connexion.close()

    print('Mistral calls OK')

if __name__ == "__main__":
    main()