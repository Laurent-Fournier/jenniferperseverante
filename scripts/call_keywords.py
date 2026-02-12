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

    current_path = os.getcwd()
    print(f"Current path : {current_path}")

    connexion = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    cursor = connexion.cursor(dictionary=True)

    sql = """
        SELECT post_name
        FROM beautifuldata_transbeaute.wor4471_posts
        WHERE
	        post_type='post'
	        AND post_parent=0
	        AND post_status='publish'
        """
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    slugs = []
    for row in rows:
        slugs.append(row['post_name'])
    
    nb = len(slugs)

    keywords = []
    i = 0
    for slug in slugs:
        i = i + 1
        keys = get_meta_keywords(f'https://transbeaute.fr/{slug}')
        print(f"[{i}/{nb}] URL: {slug}\nMots-clés: {keys}\n")
        keywords = keywords + keys
        
    keywords = list(set(keywords))  # retire doublons
    keywords.sort()  # tri le tableau

    # Save the keywords in a file
    filename = os.path.dirname(os.path.abspath(__file__))+'/keywords.txt'
    with open(filename, "w", encoding="utf-8") as fichier:
        for keyword in keywords:
            fichier.write(keyword + "\n")
    print(f"✅ Fichier {filename} créé")
     
    
    cursor.close()
    connexion.close()

    print('✅ fin du script')


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