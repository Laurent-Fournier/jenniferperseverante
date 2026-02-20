#!/usr/bin/env python

"""
Description : Analysis of messages submitted on the JenniferPerseverante website for spam identification.
Trains a separate model for each detected language, and automatically marks Russian messages as spam.

Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/analyze_messages.py

Libraries :
pip install pandas scikit-learn langdetect nltk mysql-connector-python python-dotenv
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
from langdetect import detect, DetectorFactory
import joblib
from nltk.corpus import stopwords
import nltk


# Download NLTK stopwords (only needed once)
nltk.download('stopwords')

# Ensure consistent results from langdetect
DetectorFactory.seed = 0

# Languages to always mark as spam
BLOCKED_LANGUAGES = {'ru', 'hu', 'et', 'pl', 'id'}

def detect_language(text):
    """Detect the language of a text."""
    try:
        return detect(text)
    except:
        return 'en'  # Default to English if detection fails

def get_stop_words(language):
    """Return stopwords list based on detected language."""
    print(f'get_stop_words({language})')
    try:
        return stopwords.words(language)
    except:
        return stopwords.words('english')  # Default to English if language not supported


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
        SELECT 
            id, is_spam, 
            msg_name, msg_email, msg_subject, msg_text, 
            msg_address, msg_event, msg_date, msg_time, msg_makeup
        FROM beautifuldata_jp.message
        WHERE is_spam IS NOT NULL
        ORDER BY id ASC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=[
        'msg_name', 'msg_email', 'msg_subject', 'msg_text', 
         'msg_address', 'msg_event', 'msg_date', 'msg_time', 'msg_makeup',
        'is_spam'
    ])
    df = df.fillna('') # Replace missing values with an empty string

    # Combine text fields
    df['full_text'] = df['msg_name'] + ' ' + df['msg_email'] + ' ' + df['msg_subject'] + ' ' + df['msg_text'] + ' '
    df['full_text'] += df['msg_address'] + ' ' + df['msg_event'] + ' ' + df['msg_date'] + ' ' + df['msg_time'] + ' ' + df['msg_makeup']
    
    print("Data preview:")
    print(df.head())

    # Detect language for each message
    df['language'] = df['full_text'].apply(detect_language)

    # Train one model per language
    models = {}
    vectorizers = {}

    for lang in df['language'].unique():
        if lang in BLOCKED_LANGUAGES:
            print(f"\n--- Skipping {lang}: messages will be automatically marked as spam ---")
            continue        
        
        print(f"\n--- Training model for language: {lang} ---")
        lang_mask = df['language'] == lang
        X = df.loc[lang_mask, 'full_text']
        y = df.loc[lang_mask, 'is_spam']

        if len(X) < 10 or len(y.unique()) < 2:  # Skip if not enough samples or only one class
            print(f"Skipping {lang}: not enough samples ({len(X)}) or only one class present ({len(y.unique())}).")
            continue

        try:
            # Vectorize
            stop_words = get_stop_words(lang)
            vectorizers[lang] = TfidfVectorizer(stop_words=stop_words, max_features=5000, ngram_range=(1, 2))
            X_vectorized = vectorizers[lang].fit_transform(X)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2, random_state=42)

            # Train model
            models[lang] = LogisticRegression(max_iter=1000)
            models[lang].fit(X_train, y_train)

            # Evaluate
            y_pred = models[lang].predict(X_test)
            print(f"\nClassification report for {lang}:")
            print(classification_report(y_test, y_pred))

            # Extract most discriminative words
            feature_names = vectorizers[lang].get_feature_names_out()
            coefs = models[lang].coef_[0]
            spam_words = sorted(zip(feature_names, coefs), key=lambda x: x[1], reverse=True)[:20]
            non_spam_words = sorted(zip(feature_names, coefs), key=lambda x: x[1])[:20]

            print(f'\n----------- Most SPAM words for {lang} -----------')
            for word, score in spam_words:
                print(f'{word}: {round(float(score), 2)}')

            print(f'\n----------- Most NON-SPAM words for {lang} -----------')
            for word, score in non_spam_words:
                print(f'{word}: {round(float(score), 2)}')

        except Exception as e:
            print(f"Error training model for {lang}: {e}")
            continue
        
    # Save models and vectorizers
    output_dir = os.getenv('OUTPUT_DIR')
    os.makedirs(output_dir, exist_ok=True)

    for lang in models:
        model_path = os.path.join(output_dir, f'spam_classifier_{lang}.joblib')
        vectorizer_path = os.path.join(output_dir, f'tfidf_vectorizer_{lang}.joblib')

        joblib.dump(models[lang], model_path)
        print(f'✅ Model saved for {lang}: {model_path}')

        joblib.dump(vectorizers[lang], vectorizer_path)
        print(f'✅ Vectorizer saved for {lang}: {vectorizer_path}')

    # Predict on unqualified messages
    sql = """
        SELECT 
            id, 
            IFNULL(msg_name, '') AS msg_name, 
            IFNULL(msg_email, '') AS msg_email,
            IFNULL(msg_subject, '') AS msg_subject, 
            IFNULL(msg_text, '') AS msg_text,
            IFNULL(msg_address, '') AS msg_address, 
            IFNULL(msg_event, '') AS msg_event, 
            IFNULL(msg_date, '') AS msg_date, 
            IFNULL(msg_time, '') AS msg_time, 
            IFNULL(msg_makeup, '') AS msg_makeup
        FROM beautifuldata_jp.message
        WHERE is_spam IS NULL
        ORDER BY id ASC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    for row in rows:
        full_text = ' '.join([
            row['msg_name'], row['msg_email'], row['msg_subject'], row['msg_text'],
            row['msg_address'], row['msg_event'], row['msg_date'], row['msg_time'], row['msg_makeup'],
        ])
        lang = detect_language(full_text)

        if lang in BLOCKED_LANGUAGES:
            calc_spam = True  # Automatically mark as spam
            print(f'✅ Message #{row["id"]} (lang: {lang}) automatically marked as spam')
        elif lang in models:
            vec = vectorizers[lang]
            X_new = vec.transform([full_text])
            prediction = models[lang].predict(X_new)
            calc_spam = bool(prediction[0])
        else:
            # Fallback: use the most common language model
            fallback_lang = next(iter(models.keys()))
            vec = vectorizers[fallback_lang]
            X_new = vec.transform([full_text])
            prediction = models[fallback_lang].predict(X_new)
            calc_spam = bool(prediction[0])
            print(f"Using fallback model for language: {lang} (model for {fallback_lang})")

        # Update the database
        sql_update = """
            UPDATE beautifuldata_jp.message
            SET calc_spam = %s
            WHERE id = %s
        """
        cursor.execute(sql_update, (calc_spam, row['id']))
        connexion.commit()
        print(f'✅ Message #{row["id"]} (lang: {lang}) updated with calc_spam={calc_spam}')
         
    cursor.close()
    connexion.close()
    print('\n✅ Script completed')


if __name__ == "__main__":
    main()