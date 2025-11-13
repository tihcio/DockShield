"""
Restore management for DockShield
"""

import os
import json
import tarfile
import gzip
import tempfile
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import logging

from dockshield.core.docker_manager import DockerManager
from dockshield.core.backup_manager import BackupManager
from dockshield.core.exceptions import (
    RestoreException,
    ContainerExistsException,
    ImageNotFoundException,
    BackupNotFoundException,
    FilesystemRestoreException,
)

logger = logging.getLogger(__name__)


class RestoreManager:
    """Manages container restore operations"""

    def __init__(self, docker_manager: DockerManager, backup_manager: BackupManager):
        """
        Initialize restore manager

        Args:
            docker_manager: DockerManager instance
            backup_manager: BackupManager instance
        """
        self.docker_manager = docker_manager
        self.backup_manager = backup_manager

    def restore_container(
        self,
        backup_id: str,
        new_name: Optional[str] = None,
        override_config: Optional[Dict[str, Any]] = None,
        start_after_restore: bool = True,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Restore container from backup

        Args:
            backup_id: Backup ID to restore
            new_name: New container name (optional, uses original if not specified)
            override_config: Configuration overrides (optional)
            start_after_restore: Start container after restore

        Returns:
            Tuple of (container_id, error_message)
            - If successful: (container_id, None)
            - If failed: (None, error_message)
        """
        try:
            logger.info(f"Starting restore from backup: {backup_id}")

            # Get backup metadata
            metadata = self.backup_manager.get_backup_metadata(backup_id)
            if not metadata:
                error_msg = f"Backup non trovato: {backup_id}"
                logger.error(error_msg)
                raise BackupNotFoundException(error_msg)

            backup_path = Path(metadata["backup_path"])
            backup_type = metadata["backup_type"]
            original_container_info = metadata["container_info"]

            # Verify backup path exists
            if not backup_path.exists():
                error_msg = f"Directory backup non trovata: {backup_path}"
                logger.error(error_msg)
                raise BackupNotFoundException(error_msg)

            # Determine container name
            container_name = new_name or original_container_info["name"]
            logger.info(f"Ripristinando container con nome: {container_name}")

            # Check if container with same name already exists
            existing_container = self.docker_manager.get_container(container_name)
            if existing_container:
                error_msg = f"Un container con nome '{container_name}' esiste già. Usa un nome diverso o rimuovi il container esistente."
                logger.error(error_msg)
                raise ContainerExistsException(error_msg)

            # Restore based on backup type
            if backup_type == "full":
                container_id = self._restore_full_backup(
                    backup_path,
                    metadata,
                    container_name,
                    override_config,
                    start_after_restore,
                )
            elif backup_type == "filesystem":
                container_id = self._restore_filesystem_backup(
                    backup_path,
                    metadata,
                    container_name,
                    override_config,
                    start_after_restore,
                )
            else:
                error_msg = f"Tipo backup sconosciuto: {backup_type}"
                logger.error(error_msg)
                raise RestoreException(error_msg)

            if container_id:
                logger.info(f"Ripristino completato con successo: {container_id}")
                return (container_id, None)
            else:
                return (None, "Ripristino fallito senza errore specifico")

        except (BackupNotFoundException, ContainerExistsException, ImageNotFoundException) as e:
            logger.error(f"Errore durante ripristino: {e}")
            return (None, str(e))
        except Exception as e:
            error_msg = f"Errore imprevisto durante ripristino: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return (None, error_msg)

    def _restore_full_backup(
        self,
        backup_path: Path,
        metadata: Dict[str, Any],
        container_name: str,
        override_config: Optional[Dict[str, Any]],
        start_after_restore: bool,
    ) -> Optional[str]:
        """Restore container from full backup"""
        try:
            container_info = metadata["container_info"]
            original_image_name = container_info["image"]

            # Load container image
            loaded_image_id = None
            image_archive = backup_path / "image.tar.gz"
            if image_archive.exists():
                logger.info(f"Restoring container image (original: {original_image_name})...")

                # Decompress image
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_image_path = Path(temp_dir) / "image.tar"
                    if not self._decompress_file(image_archive, temp_image_path):
                        raise RestoreException("Failed to decompress image archive")

                    # Load image - returns list of loaded images
                    if not self.docker_manager.load_image(str(temp_image_path)):
                        raise RestoreException("Failed to load container image from tar")

                    logger.info("Image loaded successfully")

                    # Get the loaded image - Docker might have loaded it without tags
                    # We need to find it and potentially retag it
                    try:
                        # Try to get by original name first
                        loaded_image = self.docker_manager.get_image(original_image_name)
                        if loaded_image:
                            loaded_image_id = original_image_name
                            logger.info(f"Found loaded image with original name: {original_image_name}")
                        else:
                            # Image was loaded but without tag - need to find it by ID
                            # List recent images and use the first one (just loaded)
                            images = self.docker_manager.client.images.list()
                            if images:
                                # Get the most recently created untagged image
                                for img in images:
                                    if not img.tags:  # Untagged image
                                        loaded_image_id = img.id
                                        logger.info(f"Using untagged image ID: {loaded_image_id}")
                                        # Tag it with original name for easier management
                                        try:
                                            img.tag(original_image_name)
                                            loaded_image_id = original_image_name
                                            logger.info(f"Tagged image as: {original_image_name}")
                                        except Exception as e:
                                            logger.warning(f"Could not tag image: {e}")
                                        break

                                if not loaded_image_id and images:
                                    # Fallback: use first image ID
                                    loaded_image_id = images[0].id
                                    logger.warning(f"Using fallback image ID: {loaded_image_id}")

                        if not loaded_image_id:
                            raise RestoreException("Could not find loaded image")

                    except Exception as e:
                        logger.error(f"Error finding loaded image: {e}")
                        raise RestoreException(f"Could not identify loaded image: {e}")

            # Load container configuration
            config_file = backup_path / "container_config.json"
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    container_config = json.load(f)
            else:
                container_config = container_info

            # Apply configuration overrides
            if override_config:
                container_config.update(override_config)

            # IMPORTANT: Use the loaded image ID, not the name from config
            if loaded_image_id:
                container_config["image"] = loaded_image_id
                logger.info(f"Will create container with image: {loaded_image_id}")

            # Extract environment variables
            env_dict = {}
            if "env" in container_config:
                for env_var in container_config["env"]:
                    if "=" in env_var:
                        key, value = env_var.split("=", 1)
                        env_dict[key] = value

            # Extract volume mappings
            volumes = {}
            if "mounts" in container_config:
                for mount in container_config["mounts"]:
                    if mount.get("Type") == "bind":
                        source = mount.get("Source")
                        destination = mount.get("Destination")
                        volumes[source] = {"bind": destination, "mode": "rw"}
                    elif mount.get("Type") == "volume":
                        name = mount.get("Name")
                        destination = mount.get("Destination")
                        volumes[name] = {"bind": destination, "mode": "rw"}

            # Extract port mappings
            ports = {}
            if "ports" in container_config:
                for container_port, host_bindings in container_config["ports"].items():
                    if host_bindings:
                        for binding in host_bindings:
                            host_port = binding.get("HostPort")
                            if host_port:
                                ports[container_port] = int(host_port)

            # Create container
            logger.info(f"Creating container '{container_name}' with image '{container_config['image']}'...")
            try:
                container = self.docker_manager.create_container(
                    image=container_config["image"],
                    name=container_name,
                    environment=env_dict,
                    volumes=volumes,
                    ports=ports,
                    labels=container_config.get("labels", {}),
                    detach=True,
                )

                if not container:
                    raise RestoreException("create_container returned None")

                logger.info(f"Container created successfully: {container.id}")

            except Exception as e:
                error_msg = f"Failed to create container: {e}"
                logger.error(error_msg)
                raise RestoreException(error_msg)

            # Restore filesystem data
            filesystem_archive = backup_path / "filesystem.tar.gz"
            if filesystem_archive.exists():
                logger.info("Restoring container filesystem...")
                if not self._restore_filesystem_data(container, filesystem_archive):
                    logger.warning("Failed to restore filesystem data")

            # Start container if requested
            if start_after_restore:
                logger.info("Starting container...")
                if not self.docker_manager.start_container(container):
                    logger.warning("Failed to start container")

            logger.info(f"Container restored successfully: {container.id}")
            return container.id

        except RestoreException:
            # Re-raise RestoreException to be caught by restore_container()
            raise
        except Exception as e:
            error_msg = f"Errore imprevisto durante ripristino full backup: {e}"
            logger.error(error_msg, exc_info=True)
            raise RestoreException(error_msg)

    def _restore_filesystem_backup(
        self,
        backup_path: Path,
        metadata: Dict[str, Any],
        container_name: str,
        override_config: Optional[Dict[str, Any]],
        start_after_restore: bool,
    ) -> Optional[str]:
        """Restore container from filesystem-only backup"""
        try:
            container_info = metadata["container_info"]
            image_name = container_info["image"]

            # Check if image exists
            if not self.docker_manager.get_image(image_name):
                logger.error(f"Image not found: {image_name}")
                logger.error("Cannot restore filesystem-only backup without image")
                return None

            # Create container configuration
            config = {
                "image": image_name,
                "name": container_name,
            }

            # Apply overrides
            if override_config:
                config.update(override_config)

            # Create container
            logger.info(f"Creating container '{container_name}'...")
            container = self.docker_manager.create_container(**config, detach=True)

            if not container:
                logger.error("Failed to create container")
                return None

            # Restore filesystem
            filesystem_archive = backup_path / "filesystem.tar.gz"
            if filesystem_archive.exists():
                logger.info("Restoring container filesystem...")
                if not self._restore_filesystem_data(container, filesystem_archive):
                    logger.error("Failed to restore filesystem data")
                    self.docker_manager.remove_container(container, force=True)
                    return None

            # Start container if requested
            if start_after_restore:
                logger.info("Starting container...")
                if not self.docker_manager.start_container(container):
                    logger.warning("Failed to start container")

            logger.info(f"Container restored successfully: {container.id}")
            return container.id

        except RestoreException:
            # Re-raise RestoreException to be caught by restore_container()
            raise
        except Exception as e:
            error_msg = f"Errore imprevisto durante ripristino filesystem backup: {e}"
            logger.error(error_msg, exc_info=True)
            raise RestoreException(error_msg)

    def _restore_filesystem_data(self, container, filesystem_archive: Path) -> bool:
        """
        Restore filesystem data to container

        Args:
            container: Docker container object
            filesystem_archive: Path to filesystem.tar.gz

        Returns:
            True if successful, False otherwise

        Raises:
            FilesystemRestoreException: If restore fails
        """
        try:
            logger.info("Decomprimendo archivio filesystem...")

            # Decompress filesystem archive
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_tar_path = Path(temp_dir) / "filesystem.tar"

                if not self._decompress_file(filesystem_archive, temp_tar_path):
                    raise FilesystemRestoreException("Decompressione archivio fallita")

                logger.info(f"Archivio decompresso: {temp_tar_path} ({temp_tar_path.stat().st_size} bytes)")

                # Verify tar file is valid
                try:
                    with tarfile.open(temp_tar_path, 'r') as tar:
                        members = tar.getmembers()
                        logger.info(f"Archivio contiene {len(members)} file/directory")
                except tarfile.TarError as e:
                    raise FilesystemRestoreException(f"Archivio tar non valido: {e}")

                # Put archive into container at root (/)
                # This extracts the filesystem backup into the container
                logger.info("Ripristinando filesystem nel container...")

                try:
                    with open(temp_tar_path, "rb") as f:
                        # put_archive extracts the tar archive into the container
                        # path='/' means extract at root, preserving directory structure
                        success = container.put_archive(path='/', data=f)

                        if not success:
                            raise FilesystemRestoreException("put_archive ha ritornato False")

                    logger.info("Filesystem ripristinato con successo nel container")
                    return True

                except Exception as e:
                    error_msg = f"Errore durante put_archive: {e}"
                    logger.error(error_msg, exc_info=True)
                    raise FilesystemRestoreException(error_msg)

        except FilesystemRestoreException:
            raise
        except Exception as e:
            error_msg = f"Errore imprevisto durante ripristino filesystem: {e}"
            logger.error(error_msg, exc_info=True)
            raise FilesystemRestoreException(error_msg)

    def _decompress_file(self, input_path: Path, output_path: Path) -> bool:
        """Decompress gzip file"""
        try:
            with gzip.open(input_path, "rb") as f_in:
                with open(output_path, "wb") as f_out:
                    while chunk := f_in.read(8388608):  # 8MB chunks
                        f_out.write(chunk)
            logger.debug(f"Decompressed {input_path.name} to {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Error decompressing file: {e}")
            return False

    def verify_backup_integrity(self, backup_id: str) -> bool:
        """
        Verify backup integrity

        Args:
            backup_id: Backup ID to verify

        Returns:
            True if backup is valid, False otherwise
        """
        try:
            metadata = self.backup_manager.get_backup_metadata(backup_id)
            if not metadata:
                return False

            backup_path = Path(metadata["backup_path"])

            # Verify all files exist
            for filename in metadata.get("files", []):
                file_path = backup_path / filename
                if not file_path.exists():
                    logger.error(f"Missing file: {filename}")
                    return False

            # Verify checksums
            for filename, expected_checksum in metadata.get("checksums", {}).items():
                file_path = backup_path / filename
                actual_checksum = self.backup_manager._calculate_checksum(file_path)
                if actual_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {filename}")
                    return False

            logger.info(f"Backup integrity verified: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Error verifying backup: {e}")
            return False

    def get_restore_preview(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get preview of what will be restored

        Args:
            backup_id: Backup ID

        Returns:
            Dictionary with restore preview information
        """
        try:
            metadata = self.backup_manager.get_backup_metadata(backup_id)
            if not metadata:
                return None

            container_info = metadata["container_info"]

            preview = {
                "backup_id": backup_id,
                "backup_type": metadata["backup_type"],
                "timestamp": metadata["timestamp"],
                "container_name": container_info["name"],
                "image": container_info["image"],
                "size": metadata.get("size_human", "Unknown"),
                "environment_variables": len(container_info.get("env", [])),
                "volumes": len(container_info.get("mounts", [])),
                "ports": len(container_info.get("ports", {})),
                "networks": container_info.get("networks", []),
                "files_included": metadata.get("files", []),
            }

            return preview

        except Exception as e:
            logger.error(f"Error getting restore preview: {e}")
            return None
