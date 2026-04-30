# 1. Brug en officiel Python 3.14 image som base (vores "tomme kasse")
FROM python:3.14-slim

# 2. Sæt arbejdsmappen inde i kassen til /app
WORKDIR /app

# 3. Kopier kravsfilen (indkøbslisten) ind i kassen først (for at udnytte cache)
COPY requirements.txt .

# 4. Installer Python-pakkerne (køb indkøbene)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Kopier alle vores kodefiler ind i kassen
COPY . .

# 6. Fortæl Docker, at den skal lytte på port 5000 (åbn døren)
EXPOSE 5000

# 7. Kommandoen til at starte serveren (tænd for restauranten)
# Vi bruger 0.0.0.0 så den kan tilgås udefra
CMD ["python3", "app.py"]
