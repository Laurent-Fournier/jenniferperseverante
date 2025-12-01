#!/usr/bin/env python
"""
Description : Génération des redirections 301 entre Wordpress et Django
Usage : python scripts/generate_redirections301.py
"""

# cd ~/www/jpdev_site/
# source env/bin/activate
# python scripts/generate_redirections301.py


import os
import mysql.connector


def main():
    connexion = mysql.connector.connect(
        host="mysql-beautifuldata.alwaysdata.net",
        user="430589",
        password="MZZV3XFW4SFffDYAAAC8",
        database="beautifuldata_jp"
    )
    
    cursor = connexion.cursor(dictionary=True)

    sql = """
        SELECT
            article.id,
            article_lg.art_slug,
            wor5635_posts.ID, wor5635_posts.post_name
        FROM article
        LEFT OUTER JOIN article_lg ON
            article.id = article_lg.id AND article_lg.language_code='fr'
        LEFT OUTER JOIN wor5635_posts ON
	        article.wp_id = wor5635_posts.ID
        WHERE wor5635_posts.post_name IS NOT NULL
        """
    cursor.execute(sql)
    
    rows = cursor.fetchall()

    text = ''
    for row in rows:
        print( f'/{row['post_name']} -> /fr/{row['art_slug']}' )
        print( f"path('{row['post_name']}', RedirectView.as_view(url='/fr/{row['art_slug']}', permanent=True))," )
        print()
        text += f"    path('{row['post_name']}', RedirectView.as_view(url='/fr/{row['art_slug']}', permanent=True)),\n"
        
    with open("scripts/redirections301.txt", "w", encoding="utf-8") as fichier:
        fichier.write(text)        
    
    cursor.close()
    connexion.close()

    print('Génération des redirections 301 terminée')

if __name__ == "__main__":
    main()