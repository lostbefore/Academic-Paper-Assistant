"""
PaperAssistantPlugin - Main controller for the Academic Paper Assistant.

This plugin coordinates between agents, skills, and commands to provide
a complete academic paper writing experience.
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from dotenv import load_dotenv

from agents.researcher_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from skills.literature_search import LiteratureSearchSkill
from skills.academic_rules import AcademicRulesSkill
from skills.formatting import FormattingSkill
from commands.new_paper import NewPaperCommand
from commands.format import FormatCommand

# Load environment variables
load_dotenv()


class PaperAssistantPlugin:
    """
    Main plugin class that coordinates the academic paper assistant system.

    Responsibilities:
    - Dispatch commands
    - Manage workflow between agents
    - Coordinate skills
    - Assemble final results
    """

    def __init__(self):
        """Initialize the plugin with all agents and skills."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.api_base = os.getenv("ANTHROPIC_API_BASE", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6-20251001")

        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not set. Please check your .env file.")

        # Initialize skills
        self.literature_skill = LiteratureSearchSkill()
        self.academic_rules_skill = AcademicRulesSkill()
        self.formatting_skill = FormattingSkill()

        # Initialize agents with API key and optional base URL
        self.research_agent = ResearchAgent(
            api_key=self.api_key,
            api_base=self.api_base,
            model=self.model,
            literature_skill=self.literature_skill
        )
        self.writer_agent = WriterAgent(
            api_key=self.api_key,
            api_base=self.api_base,
            model=self.model,
            academic_rules_skill=self.academic_rules_skill
        )

        # Initialize commands
        self.new_paper_cmd = NewPaperCommand(
            research_agent=self.research_agent,
            writer_agent=self.writer_agent
        )
        self.format_cmd = FormatCommand(
            formatting_skill=self.formatting_skill
        )

    def process_command(self, user_input: str) -> Optional[str]:
        """
        Process user input and dispatch to appropriate command.

        Args:
            user_input: The raw input from the user

        Returns:
            Result string or None if command not recognized
        """
        if not user_input.startswith("/"):
            return "Unknown command. Type /help for available commands."

        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "/new-paper":
            return self.new_paper_cmd.execute(args)
        elif command == "/format":
            return self.format_cmd.execute(args)
        else:
            return f"Unknown command: {command}. Type /help for available commands."

    def show_help(self) -> None:
        """Display help information."""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║              Academic Paper Assistant - Help                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  /new-paper                                                  ║
║    Create a new academic paper.                              ║
║    Interactive mode will prompt for:                         ║
║      - Title: Paper title                                    ║
║      - Keywords: Research keywords (comma-separated)         ║
║      - Field: Research field/domain                          ║
║      - Length: Expected paper length (short/medium/long)     ║
║      - Citation Style: apa, mla, ieee, gbt7714               ║
║                                                              ║
║  /format <style> [<filepath>]                                ║
║    Format a paper with specified citation style.             ║
║    Styles: apa, mla, ieee, gbt7714                           ║
║                                                              ║
║  /help                                                       ║
║    Show this help message.                                   ║
║                                                              ║
║  /quit or /exit                                              ║
║    Exit the application.                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(help_text)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the plugin and its components.

        Returns:
            Dictionary with status information
        """
        return {
            "plugin": "PaperAssistantPlugin",
            "api_key_configured": bool(self.api_key),
            "agents": {
                "research": self.research_agent is not None,
                "writer": self.writer_agent is not None,
            },
            "skills": {
                "literature_search": self.literature_skill is not None,
                "academic_rules": self.academic_rules_skill is not None,
                "formatting": self.formatting_skill is not None,
            },
            "commands": {
                "new_paper": self.new_paper_cmd is not None,
                "format": self.format_cmd is not None,
            }
        }
