# ducktyper/src/ducktyper/commands/certify.py
"""
Implementation of the 'certify' command.

The certify command generates and displays completion certificates
based on achievements and progress within the QuackVerse ecosystem.
"""

import hashlib
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ducktyper.src.ducktyper.ui.mode import is_playful_mode
from ducktyper.ui.branding import (
    COLOR_PALETTE,
    print_banner,
    print_error,
    print_info,
    print_success,
    quack_say,
    retro_box,
)
from ducktyper.utils import ensure_dir_exists, get_cache_dir
from quackcore.cli import CliContext

# Create Typer app for the certify command
app = typer.Typer(
    name="certify",
    help="Generate a completion certificate.",
    add_completion=False,
)

# Create console for rich output
console = Console()


def generate_certificate_hash(user_info: dict) -> str:
    """
    Generate a unique hash for a certificate.

    Args:
        user_info: User information

    Returns:
        Certificate hash
    """
    # Create a string with all the information
    info_str = "".join([
        user_info.get("name", ""),
        user_info.get("github_handle", ""),
        user_info.get("course", ""),
        user_info.get("completion_date", ""),
    ])

    # Generate a hash
    return hashlib.sha256(info_str.encode()).hexdigest()[:12]


def store_certificate_metadata(user_info: dict, cert_hash: str) -> str:
    """
    Store certificate metadata in the cache directory.

    Args:
        user_info: User information
        cert_hash: Certificate hash

    Returns:
        Path to the stored metadata file
    """
    # Ensure cache directory exists
    cache_dir = ensure_dir_exists(get_cache_dir() / "certificates")

    # Create metadata file
    cert_file = cache_dir / f"{cert_hash}.json"

    # Write metadata as JSON
    import json
    with open(cert_file, "w") as f:
        json.dump({
            "hash": cert_hash,
            "user_info": user_info,
            "generated_at": datetime.now().isoformat(),
        }, f, indent=2)

    return str(cert_file)


def render_certificate_ascii(user_info: dict, cert_hash: str) -> str:
    """
    Render an ASCII art certificate.

    Args:
        user_info: User information
        cert_hash: Certificate hash

    Returns:
        ASCII art certificate
    """
    name = user_info.get("name", "Anonymous Quacker")
    github = user_info.get("github_handle", "")
    course = user_info.get("course", "QuackVerse Course")
    date = user_info.get("completion_date", datetime.now().strftime("%Y-%m-%d"))

    # Create ASCII art certificate
    certificate = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                       🦆 CERTIFICATE OF COMPLETION 🦆                     ║
║                                                                          ║
║                         QUACKVERSE LEARNING PATH                         ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  This certifies that                                                     ║
║                                                                          ║
║  {name.center(66)}  ║
║  {f"@{github}".center(66) if github else " ".center(66)}  ║
║                                                                          ║
║  has successfully completed                                              ║
║                                                                          ║
║  {course.center(66)}  ║
║                                                                          ║
║  on {date.center(60)}  ║
║                                                                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Certificate ID: {cert_hash.ljust(50)}  ║
║                                                                          ║
║  Verify at: https://ducktyper.ai/verify/{cert_hash.ljust(37)}  ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    return certificate


def render_certificate_markdown(user_info: dict, cert_hash: str) -> str:
    """
    Render a Markdown certificate for sharing.

    Args:
        user_info: User information
        cert_hash: Certificate hash

    Returns:
        Markdown certificate
    """
    name = user_info.get("name", "Anonymous Quacker")
    github = user_info.get("github_handle", "")
    course = user_info.get("course", "QuackVerse Course")
    date = user_info.get("completion_date", datetime.now().strftime("%Y-%m-%d"))

    github_text = f"GitHub: @{github}" if github else ""

    markdown = f"""
# 🦆 Certificate of Completion

## QuackVerse Learning Path

This certifies that

### {name}
{github_text}

has successfully completed

## {course}

on {date}

---

**Certificate ID:** {cert_hash}  
**Verify at:** https://ducktyper.ai/verify/{cert_hash}

![QuackVerse](https://ducktyper.ai/badge/{course.lower().replace(" ", "-")}.svg)
"""
    return markdown


