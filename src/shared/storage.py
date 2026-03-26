'''
Storage Service Module
This module handles the interactions with Azure Blob Storage.
responsible for uploading the final markdown reports , so they can be 
accessed permanently , even after the container shuts down.

'''
from azure.storage.blob import BlobServiceClient
from src.shared.config import settings


class StorageService:
    def __init__(self):
        connection_string = settings.azure_blob_storage_connection_string
        if not connection_string:
            raise ValueError("AZURE_BLOB_STORAGE_CONNECTION_STRING is missing in configuration.")

        # Initialize the connection using string from .env
        try:
            self.service_client = BlobServiceClient.from_connection_string(connection_string)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Azure Blob Storage client: {e}") from e

        self.container_name = "reports"
        # Ensure thay the container exists (like creating a folder)
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        '''
        Creates the reports container if it doesnt exists
        '''
        try:
            container_client = self.service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
        except Exception as e:
            raise RuntimeError(
                f"Failed to ensure Azure Blob container '{self.container_name}' exists: {e}"
            ) from e

    
    def upload_file(self,file_path: str, destination_name : str) -> str:

        '''
        Uploads a local file to azure blob storage.
        agrs : file path (eg. report.md)
        destination_name : name it should have in the cloud
        '''
        try:
            blob_client = self.service_client.get_blob_client(
                container = self.container_name,
                blob = destination_name
            )

            # read the local file and upload
            with open(file_path , "rb") as data:
                blob_client.upload_blob(data,overwrite=True)
            return f"https://{self.service_client.account_name}.blob.core.windows.net/{self.container_name}/{destination_name}"
# https://[your_account].blob.core.windows.net/[container]/[filename]
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Report file not found for upload: {file_path}") from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to upload '{file_path}' to Azure Blob Storage: {e}"
            ) from e
