import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# Si tu modifies ces SCOPES, supprime le fichier token.json pour forcer une nouvelle authentification.
# Ce scope donne un accès complet en lecture/écriture à Google Drive.
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """
    Gère le processus d'authentification OAuth 2.0 et retourne un objet service Google Drive.
    """
    creds = None
    # Le fichier token.json stocke les jetons d'accès et d'actualisation de l'utilisateur,
    # et est créé automatiquement la première fois que le flux d'autorisation est effectué.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Si aucune donnée d'identification valide n'est disponible, l'utilisateur est invité à se connecter.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Le fichier credentials.json est celui que tu as téléchargé depuis la Google Cloud Console.
            # Assure-toi qu'il est dans le même répertoire que ton script.
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Enregistre les données d'identification pour les prochaines exécutions
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(folder_id):
    """
    Liste les fichiers et sous-dossiers contenus dans un dossier Google Drive donné.
    Args:
        folder_id: L'ID du dossier parent.
    Returns:
        Une liste de dictionnaires, chaque dictionnaire représentant un fichier/dossier.
    """
    try:
        service = get_drive_service() # Utilise la fonction d'authentification

        files = []
        page_token = None
        while True:
            response = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields='nextPageToken, files(id, name, mimeType, parents)',
                corpora='user',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageToken=page_token
            ).execute()

            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return files

    except HttpError as error:
        print(f'Une erreur est survenue : {error}')
        return []

def download_file(file_id, file_name, save_path='./downloadsgoogle'):
    """
    Télécharge un fichier depuis Google Drive vers le chemin spécifié.
    Args:
        file_id: L'ID du fichier à télécharger.
        file_name: Le nom sous lequel le fichier sera sauvegardé.
        save_path: Le chemin du répertoire où sauvegarder le fichier.
    """
    try:
        service = get_drive_service()

        # Crée le répertoire de sauvegarde s'il n'existe pas
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        file_path = os.path.join(save_path, file_name)

        # Effectue la requête de téléchargement du contenu du fichier
        request = service.files().get_media(fileId=file_id)

        with open(file_path, 'wb') as f:
            # Utilise un objet de requête HTTP pour télécharger le fichier
            # En morceaux pour les gros fichiers
            downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # Affiche la progression du téléchargement (optionnel)
                print(f"Téléchargement {int(status.progress() * 100)}%.")
        
        print(f"Le fichier '{file_name}' a été téléchargé avec succès dans '{file_path}'.")

    except HttpError as error:
        print(f'Une erreur est survenue lors du téléchargement : {error}')


# --- Utilisation de la fonction ---
if __name__ == '__main__':
    # REMPLACE CECI PAR L'ID RÉEL DE TON DOSSIER GOOGLE DRIVE
    # Pour trouver l'ID d'un dossier : Ouvre le dossier dans Google Drive via ton navigateur.
    # L'ID est la longue chaîne de caractères dans l'URL après "folders/".
    # Exemple: https://drive.google.com/drive/folders/1aBcDeFGhIjKlMnOpQrStUvWzYxZ
    # L'ID serait: 1aBcDeFGhIjKlMnOpQrStUvWzYxZ
    mon_dossier_id = '1sFGFpjVvtkeuSv5MxKjXj8O7qGtS4Ez_'

    if mon_dossier_id == 'VOTRE_ID_DU_DOSSIER_ICI':
        print("Veuillez remplacer 'VOTRE_ID_DU_DOSSIER_ICI' par l'ID réel de votre dossier Google Drive.")
        print("Pour trouver l'ID : ouvrez le dossier dans Google Drive, l'ID est dans l'URL.")
    else:
        print(f"Tentative de récupération des fichiers du dossier avec l'ID : {mon_dossier_id}")
        fichiers_du_dossier = list_files_in_folder(mon_dossier_id)

        if fichiers_du_dossier:
            print(f"\nFichiers et dossiers trouvés dans '{mon_dossier_id}' :")
            for item in fichiers_du_dossier:
                print(f"- Nom: {item['name']}, ID: {item['id']}, Type: {item['mimeType']}")
                file_to_download_id = item['id']
                file_to_download_name = item['name']
                if file_to_download_id == 'VOTRE_ID_DU_FICHIER_A_TELECHARGER_ICI':
                    print("Veuillez remplacer l'ID et le nom du fichier à télécharger.")
                else:
                    print(f"\nDébut du téléchargement du fichier : '{file_to_download_name}'...")
                    download_file(file_to_download_id, file_to_download_name)
        
        else:
            print("Aucun fichier trouvé ou une erreur est survenue. Vérifiez l'ID du dossier et vos permissions.")
    

#--------------pârtie téléchargement------------------