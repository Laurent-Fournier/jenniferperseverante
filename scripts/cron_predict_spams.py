#!/usr/bin/env python3

"""
Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/cron_predict_spams.py

This script loads pre-trained spam classification models and predicts whether new messages are spam.
It updates the database accordingly and handles language detection and fallback logic.
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv
import mysql.connector
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from langdetect import detect, DetectorFactory, LangDetectException
import joblib
from nltk.corpus import stopwords
import nltk


# Ensure consistent language detection
DetectorFactory.seed = 0

# Languages to always mark as spam
BLOCKED_LANGUAGES = {'ru', 'hu', 'et', 'pl', 'id'}

def detect_language(text: str) -> str:
    """
    Detect the language of the provided text.

    Args:
        text: The text to analyze.

    Returns:
        The detected language code, or 'en' if detection fails.
    """    
    try:
        return detect(text)
    except:
        return 'en'  # Default language

def preprocess_message(msg_name, msg_email, msg_subject, msg_text, msg_address, msg_event, msg_date, msg_time, msg_people, msg_makeup):
    """Combine les champs textuels pour former le texte complet."""
    return f"{msg_name} {msg_email} {msg_subject} {msg_text} {msg_address}, {msg_event}, {msg_date}, {msg_time}, {msg_people}, {msg_makeup}"


def load_models_and_vectorizers(current_path: str) -> Dict[str, Any]:
    """
    Load all pre-trained models and vectorizers from the output directory.

    Args:
        current_path: Path to the script directory.

    Returns:
        Dictionary of models and vectorizers, keyed by language.
    """    
    models = {}
    vectorizers = {}
    output_dir = os.path.join(current_path, 'output')

    for file in os.listdir(output_dir):
        if file.startswith('spam_classifier_') and file.endswith('.joblib'):
            lang = file.split('_')[2].split('.')[0]
            models[lang] = joblib.load(os.path.join(output_dir, file))
            vectorizers[lang] = joblib.load(os.path.join(output_dir, f'tfidf_vectorizer_{lang}.joblib'))

    print("Loaded models and vectorizers for languages:", models.keys())
    return models, vectorizers
   

def predict_spams(models: Dict[str, Any], vectorizers: Dict[str, Any]) -> None:
    """
    Predict spam status for unqualified messages in the database.

    Args:
        models: Dictionary of pre-trained models, keyed by language.
        vectorizers: Dictionary of TF-IDF vectorizers, keyed by language.
    """    
    load_dotenv()  # Load environment variables from .env
    current_path = os.path.dirname(os.path.abspath(__file__))

    try:
        # Connect to the database
        connexion = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
        )
        cursor = connexion.cursor(dictionary=True)
    
        # Fetch unqualified messages
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
                IFNULL(msg_people, '') AS msg_people, 
                IFNULL(msg_makeup, '') AS msg_makeup
            FROM beautifuldata_jp.message
            WHERE is_spam IS NULL
            ORDER BY id ASC
        """
        cursor.execute(sql)
        rows = cursor.fetchall()    

        for row in rows:
            full_text = preprocess_message(row['msg_name'], row['msg_email'], row['msg_subject'], row['msg_text'], row['msg_address'], row['msg_event'], row['msg_date'], row['msg_time'], row['msg_people'], row['msg_makeup'])
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
                SET calc_spam = %s, calc_lg=%s
                WHERE id = %s
            """
            cursor.execute(sql_update, (calc_spam, lang, row['id']))
            connexion.commit()
            print(f'✅ Message #{row["id"]} (lang: {lang}) updated with calc_spam={calc_spam}')
    
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        raise
    finally:
        cursor.close()
        connexion.close()
    
    print('\n✅ Script completed')
    

async def main() -> None:
    """
    Main async function to handle script execution and locking.
    """    
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

        # Load models and vectorizers
        models, vectorizers = load_models_and_vectorizers(current_path)
        if not models:
            print("❌ No models found. Exiting.")
            sys.exit(1)

        # Predict spams
        predict_spams(models, vectorizers)

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        raise
    finally:
        # Remove the lock file when done
        if Path(lock_file).exists():
            os.remove(lock_file)
            print("Lock released.")
            
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")    


if __name__ == "__main__":
    asyncio.run(main())