def render_certificate_svg(user_info: dict, cert_hash: str) -> str:
    """
    Render an SVG certificate for downloading.

    Args:
        user_info: User information
        cert_hash: Certificate hash

    Returns:
        SVG certificate
    """
    name = user_info.get("name", "Anonymous Quacker")
    github = user_info.get("github_handle", "")
    course = user_info.get("course", "QuackVerse Course")
    date = user_info.get("completion_date", datetime.now().strftime("%Y-%m-%d"))

    # This is a simplified SVG template - in a real implementation,
    # you'd have a more sophisticated design
    svg = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="600" fill="#f9f9f9" stroke="#333" stroke-width="2" />
  <text x="400" y="80" font-family="Arial" font-size="32" text-anchor="middle" fill="#333">
    Certificate of Completion
  </text>
  <text x="400" y="120" font-family="Arial" font-size="24" text-anchor="middle" fill="#666">
    QuackVerse Learning Path
  </text>
  <text x="400" y="170" font-family="Arial" font-size="18" text-anchor="middle" fill="#333">
    This certifies that
  </text>
  <text x="400" y="220" font-family="Arial" font-size="28" text-anchor="middle" font-weight="bold" fill="#333">
    {name}
  </text>
  <text x="400" y="250" font-family="Arial" font-size="18" text-anchor="middle" fill="#666">
    {f"@{github}" if github else ""}
  </text>
  <text x="400" y="300" font-family="Arial" font-size="18" text-anchor="middle" fill="#333">
    has successfully completed
  </text>
  <text x="400" y="350" font-family="Arial" font-size="28" text-anchor="middle" font-weight="bold" fill="#333">
    {course}
  </text>
  <text x="400" y="400" font-family="Arial" font-size="18" text-anchor="middle" fill="#333">
    on {date}
  </text>
  <text x="400" y="500" font-family="Arial" font-size="14" text-anchor="middle" fill="#666">
    Certificate ID: {cert_hash}
  </text>
  <text x="400" y="520" font-family="Arial" font-size="14" text-anchor="middle" fill="#666">
    Verify at: https://ducktyper.ai/verify/{cert_hash}
  </text>
  <!-- Duck logo -->
  <text x="400" y="450" font-family="Arial" font-size="48" text-anchor="middle" fill="#f39c12">
    🦆
  </text>
