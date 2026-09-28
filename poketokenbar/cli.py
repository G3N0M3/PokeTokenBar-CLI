"""CLI entry point for PokeTokenBar: launches interactive terminal user interface."""

from poketokenbar.tui import PokeTokenBarTUI


def main():
    """Launch the interactive TUI application."""
    tui = PokeTokenBarTUI()
    tui.run()


if __name__ == "__main__":
    main()
