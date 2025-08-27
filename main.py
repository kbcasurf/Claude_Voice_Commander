#!/usr/bin/env python3
"""
Claude Voice Commander - Main Entry Point

A voice automation system that captures microphone input, converts speech to text 
using OpenAI Whisper, and sends commands to Claude Code CLI programmatically.
"""

import asyncio
import logging
from src.config import Config
from src.voice_commander import VoiceCommander


async def main():
    """Main entry point for the voice commander application."""
    try:
        # Initialize configuration
        config = Config()
        
        # Set up logging
        logging.basicConfig(
            level=config.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        
        logger.info("Starting Claude Voice Commander...")
        
        # Initialize and run voice commander
        commander = VoiceCommander(config)
        await commander.start()
        
    except KeyboardInterrupt:
        logger.info("Voice Commander stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())