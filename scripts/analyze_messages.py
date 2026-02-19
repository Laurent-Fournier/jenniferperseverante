#!/usr/bin/env python

"""
Description : Analysis of messages submitted on the JenniferPerseverante website for spam identification.

Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/analyze_messages.py

Libraries :
pip install pandas scikit-learn mysql-connector-python python-dotenv
"""

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
# - faire des prévisions sur ce modèle
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

def main():
    load_dotenv()  # Load environment variables from .env

    current_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Current path : {current_path}")

    # Connect to the database
    connexion = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    cursor = connexion.cursor(dictionary=True)

    # Fetch qualified data
    sql = """
        SELECT id, is_spam, msg_name, msg_email, msg_subject, msg_text
        FROM beautifuldata_jp.message
        WHERE is_spam IS NOT NULL
        ORDER BY id ASC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=['msg_name', 'msg_email', 'msg_subject', 'msg_text', 'is_spam'])
    df = df.fillna('') # Replace missing values with an empty string

    # Combine text fields
    df['full_text'] = df['msg_name'] + ' ' + df['msg_email'] + ' ' + df['msg_subject'] + ' ' + df['msg_text']
    df = df[['full_text', 'is_spam']]
    
    print("Data preview:")
    print(df.head())

    # 2. Prepare data
    X = df['full_text']
    y = df['is_spam']

    # 3. TF-IDF Vectorization
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000, ngram_range=(1, 2))
    X_vectorized = vectorizer.fit_transform(X)

    # 4. Split data
    X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2, random_state=42)

    # 5. Train the model
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    # 6. Evaluate the model
    y_pred = model.predict(X_test)
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))

    # 7. Extract the most discriminative words
    feature_names = vectorizer.get_feature_names_out()
    coefs = model.coef_[0]
    spam_words = sorted(zip(feature_names, coefs), key=lambda x: x[1], reverse=True)[:20]
    non_spam_words = sorted(zip(feature_names, coefs), key=lambda x: x[1])[:20]

    print('\n----------- Most SPAM words -----------')
    for word, score in spam_words:
        print(f'{word}: {round(float(score), 2)}')

    #print("Mots les plus non-spam :", non_spam_words)
    print('\n----------- Most NON-SPAM words -----------')
    for word, score in non_spam_words:
        print(f'{word}: {round(float(score), 2)}')
    

    # 8. Save the model and vectorizer
    output_dir = os.path.join(current_path, 'output')
    os.makedirs(output_dir, exist_ok=True)  # Create the directory if it does not exist

    model_path = os.path.join(output_dir, 'spam_classifier.joblib')
    vectorizer_path = os.path.join(output_dir, 'tfidf_vectorizer.joblib')
    
    joblib.dump(model, model_path)
    print(f'✅ Model saved: {model_path}')

    joblib.dump(vectorizer, vectorizer_path)
    print(f'✅ Vectorizer saved: {vectorizer_path}')
    

    # 9. Predict on unqualified messages
    sql = """
        SELECT id, IFNULL(msg_name, '') AS msg_name, IFNULL(msg_email, '') AS msg_email, IFNULL(msg_subject, '') AS msg_subject, IFNULL(msg_text, '') AS msg_text
        FROM beautifuldata_jp.message
        WHERE is_spam IS NULL AND calc_spam IS NULL
        ORDER BY id ASC
    """    
    cursor.execute(sql)
    rows = cursor.fetchall()

    for row in rows:
        # model = joblib.load('spam_classifier.joblib')
        # vectorizer = joblib.load('tfidf_vectorizer.joblib')
        full_text = ' '.join([row['msg_name'], row['msg_email'], row['msg_subject'], row['msg_text']])
        X_new = vectorizer.transform([full_text])
        prediction = model.predict(X_new)
        calc_spam = bool(prediction[0])
        
        # Exécution de la requête UPDATE
        sql_update = """
            UPDATE beautifuldata_jp.message
            SET calc_spam = %s
            WHERE id = %s
        """
        values = (calc_spam, row['id'])
        cursor.execute(sql_update, values)        
        connexion.commit()
        print(f'✅ Message #{row['id']} updated with calc_spam={calc_spam}')
    
    cursor.close()
    connexion.close()
    print('\n✅ Script completed')


if __name__ == "__main__":
    main()