#!/usr/bin/env python3
"""
Pre-cache the sentence transformer model during build time
This ensures the model is downloaded and ready when the server starts
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def precache_model():
    """Download and cache the sentence transformer model"""
    try:
        logger.info("Starting model pre-cache process...")

        # Import sentence transformers
        from sentence_transformers import SentenceTransformer

        # Load the model (this downloads and caches it)
        model_name = 'all-MiniLM-L12-v2'
        logger.info(f"Loading model: {model_name}")
        model = SentenceTransformer(model_name)

        # Test the model with a simple encoding
        test_text = "test"
        embedding = model.encode(test_text)

        logger.info(f"Model loaded successfully! Embedding dimension: {len(embedding)}")
        logger.info("Pre-cache process completed successfully")

    except Exception as e:
        logger.error(f"Pre-cache failed: {e}")
        raise

if __name__ == '__main__':
    precache_model()