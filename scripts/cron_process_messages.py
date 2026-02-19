#!/usr/bin/env python3

"""
Usage : 
cd ~/www/jpdev_site/
source env/bin/activate
python scripts/cron_process_messages.py
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


def train_models():
    print("Train models...")
    
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
    output_dir = os.path.join(current_path, 'output')
    os.makedirs(output_dir, exist_ok=True)

    for lang in models:
        model_path = os.path.join(output_dir, f'spam_classifier_{lang}.joblib')
        vectorizer_path = os.path.join(output_dir, f'tfidf_vectorizer_{lang}.joblib')

        joblib.dump(models[lang], model_path)
        print(f'✅ Model saved for {lang}: {model_path}')

        joblib.dump(vectorizers[lang], vectorizer_path)
        print(f'✅ Vectorizer saved for {lang}: {vectorizer_path}')

     
    print("✅ Task completed.")
    


async def main():
    start_time = time.time()
    
    current_path = os.path.dirname(os.path.abspath(__file__))
    lock_file = os.path.join(current_path, 'token',  'cron_process_messages.lock')

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
        train_models()

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