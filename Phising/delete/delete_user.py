"""
Script pour SUPPRIMER un UTILISATEUR spécifique (gestion correcte des contraintes de clés étrangères)
"""

import sys
import os

# Ajouter le dossier parent au path pour pouvoir importer database.db
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_connection


def delete_user_safely(user_id=None, user_email=None):
    """
    Supprimer un utilisateur et TOUTES les données associées
    (events, campaign_targets) dans le bon ordre
    """    
    if not user_id and not user_email:
        print("❌ Doit fournir user_id ou user_email")
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Rechercher l'utilisateur
        if user_id:
            cursor.execute("SELECT user_id, user_email FROM users WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT user_id, user_email FROM users WHERE user_email = ?", (user_email,))
        
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Utilisateur introuvable")
            return False
        
        found_user_id = user[0]
        found_user_email = user[1]
        
        print(f"\n🔍 Utilisateur trouvé:")
        print(f"   ID: {found_user_id}")
        print(f"   Email: {found_user_email}")
        
        # Compter les enregistrements associés
        cursor.execute("SELECT COUNT(*) FROM events WHERE user_id = ?", (found_user_id,))
        events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaign_targets WHERE user_id = ?", (found_user_id,))
        targets_count = cursor.fetchone()[0]
        
        print(f"\n📊 Données associées:")
        print(f"   Événements: {events_count}")
        print(f"   Cibles de campagne: {targets_count}")
        
        # Confirmation
        print(f"\n⚠️  Sera SUPPRIMÉ:")
        print(f"   • {events_count} événements")
        print(f"   • {targets_count} cibles de campagne")
        print(f"   • Utilisateur {found_user_email}")
        
        confirm = input("\nAppuyez sur 'Y' pour CONFIRMER LA SUPPRESSION: ")
        
        if confirm.upper() != 'Y':
            print("\n❌ Annulé")
            return False
        
        print("\n🗑️  Suppression en cours...")
        
        # Supprimer dans l'ordre (sécurisé pour les clés étrangères)
        # 1. Supprimer les événements d'abord
        cursor.execute("DELETE FROM events WHERE user_id = ?", (found_user_id,))
        print(f"   ✅ {events_count} événements supprimés")
        
        # 2. Supprimer campaign_targets
        cursor.execute("DELETE FROM campaign_targets WHERE user_id = ?", (found_user_id,))
        print(f"   ✅ {targets_count} cibles de campagne supprimées")
        
        # 3. Enfin supprimer l'utilisateur
        cursor.execute("DELETE FROM users WHERE user_id = ?", (found_user_id,))
        print(f"   ✅ Utilisateur {found_user_email} supprimé")
        
        conn.commit()
        
        print("\n✨ Terminé! L'utilisateur a été supprimé en toute sécurité.")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def list_all_users():
    """Lister tous les utilisateurs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            u.user_id,
            u.user_email,
            COUNT(DISTINCT ct.campaign_id) as campaigns,
            COUNT(DISTINCT e.id) as events
        FROM users u
        LEFT JOIN campaign_targets ct ON u.user_id = ct.user_id
        LEFT JOIN events e ON u.user_id = e.user_id
        GROUP BY u.user_id, u.user_email
        ORDER BY u.user_id
    """)
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        print("\nℹ️  Aucun utilisateur dans la base de données")
        return
    
    print(f"\n📋 LISTE DES UTILISATEURS ({len(users)} utilisateurs):")
    print("=" * 80)
    print(f"{'ID':<5} {'Email':<40} {'Campagnes':<12} {'Événements':<12}")
    print("=" * 80)
    
    for user in users:
        print(f"{user[0]:<5} {user[1]:<40} {user[2]:<12} {user[3]:<12}")
    
    print("=" * 80)


def delete_multiple_users(user_ids):
    """Supprimer plusieurs utilisateurs en même temps"""
    print(f"\n🗑️  Suppression de {len(user_ids)} utilisateurs...")
    
    success = 0
    failed = 0
    
    for user_id in user_ids:
        print(f"\n--- Suppression de l'utilisateur ID: {user_id} ---")
        if delete_user_safely(user_id=user_id):
            success += 1
        else:
            failed += 1
    
    print(f"\n📊 Résultat:")
    print(f"   ✅ Réussi: {success}")
    print(f"   ❌ Échoué: {failed}")


if __name__ == "__main__":
    print("=" * 80)
    print("🗑️  OUTIL DE SUPPRESSION SÉCURISÉE D'UTILISATEUR")
    print("=" * 80)
    
    # Afficher tous les utilisateurs d'abord
    list_all_users()
    
    print("\n📝 OPTIONS:")
    print("  1 - Supprimer 1 utilisateur par ID")
    print("  2 - Supprimer 1 utilisateur par Email")
    print("  3 - Supprimer plusieurs utilisateurs par IDs")
    print("  0 - Quitter")
    
    choice = input("\nChoisir (0-3): ").strip()
    
    if choice == "1":
        user_id = input("\nEntrer l'ID de l'utilisateur à supprimer: ").strip()
        if user_id.isdigit():
            delete_user_safely(user_id=int(user_id))
        else:
            print("❌ L'ID utilisateur doit être un nombre")
    
    elif choice == "2":
        email = input("\nEntrer l'Email à supprimer: ").strip()
        delete_user_safely(user_email=email)
    
    elif choice == "3":
        ids_str = input("\nEntrer les IDs utilisateurs séparés par des virgules (ex: 1,2,3): ").strip()
        try:
            user_ids = [int(x.strip()) for x in ids_str.split(',')]
            
            # Confirmer avant de supprimer plusieurs
            print(f"\n⚠️  Suppression de {len(user_ids)} utilisateurs: {user_ids}")
            confirm_all = input("Tapez 'OUI' pour confirmer la suppression de TOUS: ")
            
            if confirm_all.upper() == 'OUI':
                delete_multiple_users(user_ids)
            else:
                print("❌ Annulé")
        except ValueError:
            print("❌ Format incorrect. Doit être des nombres séparés par des virgules")
    
    else:
        print("\n❌ Annulé")
