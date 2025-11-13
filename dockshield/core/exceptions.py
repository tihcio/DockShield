"""
Custom exceptions for DockShield
"""


class DockShieldException(Exception):
    """Base exception for DockShield"""
    pass


class BackupException(DockShieldException):
    """Exception raised during backup operations"""
    pass


class RestoreException(DockShieldException):
    """Exception raised during restore operations"""
    pass


class ContainerNotFoundException(RestoreException):
    """Exception raised when container is not found"""
    pass


class ImageNotFoundException(RestoreException):
    """Exception raised when image is not found"""
    pass


class ContainerExistsException(RestoreException):
    """Exception raised when container already exists"""
    pass


class BackupNotFoundException(RestoreException):
    """Exception raised when backup is not found"""
    pass


class FilesystemRestoreException(RestoreException):
    """Exception raised when filesystem restore fails"""
    pass


class DockerConnectionException(DockShieldException):
    """Exception raised when Docker connection fails"""
    pass