</svg>
"""
    return svg


def save_certificate(cert_format: str, content: str, cert_hash: str) -> str:
    """
    Save a certificate to disk.

    Args:
        cert_format: Certificate format ("svg", "md", or "txt")
        content: Certificate content
        cert_hash: Certificate hash

    Returns:
        Path to the saved certificate
    """
    # Ensure certificates directory exists
    cert_dir = ensure_dir_exists(Path.home() / "tests" / "certificates")

    # Determine file extension
    ext = {"svg": ".svg", "md": ".md", "txt": ".txt"}[cert_format]

    # Create filename
    filename = cert_dir / f"certificate_{cert_hash}{ext}"

    # Write certificate
    with open(filename, "w") as f:
        f.write(content)

    return str(filename)


@app.callback(invoke_without_command=True)
def generate_certificate(
        ctx: typer.Context,
        name: str | None = typer.Option(
            None, "--name", "-n", help="Your name"
        ),
        github: str | None = typer.Option(
            None, "--github", "-g", help="Your GitHub handle"
        ),
        course: str = typer.Option(
            "QuackVerse Fundamentals", "--course", "-c", help="Course name"
        ),
        date: str | None = typer.Option(
            None, "--date", "-d", help="Completion date (YYYY-MM-DD)"
        ),
        format: str = typer.Option(
            "all", "--format", "-f", help="Output format (svg, md, txt, or all)"
        ),
) -> None:
    """
    Generate a completion certificate.

    This command creates a certificate based on your achievements in the
    QuackVerse ecosystem. It generates a unique certificate ID and allows
    you to share your accomplishment.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Show welcome
        if is_playful_mode():
            print_banner("QuackVerse Certificate Generator",
                         "Celebrate your achievements!", mood="wizard")
            quack_say("Let's create a certificate for your accomplishments!")
        else:
            print_info("QuackVerse Certificate Generator")

        # Get user information interactively if not provided
        user_info = {}

        if name is None:
            user_info["name"] = Prompt.ask("Your name", default="")
        else:
            user_info["name"] = name

        if github is None:
            github_handle = Prompt.ask("Your GitHub handle (optional)", default="")
            if github_handle and not github_handle.startswith("@"):
                github_handle = f"@{github_handle}"
            user_info["github_handle"] = github_handle.strip("@")
        else:
            user_info["github_handle"] = github.strip("@")

        user_info["course"] = course

        if date is None:
            # Use current date by default
            user_info["completion_date"] = datetime.now().strftime("%Y-%m-%d")
        else:
            user_info["completion_date"] = date

        # Generate certificate hash
        cert_hash = generate_certificate_hash(user_info)

        # Store certificate metadata
        metadata_path = store_certificate_metadata(user_info, cert_hash)

        # Generate certificate based on format
        if format in ["txt", "all"]:
            ascii_cert = render_certificate_ascii(user_info, cert_hash)
            txt_path = save_certificate("txt", ascii_cert, cert_hash)

            if is_playful_mode():
                console.print(
                    Panel(ascii_cert, border_style=COLOR_PALETTE["highlight"]))
            else:
                print(ascii_cert)

            print_success(f"ASCII certificate saved to: {txt_path}")

        if format in ["md", "all"]:
            md_cert = render_certificate_markdown(user_info, cert_hash)
            md_path = save_certificate("md", md_cert, cert_hash)

            if format == "md":
                console.print(Markdown(md_cert))

            print_success(f"Markdown certificate saved to: {md_path}")

        if format in ["svg", "all"]:
            svg_cert = render_certificate_svg(user_info, cert_hash)
            svg_path = save_certificate("svg", svg_cert, cert_hash)
            print_success(f"SVG certificate saved to: {svg_path}")

            # Offer to open in browser
            if Confirm.ask("Open SVG certificate in browser?", default=True):
                # Create an HTML wrapper for the SVG
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>QuackVerse Certificate</title>
                    <style>
                        body {{ margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; }}
                        .certificate {{ max-width: 800px; max-height: 100vh; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                    </style>
                </head>
                <body>
                    {svg_cert}
                </body>
                </html>
                """

                # Save the HTML file
                html_path = svg_path.replace(".svg", ".html")
                with open(html_path, "w") as f:
                    f.write(html_content)

                # Open in browser
                webbrowser.open(f"file://{html_path}")

        # Share options
        if is_playful_mode():
            quack_say(f"Your certificate has been generated with ID: {cert_hash}")
            retro_box("Share Your Achievement", f"""
To share your certificate, use one of these methods:

1. Share the verification link:
   https://ducktyper.ai/verify/{cert_hash}

2. Add this badge to your GitHub profile:
   ![Certified QuackVerse Developer](https://ducktyper.ai/badge/{course.lower().replace(" ", "-")}.svg)
""")
        else:
            print_info(f"\nCertificate ID: {cert_hash}")
            print_info(f"Verification URL: https://ducktyper.ai/verify/{cert_hash}")
            print_info(
                f"\nGitHub Badge:\n![Certified QuackVerse Developer](https://ducktyper.ai/badge/{course.lower().replace(' ', '-')}.svg)")

    except KeyboardInterrupt:
        print("\nCertificate generation cancelled.")
    except Exception as e:
        print_error(f"Error generating certificate: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in certify command")
        sys.exit(1)


def verify_github_contributions(user_info: dict) -> bool:
    """
    Verify user's GitHub contributions for certification.

    Args:
        user_info: User information

    Returns:
        True if contributions verified, False otherwise
    """
    github_handle = user_info.get("github_handle")
    if not github_handle:
        return False

    try:
        # Initialize GitHub integration
        github = registry.get_integration("GitHub")
        init_result = github.initialize()

        if not init_result.success:
            return False

        # Get user information
        user_result = github.get_current_user()
        if not user_result.success:
            return False

        # Verify contributions to QuackVerse repos
        repos = ["tests-ai/tests", "tests-ai/quackcore",
                 "tests-ai/quackster"]

        for repo in repos:
            # Check if user has PRs to this repo
            prs_result = github.list_pull_requests(repo=repo, author=github_handle)
            if prs_result.success and prs_result.content:
                return True

        return False
    except Exception:
        return False
