"""
Docker container management for DockShield
"""

import docker
from docker.models.containers import Container
from docker.errors import DockerException, NotFound, APIError
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker container operations"""

    def __init__(self, socket_url: str = "unix:///var/run/docker.sock", timeout: int = 300):
        """
        Initialize Docker manager

        Args:
            socket_url: Docker socket URL
            timeout: Timeout for Docker operations in seconds
        """
        self.socket_url = socket_url
        self.timeout = timeout
        self.client: Optional[docker.DockerClient] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Docker daemon"""
        try:
            self.client = docker.DockerClient(base_url=self.socket_url, timeout=self.timeout)
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise ConnectionError(f"Cannot connect to Docker daemon at {self.socket_url}") from e

    def is_connected(self) -> bool:
        """
        Check if connected to Docker daemon

        Returns:
            True if connected, False otherwise
        """
        try:
            if self.client:
                self.client.ping()
                return True
        except Exception:
            pass
        return False

    def get_containers(self, all_containers: bool = True) -> List[Container]:
        """
        Get list of containers

        Args:
            all_containers: If True, include stopped containers

        Returns:
            List of Container objects
        """
        try:
            containers = self.client.containers.list(all=all_containers)
            logger.debug(f"Found {len(containers)} containers")
            return containers
        except DockerException as e:
            logger.error(f"Error listing containers: {e}")
            return []

    def get_container(self, container_id: str) -> Optional[Container]:
        """
        Get container by ID or name

        Args:
            container_id: Container ID or name

        Returns:
            Container object or None if not found
        """
        try:
            return self.client.containers.get(container_id)
        except NotFound:
            logger.warning(f"Container not found: {container_id}")
            return None
        except DockerException as e:
            logger.error(f"Error getting container {container_id}: {e}")
            return None

    def get_container_info(self, container: Container) -> Dict[str, Any]:
        """
        Get detailed container information

        Args:
            container: Container object

        Returns:
            Dictionary with container information
        """
        try:
            container.reload()
            attrs = container.attrs

            return {
                "id": container.id,
                "short_id": container.short_id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "created": attrs.get("Created"),
                "started": attrs.get("State", {}).get("StartedAt"),
                "ports": attrs.get("NetworkSettings", {}).get("Ports", {}),
                "mounts": attrs.get("Mounts", []),
                "env": attrs.get("Config", {}).get("Env", []),
                "labels": attrs.get("Config", {}).get("Labels", {}),
                "command": attrs.get("Config", {}).get("Cmd", []),
                "networks": list(attrs.get("NetworkSettings", {}).get("Networks", {}).keys()),
            }
        except Exception as e:
            logger.error(f"Error getting container info: {e}")
            return {}

    def get_container_logs(self, container: Container, lines: int = 1000) -> str:
        """
        Get container logs

        Args:
            container: Container object
            lines: Number of log lines to retrieve

        Returns:
            Container logs as string
        """
        try:
            logs = container.logs(tail=lines, timestamps=True)
            return logs.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            return ""

    def stop_container(self, container: Container, timeout: int = 10) -> bool:
        """
        Stop container

        Args:
            container: Container object
            timeout: Timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            container.stop(timeout=timeout)
            logger.info(f"Stopped container {container.name}")
            return True
        except Exception as e:
            logger.error(f"Error stopping container {container.name}: {e}")
            return False

    def start_container(self, container: Container) -> bool:
        """
        Start container

        Args:
            container: Container object

        Returns:
            True if successful, False otherwise
        """
        try:
            container.start()
            logger.info(f"Started container {container.name}")
            return True
        except Exception as e:
            logger.error(f"Error starting container {container.name}: {e}")
            return False

    def export_container_filesystem(self, container: Container, output_path: str) -> bool:
        """
        Export container filesystem

        Args:
            container: Container object
            output_path: Path to save exported filesystem

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, "wb") as f:
                for chunk in container.export():
                    f.write(chunk)
            logger.info(f"Exported container {container.name} filesystem to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting container filesystem: {e}")
            return False

    def commit_container(self, container: Container, repository: str, tag: str = "backup") -> bool:
        """
        Commit container to image

        Args:
            container: Container object
            repository: Image repository name
            tag: Image tag

        Returns:
            True if successful, False otherwise
        """
        try:
            container.commit(repository=repository, tag=tag)
            logger.info(f"Committed container {container.name} to image {repository}:{tag}")
            return True
        except Exception as e:
            logger.error(f"Error committing container: {e}")
            return False

    def get_image(self, image_name: str):
        """
        Get image by name

        Args:
            image_name: Image name or ID

        Returns:
            Image object or None
        """
        try:
            return self.client.images.get(image_name)
        except NotFound:
            logger.warning(f"Image not found: {image_name}")
            return None
        except DockerException as e:
            logger.error(f"Error getting image {image_name}: {e}")
            return None

    def save_image(self, image_name: str, output_path: str) -> bool:
        """
        Save image to tar file

        Args:
            image_name: Image name or ID
            output_path: Path to save image

        Returns:
            True if successful, False otherwise
        """
        try:
            image = self.get_image(image_name)
            if not image:
                return False

            with open(output_path, "wb") as f:
                for chunk in image.save():
                    f.write(chunk)
            logger.info(f"Saved image {image_name} to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return False

    def load_image(self, image_path: str) -> bool:
        """
        Load image from tar file

        Args:
            image_path: Path to image tar file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(image_path, "rb") as f:
                self.client.images.load(f)
            logger.info(f"Loaded image from {image_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return False

    def create_container(
        self,
        image: str,
        name: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        ports: Optional[Dict[str, int]] = None,
        **kwargs
    ) -> Optional[Container]:
        """
        Create new container

        Args:
            image: Image name
            name: Container name
            environment: Environment variables
            volumes: Volume mappings
            ports: Port mappings
            **kwargs: Additional arguments for container creation

        Returns:
            Container object or None if failed
        """
        try:
            container = self.client.containers.create(
                image=image,
                name=name,
                environment=environment,
                volumes=volumes,
                ports=ports,
                **kwargs
            )
            logger.info(f"Created container {name or container.id}")
            return container
        except Exception as e:
            logger.error(f"Error creating container: {e}")
            return None

    def remove_container(self, container: Container, force: bool = False) -> bool:
        """
        Remove container

        Args:
            container: Container object
            force: Force removal

        Returns:
            True if successful, False otherwise
        """
        try:
            container.remove(force=force)
            logger.info(f"Removed container {container.name}")
            return True
        except Exception as e:
            logger.error(f"Error removing container: {e}")
            return False

    def get_volumes(self) -> List[Dict[str, Any]]:
        """
        Get list of volumes

        Returns:
            List of volume information dictionaries
        """
        try:
            volumes = self.client.volumes.list()
            return [
                {
                    "name": vol.name,
                    "driver": vol.attrs.get("Driver"),
                    "mountpoint": vol.attrs.get("Mountpoint"),
                }
                for vol in volumes
            ]
        except Exception as e:
            logger.error(f"Error listing volumes: {e}")
            return []

    def close(self) -> None:
        """Close Docker client connection"""
        if self.client:
            self.client.close()
            logger.info("Docker client connection closed")
