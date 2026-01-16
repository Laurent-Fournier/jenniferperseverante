#!/usr/bin/env python
"""
Description : Migrate comments from Wordpress 'wor4471_comments' table to 'comment' table
Usage : python scripts/migrate_comments.py
"""

# cd ~/www/jpdev_site/
# source env/bin/activate
# python scripts/migrate_comments.py

import mysql.connector
import requests

import os
from dotenv import load_dotenv

def main():
    load_dotenv()  # load variables from .env
        
    connexion = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    cursor = connexion.cursor(dictionary=True)

    # Récupération des commentaires
    sql_select = """
        SELECT * FROM beautifuldata_transbeaute.wor4471_comments
        ORDER BY comment_ID ASC
    """
    cursor.execute(sql_select)
    rows = cursor.fetchall()
    
    for row in rows:
        wordpress_id = row['comment_ID']
        post_id = row['comment_post_ID']
        if post_id==1:
            post_id=2
        author = row['comment_author']
        author_email = row['comment_author_email']
        date = row['comment_date']
        content = row['comment_content']
        approved = row['comment_approved']
        parent_id = row['comment_parent']
        
        # Vérification de l'existence        
        sql_exists = "SELECT COUNT(*) AS nb FROM beautifuldata_transbeaute.comment WHERE id=%s"
        cursor.execute(sql_exists, (wordpress_id,))
        result = cursor.fetchone()
        nb = result['nb'] if result else 0
        
        if nb==0: # INSERT
            sql_insert = f"""
               INSERT INTO beautifuldata_transbeaute.comment
               (id, art_id, com_author, com_author_email, com_date, com_content, com_approved, parent_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (wordpress_id, post_id, author, author_email, date, content, approved, parent_id))
            print(f'Insert {wordpress_id}')
               
        else: # UPDATE
            sql_update = """
                UPDATE beautifuldata_transbeaute.comment
                SET art_id=%s, com_author=%s, com_author_email=%s, com_date=%s, com_content=%s, com_approved=%s, parent_id=%s
                WHERE id=%s
            """
            cursor.execute(sql_update, (post_id, author, author_email, date, content, approved, parent_id, wordpress_id))
            print(f'Update {wordpress_id}')

    # Valider la transaction à la fin
    connexion.commit()
            
    cursor.close()
    connexion.close()

    print('Migrate Comments OK')

if __name__ == "__main__":
    main()