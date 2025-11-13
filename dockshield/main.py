#!/usr/bin/env python3
"""
DockShield - Docker Container Backup and Restore for KDE Plasma
Main application entry point
"""

import sys
import argparse
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

from dockshield import __version__
from dockshield.core.config import Config
from dockshield.utils.logger import setup_logging
from dockshield.ui.main_window import MainWindow


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="DockShield - Docker Container Backup and Restore for KDE Plasma",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"DockShield {__version__}",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to configuration file",
    )

    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level",
    )

    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run without GUI (CLI mode - not yet implemented)",
    )

    return parser.parse_args()


def setup_application(config: Config) -> QApplication:
    """
    Setup Qt application

    Args:
        config: Application configuration

    Returns:
        QApplication instance
    """
    # Set application metadata
    QCoreApplication.setOrganizationName("DockShield")
    QCoreApplication.setOrganizationDomain("dockshield.org")
    QCoreApplication.setApplicationName("DockShield")
    QCoreApplication.setApplicationVersion(__version__)

    # Create application
    app = QApplication(sys.argv)

    # Set application style
    theme = config.get("ui.theme", "auto")

    if theme == "dark":
        # Apply dark theme
        app.setStyle("Fusion")
        # Note: Full dark theme would be applied in MainWindow

    return app


def main():
    """Main application entry point"""
    # Parse arguments
    args = parse_arguments()

    # Load configuration
    config = Config(config_path=args.config)

    # Setup logging
    log_level = args.log_level or config.get("general.log_level", "INFO")
    log_file = config.get_log_file()
    setup_logging(log_file=log_file, log_level=log_level)

    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Starting DockShield {__version__}")
    logger.info(f"Configuration loaded from: {config.config_path or 'defaults'}")

    # Check for CLI mode
    if args.no_gui:
        logger.error("CLI mode not yet implemented")
        print("Error: CLI mode is not yet implemented")
        print("Please run without --no-gui flag to use the GUI")
        sys.exit(1)

    # Create and run GUI application
    try:
        app = setup_application(config)

        # Create main window
        main_window = MainWindow(config)
        main_window.show()

        logger.info("Application started successfully")

        # Run application
        sys.exit(app.exec())

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
