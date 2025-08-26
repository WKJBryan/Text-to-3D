#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

def read_requirements():
    """Read requirements from requirements.txt"""
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            return [line.strip() for line in f 
                   if line.strip() and not line.startswith('#')]
    return []

def read_long_description():
    """Read long description from README"""
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name="text-to-3d-cad",
    version="1.0.0",
    author="Bryan Wang",
    author_email="bryan_wang@mymail.sutd.edu.sg",
    description="AI-powered 3D CAD generation system with RAG and intelligent reasoning",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/WKJBryan/Text-to-3D",
    
    # Package discovery
    packages=find_packages(),
    include_package_data=True,
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Extra dependencies for development
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
        "gpu": [
            "faiss-gpu>=1.7.4",  # Alternative to faiss-cpu
        ],
    },
    
    # Console scripts - users can run 'text-to-3d' after installation
    entry_points={
        "console_scripts": [
            "text-to-3d=main:main",
            "text-to-3d-gui=desktop_app:main",
        ],
    },
    
    # Package metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing", 
        "Topic :: Scientific/Engineering :: Computer Aided Design",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    
    python_requires=">=3.9",
    keywords=[
        "CAD", "AI", "RAG", "3D-modeling", "manufacturing", 
        "ollama", "cadquery", "desktop-app", "machine-learning",
        "retrieval-augmented-generation", "computer-aided-design"
    ],
    
    # Important: tells setuptools this is not a zip-safe package
    zip_safe=False,
)