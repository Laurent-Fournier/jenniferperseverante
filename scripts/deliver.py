#!/usr/bin/env python
"""
Description : Copy file from dev to UAT or PROD environement
Usage : python scripts/deliver.py --target=UAT
Usage : python scripts/deliver.py --target=PROD
"""

# cd ~/www/jpdev_site/
# source env/bin/activate
# python scripts/deliver.py


import os
import argparse


def main():
    parser = argparse.ArgumentParser(description="Copy files from DEV to UAT/PROD Django environnement.")
    parser.add_argument("--target", help="Target Django environment (UAT or PROD)", required=True)

    args = parser.parse_args()
    print(f"TArget : {args.target}")

    print('Delivery scussefull!')

if __name__ == "__main__":
    main()