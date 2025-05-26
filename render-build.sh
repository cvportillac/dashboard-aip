#!/bin/bash
set -o errexit

# Instalar dependencias del sistema necesarias
apt-get update
apt-get install -y --no-install-recommends \
    libgdal-dev \
    python3-gdal \
    libgeos-dev \
    libproj-dev

# Instalar dependencias de Python
pip install --upgrade pip
pip install -r requirements.txt

