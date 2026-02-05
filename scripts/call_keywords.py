#!/usr/bin/env python
"""
Description : Récupération des mots clés des pages du site Transbeauté
Usage : python scripts/call_keywords.py

pip install beautifulsoup4
"""

# cd ~/www/jpdev_site/
# source env/bin/activate
# python scripts/call_keywords.py

import mysql.connector
import requests
from bs4 import BeautifulSoup

import os
from dotenv import load_dotenv


def main():
    load_dotenv()  # load variables from .env

    urls = [
'sortir-paris-transgenre',
'cours-makeup',
'gardiennage',
'dominique-travesti-histoire',
'maquillage-rapide',
'roxane',
'caroll-temoignage',
'portrait-de-mathilde',
'july-temoignage',
'coralia-recit',
'angelina-recit-transgenre',
'mon-mari-se-travestit',
'dominique-evolution-un',
'johanna',
'paloma-compagne',
'aphrodita',
'sandra-feminisation',
'laura-transition-de-genre',
'dominique-feminisation',
'vanessa-temoignage-anonyme-sur-sa-feminisation',
'blanche-temoignage',
'seance-feminisation-maquillage-habillage',
'experience-feminisation-transgenre',
'cours-maquillage-transgenre-travesti',
'de-july-au-diner-de-charly',
'le-diner-de-charly-tout-savoir-ou-presque',
'maquillage-transition-allie-confiance',
'se-sentir-femme-en-secret',
'culotte-pour-transgenre-travesti',
'vivre-sa-transidentite-sortir',
'medecine-esthetique-transidentite',
'soiree-glits-transbeaute-paris',
'diner-sortir-paris-travesti-transgenre',
'feminiser-visage-trans',
'transidentite-universelle',
'venise-trans-beaute-crossdressing',
'posterieur-trans-secret',
'temoignage-jennifer-trans-beaute',
'temoignage-lucille-travesti',
'coaching-online',
'charly-dernier-diner',
'difference-travesti-transgenre',
'purge-travesti-solution',
'temoignage-fanny-trans-beaute',
'bas-collant-travestissement-trans-beaute',
'travestir-dire-ou-pas',
'temoignage-marie-feminite',
'soiree-transbeaute-jensgirls',
'cinema-trav-trans-beaute',
'premiere-soiree-transbeaute',
'melissa-feminisation-trans-beaute',
'weekend-feminite-transbeaute',
'londres-escapade-trans-beaute',
'travestissement-controle-police-idees-recues',
'premiere-soiree-trans-beaute',
    ]

    keywords = []
    for url in urls:
        keys = get_meta_keywords(f'https://transbeaute.fr/{url}')
        print(f"URL: {url}\nMots-clés: {keys}\n")
        keywords = keywords + keys
        
    print('----------- AAA -----------------')
    print(keywords)
    print('----------- BBB -----------------')
    keywords = list(set(keywords))  # retire doublons
    print(keywords)
    print('---------- CCC -------------')
    keywords.sort()  # tri le tableau
    print(keywords)
    print('----------- DDD --------------')
        
    # connexion = mysql.connector.connect(
    #     host=os.getenv('DB_HOST'),
    #     user=os.getenv('DB_USER'),
    #     password=os.getenv('DB_PASSWORD'),
    #     database=os.getenv('DB_NAME'),
    # )
    # cursor = connexion.cursor(dictionary=True)

    # id = 10159
    # sql = f"""SELECT language_code, art_slug FROM beautifuldata_transbeaute.article_lg WHERE id={id} """
    # cursor.execute(sql)
    # rows = cursor.fetchall()
    # slug = {'fr': None, 'en': None, 'es': None}
    # for row in rows:
    #     if row['language_code']=='fr':
    #         slug['fr'] = row['art_slug']
    #     if row['language_code']=='en':
    #         slug['en'] = row['art_slug']
    #     if row['language_code']=='es':
    #         slug['es'] = row['art_slug']

    # print(slug)

    # api = MistralAPI(api_key=os.getenv('MISTRAL_API_KEY'))
    # slug_en = api.call(api.PROMPT_URL_TRANLSATION_EN, slug['fr'])
    # slug_es = api.call(api.PROMPT_URL_TRANLSATION_ES, slug['fr'])
    # print('-------------------')
    # print(slug_en)
    # print('-------------------')
    # print(slug_es)
    # print('-------------------')


    # quit()
    
    # cursor.close()
    # connexion.close()

    print('Recherche des mots clés OK')


def get_meta_keywords(url):
    try:
        # Récupérer le contenu HTML de la page
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Lever une erreur si la requête échoue

        # Analyser le HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trouver la balise meta avec name="keywords"
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})

        # Extraire la valeur de l'attribut 'content' si la balise existe
        if meta_keywords and 'content' in meta_keywords.attrs:
            return meta_keywords['content'].split(',')
        else:
            # return ["Aucune balise meta 'keywords' trouvée."]
            return []

    except Exception as e:
        # return f"Erreur lors de la récupération de {url}: {e}"
        return []

if __name__ == "__main__":
    main()