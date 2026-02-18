#!/usr/bin/env python

"""
Description : Analyse des messages déposés sur le site JenniferPerseverante pour identification des spams
Usage : python scripts/analyze_messages.py

pip install pandas
pip install sklearn
pip install -U scikit-learn
"""

# cd ~/www/jpdev_site/
# source env/bin/activate
# python scripts/analyze_messages.py

# -------------------------------
# Prompt IA : Classification supervisée
# -------------------------------
# Un site Internet propose un formulaire de saisie contenant les champs suivants:
# - is_spam : qualifie manuellement si le message est un spam ou non
# - msg_name : nom de l'expéditeur
# - msg_email : email de l'expéditeur
# - msg_subject : sujet du message
# - msg_text : contenu du message

# Ces données sont en différentes langues (fr, en et es) et sont stockées en base de données et qualifiées manuellement comme Spam ou Non spam.
# La récupération des données se fait par requêtes SQL avec mysql.connector
# Comment utiliser au sein d'un script Python la librairie python scikit-learn pour estimer la classification des futurs envois ?

# Je souhaite obtenir aussi :
# - les mots les plus spam
# - les signaux non-spam
# -------------------------------

import os
from dotenv import load_dotenv

import mysql.connector
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
from django.apps import apps



def main():
    load_dotenv()  # load variables from .env

    current_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Current path : {current_path}")

    connexion = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    cursor = connexion.cursor(dictionary=True)

    # Récupération des données
    sql = """
        SELECT id, is_spam, msg_name, msg_email, msg_subject, msg_text
        FROM beautifuldata_jp.message
        WHERE is_spam IS NOT NULL
        ORDER BY id ASC
    """
   
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    # Création du DataFrame
    df = pd.DataFrame(rows, columns=['msg_name', 'msg_email', 'msg_subject', 'msg_text', 'is_spam'])

    # Remplacer les valeurs None/NaN par une chaîne vide
    df = df.fillna('')

    # Combinaison des champs textuels
    df['full_text'] = df['msg_name'] + ' ' + df['msg_email'] + ' ' + df['msg_subject'] + ' ' + df['msg_text']
    
    df = df[['full_text', 'is_spam']]
    
    print(df.head())

    # 2. Préparation des données
    X = df['full_text']
    y = df['is_spam']

    # 3. Vectorisation TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, ngram_range=(1, 2))
    X_vectorized = vectorizer.fit_transform(X)

    # 4. Division des données
    X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2, random_state=42)

    # 5. Entraînement du modèle
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    # 6. Évaluation
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    # 7. Extraction des mots les plus discriminants
    feature_names = vectorizer.get_feature_names_out()
    coefs = model.coef_[0]
    spam_words = sorted(zip(feature_names, coefs), key=lambda x: x[1], reverse=True)[:20]
    non_spam_words = sorted(zip(feature_names, coefs), key=lambda x: x[1])[:20]

    #print("Mots les plus spam :", spam_words)
    print('----------- SPAMS -----------')
    for word in spam_words:
        print(f'{word[0]}: {round(float(word[1]), 2)}')
    print('----------------------------\n\n')

    #print("Mots les plus non-spam :", non_spam_words)
    print('-------- NON SPAMS ---------')
    for word in non_spam_words:
        print(f'{word[0]}: {round(float(word[1]), 2)}')
    print('----------------------------\n\n')
    

    # 8. Sauvegarde du modèle et du vectoriseur
    joblib.dump(model, f'{current_path}/output/spam_classifier.joblib')
    print(f'✅ Création du fichier {current_path}/output/spam_classifier.joblib')

    joblib.dump(vectorizer, f'{current_path}/output/tfidf_vectorizer.joblib')
    print(f'✅ Création du fichier {current_path}/output/tfidf_vectorizer.joblib')
    
    # for row in rows:
    #     print(f'{row['id']} {row['is_spam']} {row['msg_name']} {row['msg_email']} {row['msg_subject']} {row['msg_text']}')
    
    cursor.close()
    connexion.close()

    print('✅ fin du script')


if __name__ == "__main__":
    main()