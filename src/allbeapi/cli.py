import typer
import sys
import os
import subprocess
import asyncio
import json
import importlib
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import internal modules
# We need to ensure the current directory is in sys.path to import allbeapi if it's not installed
sys.path.append(os.getcwd())

try:
    from allbeapi.analyzer import APIAnalyzer
    from allbeapi.generator import generate_mcp_server, generate_requirements
    from allbeapi.utils.installer import install_dependency
except ImportError as e:
    print(f"Error importing allbeapi modules: {e}")
    print("Please ensure you are running this from the root of the project or have allbeapi installed.")
    sys.exit(1)

app = typer.Typer(help="AllBeAPI - Turn any Python library into an MCP Server")
console = Console()

def _ensure_library_installed(library_name: str):
    """Helper to ensure library is installed"""
    with console.status(f"[bold green]Checking library {library_name}...[/bold green]"):
        try:
            install_dependency(library_name)
            console.print(f"[green][OK] Library {library_name} is ready[/green]")
        except Exception as e:
            console.print(f"[red][ERROR] Failed to install {library_name}: {e}[/red]")
            raise typer.Exit(code=1)

def _run_analysis(library_name: str) -> APIAnalyzer:
    """Helper to run analysis"""
    console.print(f"[bold blue]Analyzing {library_name}...[/bold blue]")
    
    # Initialize analyzer with default settings
    analyzer = APIAnalyzer(
        library_name=library_name,
        max_depth=2,
        enable_quality_filter=True,
        quality_mode='balanced'
    )
    
    # Run analysis
    spec = analyzer.analyze()
    
    if "error" in spec:
        console.print(f"[red]Analysis failed: {spec['error']}[/red]")
        raise typer.Exit(code=1)
        
    return analyzer, spec

@app.command()
def inspect(library_name: str):
    """
    Analyze a library and show API quality report without generating files.
    """
    _ensure_library_installed(library_name)
    
    try:
        analyzer, _ = _run_analysis(library_name)
        stats = analyzer.quality_stats
        
        if not stats:
            console.print("[yellow]No quality stats available.[/yellow]")
            return

        # Display Summary
        console.print("\n[bold]Analysis Report[/bold]")
        console.print(f"Total Modules Scanned: {stats.get('total_modules_scanned', 0)}")
        console.print(f"Total Functions Found: {stats.get('total_functions_found', 0)}")
        console.print(f"Exposed APIs: [bold green]{stats.get('functions_after_filtering', 0)}[/bold green]")
        console.print(f"Average Quality Score: [bold blue]{stats.get('avg_score', 0):.1f}/100[/bold blue]")
        
        # Display Score Distribution
        table = Table(title="Quality Score Distribution")
        table.add_column("Score Range", style="cyan")
        table.add_column("Count", style="magenta")
        
        dist = stats.get('score_distribution', {})
        for range_name, count in dist.items():
            table.add_row(range_name, str(count))
        
        console.print(table)
        
        # Display Top APIs
        top_apis = stats.get('top_10_functions', [])
        if top_apis:
            console.print("\n[bold]Top Rated APIs:[/bold]")
            for i, api in enumerate(top_apis, 1):
                console.print(f"{i}. {api['name']} (Score: {api['score']})")

    except Exception as e:
        console.print(f"[red]Error during inspection: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def generate(
    library_name: str, 
    output_dir: str = typer.Option(".", help="Directory to output generated files")
):
    """
    Generate MCP server code for a library.
    """
    _ensure_library_installed(library_name)
    
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        analyzer, spec = _run_analysis(library_name)
        
        # Generate Server Code
        server_file = output_path / f"{library_name}_mcp_server.py"
        console.print(f"Generating server code at {server_file}...")
        generate_mcp_server(spec, str(server_file), library_name)
        
        # Generate Requirements
        console.print("Generating requirements...")
        # Note: generate_requirements currently writes to CWD, we might need to move it
        # For now, we assume it writes to CWD and we move it if needed, 
        # or we just let it be since generate_requirements implementation is simple.
        # Let's check generate_requirements implementation... it writes to f"{library_name}_mcp_requirements.txt"
        generate_requirements(library_name)
        
        req_file = Path(f"{library_name}_mcp_requirements.txt")
        if output_path != Path("."):
            if req_file.exists():
                target_req = output_path / req_file.name
                req_file.rename(target_req)
                console.print(f"Moved requirements to {target_req}")

        console.print(f"[bold green][OK] Successfully generated MCP server for {library_name}[/bold green]")
        console.print(f"Run it with: [bold]python {server_file}[/bold]")

    except Exception as e:
        console.print(f"[red]Error during generation: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def start(
    library_name: str,
    port: int = typer.Option(8000, help="Port to bind the server to"),
    host: str = typer.Option("127.0.0.1", help="Host to bind the server to"),
    rebuild: bool = typer.Option(False, help="Force regenerate server code")
):
    """
    One-click start: Install, Generate, and Run the MCP server.
    """
    _ensure_library_installed(library_name)
    
    server_file = Path(f"{library_name}_mcp_server.py")
    
    # Check if generation is needed
    if rebuild or not server_file.exists():
        console.print("[yellow]Server code not found or rebuild requested. Generating...[/yellow]")
        try:
            analyzer, spec = _run_analysis(library_name)
            generate_mcp_server(spec, str(server_file), library_name)
            generate_requirements(library_name)
        except Exception as e:
            console.print(f"[red]Generation failed: {e}[/red]")
            raise typer.Exit(code=1)
    else:
        console.print(f"[green][OK] Found existing server code: {server_file}[/green]")

    # Start the server
    console.print(f"[bold green][START] Starting {library_name} MCP Server on http://{host}:{port}/mcp[/bold green]")
    
    cmd = [
        sys.executable,
        str(server_file),
        "--http",
        "--host", host,
        "--port", str(port)
    ]
    
    try:
        # Use subprocess to run the server
        # We don't capture output so it streams to the console
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user.[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]Server crashed with exit code {e.returncode}[/red]")
        raise typer.Exit(code=e.returncode)
    except Exception as e:
        console.print(f"\n[red]Failed to start server: {e}[/red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
