'''
storage Service Module
This module handles the interacations with Azure Blob Storage.
responsible for uploading the final markdown report, so they can be accessed permenantly, even after the container shuts down

'''

from azure.storage.blob import BlobServiceClient
from src.shared.config import settings
import os


class StorageService:
    def __init__(self):
        # Initiatlize connection using string from .env
        self.service_client = BlobServiceClient.from_connection_string(settings.azure_blob_storage_connection_string)
        self.container_name="reports"
        # Ensure thay the container exists (like creating a folder)
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        '''
        create the reports if it doesn't exits 
        '''
        try:
            container_client=self.service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
        except Exception as e:
            print(f"warning checking container: {e}")

    def upload_file(self,filepath:str,destination_name:str)->str:
        '''
        Uploads a local file to azure blob storage.
        agrs : file path (eg. report.md)
        destination_name : name it should have in the cloud
        '''
        try:
            blob_client=self.service_client.get_blob_client(
                container=self.container_name,
                blob=destination_name
            )
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            return f"https://{self.service_client.account_name}.blob.core.windows.net/{self.container_name}/{destination_name}"
# https://[your_account].blob.core.windows.net/[container]/[filename]
        except Exception as e:
            return f"Error uploading to Azure : {str(e)}"
        






        



