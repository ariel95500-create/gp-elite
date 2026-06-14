"""Point d'entrée ligne de commande : `gp-elite` ou `python -m gp_elite`.

Lance le menu interactif du moteur (modes 1-D, N-D, Syracuse, CSV générique).
Le guard if __name__ est requis pour le parallélisme (multiprocessing spawn).
"""
import sys
import traceback

from . import core


def main():
    try:
        core._interactive_menu()
    except KeyboardInterrupt:
        print("\nInterrompu.")
        sys.exit(130)
    except Exception:
        print("\n" + "=" * 70)
        print("ERREUR FATALE — traceback complet :")
        print("=" * 70)
        traceback.print_exc()
        print("=" * 70)
        try:
            input("\nAppuyez sur Entrée pour quitter...")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
