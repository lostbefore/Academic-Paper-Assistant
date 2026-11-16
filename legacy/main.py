"""
Academic Paper Assistant - Main Entry Point

An AI-powered academic paper assistant designed for university students.
Helps generate high-quality academic papers based on title or research topic.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from plugin.paper_plugin import PaperAssistantPlugin
from config import Config


def main():
    """Main entry point for the Academic Paper Assistant."""
    print("=" * 60)
    print("Academic Paper Assistant for Universities")
    print("=" * 60)

    # Validate configuration
    config_status = Config.validate()
    if not config_status['valid']:
        print("\n❌ Configuration Errors:")
        for issue in config_status['issues']:
            print(f"   - {issue}")
        print("\nPlease check your .env file.")
        sys.exit(1)

    if config_status['warnings']:
        print("\n⚠️  Warnings:")
        for warning in config_status['warnings']:
            print(f"   - {warning}")

    # Show configuration summary
    print(f"\n📋 Configuration:")
    config_dict = Config.to_dict()
    print(f"   - Images: {'✅ Enabled' if config_dict['enable_images'] else '❌ Disabled'}")
    print(f"   - Max images per paper: {config_dict['max_images_per_paper']}")
    print(f"   - Image sources: {', '.join(config_dict['image_sources'])}")
    print(f"   - Web search: {'✅ Configured' if config_dict['web_search_configured'] else '⚠️ Limited'}")
    print(f"   - Citation style: {config_dict['default_citation_style'].upper()}")
    print()

    print("Available Commands:")
    print("  /new-paper  - Create a new academic paper")
    print("  /help       - Show help information")
    print("  /quit       - Exit the application")
    print()

    plugin = PaperAssistantPlugin()

    try:
        while True:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
                    print("\nThank you for using Academic Paper Assistant. Goodbye!")
                    break

                if user_input.lower() in ["/help", "help"]:
                    plugin.show_help()
                    continue

                # Process the command
                result = plugin.process_command(user_input)

                if result:
                    print("\n" + "=" * 60)
                    print("RESULT")
                    print("=" * 60)
                    print(result)

            except KeyboardInterrupt:
                print("\n\nOperation cancelled.")
                continue
            except Exception as e:
                print(f"\nError: {e}")
                continue

    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
