#!/usr/bin/env python3

"""
Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/cron_predict_spams.py
"""

import os
import sys
import time
import asyncio
from pathlib import Path

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


DetectorFactory.seed = 0

# Languages to always mark as spam
BLOCKED_LANGUAGES = {'ru', 'hu', 'et', 'pl', 'id'}

def detect_language(text):
    try:
        return detect(text)
    except:
        return 'en'  # Langue par défaut

def preprocess_message(msg_name, msg_email, msg_subject, msg_text, msg_address, msg_event, msg_date, msg_time, msg_makeup):
    """Combine les champs textuels pour former le texte complet."""
    return f"{msg_name} {msg_email} {msg_subject} {msg_text} {msg_address}, {msg_event}, {msg_date}, {msg_time}, {msg_makeup}"


def predict_spams():
    load_dotenv()  # Load environment variables from .env

    current_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Current path : {current_path}")

    models = {}
    vectorizers = {}

    # Charger tous les fichiers .joblib dans le dossier
    for file in os.listdir(current_path + '/output'):
        if file.startswith('spam_classifier_') and file.endswith('.joblib'):
            lang = file.split('_')[2].split('.')[0]  # Extraire le code de langue (ex: 'fr')
            models[lang] = joblib.load(os.path.join(current_path, 'output', file))
            vectorizers[lang] = joblib.load(os.path.join(current_path, 'output', f'tfidf_vectorizer_{lang}.joblib'))

    print("Modèles et vectoriseurs chargés :", models.keys())

    # Connect to the database
    connexion = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    cursor = connexion.cursor(dictionary=True)
    
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
        full_text = preprocess_message(row['msg_name'], row['msg_email'], row['msg_subject'], row['msg_text'], row['msg_address'], row['msg_event'], row['msg_date'], row['msg_time'], row['msg_makeup'])
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
    

async def main():
    start_time = time.time()
    
    current_path = os.path.dirname(os.path.abspath(__file__))
    lock_file = os.path.join(current_path, 'token',  'cron_train_language_model.lock')

    # Check if the lock file already exists
    if Path(lock_file).exists():
        print(f"❌ Another process is already running (lock file {lock_file} exists).")
        sys.exit(1)

    # Create the lock file
    try:
        with open(lock_file, "w") as f:
            f.write(f"Process started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("✅ Lock acquired. Starting execution.")

        # --- YOUR TASK GOES HERE ---
        predict_spams()

    except Exception as e:
        print(f"❌ Error during execution: {e}")
    finally:
        # Remove the lock file when done
        if Path(lock_file).exists():
            os.remove(lock_file)
            print("Lock released.")
            
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")    


if __name__ == "__main__":
    asyncio.run(main())