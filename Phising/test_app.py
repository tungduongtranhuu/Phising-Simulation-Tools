"""
Script de test rapide pour vérifier que l'application fonctionne
Lance des requêtes de test et affiche les résultats
"""

import requests
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(name, url, expected_status, follow_redirects=True):
    """Teste un endpoint et affiche le résultat"""
    try:
        response = requests.get(url, allow_redirects=follow_redirects)
        status = response.status_code
        
        if status == expected_status:
            print(f"✅ {name}: OK (status {status})")
            return True
        else:
            print(f"❌ {name}: ERREUR - attendu {expected_status}, reçu {status}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: ERREUR - Impossible de se connecter")
        print("   → Vérifiez que l'application tourne (python app.py)")
        return False
    except Exception as e:
        print(f"❌ {name}: ERREUR - {e}")
        return False

def main():
    print("🧪 TEST DE L'APPLICATION PHISHING SIMULATOR\n")
    print("=" * 60)
    
    tests = [
        ("Page d'accueil", f"{BASE_URL}/", 200),
        ("Dashboard", f"{BASE_URL}/dashboard", 200),
        ("Création campagne (GET)", f"{BASE_URL}/campaign/create", 200),
        ("Landing page", f"{BASE_URL}/landing", 200),
        ("Tracking sans params", f"{BASE_URL}/track", 200),
        ("Tracking params invalides", f"{BASE_URL}/track?cid=999&uid=999", 200),
    ]
    
    results = []
    for name, url, expected in tests:
        result = test_endpoint(name, url, expected)
        results.append(result)
        print()
    
    print("=" * 60)
    print(f"\nRÉSULTAT : {sum(results)}/{len(results)} tests réussis\n")
    
    if all(results):
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ L'application fonctionne correctement")
        return 0
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("→ Vérifiez les erreurs ci-dessus")
        print("→ Consultez CORRECTIFS.md pour plus d'infos")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
        sys.exit(1)
