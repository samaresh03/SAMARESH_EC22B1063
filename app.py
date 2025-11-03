#!/usr/bin/env python
"""
Quant Trading Dashboard - Unified Application Runner

This script starts both the FastAPI backend and Streamlit frontend in separate processes.
Run this script to launch the complete application.

Usage:
    python app.py
    
Then open:
    - Backend API: http://localhost:8000/api/docs
    - Frontend Dashboard: http://localhost:8501
"""

import subprocess
import sys
import time
import os
from pathlib import Path
import signal
import atexit
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Store process references for cleanup
processes = []

def cleanup():
    """Cleanup function to terminate all child processes"""
    logger.info("Shutting down application...")
    for process in processes:
        try:
            if process.poll() is None:  # Process is still running
                logger.info(f"Terminating process {process.pid}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing process {process.pid}...")
                    process.kill()
        except Exception as e:
            logger.error(f"Error terminating process: {e}")
    logger.info("Application shutdown complete")

# Register cleanup function
atexit.register(cleanup)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("\nReceived interrupt signal, shutting down...")
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'fastapi': 'FastAPI',
        'streamlit': 'Streamlit',
        'pandas': 'Pandas',
        'sqlalchemy': 'SQLAlchemy',
        'plotly': 'Plotly',
        'statsmodels': 'Statsmodels'
    }
    
    missing_packages = []
    for package, name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(name)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Please install dependencies: pip install -r requirements.txt")
        return False
    
    return True

def initialize_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    try:
        os.chdir(BACKEND_DIR)
        result = subprocess.run(
            [sys.executable, "-c", "from app.models import init_db; init_db()"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            logger.warning(f"Database initialization warning: {result.stderr}")
        else:
            logger.info("Database initialized successfully")
        
        os.chdir(PROJECT_ROOT)
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        os.chdir(PROJECT_ROOT)
        return False

def start_backend():
    """Start the FastAPI backend server"""
    logger.info("Starting FastAPI backend server...")
    logger.info(f"Backend directory: {BACKEND_DIR}")
    
    try:
        # Change to backend directory
        os.chdir(BACKEND_DIR)
        
        # Start the backend process
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        processes.append(process)
        logger.info(f"Backend server started (PID: {process.pid})")
        logger.info("Backend API will be available at: http://localhost:8000/api/docs")
        
        # Change back to project root
        os.chdir(PROJECT_ROOT)
        
        return process
        
    except Exception as e:
        logger.error(f"Error starting backend: {e}")
        os.chdir(PROJECT_ROOT)
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    logger.info("Starting Streamlit frontend...")
    logger.info(f"Frontend directory: {FRONTEND_DIR}")
    
    try:
        # Change to frontend directory
        os.chdir(FRONTEND_DIR)
        
        # Start the frontend process
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--logger.level=info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        processes.append(process)
        logger.info(f"Frontend started (PID: {process.pid})")
        logger.info("Frontend dashboard will be available at: http://localhost:8501")
        
        # Change back to project root
        os.chdir(PROJECT_ROOT)
        
        return process
        
    except Exception as e:
        logger.error(f"Error starting frontend: {e}")
        os.chdir(PROJECT_ROOT)
        return None

def monitor_processes():
    """Monitor running processes and log output"""
    logger.info("Monitoring processes...")
    
    while True:
        try:
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    # Process has terminated
                    logger.error(f"Process {i} (PID: {process.pid}) has terminated unexpectedly")
                    
                    # Try to read any remaining output
                    stdout, stderr = process.communicate(timeout=1)
                    if stderr:
                        logger.error(f"Process error output:\n{stderr}")
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error monitoring processes: {e}")
            time.sleep(5)

def main():
    """Main application entry point"""
    logger.info("=" * 70)
    logger.info("Quant Trading Dashboard - Starting Application")
    logger.info("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        logger.warning("Database initialization failed, continuing anyway...")
    
    # Wait a moment before starting services
    time.sleep(1)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        logger.error("Failed to start backend server")
        sys.exit(1)
    
    # Wait for backend to be ready
    logger.info("Waiting for backend to be ready...")
    time.sleep(3)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        logger.error("Failed to start frontend")
        cleanup()
        sys.exit(1)
    
    # Wait for frontend to be ready
    logger.info("Waiting for frontend to be ready...")
    time.sleep(3)
    
    logger.info("=" * 70)
    logger.info("Application Started Successfully!")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Backend API:      http://localhost:8000/api/docs")
    logger.info("Frontend:         http://localhost:8501")
    logger.info("")
    logger.info("Press Ctrl+C to stop the application")
    logger.info("=" * 70)
    
    # Monitor processes
    try:
        monitor_processes()
    except KeyboardInterrupt:
        logger.info("\nShutdown signal received")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
