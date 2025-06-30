"""
CLI interface for nadle_backend package.
"""
import argparse
import logging
import sys
from pathlib import Path

# Import main application
from .config import settings


def start_server():
    """Start the FastAPI server."""
    try:
        import uvicorn
        import os
        # Import from parent directory
        import sys
        from pathlib import Path
        
        # Add parent directory to path to import main
        parent_dir = Path(__file__).parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        
        # Change to backend directory
        os.chdir(parent_dir)
        
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Starting {settings.api_title} server...")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Host: {settings.host}:{settings.port}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Start the server
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.environment == "development",
            log_level=settings.log_level.lower(),
            access_log=True
        )
        
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


def show_config():
    """Show current configuration."""
    print(f"nadle_backend Configuration:")
    print(f"  Environment: {settings.environment}")
    print(f"  API Title: {settings.api_title}")
    print(f"  Version: {settings.api_version}")
    print(f"  Host: {settings.host}")
    print(f"  Port: {settings.port}")
    print(f"  Database: {settings.database_name}")
    print(f"  Log Level: {settings.log_level}")
    print(f"  Docs Enabled: {settings.enable_docs}")


def check_health():
    """Check system health and dependencies."""
    import asyncio
    
    async def _check_health():
        try:
            from .database.connection import database
            
            # Check database connection
            await database.connect()
            print("✓ Database connection: OK")
            await database.disconnect()
            
            print("✓ Health check: All systems operational")
            return True
            
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    success = asyncio.run(_check_health())
    sys.exit(0 if success else 1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="nadle_backend CLI - FastAPI content management backend"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start server command
    start_parser = subparsers.add_parser('start', help='Start the FastAPI server')
    start_parser.add_argument(
        '--host', 
        default=settings.host,
        help=f'Host to bind to (default: {settings.host})'
    )
    start_parser.add_argument(
        '--port', 
        type=int,
        default=settings.port,
        help=f'Port to bind to (default: {settings.port})'
    )
    start_parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show current configuration')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check system health')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        # Override settings if provided
        if args.host != settings.host:
            settings.host = args.host
        if args.port != settings.port:
            settings.port = args.port
            
        start_server()
        
    elif args.command == 'config':
        show_config()
        
    elif args.command == 'health':
        check_health()
        
    elif args.command == 'version':
        from . import __version__
        print(f"nadle_backend version {__version__}")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()