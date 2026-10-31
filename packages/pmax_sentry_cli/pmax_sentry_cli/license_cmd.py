from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

import json
from pmax_sentry_pro._auth import verify_license, get_polar_org_id, ORG_ID_FILE

app = typer.Typer(name="license", help="Manage PMax Sentry Pro license keys and subscription status.")
console = Console()

DEFAULT_POLAR_URL = "https://polar.sh/pmax-sentry"
LICENSE_FILE = Path.home() / ".pmax_license_key"
CHECKOUT_URL_FILE = Path.home() / ".pmax_polar_url"


def get_checkout_url() -> str:
    if "POLAR_CHECKOUT_URL" in os.environ and os.environ["POLAR_CHECKOUT_URL"].strip():
        return os.environ["POLAR_CHECKOUT_URL"].strip()
    if CHECKOUT_URL_FILE.exists():
        try:
            val = CHECKOUT_URL_FILE.read_text(encoding="utf-8").strip()
            if val:
                return val
        except Exception:
            pass
    return DEFAULT_POLAR_URL



def get_stored_key() -> Optional[str]:
    if "PMAX_API_KEY" in os.environ:
        return os.environ["PMAX_API_KEY"]
    if "PMAX_LICENSE_KEY" in os.environ:
        return os.environ["PMAX_LICENSE_KEY"]
    if LICENSE_FILE.exists():
        try:
            return LICENSE_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return None


@app.command("status")
def status_cmd() -> None:
    """Check current PMax Sentry Pro license status and tier."""
    key = get_stored_key()
    if not key:
        console.print(
            Panel(
                Text(
                    "No PMax Sentry Pro license active.\n"
                    "Running in Free Open-Core mode.\n\n"
                    "Upgrade to unlock White-Label Pitch Decks, Business Data Ingestion, "
                    "and Causal Incrementality Validation.\n"
                    f"Buy link: {get_checkout_url()}",
                    style="yellow",
                ),
                title="[bold yellow]License Status: Free Tier[/bold yellow]",
                border_style="yellow",
            )
        )
        return

    try:
        res = verify_license(key)
        tier_title = "Agency Pro (Unlimited White-Label Decks)" if res["tier"] == "agency_pro" else "Single Audit Pass"
        cached_info = " (24h local HMAC cache)" if res.get("cached") else ""
        test_info = " [TEST MODE]" if res.get("test_mode") else ""

        text = Text()
        text.append(f"Status:        ACTIVE / GRANTED{test_info}\n", style="bold green")
        text.append(f"Tier:          {tier_title}\n", style="bold cyan")
        text.append(f"Account Limit: {res.get('accounts_limit', 1)} accounts\n")
        text.append(f"Source:        Polar.sh API{cached_info}\n", style="dim")
        masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "****"
        text.append(f"Key:           {masked_key}\n", style="dim")

        console.print(
            Panel(
                text,
                title="[bold green][OK] PMax Sentry Pro License Active[/bold green]",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(f"[bold red]License verification failed:[/bold red] {e}")


@app.command("activate")
def activate_cmd(
    key: str = typer.Argument(..., help="Polar.sh license key (e.g. PMAX_PRO_... or PMAX_TEST_AGENCY_PRO_KEY_12345)"),
) -> None:
    """Activate a PMax Sentry Pro license key and save locally."""
    try:
        res = verify_license(key.strip())
        LICENSE_FILE.write_text(key.strip(), encoding="utf-8")
        console.print(f"[bold green][OK] License successfully activated![/bold green] Tier: [bold cyan]{res['tier']}[/bold cyan]")
        console.print(f"Key saved to {LICENSE_FILE}")
    except Exception as e:
        console.print(f"[bold red]Activation failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("buy")
def buy_cmd() -> None:
    """Print checkout buy links for PMax Sentry Pro on Polar.sh."""
    base_url = get_checkout_url()
    text = Text()
    text.append("PMax Sentry Pro - Official Polar.sh Checkout Tiers\n\n", style="bold white")
    text.append("1. Single Audit Pass (149 EUR one-time):\n", style="bold yellow")
    text.append("   - Single customer ID full audit & reconciliation\n")
    text.append("   - Standalone White-Label HTML/PDF Pitch Deck\n")
    text.append(f"   Buy Link: {base_url}/products/single-pass\n\n", style="cyan")

    text.append("2. Agency Pro Retainer (149 EUR / month):\n", style="bold green")
    text.append("   - Up to 50 client Google Ads accounts\n")
    text.append("   - Unlimited White-Label Pitch Decks for new-business pitches\n")
    text.append("   - Causal Experiment Design & Power Protocol Generator\n")
    text.append("   - FastMCP server integration for Cursor & Claude Desktop\n")
    text.append(f"   Buy Link: {base_url}/products/agency-pro\n\n", style="cyan")

    text.append("Instant delivery: Polar.sh automatically generates your license key upon checkout.", style="dim")
    console.print(Panel(text, title="[bold]Polar.sh Checkout[/bold]", border_style="blue"))


@app.command("config")
def config_cmd(
    org_id: Optional[str] = typer.Option(None, "--org-id", help="Polar.sh Organization ID (UUID)"),
    checkout_url: Optional[str] = typer.Option(None, "--checkout-url", help="Base Polar checkout URL"),
) -> None:
    """Configure custom Polar.sh Organization ID and checkout URL."""
    updated = False
    if org_id is not None:
        ORG_ID_FILE.write_text(org_id.strip(), encoding="utf-8")
        console.print(f"[bold green][OK][/bold green] Set Polar Org ID: [cyan]{org_id.strip()}[/cyan]")
        updated = True
    if checkout_url is not None:
        CHECKOUT_URL_FILE.write_text(checkout_url.strip(), encoding="utf-8")
        console.print(f"[bold green][OK][/bold green] Set Polar Checkout URL: [cyan]{checkout_url.strip()}[/cyan]")
        updated = True

    if not updated:
        curr_org = get_polar_org_id()
        curr_url = get_checkout_url()
        console.print(f"Polar Org ID:      [cyan]{curr_org}[/cyan]")
        console.print(f"Polar Checkout URL:[cyan]{curr_url}[/cyan]")

