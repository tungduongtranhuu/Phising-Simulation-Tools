"""
Script pour SUPPRIMER une CAMPAGNE spécifique (gestion correcte des contraintes de clés étrangères)
"""

import sys
import os

# Ajouter le dossier parent au path pour pouvoir importer database.db
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_connection


def delete_campaign_safely(campaign_id):
    """
    Supprimer une campagne et TOUTES les données associées
    (events, campaign_targets) dans le bon ordre
    """
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Rechercher la campagne
        cursor.execute("SELECT campaign_id, campaign_name FROM campaigns WHERE campaign_id = ?", (campaign_id,))
        campaign = cursor.fetchone()
        
        if not campaign:
            print(f"❌ Campagne ID {campaign_id} introuvable")
            return False
        
        campaign_name = campaign[1]
        
        print(f"\n🔍 Campagne trouvée:")
        print(f"   ID: {campaign_id}")
        print(f"   Nom: {campaign_name}")
        
        # Compter les enregistrements associés
        cursor.execute("SELECT COUNT(*) FROM events WHERE campaign_id = ?", (campaign_id,))
        events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaign_targets WHERE campaign_id = ?", (campaign_id,))
        targets_count = cursor.fetchone()[0]
        
        print(f"\n📊 Données associées:")
        print(f"   Événements: {events_count}")
        print(f"   Cibles de campagne: {targets_count}")
        
        # Confirmation
        print(f"\n⚠️  Sera SUPPRIMÉ:")
        print(f"   • {events_count} événements")
        print(f"   • {targets_count} cibles de campagne")
        print(f"   • Campagne '{campaign_name}'")
        print(f"\n   ℹ️  Les utilisateurs ne seront PAS supprimés (seulement les liens)")
        
        confirm = input("\nAppuyez sur 'Y' pour CONFIRMER LA SUPPRESSION: ")
        
        if confirm.upper() != 'Y':
            print("\n❌ Annulé")
            return False
        
        print("\n🗑️  Suppression en cours...")
        
        # Supprimer dans l'ordre (sécurisé pour les clés étrangères)
        # 1. Supprimer les événements d'abord
        cursor.execute("DELETE FROM events WHERE campaign_id = ?", (campaign_id,))
        print(f"   ✅ {events_count} événements supprimés")
        
        # 2. Supprimer campaign_targets
        cursor.execute("DELETE FROM campaign_targets WHERE campaign_id = ?", (campaign_id,))
        print(f"   ✅ {targets_count} cibles de campagne supprimées")
        
        # 3. Enfin supprimer la campagne
        cursor.execute("DELETE FROM campaigns WHERE campaign_id = ?", (campaign_id,))
        print(f"   ✅ Campagne '{campaign_name}' supprimée")
        
        conn.commit()
        
        print("\n✨ Terminé! La campagne a été supprimée en toute sécurité.")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def list_all_campaigns():
    """Lister toutes les campagnes"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            c.campaign_id,
            c.campaign_name,
            c.campaign_status,
            COUNT(DISTINCT ct.user_id) as users,
            COUNT(DISTINCT e.id) as events
        FROM campaigns c
        LEFT JOIN campaign_targets ct ON c.campaign_id = ct.campaign_id
        LEFT JOIN events e ON c.campaign_id = e.campaign_id
        GROUP BY c.campaign_id, c.campaign_name, c.campaign_status
        ORDER BY c.campaign_id
    """)
    
    campaigns = cursor.fetchall()
    conn.close()
    
    if not campaigns:
        print("\nℹ️  Aucune campagne dans la base de données")
        return
    
    print(f"\n📋 LISTE DES CAMPAGNES ({len(campaigns)} campagnes):")
    print("=" * 90)
    print(f"{'ID':<5} {'Nom':<30} {'Statut':<12} {'Utilisateurs':<13} {'Événements':<12}")
    print("=" * 90)
    
    for camp in campaigns:
        print(f"{camp[0]:<5} {camp[1]:<30} {camp[2]:<12} {camp[3]:<13} {camp[4]:<12}")
    
    print("=" * 90)


def delete_multiple_campaigns(campaign_ids):
    """Supprimer plusieurs campagnes en même temps"""
    print(f"\n🗑️  Suppression de {len(campaign_ids)} campagnes...")
    
    success = 0
    failed = 0
    
    for campaign_id in campaign_ids:
        print(f"\n--- Suppression de la campagne ID: {campaign_id} ---")
        if delete_campaign_safely(campaign_id):
            success += 1
        else:
            failed += 1
    
    print(f"\n📊 Résultat:")
    print(f"   ✅ Réussi: {success}")
    print(f"   ❌ Échoué: {failed}")


if __name__ == "__main__":
    print("=" * 90)
    print("🗑️  OUTIL DE SUPPRESSION SÉCURISÉE DE CAMPAGNE")
    print("=" * 90)
    
    # Afficher toutes les campagnes d'abord
    list_all_campaigns()
    
    print("\n📝 OPTIONS:")
    print("  1 - Supprimer 1 campagne par ID")
    print("  2 - Supprimer plusieurs campagnes par IDs")
    print("  0 - Quitter")
    
    choice = input("\nChoisir (0-2): ").strip()
    
    if choice == "1":
        campaign_id = input("\nEntrer l'ID de la campagne à supprimer (ex: 36 ou 37): ").strip()
        if campaign_id.isdigit():
            delete_campaign_safely(int(campaign_id))
        else:
            print("❌ L'ID de campagne doit être un nombre")
    
    elif choice == "2":
        ids_str = input("\nEntrer les IDs des campagnes séparés par des virgules (ex: 36,37): ").strip()
        try:
            campaign_ids = [int(x.strip()) for x in ids_str.split(',')]
            
            # Confirmer avant de supprimer plusieurs
            print(f"\n⚠️  Suppression de {len(campaign_ids)} campagnes: {campaign_ids}")
            confirm_all = input("Tapez 'OUI' pour confirmer la suppression de TOUTES: ")
            
            if confirm_all.upper() == 'OUI':
                delete_multiple_campaigns(campaign_ids)
            else:
                print("❌ Annulé")
        except ValueError:
            print("❌ Format incorrect. Doit être des nombres séparés par des virgules")
    
    else:
        print("\n❌ Annulé")
